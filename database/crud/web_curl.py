"""Curls run from the /web curl tab, kept KEEP_DAYS days: OK ones to reuse (history), failed ones (ok FALSE) for ADMIN."""

from __future__ import annotations

import json
from typing import Any

from psycopg2.extras import RealDictCursor

from database.connection import get_connection

KEEP_DAYS = 15
_PURGE = f"DELETE FROM web_curl_history WHERE created_at < NOW() - INTERVAL '{KEEP_DAYS} days'"


def save_curl(entry: dict[str, Any]) -> int:
    """Store one run (body without the token) and drop rows older than KEEP_DAYS."""
    sql = """
        INSERT INTO web_curl_history (username, staff_code, house, port, passport_number, full_name, visa_type, body, seconds,
                                      ok, error, timings)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb)
        RETURNING id
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(_PURGE)
                cursor.execute(sql, (entry["username"], entry.get("staff_code", ""), entry["house"], entry["port"],
                                     entry.get("passport_number", ""), entry.get("full_name", ""), entry.get("visa_type", ""),
                                     json.dumps(entry["body"], ensure_ascii=False), float(entry.get("seconds") or 0),
                                     bool(entry.get("ok", True)), str(entry.get("error") or ""),
                                     json.dumps(entry.get("timings") or {})))
                return int(cursor.fetchone()[0])
    finally:
        conn.close()


def list_curls(username: str | None, q: str = "", limit: int = 10, offset: int = 0, house: str = "",
               ok: bool = True) -> tuple[list[dict[str, Any]], int]:
    """One page, newest first, plus the total matching rows. username None = every user (ADMIN).
    ok False = the failed runs."""
    where, params = [f"created_at >= NOW() - INTERVAL '{KEEP_DAYS} days'", "ok = %s"], [bool(ok)]
    if username is not None:
        where.append("username = %s")
        params.append(username)
    house = str(house or "").strip().upper()
    if house:
        where.append("house = %s")
        params.append(house)
    q = str(q or "").strip()
    if q:
        like = "%" + q.replace("%", "").replace("_", "") + "%"
        where.append("(passport_number ILIKE %s OR full_name ILIKE %s OR visa_type ILIKE %s OR staff_code ILIKE %s)")
        params += [like, like, like, like]
    sql = f"""
        SELECT id, username, staff_code, house, port, passport_number, full_name, visa_type, body, seconds, created_at,
               ok, error, timings, COUNT(*) OVER () AS total
        FROM web_curl_history WHERE {' AND '.join(where)}
        ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(_PURGE)
                cursor.execute(sql, [*params, max(1, min(int(limit), 300)), max(0, int(offset))])
                rows = [dict(r) for r in cursor.fetchall()]
                if not rows and offset > 0:   # page past the end: still report the total
                    cursor.execute(f"SELECT COUNT(*) FROM web_curl_history WHERE {' AND '.join(where)}", params)
                    total = int(cursor.fetchone()["count"])
                else:
                    total = int(rows[0]["total"]) if rows else 0
    finally:
        conn.close()
    for r in rows:
        r.pop("total", None)
        r["created_at"] = r["created_at"].isoformat()
        r["seconds"] = round(float(r["seconds"] or 0), 1)
    return rows, total


def delete_failed(row_id: int) -> bool:
    """Remove one failed run (ADMIN). Rows that ran OK are never removed here."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM web_curl_history WHERE id = %s AND ok = FALSE", (int(row_id),))
                return cursor.rowcount > 0
    finally:
        conn.close()
