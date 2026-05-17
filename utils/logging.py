import json
import time
from typing import Any, Dict


def log_event(event: Dict[str, Any], path: str = "run.log") -> None:
    """Append one JSON line log."""
    event["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


async def notify(message: str) -> None:
    """
    Demo noti: in thực tế bạn thay bằng Telegram/Slack/Email.
    Ví dụ Telegram: gọi Bot API sendMessage.
    """
    print(f"[NOTI] {message}")
