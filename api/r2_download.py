import io
import zipfile
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config

from utils.r2_env import get_active_r2_config


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

    config = get_active_r2_config(log=True)
    client = boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        config=Config(signature_version="s3v4"),
    )
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

    config = get_active_r2_config(log=True)
    client = boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        config=Config(signature_version="s3v4"),
    )
    resp = client.get_object(Bucket=config.bucket_name, Key=key)
    body = resp["Body"].read()
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

    config = get_active_r2_config(log=True)
    client = boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        config=Config(signature_version="s3v4"),
    )

    paginator = client.get_paginator("list_objects_v2")
    zip_buffer = io.BytesIO()
    file_count = 0
    total_size = 0

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for page in paginator.paginate(Bucket=config.bucket_name, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = str(obj.get("Key") or "").strip()
                if not key or key.endswith("/"):
                    continue

                resp = client.get_object(Bucket=config.bucket_name, Key=key)
                body = resp["Body"].read()
                relative_name = key[len(prefix):].lstrip("/")
                if not relative_name:
                    relative_name = Path(key).name
                zf.writestr(relative_name, body)
                file_count += 1
                total_size += len(body)

    zip_size = zip_buffer.getbuffer().nbytes
    zip_buffer.seek(0)
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
