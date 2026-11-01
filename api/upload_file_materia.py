from io import BytesIO
from pathlib import Path
from typing import Any
import os
import mimetypes

import httpx
from PIL import Image, UnidentifiedImageError
from models import UploadMaterialBody
from utils import build_upload_headers
from constants import (
    BASE_FILE_UPLOAD_URL
)

_JPEG_FORMATS = {"JPEG", "MPO"}  # MPO: multi-picture JPEG from phone cameras
_JPEG_SUFFIXES = {".jpg", ".jpeg"}


def _prepare_upload_file(file_path: str, file_name: str) -> tuple[str, bytes]:
    """Return ``(file_name, content)`` whose extension matches the real format.

    COVA checks the file content (FileRealTypeInvalid), so a JPEG saved as
    ``.png`` is renamed to ``.jpg``, and other image formats (webp, bmp...)
    are converted to JPEG. Non-images (pdf...) are sent unchanged.
    """
    with open(file_path, "rb") as f:
        content = f.read()
    try:
        with Image.open(BytesIO(content)) as img:
            real_format = (img.format or "").upper()
            stem = Path(file_name).stem
            suffix = Path(file_name).suffix.lower()
            if real_format in _JPEG_FORMATS:
                return (file_name if suffix in _JPEG_SUFFIXES else f"{stem}.jpg"), content
            if real_format == "PNG":
                return (file_name if suffix == ".png" else f"{stem}.png"), content
            out = BytesIO()
            img.convert("RGB").save(out, format="JPEG", quality=92)
            return f"{stem}.jpg", out.getvalue()
    except (UnidentifiedImageError, OSError):
        return file_name, content


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
        filename, content = _prepare_upload_file(
            body.filePath, os.path.basename(body.fileName or body.filePath)
        )
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        data = {
            "fileName": filename,
            "categoryCode": body.categoryCode,
            "materialCode": body.materialCode,
            "businessId": body.businessId,
        }
        files = {"file": (filename, content, mime)}
        resp = await client.post(url, headers=headers, data=data, files=files)
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
 