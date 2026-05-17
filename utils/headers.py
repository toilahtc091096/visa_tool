from typing import Dict

from constants import (
    DEFAULT_EMAIL,
    DEFAULT_GUID,
    DEFAULT_UID,
    ORIGIN,
    PLT,
    REFERER,
    SEC_CH_UA,
    USER_AGENT,
)


def build_headers(access_token: str, tmp_secret: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Tmp-Secret": tmp_secret,
        "Content-Type": "application/json",
        "Accept": "application/json",
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
        'sec-ch-ua-platform': '"Windows"',
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
        "email": email,
        "guid": guid,
        "origin": ORIGIN,
        "plt": PLT,
        "priority": "u=1, i",
        "referer": REFERER,
        "sec-ch-ua": SEC_CH_UA,
        "sec-ch-ua-mobile": "?0",
        'sec-ch-ua-platform': '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "tmp_secret": tmp_secret,
        "token": token,
        "uid": DEFAULT_UID,
        "user-agent": user_agent,
    }
