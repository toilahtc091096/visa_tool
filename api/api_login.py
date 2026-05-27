import requests
from typing import Optional, Dict, Any
from utils import build_login_headers
from models import LoginApiResponse
from constants import (
    LOGIN_API_URL,
)

URL = LOGIN_API_URL


def login(authorization: str, timeout: int = 30) -> LoginApiResponse:
    r = requests.post(
        URL, headers=build_login_headers(authorization), timeout=timeout
    )
    r.raise_for_status()
    return LoginApiResponse.from_dict(r.json())

def needs_relogin(parsed) -> bool:
    """
    Decide if we should re-login based on presence of 'token' in any message field.
    Safe against missing keys / None.
    """
    if getattr(parsed, "message_includes", None) and parsed.message_includes("token"):
        return True

    msg = (
        (getattr(parsed, "raw", None) or {})
        .get("response", {})
        .get("message")
    )
    return isinstance(msg, str) and ("token" in msg.casefold())

 