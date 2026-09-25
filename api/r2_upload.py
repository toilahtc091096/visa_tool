from io import BytesIO
from typing import Any

from utils.r2_env import build_r2_client


def api_upload_r2_object(
    key: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> dict[str, Any]:
    try:
        key = str(key).strip()
        if not key:
            return {"ok": False, "error": "missing_key"}

        client, config = build_r2_client(log=True)
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
