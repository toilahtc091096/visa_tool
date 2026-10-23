from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from api.api_login import login
from api.get_list_old_by_visa_number import api_list_online_applications
from utils.token_store import load_authorization, load_login_payload, save_login_data


_TOKEN_ERROR_HINTS = ("token", "unauthorized", "login", "登录", "过期", "失效")


def load_canary_passports() -> list[str]:
    """Số HC chắc chắn có trên tài khoản đang dùng (mỗi file .env một tài khoản)."""
    raw_value = os.getenv("TRACKER_TOKEN_CANARY_PASSPORTS", "")
    return [
        item.strip().upper()
        for item in raw_value.replace(";", ",").split(",")
        if item.strip()
    ]


def describe_token_error(response: Any) -> str:
    """Trả về lý do nếu response của API list cho thấy token không dùng được."""
    if not isinstance(response, dict):
        return "unexpected_response"

    message = str(response.get("msg") or response.get("message") or "").strip()
    code = response.get("code")
    if code not in (None, "", 200, "200"):
        return f"code={code} msg={message}".strip()
    if any(hint in message.casefold() for hint in _TOKEN_ERROR_HINTS):
        return message
    return ""


async def _probe_list_api(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    authorization: str,
    canary_passports: list[str],
) -> str:
    """Gọi API list một lần; trả về lý do lỗi, hoặc chuỗi rỗng nếu token còn sống."""
    passport_no = canary_passports[0] if canary_passports else ""
    ok, remote = await api_list_online_applications(
        client=client,
        token=token,
        tmp_secret=tmp_secret,
        passportNo=passport_no,
        pageNum=1,
        pageSize=10,
        authorization=authorization or None,
    )
    if not ok:
        return f"http_{remote.get('status_code')} {remote.get('error', '')}".strip()

    response = remote.get("response") or {}
    reason = describe_token_error(response)
    if reason:
        return reason

    if passport_no:
        rows = response.get("rows") if isinstance(response, dict) else None
        if not rows:
            return f"canary_passport_not_found passport={passport_no}"
    return ""


async def _relogin(authorization: str) -> str:
    try:
        login_response = await asyncio.to_thread(login, authorization)
    except Exception as exc:
        return f"login_failed {type(exc).__name__}: {exc}"

    if login_response.code not in (0, 200) or login_response.data is None:
        return f"login_failed code={login_response.code} msg={login_response.msg}"
    if not login_response.data.token or not login_response.data.tmpSecret:
        return "login_failed missing token/tmpSecret"

    save_login_data(login_response.data)
    return ""


async def check_token_alive(
    client: httpx.AsyncClient,
    authorization: str = "",
    force_relogin: bool = False,
) -> dict[str, Any]:
    """Kiểm tra token còn gọi được API list hay không.

    1. Thử token/tmpSecret đang lưu (trừ khi ``force_relogin``).
    2. Nếu hỏng thì login lại bằng ``authorization`` rồi thử lần nữa.
    """
    canary_passports = load_canary_passports()
    auth = authorization.strip() or load_authorization()

    reason = ""
    if not force_relogin:
        payload = load_login_payload()
        token = str(payload.get("token", "") or "").strip()
        tmp_secret = str(payload.get("tmpSecret", "") or "").strip()
        if token and tmp_secret:
            reason = await _probe_list_api(
                client, token, tmp_secret, auth, canary_passports
            )
            if not reason:
                return {"ok": True, "relogged_in": False, "reason": ""}
        else:
            reason = "missing_token_or_tmpSecret"

    if not auth:
        return {"ok": False, "relogged_in": False, "reason": reason or "missing_authorization"}

    login_error = await _relogin(auth)
    if login_error:
        return {"ok": False, "relogged_in": False, "reason": login_error}

    payload = load_login_payload()
    reason = await _probe_list_api(
        client,
        str(payload.get("token", "") or "").strip(),
        str(payload.get("tmpSecret", "") or "").strip(),
        auth,
        canary_passports,
    )
    return {"ok": not reason, "relogged_in": True, "reason": reason}
