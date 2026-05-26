from dataclasses import asdict
from typing import Any

import httpx

from utils import build_upload_headers

from constants import (
    BASE_URL
)

async def api_get_work_info(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    applyid: str,
) -> tuple[bool, dict[str, Any]]:
    """POST to ``{base_url}/api/cova-service/Visa/Apply/V1/GetWorkInfo`` (form-urlencoded).

    Returns ``(True, {status_code, response})`` on HTTP 200/201, else
    ``(False, {status_code, error})``. Network/parsing errors return
    ``status_code`` -1 and the exception message as ``error``.
    """
    try:
        url = f"{BASE_URL}/GetWorkInfo"

        headers = build_upload_headers(
            token=token,
            tmp_secret=tmp_secret,
        )

        form = {
            "applyid": applyid,
        }

        resp = await client.post(url, headers=headers, data=form)

        data = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )

        ok = resp.status_code in (200, 201)
        if not ok:
            return False, {
                "status_code": resp.status_code,
                "error": "failedGetWorkInfo",
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