from __future__ import annotations

import os
from typing import Any

import httpx


def _bridge_url() -> str:
    return os.getenv("ZALO_BRIDGE_URL", "http://127.0.0.1:3100").strip().rstrip("/")


def bridge_secret() -> str:
    return os.getenv("ZALO_BRIDGE_SECRET", "").strip()


async def send_zalo_message(
    thread_id: str,
    text: str,
    thread_type: str = "group",
) -> dict[str, Any]:
    """Gửi tin nhắn qua zalo-bridge (Node, zca-js). ``thread_type``: group | user."""
    thread_id = str(thread_id or "").strip()
    if not thread_id or not text:
        return {"ok": False, "error": "missing_thread_id_or_text"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{_bridge_url()}/send",
                headers={"x-bridge-secret": bridge_secret()},
                json={"thread_id": thread_id, "thread_type": thread_type, "text": text},
            )
        if resp.status_code != 200:
            print(
                f"[zalo_notify] send failed status={resp.status_code} body={resp.text[:300]}",
                flush=True,
            )
            return {"ok": False, "status_code": resp.status_code, "error": resp.text}
        return {"ok": True}
    except Exception as exc:
        print(f"[zalo_notify] send failed error={type(exc).__name__}: {exc}", flush=True)
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


async def notify_group(text: str, group_id: str = "") -> dict[str, Any]:
    return await send_zalo_message(
        group_id or os.getenv("TRACKER_ZALO_GROUP_ID", ""), text, "group"
    )


async def notify_admin(text: str) -> dict[str, Any]:
    return await send_zalo_message(os.getenv("TRACKER_ADMIN_ZALO_ID", ""), text, "user")
