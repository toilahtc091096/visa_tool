from dataclasses import asdict
from typing import Any, Dict, Tuple

import httpx

from models import GetDraftListBody, GetDraftListResult
from utils import build_get_draft_headers

from constants import (
    BASE_URL
)

async def api_get_draft(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    body: GetDraftListBody,
) -> Tuple[bool, Dict[str, Any]]:
    url = f"{BASE_URL}/GetDraftList"
    headers = build_get_draft_headers(token, tmp_secret)
    payload = asdict(body)

    try:
        resp = await client.post(url, headers=headers, json=payload)
        data = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )

        ok = resp.status_code in (200, 201)
        result = GetDraftListResult.from_dict(data) if ok else None

        return ok, {
            "status_code": resp.status_code,
            "response": asdict(result) if result is not None else data,
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
 