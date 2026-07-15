from __future__ import annotations

import base64
import binascii
import io
import mimetypes
import os
import re
import uuid
from pathlib import Path
from typing import Any

from utils.r2_env import build_r2_client


_SAFE_SUFFIX_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _build_r2_client():
    client, config = build_r2_client(log=True)
    return client, config


def _missing_r2_env_vars() -> list[str]:
    missing: list[str] = []
    if not os.getenv("R2_ENDPOINT_URL", "").strip():
        missing.append("R2_ENDPOINT_URL")
    if not os.getenv("R2_ACCESS_KEY_ID", "").strip():
        missing.append("R2_ACCESS_KEY_ID")
    if not os.getenv("R2_SECRET_ACCESS_KEY", "").strip():
        missing.append("R2_SECRET_ACCESS_KEY")
    if not os.getenv("R2_BUCKET_NAME", "").strip():
        missing.append("R2_BUCKET_NAME")
    return missing


def _normalize_folder(folder: str) -> str:
    text = str(folder or "").strip().lstrip("/").rstrip("/")
    return text


def _sanitize_filename(filename: str) -> str:
    name = Path(str(filename or "")).name.strip()
    if not name:
        return f"image_{uuid.uuid4().hex}.png"
    cleaned = _SAFE_SUFFIX_RE.sub("_", name)
    cleaned = cleaned.strip("._-")
    return cleaned or f"image_{uuid.uuid4().hex}.png"


def _normalize_key(folder: str, filename: str) -> str:
    folder = _normalize_folder(folder)
    filename = _sanitize_filename(filename)
    if folder:
        return f"{folder}/{filename}"
    return filename


def _guess_content_type(filename: str, provided: str | None) -> str:
    if provided:
        return str(provided).strip()
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def _decode_base64_image(image_base64: str) -> bytes:
    text = str(image_base64 or "").strip()
    if not text:
        raise ValueError("missing_image_base64")
    if "," in text and text.lower().startswith("data:"):
        text = text.split(",", 1)[1]
    try:
        return base64.b64decode(text, validate=True)
    except binascii.Error as exc:
        raise ValueError("invalid_image_base64") from exc


def api_delete_r2_objects(
    *,
    key: str = "",
    prefix: str = "",
) -> dict[str, Any]:
    missing = _missing_r2_env_vars()
    if missing:
        return {"ok": False, "error": "missing_r2_env_vars", "missing": missing}

    normalized_key = str(key or "").strip().lstrip("/")
    normalized_prefix = str(prefix or "").strip().lstrip("/")

    if not normalized_key and not normalized_prefix:
        return {"ok": False, "error": "missing_key_or_prefix"}

    try:
        client, config = _build_r2_client()
        if normalized_key:
            client.delete_object(Bucket=config.bucket_name, Key=normalized_key)
            return {
                "ok": True,
                "mode": "delete_key",
                "bucket": config.bucket_name,
                "key": normalized_key,
                "deleted": 1,
            }

        prefix_value = normalized_prefix
        if prefix_value and not prefix_value.endswith("/"):
            prefix_value += "/"

        paginator = client.get_paginator("list_objects_v2")
        deleted_count = 0
        for page in paginator.paginate(Bucket=config.bucket_name, Prefix=prefix_value):
            contents = page.get("Contents", [])
            if not contents:
                continue

            keys = [{"Key": obj["Key"]} for obj in contents]
            resp = client.delete_objects(
                Bucket=config.bucket_name,
                Delete={"Objects": keys, "Quiet": True},
            )
            deleted_count += len(resp.get("Deleted", []))
            errors = resp.get("Errors", [])
            if errors:
                return {
                    "ok": False,
                    "error": "delete_errors",
                    "errors": errors,
                }

        return {
            "ok": True,
            "mode": "delete_prefix",
            "bucket": config.bucket_name,
            "prefix": prefix_value,
            "deleted": deleted_count,
        }
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "message": str(exc)}


def api_sign_and_push_image_to_r2(
    *,
    mode: str = "upload",
    folder: str = "",
    key: str = "",
    filename: str = "",
    content_type: str = "",
    expires_in: int = 900,
    image_base64: str = "",
    file_bytes: bytes | None = None,
    file_name: str = "",
    file_content_type: str = "",
) -> dict[str, Any]:
    missing = _missing_r2_env_vars()
    if missing:
        return {"ok": False, "error": "missing_r2_env_vars", "missing": missing}

    client, config = _build_r2_client()

    normalized_mode = str(mode or "upload").strip().lower()
    if normalized_mode not in {"upload", "presign"}:
        return {"ok": False, "error": "invalid_mode"}

    target_key = str(key or "").strip().lstrip("/")
    if not target_key:
        source_name = filename or file_name or ""
        if not source_name:
            source_name = f"image_{uuid.uuid4().hex}.png"
        target_key = _normalize_key(folder, source_name)

    if normalized_mode == "presign":
        try:
            upload_url = client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": config.bucket_name,
                    "Key": target_key,
                    "ContentType": _guess_content_type(
                        filename or file_name or target_key,
                        content_type or file_content_type,
                    ),
                },
                ExpiresIn=max(60, int(expires_in)),
            )
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__, "message": str(exc)}

        public_base = os.getenv("R2_PUBLIC_BASE", "").rstrip("/")
        return {
            "ok": True,
            "mode": "presign",
            "bucket": config.bucket_name,
            "key": target_key,
            "expires_in": max(60, int(expires_in)),
            "upload_url": upload_url,
            "method": "PUT",
            "content_type": _guess_content_type(
                filename or file_name or target_key,
                content_type or file_content_type,
            ),
            "url": f"{public_base}/{target_key}" if public_base else "",
        }

    payload: bytes
    source_content_type = content_type or file_content_type
    source_name = filename or file_name or target_key

    if file_bytes is not None:
        payload = file_bytes
    elif image_base64:
        payload = _decode_base64_image(image_base64)
    else:
        return {"ok": False, "error": "missing_image"}

    resolved_content_type = _guess_content_type(source_name, source_content_type)
    client.upload_fileobj(
        Fileobj=io.BytesIO(payload),
        Bucket=config.bucket_name,
        Key=target_key,
        ExtraArgs={"ContentType": resolved_content_type},
    )

    public_base = os.getenv("R2_PUBLIC_BASE", "").rstrip("/")
    return {
        "ok": True,
        "mode": "upload",
        "bucket": config.bucket_name,
        "key": target_key,
        "size": len(payload),
        "content_type": resolved_content_type,
        "url": f"{public_base}/{target_key}" if public_base else "",
    }
