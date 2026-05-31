from dataclasses import asdict, is_dataclass
from typing import Any

import httpx

from models import PersonInfoProfile
from utils import build_get_draft_headers
from constants import (
    BASE_URL
)


async def api_save_person_info(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    body: PersonInfoProfile,
) -> tuple[bool, dict[str, Any]]:
    url = f"{BASE_URL}/SavePersonInfo"  # Ä‘á»•i path cho Ä‘Ãºng API cá»§a báº¡n
    headers = build_get_draft_headers(token, tmp_secret)
    if is_dataclass(body):
        payload = asdict(body)
    elif isinstance(body, dict):
        payload = body
    else:
        raise TypeError(
            f"body must be dataclass instance or dict, got {type(body)!r}"
        )
    try:
        resp = await client.post(url, headers=headers, json=payload)
        data = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )
        ok = resp.status_code in (200, 201)
        if ok:
            return ok, {
                "status_code": resp.status_code,
                "response": data,
                "request": {
                    "url": url,
                    "headers": {"Authorization": "Bearer ***", "X-Tmp-Secret": "***"},
                    "json": payload,
                },
            }
        return False, {
            "status_code": resp.status_code,
            "response": data,
            "request": {
                "url": url,
                "headers": {"Authorization": "Bearer ***", "X-Tmp-Secret": "***"},
                "json": payload,
            },
        }
    except Exception as e:
        return False, {
            "status_code": None,
            "error": repr(e),
            "request": {
                "url": url,
                "headers": {"Authorization": "Bearer ***", "X-Tmp-Secret": "***"},
                "json": payload,
            },
        }
