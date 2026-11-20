"""Who may call the FastAPI server.

n8n runs on Railway and calls this server over the internet; staff run the
/run curl from their own machines. Neither has a fixed IP, so every call must
carry the shared key in the `X-Api-Key` header. Calls from the VPS itself
(127.0.0.1, e.g. scripts/sync_draft_visa_status.ps1) need no key.

ACCESS_GUARD (env):
  off      - no check (default, old behaviour)
  log      - allow everything, but log requests that would be blocked
  enforce  - block them (401 missing/bad key, 403 path not open from outside)
VISA_API_KEY         - the shared key (n8n Railway variable of the same name)
ACCESS_PUBLIC_PATHS  - comma list open to anyone without key (default "/health")
ACCESS_KEY_PATHS     - comma list open from outside with the key (default "/" = every path)
ACCESS_LOCAL_IPS     - comma list treated as local (default "127.0.0.1,::1")
"""

from __future__ import annotations

import hmac
import os
from dataclasses import dataclass

MODES = ("off", "log", "enforce")


def _csv(name: str, default: str) -> tuple[str, ...]:
    raw = os.getenv(name)
    raw = default if raw is None else raw
    return tuple(x.strip() for x in raw.split(",") if x.strip())


def _matches(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == p or path.startswith(p.rstrip("/") + "/") for p in prefixes)


@dataclass(frozen=True)
class GuardConfig:
    mode: str
    public_paths: tuple[str, ...]
    key_paths: tuple[str, ...]
    local_ips: tuple[str, ...]
    api_key: str

    @classmethod
    def from_env(cls) -> "GuardConfig":
        mode = os.getenv("ACCESS_GUARD", "off").strip().lower()
        return cls(
            mode=mode if mode in MODES else "off",
            public_paths=_csv("ACCESS_PUBLIC_PATHS", "/health"),
            key_paths=_csv("ACCESS_KEY_PATHS", "/"),
            local_ips=_csv("ACCESS_LOCAL_IPS", "127.0.0.1,::1"),
            api_key=os.getenv("VISA_API_KEY", "").strip(),
        )


@dataclass(frozen=True)
class Decision:
    allowed: bool
    status: int = 200
    reason: str = ""


def decide(cfg: GuardConfig, path: str, client_ip: str, api_key: str) -> Decision:
    """Pure rule check; the middleware applies the mode (off/log/enforce)."""
    if client_ip in cfg.local_ips:
        return Decision(True, reason="local")
    if _matches(path, cfg.public_paths):
        return Decision(True, reason="public_path")
    if _matches(path, cfg.key_paths):
        if cfg.api_key and hmac.compare_digest(api_key or "", cfg.api_key):
            return Decision(True, reason="api_key")
        return Decision(False, 401, "missing_or_bad_api_key")
    return Decision(False, 403, "not_allowed_from_outside")
