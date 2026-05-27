from dataclasses import asdict
from typing import Any

import httpx

from models import TravelInfoProfile
from utils import build_upload_headers

from constants import (
    BASE_URL
)



async def api_save_travel_info(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    body: TravelInfoProfile,
) -> tuple[bool, dict[str, Any]]:
    """POST ``TravelInfoProfile`` to ``{base_url}/SaveTravelInfo``.

    Returns ``(True, {status_code, response})`` on HTTP 200/201, else
    ``(False, {status_code, error})``. Network/parsing errors return
    ``status_code`` -1 and the exception message as ``error``.
    """
    try:
        url = f"{BASE_URL}/SaveTravelInfo"
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
                "error": data,
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