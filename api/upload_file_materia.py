from typing import Any
import os
import mimetypes

import httpx
from models import UploadMaterialBody
from utils import build_upload_headers
from constants import (
    BASE_FILE_UPLOAD_URL
)

async def api_upload_file(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret: str,
    body: UploadMaterialBody,
) -> tuple[bool, dict[str, Any]]:
    """POST ``SaveUploadAccessory`` to ``{base_url}/SaveUploadAccessory``.

    Returns ``(True, {status_code, response})`` on HTTP 200/201, else
    ``(False, {status_code, error})``. Network/parsing errors return
    ``status_code`` -1 and the exception message as ``error``.
    """
    try:
        url = f"{BASE_FILE_UPLOAD_URL}/SaveUploadAccessory"
        headers = build_upload_headers(token, tmp_secret)
        filename = os.path.basename(body.fileName or body.filePath)
        mime = mimetypes.guess_type(body.fileName)[0] or "application/octet-stream"
        data = {
            "fileName": filename,
            "categoryCode": body.categoryCode,
            "materialCode": body.materialCode,
            "businessId": body.businessId,
        }
        with open(body.filePath, "rb") as f:
            files = {"file": (body.fileName, f, mime)}
            resp = await client.post(url, headers = headers, data=data, files=files)
        data_resp = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            err = data_resp.get("Error") or data_resp.get("raw") or str(data_resp)
            return False, {"status_code": resp.status_code, "error": f"failedSaveUploadAccessory: {err}"}
        return True, {
            "status_code": resp.status_code,
            "response": data_resp,
        }
    except Exception as e:
        return False, {
            "status_code": -1,
            "error": str(e),
        }
 