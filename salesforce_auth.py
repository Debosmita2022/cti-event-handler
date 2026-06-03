# salesforce_auth.py
import time
import jwt
import httpx
from config import (
    SALESFORCE_CLIENT_ID,
    SALESFORCE_USERNAME,
    SALESFORCE_INSTANCE_URL,
    SALESFORCE_PRIVATE_KEY_PATH
)
from logger import get_logger

log = get_logger("salesforce_auth")

def _load_private_key() -> str:
    with open(SALESFORCE_PRIVATE_KEY_PATH, "r") as f:
        return f.read()

def _build_jwt() -> str:
    private_key = _load_private_key()
    now = int(time.time())
    log.info(f"CLIENT_ID={SALESFORCE_CLIENT_ID[:15]}...")
    payload = {
        "iss": SALESFORCE_CLIENT_ID,       # Connected App Consumer Key
        "sub": SALESFORCE_USERNAME,         # your SF username
        "aud": "https://orgfarm-bfae04a307-dev-ed.develop.my.salesforce.com",
        "exp": now + 300                    # 5 minute expiry
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")
    log.info(f"build_jwt | sub={SALESFORCE_USERNAME} | exp_in=300s")
    return token

async def get_salesforce_token() -> dict:
    jwt_token = _build_jwt()
    log.info(f"get_salesforce_token | requesting access token")

    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://orgfarm-bfae04a307-dev-ed.develop.my.salesforce.com/services/oauth2/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion":  jwt_token
            }
        )

    if r.status_code != 200:
        log.error(f"get_salesforce_token | FAILED | status={r.status_code} | body={r.text[:200]}")
        raise RuntimeError(f"Salesforce token request failed: {r.text}")

    data = r.json()
    log.info(f"get_salesforce_token | SUCCESS | instance_url={data.get('instance_url')}")
    return {
        "access_token":  data["access_token"],
        "instance_url":  data["instance_url"]
    }