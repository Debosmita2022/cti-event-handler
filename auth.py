# auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

bearer_scheme = HTTPBearer(auto_error=False)

def create_token(subject: str, role: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return decode_token(credentials.credentials)