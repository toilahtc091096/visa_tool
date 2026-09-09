import os
from typing import Any

import httpx

from utils import build_upload_headers
from constants import (
    BASE_URL
)


async def api_passport_ocr(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    file_path: str,                 # đường dẫn file png/jpg/pdf...
    form_field_name: str = "file",  # tùy backend: "file"/"passport"/"image"...
) -> tuple[bool, dict[str, Any]]:
    url = f"{BASE_URL}/PassportOCR"
    headers = build_upload_headers(token, tmp_secret)

    if not os.path.isfile(file_path):
        return False, {
            "status_code": None,
            "error": f"File not found: {file_path}",
            "request": {
                "url": url,
                "headers": {"Authorization": "Bearer ***", "X-Tmp-Secret": "***"},
            },
        }

    # multipart/form-data: httpx sẽ tự set Content-Type phù hợp, vì vậy không nên set Content-Type thủ công
    try:
        with open(file_path, "rb") as f:
            files = {
                form_field_name: (
                    os.path.basename(file_path),
                    f,
                    "application/octet-stream",
                )
            }
            resp = await client.post(url, headers=headers, files=files)
        data: Any
        if resp.headers.get("content-type", "").startswith("application/json"):
            data = resp.json()
        else:
            data = {"raw": resp.text}

        ok = resp.status_code in (200, 201)
        if ok:
            return True, {
                "status_code": resp.status_code,
                "response": data,
                "request": {
                    "url": url,
                    "headers": {"Authorization": "Bearer ***", "X-Tmp-Secret": "***"},
                    "file": {"path": file_path, "field": form_field_name},
                },
            }

        return False, {
            "status_code": resp.status_code,
            "response": data,
            "request": {
                "url": url,
                "headers": {"Authorization": "Bearer ***", "X-Tmp-Secret": "***"},
                "file": {"path": file_path, "field": form_field_name},
            },
        }

    except Exception as e:
        return False, {
            "status_code": None,
            "error": repr(e),
            "request": {
                "url": url,
                "headers": {"Authorization": "Bearer ***", "X-Tmp-Secret": "***"},
                "file": {"path": file_path, "field": form_field_name},
            },
        }
 