from pathlib import Path
from typing import Any

import fitz

from .r2_download import api_download_r2_object
from .r2_upload import api_upload_r2_object


def _convert_pdf_to_pngs_and_upload(pdf_path: Path) -> dict[str, Any]:
    uploaded_pngs: list[dict[str, Any]] = []
    with fitz.open(pdf_path) as doc:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            png_key = f"converted/{pdf_path.stem}/{pdf_path.stem}_page_{page_index + 1}.png"
            upload_result = api_upload_r2_object(
                png_key,
                pix.tobytes("png"),
                content_type="image/png",
            )
            if not upload_result.get("ok"):
                return {
                    "ok": False,
                    "pdf": pdf_path.name,
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
    pdf_path.unlink(missing_ok=True)
    return {
        "ok": True,
        "pdf": pdf_path.name,
        "uploaded_pngs": uploaded_pngs,
        "page_count": len(uploaded_pngs),
    }


def api_convert_input_pdfs(
    input_dir: str | Path | None = None,
    download_key: str | None = None,
) -> dict[str, Any]:
    base_dir = Path(__file__).resolve().parent.parent / "resources"
    resolved_input_dir = Path(input_dir) if input_dir is not None else base_dir / "input"

    if not resolved_input_dir.exists():
        return {
            "ok": True,
            "skipped": True,
            "reason": "resources/input does not exist",
            "input_dir": str(resolved_input_dir),
        }

    download_result = None
    if download_key not in (None, ""):
        download_result = api_download_r2_object(download_key, resolved_input_dir)
        if not download_result.get("ok"):
            return {
                "ok": False,
                "input_dir": str(resolved_input_dir),
                "download": download_result,
            }

    converted: list[dict[str, Any]] = []
    pdf_paths = sorted(
        path
        for path in resolved_input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    )
    for pdf_path in pdf_paths:
        upload_result = _convert_pdf_to_pngs_and_upload(pdf_path)
        if not upload_result.get("ok"):
            return {
                "ok": False,
                "input_dir": str(resolved_input_dir),
                "download": download_result,
                "failed_pdf": upload_result,
                "pdf_count": len(pdf_paths),
            }
        converted.append(
            {
                "pdf": pdf_path.name,
                "uploaded_pngs": upload_result["uploaded_pngs"],
                "page_count": upload_result["page_count"],
            }
        )

    return {
        "ok": True,
        "input_dir": str(resolved_input_dir),
        "download": download_result,
        "converted": converted,
        "pdf_count": len(pdf_paths),
    }
