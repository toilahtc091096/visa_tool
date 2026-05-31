from io import BytesIO
from typing import Any

import boto3
from botocore.config import Config

from constants import (
    R2_ACCESS_KEY_ID,
    R2_BUCKET_NAME,
    R2_ENDPOINT_URL,
    R2_SECRET_ACCESS_KEY,
)


def api_upload_r2_object(
    key: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> dict[str, Any]:
    try:
        key = str(key).strip()
        if not key:
            return {"ok": False, "error": "missing_key"}

        client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )
        bio = BytesIO(content)
        client.upload_fileobj(
            bio,
            R2_BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return {
            "ok": True,
            "bucket": R2_BUCKET_NAME,
            "key": key,
            "size": len(content),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }
