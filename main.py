#1. imports
import httpx
from config import SRM_BASE_URL
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from datetime import datetime
from simulator import on_call_started, on_call_ended, CallContext
from fastapi import FastAPI, BackgroundTasks, HTTPException, Security, Depends
from auth import create_token, verify_jwt
from config import CTI_API_KEY, JWT_EXPIRE_MINUTES
from fastapi import Form
from logger import get_logger
from simulator import dead_letter_store

log = get_logger("api")


# 2. app instance
app = FastAPI(title="CTI Event Handler")

# 3. call store
call_store: dict[str, CallContext] = {}

# 4. API key setup — MUST come before any route that uses it
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: str = Security(api_key_header)) -> str:
    if not key or key != CTI_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key"
        )
    return key




@app.get("/health")
async def health():
    # Actively check if SRM is reachable
    srm_healthy = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{SRM_BASE_URL}/get")
            srm_healthy = r.status_code == 200
    except Exception:
        srm_healthy = False

    status = "healthy" if srm_healthy else "degraded"
    dead_letter_count = len(dead_letter_store)

    if not srm_healthy:
        log.warning(f"health | status=degraded | srm=unreachable")
    else:
        log.info(f"health | status=healthy | srm=reachable | dead_letters={dead_letter_count}")

    return {
        "status":          status,
        "srm_reachable":   srm_healthy,
        "dead_letters":    dead_letter_count,
        "active_calls":    len(call_store)
    }

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int


class CallStartedEvent(BaseModel):
    call_id: str = Field(..., example="CALL-20250513-001")
    agent_id: str = Field(..., example="AGT-447")
    queue: str = Field(..., example="billing_support")
    phone: str = Field(..., example="+1-800-555-0192")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EventAccepted(BaseModel):
    accepted: bool
    call_id: str
    message: str


class CallEndedEvent(BaseModel):
    call_id: str = Field(..., example="CALL-20250513-001")
    transcript: str = Field(
        default="Agent resolved customer billing query. Customer satisfied.",
        example="Agent: How can I help? Customer: I have a billing question..."
    )

# simulated client registry
KNOWN_CLIENTS = {
    "telephony-system": "their-secret"
}

@app.post("/token", response_model=TokenResponse)
async def issue_token(
    grant_type:    str = Form(...),
    client_id:     str = Form(...),
    client_secret: str = Form(...),
    scope:         str = Form(default="cti:publish")
):
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported grant_type: {grant_type}"
        )
    expected = KNOWN_CLIENTS.get(client_id)
    if not expected or expected != client_secret:
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    token = create_token(subject=client_id, role=scope)
    return TokenResponse(
        access_token=token,
        expires_in=JWT_EXPIRE_MINUTES * 60
    )

async def run_call_started_pipeline(call_id: str, agent_id: str):
    ctx = await on_call_started(call_id, agent_id)
    call_store[call_id] = ctx
    log.info(f"run_call_started_pipeline | call_id={call_id} | context_stored")


async def run_call_ended_pipeline(ctx: CallContext, transcript: str = None):
    await on_call_ended(ctx, transcript)
    del call_store[ctx.call_id]
    log.info(f"run_call_ended_pipeline | call_id={ctx.call_id} | context_removed")


@app.post("/call/started", response_model=EventAccepted, status_code=202)
async def call_started(
    event: CallStartedEvent,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_api_key),
):
    log.info(f"call_started | call_id={event.call_id} | agent_id={event.agent_id}")
    background_tasks.add_task(
        run_call_started_pipeline,
        event.call_id,
        event.agent_id,
    )
    return EventAccepted(
        accepted=True,
        call_id=event.call_id,
        message=f"pipeline started for agent {event.agent_id}",
    )


# update /calls to require JWT
@app.get("/calls")
async def list_calls(claims: dict = Security(verify_jwt)):
    log.info(f"list_calls | caller={claims['sub']} | role={claims['role']}")
    return {
        "active_calls": list(call_store.keys()),
        "requested_by": claims["sub"]
    }


@app.post("/call/ended", response_model=EventAccepted, status_code=202)
async def call_ended(
    event: CallEndedEvent,
    background_tasks: BackgroundTasks,
    _: str = Security(verify_api_key),
):
    log.info(f"call_ended | call_id={event.call_id}")
    ctx = call_store.get(event.call_id)
    if not ctx:
        raise HTTPException(
            status_code=404,
            detail=f"No active call found for {event.call_id} — was call_started received?"
        )
    background_tasks.add_task(
        run_call_ended_pipeline,
        ctx,
        event.transcript    # ← pass transcript to pipeline
    )
    return EventAccepted(
        accepted=True,
        call_id=event.call_id,
        message=f"call_ended pipeline started for {event.call_id}"
    )

    
@app.get("/dead-letters")
async def list_dead_letters(_: str = Security(verify_api_key)):
    return {
        "count": len(dead_letter_store),
        "items": dead_letter_store
    }
