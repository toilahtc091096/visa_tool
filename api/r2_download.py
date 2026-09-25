import io
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from utils.app_logging import log_event
from utils.r2_env import build_r2_client

# Images/PDFs are already compressed; deflating them again only costs CPU.
_STORED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf", ".zip", ".docx"}
_DOWNLOAD_WORKERS = 8


def api_download_r2_object(key: str, target_dir: str | Path) -> dict[str, Any]:
    key = str(key).strip()
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    if not key:
        return {
            "ok": False,
            "error": "missing_key",
        }

    filename = Path(key).name
    local_path = target_path / filename

    client, config = build_r2_client(log=True)
    client.download_file(config.bucket_name, key, str(local_path))
    return {
        "ok": True,
        "bucket": config.bucket_name,
        "key": key,
        "local_path": str(local_path),
    }


def api_download_r2_object_bytes(key: str) -> dict[str, Any]:
    key = str(key).strip()
    if not key:
        return {
            "ok": False,
            "error": "missing_key",
        }

    started_at = time.perf_counter()
    client, config = build_r2_client(log=True)
    resp = client.get_object(Bucket=config.bucket_name, Key=key)
    body = resp["Body"].read()
    log_event(
        {
            "step": "timing",
            "phase": "r2_get_object",
            "key": key,
            "bytes": len(body),
            "seconds": round(time.perf_counter() - started_at, 2),
        }
    )
    return {
        "ok": True,
        "bucket": config.bucket_name,
        "key": key,
        "content": body,
        "content_type": resp.get("ContentType", "application/pdf"),
        "content_length": resp.get("ContentLength", len(body)),
    }


def api_download_r2_folder_zip(prefix: str) -> dict[str, Any]:
    prefix = str(prefix or "").strip().lstrip("/")
    if not prefix:
        return {
            "ok": False,
            "error": "missing_prefix",
        }

    if prefix and not prefix.endswith("/"):
        prefix += "/"

    started_at = time.perf_counter()
    client, config = build_r2_client(log=True)

    paginator = client.get_paginator("list_objects_v2")
    keys = [
        str(obj.get("Key") or "").strip()
        for page in paginator.paginate(Bucket=config.bucket_name, Prefix=prefix)
        for obj in page.get("Contents", [])
    ]
    keys = [key for key in keys if key and not key.endswith("/")]
    listed_at = time.perf_counter()

    def fetch(key: str) -> bytes:
        return client.get_object(Bucket=config.bucket_name, Key=key)["Body"].read()

    zip_buffer = io.BytesIO()
    total_size = 0
    with ThreadPoolExecutor(max_workers=_DOWNLOAD_WORKERS) as pool:
        bodies = pool.map(fetch, keys)
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for key, body in zip(keys, bodies):
                relative_name = key[len(prefix):].lstrip("/") or Path(key).name
                compress_type = (
                    zipfile.ZIP_STORED
                    if Path(key).suffix.lower() in _STORED_SUFFIXES
                    else zipfile.ZIP_DEFLATED
                )
                zf.writestr(relative_name, body, compress_type=compress_type)
                total_size += len(body)

    file_count = len(keys)
    log_event(
        {
            "step": "timing",
            "phase": "r2_folder_zip",
            "prefix": prefix,
            "files": file_count,
            "bytes": total_size,
            "list_seconds": round(listed_at - started_at, 2),
            "seconds": round(time.perf_counter() - started_at, 2),
        }
    )
    zip_size = zip_buffer.getbuffer().nbytes
    if file_count == 0:
        return {
            "ok": False,
            "error": "no_objects_found",
            "bucket": config.bucket_name,
            "prefix": prefix,
            "file_count": 0,
            "total_size": 0,
        }
    return {
        "ok": True,
        "bucket": config.bucket_name,
        "prefix": prefix,
        "content": zip_buffer.getvalue(),
        "content_type": "application/zip",
        "content_length": zip_size,
        "file_count": file_count,
        "total_size": total_size,
    }
