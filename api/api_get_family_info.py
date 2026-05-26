from dataclasses import asdict
from typing import Any

import httpx

from utils import build_upload_headers

from constants import BASE_URL


async def api_get_family_info(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    applyid: str,
) -> tuple[bool, dict[str, Any]]:
    """POST to ``{base_url}/api/cova-service/Visa/Apply/V1/GetFamilyInfo`` (x-www-form-urlencoded)."""
    try:
        url = f"{BASE_URL}/GetFamilyInfo"
        headers = build_upload_headers(token,tmp_secret)

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
                "error": "failedGetFamilyInfo",
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