import jwt

payload = {
    "sub": "telephony-system"
}

token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")