"""Progress of runs started from /web."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from psycopg2.extras import RealDictCursor

from database.connection import get_connection

_FINAL = {"done", "error"}


def _row(cursor) -> dict[str, Any] | None:
    row = cursor.fetchone()
    if not row:
        return None
    out = dict(row)
    for k in ("started_at", "updated_at", "finished_at"):
        if out.get(k) is not None:
            out[k] = out[k].isoformat()
    return out


def create_web_job(job: dict[str, str], username: str, first_step: dict[str, Any]) -> None:
    sql = """
        INSERT INTO web_jobs (job_id, username, staff_code, house, visa_type, source_prefix, steps)
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (job_id) DO NOTHING
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (job["job_id"], username, job["staff"], job["house"], job["visa_type"],
                                     job["source_prefix"], json.dumps([first_step], ensure_ascii=False)))
    finally:
        conn.close()


def add_web_job_step(job_id: str, step: dict[str, Any], status: str = "running") -> bool:
    """Append a step. status 'done'/'error' closes the job; a closed job only accepts nothing more.
    Returns False when the job is unknown (e.g. a run started from WF-01, not from /web)."""
    final = status in _FINAL
    sql = """
        UPDATE web_jobs SET
            steps = steps || %s::jsonb,
            status = %s,
            message = CASE WHEN %s THEN %s ELSE message END,
            updated_at = NOW(),
            finished_at = CASE WHEN %s THEN NOW() ELSE finished_at END
        WHERE job_id = %s AND status = 'running'
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (json.dumps([step], ensure_ascii=False), status if final else "running",
                                     final, step.get("message", ""), final, job_id))
                return cursor.rowcount > 0
    finally:
        conn.close()


def get_web_job(job_id: str) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM web_jobs WHERE job_id = %s", (job_id,))
            return _row(cursor)
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
