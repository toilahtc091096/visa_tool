from __future__ import annotations

import asyncio
from typing import Any

import httpx

from api.api_login import login
from constants import CHECK_OLD_LIST_BASE_URL
from utils import build_upload_headers
from utils.token_store import load_login_payload, save_login_data


async def api_list_online_applications(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    passportNo: str,
    pageNum: int = 1,
    pageSize: int = 10,
    authorization: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    """POST to ``{base_url}/application/online/list?pageNum=&pageSize=``.

    Returns ``(True, {status_code, response})`` on HTTP 200/201, else
    ``(False, {status_code, error})``. Network/parsing errors return
    ``status_code`` -1 and the exception message as ``error``.
    """
    try:
        url = f"{CHECK_OLD_LIST_BASE_URL}/application/online/list"
        params = {"pageNum": pageNum, "pageSize": pageSize}
        headers = build_upload_headers(token, tmp_secret, authorization=authorization)
        payload = {"passportNo": passportNo}
        resp = await client.post(url, params=params, headers=headers, json=payload)
        data = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            return False, {
                "status_code": resp.status_code,
                "error": "failedListOnlineApplications",
                "response": data,
            }
        return True, {
            "status_code": resp.status_code,
            "response": data,
        }

    except Exception as e:
        return False, {
            "status_code": -1,
            "error": str(e),
        }


api_get_online_application_list_by_passport = api_list_online_applications


async def api_get_list_by_han_code(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    han_code: str,
    pageNum: int = 1,
    pageSize: int = 10,
    authorization: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    """POST to ``{base_url}/application/online/list?pageNum=&pageSize=`` using ``applicationNo``."""
    try:
        token = str(token or "").strip()
        tmp_secret = str(tmp_secret or "").strip()
        auth = str(authorization or "").strip()

        if not token or not tmp_secret:
            if not auth:
                return False, {
                    "status_code": -1,
                    "error": "missing_token_tmpSecret_and_authorization",
                }

            login_response = await asyncio.to_thread(login, auth)
            if login_response.data is None:
                return False, {
                    "status_code": -1,
                    "error": "login_returned_empty_data",
                }

            save_login_data(login_response.data)
            payload = load_login_payload()
            token = str(payload.get("token", "") or "").strip()
            tmp_secret = str(payload.get("tmpSecret", "") or "").strip()

            if not token or not tmp_secret:
                return False, {
                    "status_code": -1,
                    "error": "missing_token_or_tmpSecret_after_login",
                }

        url = f"{CHECK_OLD_LIST_BASE_URL}/application/online/list"
        params = {"pageNum": pageNum, "pageSize": pageSize}
        headers = build_upload_headers(token, tmp_secret, authorization=authorization)
        payload = {"applicationNo": str(han_code).strip()}
        resp = await client.post(url, params=params, headers=headers, json=payload)
        data = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            return False, {
                "status_code": resp.status_code,
                "error": "failedListByHanCode",
                "response": data,
            }
        return True, {
            "status_code": resp.status_code,
            "response": data,
        }

    except Exception as e:
        return False, {
            "status_code": -1,
            "error": str(e),
        }


api_get_list_by_han_code = api_get_list_by_han_code
