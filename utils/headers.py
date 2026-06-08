from typing import Dict
import requests

from constants import (
    DEFAULT_EMAIL,
    DEFAULT_GUID,
    DEFAULT_UID,
    ORIGIN,
    PLT,
    REFERER,
    SEC_CH_UA,
    USER_AGENT,
    NORMAL_ACCEPT,
    DEFAULT_VI_LANGUAGE,
    LOGIN_DEFAULT_ORIGIN,
    BASE_HEADERS
)


DEFAULT_UPLOAD_AUTHORIZATION = (
    "eyJhbGciOiJIUzUxMiJ9.eyJ3ZWJzaXRlX2xvZ2luX3VzZXJfa2V5IjoiOTc0ODNhMGMtNzU1YS00MjMzLWE2MmEtMmU1ODM0MzEzMzAyIn0.AXLhc5AC0pUxdu-IgUT1Mes3cBfcqExmnFqeAfOyphaFnJeJMlxbKIvb8cbAqac5rlqW-Ok35uIcWl60fxAI8w"
)


def build_login_headers(
    authorization: str,
    referer: str,
) -> Dict[str, str]:
    return {
        **BASE_HEADERS,
        "Authorization": authorization,
        "Referer": referer,
    }


def build_get_draft_headers(
    token: str,
    tmp_secret: str,
    email: str = DEFAULT_EMAIL,
    guid: str = DEFAULT_GUID,
    user_agent: str = USER_AGENT,
) -> Dict[str, str]:
    """
    Headers matching your Postman/cURL sample as close as possible.
    Note: sample has both 'access_token' and 'token' with same value.
    """
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en_US",
        "content-type": "application/json",
        "email": email,
        "guid": guid,
        "origin": ORIGIN,
        "plt": PLT,
        "priority": "u=1, i",
        "referer": REFERER,
        "sec-ch-ua": SEC_CH_UA,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "tmp_secret": tmp_secret,
        "token": token,
        "uid": DEFAULT_UID,
        "user-agent": user_agent,
    }


def build_upload_headers(
    token: str,
    tmp_secret: str,
    authorization: str | None = None,
    email: str = DEFAULT_EMAIL,
    guid: str = DEFAULT_GUID,
    user_agent: str = USER_AGENT,
) -> Dict[str, str]:
    """
    Headers matching your Postman/cURL sample as close as possible.
    Note: sample has both 'access_token' and 'token' with same value.
    """
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en_US",
        "email": email,
        "guid": guid,
        "origin": ORIGIN,
        "plt": PLT,
        "priority": "u=1, i",
        "referer": REFERER,
        "sec-ch-ua": SEC_CH_UA,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "tmp_secret": tmp_secret,
        "token": token,
        "uid": DEFAULT_UID,
        "user-agent": user_agent,
    }

    headers["authorization"] = authorization or DEFAULT_UPLOAD_AUTHORIZATION
    return headers
