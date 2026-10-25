import re
from fastapi import Header, HTTPException
from .config import APP_KEYS, MAX_INPUT, SECURITY

async def identity(x_api_key: str | None = Header(default=None)):
    if not x_api_key or x_api_key not in APP_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return {"key":x_api_key, **APP_KEYS[x_api_key]}

def require_role(user, *roles):
    if user["role"] not in roles:
        raise HTTPException(status_code=403, detail="Role is not permitted for this operation")

def validate_text(text, field="input"):
    if not isinstance(text,str) or not text.strip():
        raise HTTPException(status_code=422, detail=f"{field} must be a non-empty string")
    if len(text)>MAX_INPUT:
        raise HTTPException(status_code=413, detail=f"{field} exceeds configured size limit")

def injection_signals(text):
    lowered=text.casefold()
    return [signal for signal in SECURITY["injection_signals"] if signal.casefold() in lowered]

def output_is_safe(text):
    return isinstance(text,str) and len(text)<=MAX_INPUT*2 and not re.search(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----", text)
