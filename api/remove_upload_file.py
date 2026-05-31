from typing import Any

import httpx

from constants import BASE_STATE_URL
from utils import build_upload_headers


async def api_remove_upload_file(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    category_code: str,
    material_code: str,
    business_id: str,
) -> tuple[bool, dict[str, Any]]:
    try:
        url = f"{BASE_STATE_URL}/RemoveApMaterial"
        headers = build_upload_headers(token, tmp_secret)
        files = {
            "categoryCode": (None, category_code),
            "materialCode": (None, material_code),
            "businessId": (None, business_id),
        }
        resp = await client.post(url, headers=headers, files=files)
        data = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            return False, {
                "status_code": resp.status_code,
                "error": "failedRemoveApMaterial",
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
