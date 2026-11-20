"""Admin reports on /web: records of ALL houses (no current-house filter, on purpose).

Read only. A record counts for the day it was first created (created_at, in
Vietnam time) and for the person who ran it first (staff_code).
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any

from psycopg2.extras import RealDictCursor

from database.connection import get_connection

UNKNOWN_STAFF = "_none"  # filter value for records without a staff (before staff was recorded)

# Status groups shown in the report.
APPROVED = ("approved",)
REJECTED = ("rejected", "cancelled")
DRAFT = ("draft",)


def _tz() -> str:
    return os.getenv("APP_TIMEZONE", "").strip() or "Asia/Ho_Chi_Minh"


def build_filters(filters: dict[str, Any]) -> tuple[str, list[Any]]:
    """WHERE clause (starting with WHERE) and params for the admin filters.

    filters: date_from, date_to (date or "YYYY-MM-DD"), staff (code or "_none"),
    house, visa_code (prefix of visa_type: "L" matches L15 and L30), status, q
    (passport number or name, partial).
    """
    where = ["TRUE"]
    params: list[Any] = []
    day = "(vr.created_at AT TIME ZONE %s)::date"
    if filters.get("date_from"):
        where.append(f"{day} >= %s")
        params += [_tz(), _as_date(filters["date_from"])]
    if filters.get("date_to"):
        where.append(f"{day} <= %s")
        params += [_tz(), _as_date(filters["date_to"])]
    staff = str(filters.get("staff") or "").strip()
    if staff == UNKNOWN_STAFF:
        where.append("vr.staff_code = ''")
    elif staff:
        where.append("vr.staff_code = %s")
        params.append(staff.upper())
    house = str(filters.get("house") or "").strip()
    if house:
        where.append("vr.house = %s")
        params.append(house.upper())
    visa_code = str(filters.get("visa_code") or "").strip()
    if visa_code:
        where.append("vr.visa_type LIKE %s")
        params.append(visa_code.upper().replace("%", "").replace("_", "") + "%")
    status = str(filters.get("status") or "").strip()
    if status:
        where.append("vr.status = %s")
        params.append(status)
    q = str(filters.get("q") or "").strip()
    if q:
        where.append("(vr.passport_number ILIKE %s OR vr.full_name ILIKE %s OR vr.application_code ILIKE %s)")
        like = "%" + q.replace("%", "").replace("_", "") + "%"
        params += [like, like, like]
    return "WHERE " + " AND ".join(where), params


def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())


def _fetch_all(sql: str, params: list[Any]) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def count_by_staff_day(filters: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per (day, staff, house): total and counts per status group."""
    where, params = build_filters(filters)
    sql = f"""
        SELECT (vr.created_at AT TIME ZONE %s)::date AS day,
               vr.staff_code,
               vr.house,
               COUNT(*) AS total,
               COUNT(*) FILTER (WHERE vr.status = ANY(%s)) AS draft,
               COUNT(*) FILTER (WHERE vr.status = ANY(%s)) AS approved,
               COUNT(*) FILTER (WHERE vr.status = ANY(%s)) AS rejected
        FROM visa_registrations vr
        {where}
        GROUP BY 1, 2, 3
        ORDER BY 1 DESC, 2, 3
    """
    rows = _fetch_all(sql, [_tz(), list(DRAFT), list(APPROVED), list(REJECTED), *params])
    for row in rows:
        row["day"] = row["day"].isoformat()
        for key in ("total", "draft", "approved", "rejected"):
            row[key] = int(row[key])
        row["in_progress"] = row["total"] - row["draft"] - row["approved"] - row["rejected"]
    return rows


def list_records(filters: dict[str, Any], limit: int = 50, offset: int = 0) -> dict[str, Any]:
    where, params = build_filters(filters)
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))
    sql = f"""
        SELECT vr.id, vr.created_at, vr.updated_at, vr.house, vr.staff_code, vr.job_id,
               vr.full_name, vr.passport_number, vr.visa_type, vr.status,
               vr.application_code, vr.first_applyid, vr.is_vip, a.code AS agency_code,
               COUNT(*) OVER () AS total_count
        FROM visa_registrations vr
        LEFT JOIN agencies a ON a.id = vr.agency_id
        {where}
        ORDER BY vr.created_at DESC, vr.id DESC
        LIMIT %s OFFSET %s
    """
    rows = _fetch_all(sql, [*params, limit, offset])
    total = int(rows[0]["total_count"]) if rows else 0
    if not rows and offset:
        total = count_records(filters)
    items = []
    for row in rows:
        row.pop("total_count", None)
        for key in ("created_at", "updated_at"):
            row[key] = row[key].isoformat() if row.get(key) else ""
        row["is_vip"] = 1 if row.get("is_vip") else 0
        row["agency_code"] = row.get("agency_code") or ""
        items.append(row)
    return {"total": total, "items": items, "limit": limit, "offset": offset}


def count_records(filters: dict[str, Any]) -> int:
    where, params = build_filters(filters)
    rows = _fetch_all(f"SELECT COUNT(*) AS n FROM visa_registrations vr {where}", params)
    return int(rows[0]["n"]) if rows else 0


def list_staff_codes() -> list[str]:
    """Staff codes seen on records or web accounts, for the filter."""
    sql = """
        SELECT staff_code FROM visa_registrations WHERE staff_code <> ''
        UNION
        SELECT staff_code FROM web_users WHERE staff_code <> ''
        ORDER BY 1
    """
    return [row["staff_code"] for row in _fetch_all(sql, [])]
