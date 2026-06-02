import json
from pathlib import Path
from typing import Optional
from typing import Any, Dict
from dataclasses import asdict

TOKEN_FILE = Path(__file__).resolve().parents[1] / "resources" / "token.json"
TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
def load_token() -> str:
    if not TOKEN_FILE.exists():
        return ""
    try:
        data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
        return data.get("token", "") or ""
    except Exception:
        return ""

def save_token(token: str) -> None:
    TOKEN_FILE.write_text(json.dumps({"token": token}, ensure_ascii=False), encoding="utf-8")

def clear_token() -> None:
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()

def load_login_payload() -> Dict[str, Any]:
    """
    Return the whole token file as a dict so you can do:
        payload = load_login_payload()
        token = payload.get("token", "")
        tmp_secret = payload.get("tmpSecret", "")
    """
    if not TOKEN_FILE.exists():
        return {}

    try:
        data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def save_login_data(login_data, path: Path = TOKEN_FILE) -> None:
    if login_data is None:
        return

    if isinstance(login_data, dict):
        payload = login_data
    else:
        payload = asdict(login_data)

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
 
