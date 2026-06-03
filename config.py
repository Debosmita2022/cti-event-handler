import os
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    """Read env var — crash loudly at startup if missing."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Required env var '{key}' is not set")
    return value

# All credentials in one place
CTI_API_KEY  = _require("CTI_API_KEY")
SRM_API_KEY  = _require("SRM_API_KEY")
SRM_BASE_URL = _require("SRM_BASE_URL")
JWT_SECRET        = _require("JWT_SECRET")
JWT_ALGORITHM     = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
OPENAI_API_KEY = _require("OPENAI_API_KEY")
SALESFORCE_CLIENT_ID    = _require("SALESFORCE_CLIENT_ID")
SALESFORCE_USERNAME     = _require("SALESFORCE_USERNAME")
SALESFORCE_INSTANCE_URL = _require("SALESFORCE_INSTANCE_URL")
SALESFORCE_PRIVATE_KEY_PATH = _require("SALESFORCE_PRIVATE_KEY_PATH")