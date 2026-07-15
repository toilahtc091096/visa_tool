from __future__ import annotations

import os
from dataclasses import dataclass

import boto3
from botocore.config import Config


@dataclass(frozen=True)
class R2Config:
    endpoint_url: str
    access_key_id: str
    secret_access_key: str
    bucket_name: str


def _mask_secret(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "<missing>"
    if len(text) <= 8:
        return f"{text[:2]}***{text[-2:]}"
    return f"{text[:4]}***{text[-4:]}"


def get_active_r2_config(*, log: bool = True) -> R2Config:
    config = R2Config(
        endpoint_url=os.getenv("R2_ENDPOINT_URL", "").strip(),
        access_key_id=os.getenv("R2_ACCESS_KEY_ID", "").strip(),
        secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY", "").strip(),
        bucket_name=os.getenv("R2_BUCKET_NAME", "").strip(),
    )

    missing = [
        name
        for name, value in [
            ("R2_ENDPOINT_URL", config.endpoint_url),
            ("R2_ACCESS_KEY_ID", config.access_key_id),
            ("R2_SECRET_ACCESS_KEY", config.secret_access_key),
            ("R2_BUCKET_NAME", config.bucket_name),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    if log:
        print(
            "[R2] active env -> "
            f"bucket={config.bucket_name}, "
            f"endpoint={config.endpoint_url}, "
            f"access_key={_mask_secret(config.access_key_id)}, "
            f"secret={_mask_secret(config.secret_access_key)}",
            flush=True,
        )

    return config


def build_r2_client(*, log: bool = True):
    config = get_active_r2_config(log=log)
    client = boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )
    return client, config
