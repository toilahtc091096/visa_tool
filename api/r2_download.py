from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config

from constants import (
    R2_ACCESS_KEY_ID,
    R2_BUCKET_NAME,
    R2_ENDPOINT_URL,
    R2_SECRET_ACCESS_KEY,
)


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

    client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )
    client.download_file(R2_BUCKET_NAME, key, str(local_path))
    return {
        "ok": True,
        "bucket": R2_BUCKET_NAME,
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

    client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )
    resp = client.get_object(Bucket=R2_BUCKET_NAME, Key=key)
    body = resp["Body"].read()
    return {
        "ok": True,
        "bucket": R2_BUCKET_NAME,
        "key": key,
        "content": body,
        "content_type": resp.get("ContentType", "application/pdf"),
        "content_length": resp.get("ContentLength", len(body)),
    }
