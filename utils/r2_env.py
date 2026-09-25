from __future__ import annotations

import json
import os
import threading
import time
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


# botocore defaults are 60s connect + 60s read timeouts with up to 4 retries,
# so one stalled connection to R2 could hold a request for ~4 minutes.
_CLIENT_CONFIG = Config(
    signature_version="s3v4",
    connect_timeout=10,
    read_timeout=30,
    retries={"total_max_attempts": 4, "mode": "standard"},
    max_pool_connections=16,
    tcp_keepalive=True,
)
_CLIENTS: dict[R2Config, object] = {}
_CLIENTS_LOCK = threading.Lock()


def _log_retry(attempts=None, caught_exception=None, response=None, operation=None, **kwargs):
    status = None
    if response is not None:
        status = (response[1] or {}).get("ResponseMetadata", {}).get("HTTPStatusCode")
    if caught_exception is None and (status is None or status < 500):
        return None
    print(
        json.dumps(
            {
                "step": "r2_retry",
                "operation": getattr(operation, "name", str(operation)),
                "attempt": attempts,
                "status": status,
                "error": repr(caught_exception) if caught_exception else None,
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        ),
        flush=True,
    )
    return None


def build_r2_client(*, log: bool = True):
    """Return the shared (thread-safe) S3 client for the active R2 config."""
    config = get_active_r2_config(log=log)
    with _CLIENTS_LOCK:
        client = _CLIENTS.get(config)
        if client is None:
            client = boto3.client(
                "s3",
                endpoint_url=config.endpoint_url,
                aws_access_key_id=config.access_key_id,
                aws_secret_access_key=config.secret_access_key,
                region_name="auto",
                config=_CLIENT_CONFIG,
            )
            client.meta.events.register("needs-retry.s3", _log_retry)
            _CLIENTS[config] = client
    return client, config
