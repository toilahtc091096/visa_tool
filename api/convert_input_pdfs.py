import os
import re
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import PurePosixPath
from typing import Any, Callable
from urllib.parse import quote

import fitz

from utils.r2_env import build_r2_client

from .r2_download import api_download_r2_object_bytes
from .r2_upload import api_upload_r2_object

# 1.5x zoom ~ 108 DPI: đọc rõ chữ, PNG nhỏ -> render và upload nhanh.
_RENDER_MATRIX = fitz.Matrix(1.5, 1.5)
# Upload là phần chậm nhất (mỗi trang 1 request mạng) -> chạy song song.
# Giữ <= max_pool_connections của R2 client (16).
_UPLOAD_WORKERS = 8


def _page_key_prefix(pdf_key: str) -> str:
    """`folder/12. DO HUNG THINH.pdf` -> `folder/12. DO HUNG THINH_page_`.

    Giữ nguyên thư mục của PDF để các hồ sơ trùng tên file không ghi đè nhau.
    """
    path = PurePosixPath(pdf_key)
    parent = path.parent.as_posix()
    base = f"{path.stem}_page_"
    return base if parent in ("", ".") else f"{parent}/{base}"


def public_r2_url(key: str) -> str | None:
    public_base = os.getenv("R2_PUBLIC_BASE", "").rstrip("/")
    if not public_base:
        return None
    return f"{public_base}/{quote(key)}"


def _list_page_keys(key_prefix: str) -> dict[str, int]:
    """Trả về {key: số trang} của các ảnh `<prefix><N>.png` đang có trên R2."""
    client, config = build_r2_client(log=False)
    pattern = re.compile(re.escape(key_prefix) + r"(\d+)\.png")
    found: dict[str, int] = {}
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=config.bucket_name, Prefix=key_prefix):
        for obj in page.get("Contents", []):
            key = obj.get("Key") or ""
            match = pattern.fullmatch(key)
            if match:
                found[key] = int(match.group(1))
    return found


def _delete_keys(keys: list[str]) -> dict[str, Any]:
    if not keys:
        return {"ok": True, "deleted": []}
    try:
        client, config = build_r2_client(log=False)
        errors: list[Any] = []
        # delete_objects nhận tối đa 1000 key/lần
        for start in range(0, len(keys), 1000):
            resp = client.delete_objects(
                Bucket=config.bucket_name,
                Delete={
                    "Objects": [{"Key": k} for k in keys[start:start + 1000]],
                    "Quiet": True,
                },
            )
            errors.extend(resp.get("Errors", []))
        if errors:
            return {"ok": False, "error": "delete_errors", "errors": errors}
        return {"ok": True, "deleted": keys}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "message": str(exc)}


def _upload_png(key: str, png_bytes: bytes) -> dict[str, Any]:
    return api_upload_r2_object(key, png_bytes, content_type="image/png", log=False)


def render_pdf_pages_to_r2(
    pdf_bytes: bytes,
    page_key: Callable[[int], str],
    pool: ThreadPoolExecutor,
) -> dict[str, Any]:
    """Render từng trang PDF thành PNG và upload lên R2 với key `page_key(số trang)`.

    Render tuần tự (fitz không thread-safe trên cùng 1 document) nhưng upload
    song song: trang N đang upload trong lúc trang N+1 được render.
    Lỗi ở bất kỳ trang nào -> xóa các trang đã upload trong lần này.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        return {"ok": False, "error": "invalid_pdf", "message": str(exc), "uploaded_pngs": []}

    futures: list[tuple[int, str, Future]] = []
    render_error: dict[str, Any] | None = None
    with doc:
        page_count = len(doc)
        for page_index in range(page_count):
            page_number = page_index + 1
            key = page_key(page_number)
            try:
                pix = doc.load_page(page_index).get_pixmap(matrix=_RENDER_MATRIX, alpha=False)
                png_bytes = pix.tobytes("png")
            except Exception as exc:
                render_error = {
                    "key": key,
                    "page": page_number,
                    "upload": {"ok": False, "error": "render_failed", "message": str(exc)},
                }
                break
            futures.append((page_number, key, pool.submit(_upload_png, key, png_bytes)))

    uploaded_pngs: list[dict[str, Any]] = []
    failed = render_error
    for page_number, key, future in futures:
        try:
            result = future.result()
        except Exception as exc:
            result = {"ok": False, "error": type(exc).__name__, "message": str(exc)}
        if result.get("ok"):
            uploaded_pngs.append(
                {"page": page_number, "key": key, "url": public_r2_url(key), "upload": result}
            )
        elif failed is None:
            failed = {"key": key, "page": page_number, "upload": result}

    if failed is not None:
        # Không để lại bộ ảnh dở dang.
        rollback = _delete_keys([item["key"] for item in uploaded_pngs])
        return {"ok": False, "error": "upload_failed", "uploaded_pngs": [], "failed": failed, "rollback": rollback}

    return {"ok": True, "uploaded_pngs": uploaded_pngs, "page_count": page_count}


def _convert_pdf_bytes_to_png_uploads(pdf_key: str, pdf_bytes: bytes) -> dict[str, Any]:
    pdf_name = PurePosixPath(pdf_key).name
    key_prefix = _page_key_prefix(pdf_key)

    with ThreadPoolExecutor(max_workers=_UPLOAD_WORKERS) as pool:
        # Liệt kê ảnh cũ song song với upload; ảnh cũ trang <= page_count
        # sẽ bị ghi đè, chỉ ảnh trang > page_count mới cần xóa.
        existing_future = pool.submit(_list_page_keys, key_prefix)
        result = render_pdf_pages_to_r2(
            pdf_bytes, lambda n: f"{key_prefix}{n}.png", pool
        )
        try:
            existing = existing_future.result()
        except Exception as exc:
            existing = None
            list_error = {"ok": False, "error": type(exc).__name__, "message": str(exc)}

    if not result.get("ok"):
        return {"pdf": pdf_name, **result}

    # PDF upload lại có ít trang hơn -> xóa ảnh các trang thừa từ lần convert trước.
    page_count = result["page_count"]
    if existing is None:
        stale_cleanup = list_error
    else:
        stale_cleanup = _delete_keys(
            [key for key, page in existing.items() if page > page_count]
        )

    return {
        "ok": True,
        "pdf": pdf_name,
        "uploaded_pngs": result["uploaded_pngs"],
        "page_count": page_count,
        "stale_cleanup": stale_cleanup,
    }


_PAGE_IMAGE_KEY = re.compile(r".+_page_\d+\.png")


def api_cleanup_pdf_page_images(
    pdf_key: str | None = None,
    keys: list[str] | None = None,
) -> dict[str, Any]:
    """Xóa ảnh trang sau khi đã merge lại thành PDF.

    - `pdf_key`: xóa mọi `<pdf>_page_N.png` sinh ra từ PDF đó (/convert-input-pdfs).
    - `keys`: xóa đúng danh sách ảnh (vd: key trả về từ /pdf-to-images).
    Chỉ xóa key dạng `*_page_N.png` để không lỡ tay xóa file khác.
    """
    pdf_key = str(pdf_key or "").strip().lstrip("/")
    key_list = [str(k or "").strip().lstrip("/") for k in (keys or [])]
    key_list = [k for k in key_list if k]
    if not pdf_key and not key_list:
        return {"ok": False, "error": "missing_key_or_keys"}

    rejected = [k for k in key_list if not _PAGE_IMAGE_KEY.fullmatch(k)]
    if rejected:
        return {"ok": False, "error": "not_page_image_keys", "rejected": rejected}

    to_delete = list(key_list)
    if pdf_key:
        if PurePosixPath(pdf_key).suffix.lower() != ".pdf":
            return {"ok": False, "error": "not_a_pdf_key", "key": pdf_key}
        try:
            to_delete.extend(_list_page_keys(_page_key_prefix(pdf_key)))
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__, "message": str(exc)}

    result = _delete_keys(sorted(set(to_delete)))
    if result.get("ok"):
        result["deleted_count"] = len(result["deleted"])
    return result


def api_convert_input_pdfs(download_key: str | None = None) -> dict[str, Any]:
    download_key = str(download_key or "").strip().lstrip("/")
    if not download_key:
        return {
            "ok": False,
            "error": "missing_key",
        }
    if PurePosixPath(download_key).suffix.lower() != ".pdf":
        return {
            "ok": False,
            "error": "not_a_pdf_key",
            "key": download_key,
        }

    download_result = api_download_r2_object_bytes(download_key)
    if not download_result.get("ok"):
        return {
            "ok": False,
            "error": "download_failed",
            "download": download_result,
        }

    download_info = {
        "bucket": download_result.get("bucket"),
        "key": download_result.get("key"),
        "content_length": download_result.get("content_length"),
        "content_type": download_result.get("content_type"),
    }
    upload_result = _convert_pdf_bytes_to_png_uploads(
        download_result["key"],
        download_result["content"],
    )
    if not upload_result.get("ok"):
        return {
            "ok": False,
            "error": upload_result.get("error", "upload_failed"),
            "download": download_info,
            "failed_pdf": upload_result,
        }

    return {
        "ok": True,
        "download": download_info,
        "converted": [upload_result],
        "pdf_count": 1,
    }
