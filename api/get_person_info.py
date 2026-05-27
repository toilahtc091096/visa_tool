from typing import Any, Optional
import time

import httpx

from utils import build_upload_headers
from constants import BASE_URL


async def api_get_person_info(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    applyid: str,
    t_ms: Optional[int] = None,
) -> tuple[bool, dict[str, Any]]:
    """POST to ``{base_url}/api/cova-service/Visa/Apply/V1/GetPersonInfo`` (form-urlencoded).

    Returns ``(True, {status_code, response})`` on HTTP 200/201, else
    ``(False, {status_code, error, response})``. Network/parsing errors return
    ``status_code`` -1 and the exception message as ``error``.
    """
    try:
        url = f"{BASE_URL}/GetPersonInfo"

        headers = build_upload_headers(
            token=token,
            tmp_secret=tmp_secret,
        )

        if t_ms is None:
            t_ms = int(time.time() * 1000)

        form = {
            "applyid": applyid,
            "_t": str(t_ms),
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
                "error": "failedGetPersonInfo",
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