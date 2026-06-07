import json
import sys
import time
import traceback
from typing import Any, Dict


def log_event(event: Dict[str, Any], path: str = "run.log") -> None:
    """Append one JSON line log."""
    payload = dict(event)
    payload["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    line = json.dumps(payload, ensure_ascii=False)

    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    # Emit to stdout so VPS deployments can collect logs like Render does.
    print(line, file=sys.stdout, flush=True)


async def notify(message: str) -> None:
    """
    Demo noti: in thực tế bạn thay bằng Telegram/Slack/Email.
    Ví dụ Telegram: gọi Bot API sendMessage.
    """
    print(f"[NOTI] {message}", file=sys.stdout, flush=True)

def log_exception(exc: Exception, event: Dict[str, Any], path: str = "run.log") -> None:
    payload = dict(event)
    payload.update({
        "level": "error",
        "error_type": type(exc).__name__,
        "error_msg": str(exc),
        "traceback": traceback.format_exc(),
    })
    log_event(payload, path)
