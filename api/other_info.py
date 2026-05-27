from dataclasses import asdict
from typing import Any

import httpx

from models import OtherInformationProfile
from utils import build_upload_headers

from constants import (
    BASE_URL
)


async def api_save_other_info(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    body: OtherInformationProfile,
) -> tuple[bool, dict[str, Any]]:
    """
    POST ``OtherInformationProfile`` to
    ``{BASE_URL}/SaveOtherInfo``.

    Returns:
        (True, response_data)
        (False, error_data)
    """

    try:
        url = f"{BASE_URL}/SaveOtherInfo"

        headers = build_upload_headers(
            token=token,
            tmp_secret=tmp_secret,
        )

        payload = asdict(body)

        resp = await client.post(
            url,
            headers=headers,
            json=payload,
        )

        data = (
            resp.json()
            if resp.headers.get(
                "content-type", ""
            ).startswith("application/json")
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