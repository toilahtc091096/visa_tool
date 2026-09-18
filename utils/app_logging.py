import json
import sys
import time
import traceback
from typing import Any, Dict


def _safe_print(text: str) -> None:
    """Print an arbitrary Unicode string to stdout, working around consoles
    (typical on Windows, codepage cp1252/cp936/...) that can't encode every
    character. Falls back to writing UTF-8 bytes directly when needed.
    """
    try:
        print(text, file=sys.stdout, flush=True)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
        sys.stdout.flush()


def log_event(event: Dict[str, Any], path: str = "run.log") -> None:
    """Emit one JSON line log to stdout only."""
    payload = dict(event)
    payload["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    line = json.dumps(payload, ensure_ascii=False)

    _safe_print(line)


async def notify(message: str) -> None:
    """
    Demo noti: in thực tế bạn thay bằng Telegram/Slack/Email.
    Ví dụ Telegram: gọi Bot API sendMessage.
    """
    _safe_print(f"[NOTI] {message}")


def log_exception(exc: Exception, event: Dict[str, Any], path: str = "run.log") -> None:
    payload = dict(event)
    payload.update(
        {
            "level": "error",
            "error_type": type(exc).__name__,
            "error_msg": str(exc),
            "traceback": traceback.format_exc(),
        }
    )
    log_event(payload, path)
