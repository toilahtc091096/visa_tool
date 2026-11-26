"""Live progress of /run, so the web page can show the step being run.

/run is given a `run_id` (made by the page). While the flow runs, `_timed`
in flows/run_flow.py reports each phase here; the page polls
GET /run/progress/{run_id} (through /web/run-progress). Kept in memory of the
instance that runs the case, dropped after an hour.
"""
from __future__ import annotations

import contextvars
import re
import threading
import time
from typing import Any

KEEP_SECONDS = 3600
_RUN_ID = re.compile(r"^[A-Za-z0-9_-]{6,64}$")

current_run_id: contextvars.ContextVar[str] = contextvars.ContextVar("current_run_id", default="")

_lock = threading.Lock()
_runs: dict[str, dict[str, Any]] = {}


def valid_run_id(run_id: Any) -> str:
    text = str(run_id or "").strip()
    return text if _RUN_ID.match(text) else ""


def _prune(now: float) -> None:
    for rid in [k for k, v in _runs.items() if now - v["updated"] > KEEP_SECONDS]:
        _runs.pop(rid, None)


def begin(run_id: str) -> None:
    if not run_id:
        return
    now = time.time()
    with _lock:
        _prune(now)
        _runs[run_id] = {"started": now, "updated": now, "phase": "", "phase_started": now,
                         "done": [], "status": "running", "ctx": None}


def phase_start(phase: str, ctx: Any = None) -> None:
    run_id = current_run_id.get()
    if not run_id:
        return
    now = time.time()
    with _lock:
        r = _runs.get(run_id)
        if r is None:
            return
        r.update(phase=phase, phase_started=now, updated=now, ctx=ctx)


def phase_end(phase: str, seconds: float) -> None:
    run_id = current_run_id.get()
    if not run_id:
        return
    with _lock:
        r = _runs.get(run_id)
        if r is None:
            return
        r["done"].append([phase, seconds])
        r.update(phase="", updated=time.time())


def finish(run_id: str, ok: bool) -> None:
    if not run_id:
        return
    with _lock:
        r = _runs.get(run_id)
        if r is not None:
            r.update(status="done" if ok else "error", phase="", ctx=None, updated=time.time())


def snapshot(run_id: str) -> dict[str, Any] | None:
    now = time.time()
    with _lock:
        r = _runs.get(run_id)
        if r is None:
            return None
        ctx = r["ctx"]
        return {
            "status": r["status"],
            "elapsed": round(now - r["started"], 2),
            "done": [list(x) for x in r["done"]],
            "phase": r["phase"],
            "phase_elapsed": round(now - r["phase_started"], 2) if r["phase"] else 0,
            # finer step inside the phase (ctx.step in flows/flow_step/*)
            "step": str(getattr(ctx, "step", "") or "") if r["phase"] and ctx is not None else "",
        }
