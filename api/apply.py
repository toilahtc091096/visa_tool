from dataclasses import asdict
from typing import Any

import httpx

from models import ApplyInfoProfile
from utils import build_upload_headers

from constants import (
    BASE_URL
)
async def api_save_apply_info(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    body: ApplyInfoProfile,
) -> tuple[bool, dict[str, Any]]:
    """POST ``ApplyInfoProfile`` to ``{base_url}/SaveApplyInfo``.

    Returns ``(True, {status_code, response})`` on HTTP 200/201, else
    ``(False, {status_code, error})``. Network/parsing errors return
    ``status_code`` -1 and the exception message as ``error``.
    """
    try:
        url = f"{BASE_URL}/SaveApplyInfo"
        headers = build_upload_headers(token, tmp_secret)
        payload = asdict(body)

        resp = await client.post(url, headers=headers, json=payload)
        data = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            return False, {
                "status_code": resp.status_code,
                "error": "failedSaveApplyInfo",
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
