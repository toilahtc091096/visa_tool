from io import BytesIO
from typing import Any

import boto3
from botocore.config import Config

from utils.r2_env import get_active_r2_config


def api_upload_r2_object(
    key: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> dict[str, Any]:
    try:
        key = str(key).strip()
        if not key:
            return {"ok": False, "error": "missing_key"}

        config = get_active_r2_config(log=True)
        client = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            config=Config(signature_version="s3v4"),
        )
        bio = BytesIO(content)
        client.upload_fileobj(
            bio,
            config.bucket_name,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return {
            "ok": True,
            "bucket": config.bucket_name,
            "key": key,
            "size": len(content),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }
