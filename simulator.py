# simulator.py
import asyncio
import time
from dataclasses import dataclass
import httpx
from llm import generate_call_summary_cot, generate_call_summary_structured
from config import SRM_API_KEY, SRM_BASE_URL
from salesforce_cases import get_sf_connection, create_case, update_case_with_summary, close_case
from logger import get_logger
import asyncio
import time
from logger import get_logger

log = get_logger("simulator")

# Maximum attempts including the first try
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1  # seconds — doubles each attempt




def make_srm_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=SRM_BASE_URL,
        headers={
            "Authorization": f"Bearer {SRM_API_KEY}",
            "Content-Type":  "application/json",
            "X-Service-Name": "cti-event-handler",
        },
        timeout=30,
    )


@dataclass
class CallContext:
    call_id:    str
    queue:      str
    phone:      str
    agent_id:   str
    agent_name: str
    skills:     list
    start_time: float = 0.0


async def fetch_call_metadata(client, call_id):
    log.info(f"fetch_call_metadata | call_id={call_id} | starting")
    r = await client.post(
        "https://httpbin.org/post",
        json={"call_id": call_id, "source": "telephony"}
    )
    log.info(f"fetch_call_metadata | call_id={call_id} | status={r.status_code}")
    return {"queue": "billing_support", "phone": "+1-800-555-0192"}


async def fetch_agent_profile(client, agent_id):
    log.info(f"fetch_agent_profile | agent_id={agent_id} | starting")
    r = await client.post(
        "https://httpbin.org/post",
        json={"agent_id": agent_id, "source": "workforce_mgmt"}
    )
    log.info(f"fetch_agent_profile | agent_id={agent_id} | status={r.status_code}")
    return {"name": "Priya Sharma", "skills": ["billing", "retention"]}


async def on_call_started(call_id: str, agent_id: str) -> CallContext:
    log.info(f"on_call_started | call_id={call_id} | agent_id={agent_id} | event=call_started")
    start = time.time()

    async with httpx.AsyncClient(timeout=30) as client:
        meta, agent = await asyncio.gather(
            fetch_call_metadata(client, call_id),
            fetch_agent_profile(client, agent_id)
        )

    ctx = CallContext(
        call_id=call_id,
        queue=meta["queue"],
        phone=meta["phone"],
        agent_id=agent_id,
        agent_name=agent["name"],
        skills=agent["skills"],
        start_time=start
    )
    elapsed = round(time.time() - start, 2)
    log.info(f"on_call_started | call_id={call_id} | context_built | elapsed={elapsed}s | agent={ctx.agent_name} | queue={ctx.queue}")
    return ctx



# simulator.py — update post_summary_to_srm signature
async def post_summary_to_srm(
    client: httpx.AsyncClient,
    ctx: CallContext,
    ai_summary: dict = None        # ← new parameter
) -> int:
    log.info(f"post_summary_to_srm | call_id={ctx.call_id} | agent_id={ctx.agent_id} | starting")
    duration = round(time.time() - ctx.start_time, 1)

    # Use AI summary if provided, fallback to default
    if ai_summary:
        summary_text    = ai_summary.get("issue", "No summary available")
        resolution_text = ai_summary.get("resolution", "")
        nba_text        = ai_summary.get("next_best_action", "")
        sentiment       = ai_summary.get("sentiment", "neutral")
        escalation      = ai_summary.get("escalation_required", False)
    else:
        summary_text    = "Customer queried billing discrepancy. Agent applied retention offer. Resolved."
        resolution_text = ""
        nba_text        = ""
        sentiment       = "neutral"
        escalation      = False

    payload = {
        "call_id":            ctx.call_id,
        "agent_id":           ctx.agent_id,
        "agent_name":         ctx.agent_name,
        "queue":              ctx.queue,
        "duration_s":         duration,
        "summary":            summary_text,
        "resolution":         resolution_text,
        "next_best_action":   nba_text,
        "sentiment":          sentiment,
        "escalation_required": escalation
    }

    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(f"post_summary_to_srm | call_id={ctx.call_id} | attempt={attempt}/{MAX_RETRIES} | posting")
            r = await client.post("/post", json=payload)
            if r.status_code >= 500:
                raise ValueError(f"SRM returned {r.status_code}")
            echo = r.json()["json"]
            log.info(f"post_summary_to_srm | call_id={ctx.call_id} | status={r.status_code} | confirmed_id={echo['call_id']} | sentiment={sentiment} | escalation={escalation}")
            return r.status_code
        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                log.warning(f"post_summary_to_srm | call_id={ctx.call_id} | attempt={attempt} | FAILED | error={e} | retry_in={delay}s")
                await asyncio.sleep(delay)
            else:
                log.error(f"post_summary_to_srm | call_id={ctx.call_id} | attempt={attempt} | EXHAUSTED | sending_to_dead_letter")

    raise RuntimeError(f"SRM post failed after {MAX_RETRIES} attempts for call_id={ctx.call_id}") from last_exception

async def post_summary_to_salesforce(ctx: CallContext, ai_summary: dict) -> str:
    """Creates a Salesforce Case and updates it with AI summary. Returns Case ID."""
    import asyncio
    log.info(f"post_summary_to_salesforce | call_id={ctx.call_id} | starting")

    # Run synchronous Salesforce calls in thread pool
    # simple_salesforce is sync — asyncio.to_thread prevents blocking
    loop = asyncio.get_event_loop()

    sf = await loop.run_in_executor(None, get_sf_connection)

    # Create a new Case for this call
    subject = ai_summary.get("issue", f"Call {ctx.call_id}")[:80]
    description = f"Call ID: {ctx.call_id} | Agent: {ctx.agent_name} | Queue: {ctx.queue}"

    case_id = await loop.run_in_executor(
        None, create_case, sf, subject, description,
        "High" if ai_summary.get("escalation_required") else "Medium"
    )
    log.info(f"post_summary_to_salesforce | call_id={ctx.call_id} | case_created={case_id}")

    # Update Case with full AI summary
    await loop.run_in_executor(
        None, update_case_with_summary, sf, case_id, ai_summary, ctx.call_id
    )
    log.info(f"post_summary_to_salesforce | call_id={ctx.call_id} | summary_written | escalation={ai_summary.get('escalation_required')}")

    return case_id


async def trigger_acw(client: httpx.AsyncClient, ctx: CallContext):
    log.info(f"trigger_acw | call_id={ctx.call_id} | agent_id={ctx.agent_id} | starting")
    payload = {
        "call_id":  ctx.call_id,
        "agent_id": ctx.agent_id,
        "skills":   ctx.skills,
        "acw_type": "wrap_and_disposition",
    }
    r = await client.post("/post", json=payload)
    log.info(f"trigger_acw | call_id={ctx.call_id} | status={r.status_code}")
    return r.status_code


# Add at top of simulator.py — shared dead letter store
# In production this is Redis or SQS — for now in-memory
dead_letter_store: list[dict] = []

async def trigger_acw_async(ctx: CallContext) -> int:
    """Triggers ACW — posts to workforce management system."""
    log.info(f"trigger_acw | call_id={ctx.call_id} | agent_id={ctx.agent_id} | starting")
    async with make_srm_client() as client:
        payload = {
            "call_id":  ctx.call_id,
            "agent_id": ctx.agent_id,
            "skills":   ctx.skills,
            "acw_type": "wrap_and_disposition",
        }
        r = await client.post("/post", json=payload)
        log.info(f"trigger_acw | call_id={ctx.call_id} | status={r.status_code}")
        return r.status_code

async def on_call_ended(ctx: CallContext, transcript: str = None):
    log.info(f"on_call_ended | call_id={ctx.call_id} | event=call_ended | starting")
    start = time.time()

    # Step 1 — LLM inference
    ai_summary = None
    if transcript:
        try:
            log.info(f"on_call_ended | call_id={ctx.call_id} | running LLM inference")
            ai_summary = await generate_call_summary_cot(transcript)
            log.info(f"on_call_ended | call_id={ctx.call_id} | llm_complete | sentiment={ai_summary['sentiment']} | escalation={ai_summary['escalation_required']}")
        except Exception as e:
            log.error(f"on_call_ended | call_id={ctx.call_id} | llm_failed | error={e}")
            ai_summary = None

    # Step 2 — post to Salesforce + trigger ACW concurrently
    salesforce_task = post_summary_to_salesforce(ctx, ai_summary) if ai_summary else None
    acw_task = trigger_acw_async(ctx)

    if salesforce_task:
        results = await asyncio.gather(
            salesforce_task,
            acw_task,
            return_exceptions=True
        )
        sf_result, acw_result = results

        if isinstance(sf_result, Exception):
            log.error(f"on_call_ended | call_id={ctx.call_id} | salesforce=FAILED | error={sf_result}")
            dead_letter_store.append({
                "call_id":   ctx.call_id,
                "agent_id":  ctx.agent_id,
                "queue":     ctx.queue,
                "failed_at": time.time(),
                "reason":    str(sf_result)
            })
            log.warning(f"on_call_ended | call_id={ctx.call_id} | dead_letter | total_failed={len(dead_letter_store)}")
        else:
            log.info(f"on_call_ended | call_id={ctx.call_id} | salesforce=OK | case_id={sf_result}")

        if isinstance(acw_result, Exception):
            log.error(f"on_call_ended | call_id={ctx.call_id} | acw=FAILED | error={acw_result}")
        else:
            log.info(f"on_call_ended | call_id={ctx.call_id} | acw=OK")
    else:
        await acw_task
        log.warning(f"on_call_ended | call_id={ctx.call_id} | no_transcript | skipped_salesforce")

    # Step 3 — escalation flag
    if ai_summary and ai_summary.get("escalation_required"):
        log.warning(f"on_call_ended | call_id={ctx.call_id} | ESCALATION_REQUIRED | nba={ai_summary.get('next_best_action', '')[:80]}")

    elapsed = round(time.time() - start, 2)
    log.info(f"on_call_ended | call_id={ctx.call_id} | complete | elapsed={elapsed}s")


