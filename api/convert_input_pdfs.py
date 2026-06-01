from pathlib import Path
from typing import Any

import fitz

from .r2_download import api_download_r2_object_bytes
from .r2_upload import api_upload_r2_object


def _convert_pdf_bytes_to_png_uploads(pdf_name: str, pdf_bytes: bytes) -> dict[str, Any]:
    uploaded_pngs: list[dict[str, Any]] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            png_key = f"{Path(pdf_name).stem}_page_{page_index + 1}.png"
            upload_result = api_upload_r2_object(
                png_key,
                pix.tobytes("png"),
                content_type="image/png",
            )
            if not upload_result.get("ok"):
                return {
                    "ok": False,
                    "pdf": pdf_name,
                    "uploaded_pngs": uploaded_pngs,
                    "failed": {
                        "key": png_key,
                        "upload": upload_result,
                    },
                }
            uploaded_pngs.append(
                {
                    "key": png_key,
                    "upload": upload_result,
                }
            )
    return {
        "ok": True,
        "pdf": pdf_name,
        "uploaded_pngs": uploaded_pngs,
        "page_count": len(uploaded_pngs),
    }


def api_convert_input_pdfs(download_key: str | None = None) -> dict[str, Any]:
    if download_key in (None, ""):
        return {
            "ok": False,
            "error": "missing_key",
        }

    download_result = api_download_r2_object_bytes(download_key)
    if not download_result.get("ok"):
        return {
            "ok": False,
            "download": download_result,
        }

    upload_result = _convert_pdf_bytes_to_png_uploads(
        Path(download_result["key"]).name,
        download_result["content"],
    )
    if not upload_result.get("ok"):
        return {
            "ok": False,
            "download": {
                "bucket": download_result.get("bucket"),
                "key": download_result.get("key"),
                "content_length": download_result.get("content_length"),
                "content_type": download_result.get("content_type"),
            },
            "failed_pdf": upload_result,
        }

    return {
        "ok": True,
        "download": {
            "bucket": download_result.get("bucket"),
            "key": download_result.get("key"),
            "content_length": download_result.get("content_length"),
            "content_type": download_result.get("content_type"),
        },
        "converted": [upload_result],
        "pdf_count": 1,
    }
 