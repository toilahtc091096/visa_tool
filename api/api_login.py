import logging

import requests
from utils import build_login_headers
from models import LoginApiResponse
from constants import (
    LOGIN_API_URL,
    BASE_HEADERS
)

logger = logging.getLogger(__name__)


def login(authorization: str, timeout: int = 60) -> LoginApiResponse:
    """Log in and return the fresh API token.

    The homepage request is only used to obtain any cookies set by the site.
    It must not prevent the login API from being attempted: the homepage has
    occasionally been slow while the API endpoint is still available.
    """
    session = requests.Session()

    # Cookie warm-up is optional.  Keep its timeout short so a slow homepage
    # does not abort the actual login request.
    try:
        session.get(
            "https://bio.visaforchina.cn",
            headers=BASE_HEADERS,
            timeout=(10, min(timeout, 15)),
        )
    except requests.RequestException as exc:
        logger.warning("Cookie warm-up failed; continuing with login API: %s", exc)

    referer = (
        "https://bio.visaforchina.cn/onlineWeb/" "personalCenter/visa/historyForms"
    )

    r = session.post(
        LOGIN_API_URL,
        headers=build_login_headers(
            authorization=authorization,
            referer=referer,
        ),
        timeout=(10, timeout),
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

    msg = (getattr(parsed, "raw", None) or {}).get("response", {}).get("message")
    return isinstance(msg, str) and ("token" in msg.casefold())
