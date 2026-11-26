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
UNKNOWN_AGENCY = "_none"  # filter value for records without an agency

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
    vip = str(filters.get("vip") or "").strip()
    if vip in ("1", "0"):
        where.append("vr.is_vip" if vip == "1" else "NOT vr.is_vip")
    agency = str(filters.get("agency") or "").strip()
    if agency == UNKNOWN_AGENCY:
        where.append("vr.agency_id IS NULL")
    elif agency:
        # Agencies are per house: one code can exist in several houses -> match by code.
        where.append("vr.agency_id IN (SELECT id FROM agencies WHERE code = %s)")
        params.append(agency.upper())
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
               COALESCE(vr.payload->'sync'->'matched_row'->>'rejectReason', '') AS reject_reason,
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


def list_agencies() -> list[dict[str, Any]]:
    """Agency codes for the filter (codes are per house; the same code in two houses is one entry)."""
    sql = """
        SELECT a.code,
               MIN(NULLIF(a.name, '')) AS name,
               ARRAY_AGG(DISTINCT a.house ORDER BY a.house) AS houses
        FROM agencies a
        GROUP BY a.code
        ORDER BY a.code
    """
    rows = _fetch_all(sql, [])
    return [{"code": r["code"], "name": r["name"] or r["code"], "houses": [h for h in (r["houses"] or []) if h]} for r in rows]


# Visa group shown in charts: Q1/Q2/X1/X2/S2 keep 2 letters, others the first letter (L15, L30 -> L).
_VISA_GROUP = (
    "CASE WHEN UPPER(vr.visa_type) ~ '^(Q1|Q2|X1|X2|S2)' THEN UPPER(SUBSTRING(vr.visa_type FROM 1 FOR 2)) "
    "WHEN vr.visa_type = '' THEN '' ELSE UPPER(SUBSTRING(vr.visa_type FROM 1 FOR 1)) END"
)
IN_PROGRESS = ("submitted", "pending_review", "under_review", "needs_fix")


def _merge_houses(rows: list[dict[str, Any]], extra: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    """Rows grouped by (key, house) -> one row per key with totals and `houses` {house: n}."""
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        key = r["key"].isoformat() if isinstance(r["key"], date) else ("" if r["key"] is None else str(r["key"]))
        row = out.setdefault(key, {"key": key, "n": 0, **{k: 0 for k in extra}, "houses": {}})
        n = int(r["n"])
        row["n"] += n
        for k in extra:
            row[k] += int(r.get(k) or 0)
        house = str(r.get("house") or "")
        row["houses"][house] = row["houses"].get(house, 0) + n
    return list(out.values())


def chart_summary(filters: dict[str, Any]) -> dict[str, Any]:
    """Everything the chart page needs for one filter set; every series is split by house."""
    where, params = build_filters(filters)
    base = f"FROM visa_registrations vr LEFT JOIN agencies a ON a.id = vr.agency_id {where}"

    def grouped(expr: str, by_key: bool = False) -> list[dict[str, Any]]:
        rows = _fetch_all(
            f"""SELECT {expr} AS key,
                       vr.house AS house,
                       COUNT(*) AS n,
                       COUNT(*) FILTER (WHERE vr.status = ANY(%s)) AS approved,
                       COUNT(*) FILTER (WHERE vr.status = ANY(%s)) AS rejected
                {base} GROUP BY 1, 2""",
            [list(APPROVED), list(REJECTED), *params],
        )
        merged = _merge_houses(rows, ("approved", "rejected"))
        merged.sort(key=(lambda r: r["key"]) if by_key else (lambda r: (-r["n"], r["key"])))
        return merged

    by_day = _fetch_all(
        f"SELECT (vr.created_at AT TIME ZONE %s)::date AS key, vr.house AS house, COUNT(*) AS n {base} GROUP BY 1, 2",
        [_tz(), *params],
    )
    by_status = grouped("vr.status")
    total = sum(r["n"] for r in by_status)
    count = {r["key"]: r["n"] for r in by_status}
    approved = sum(count.get(s, 0) for s in APPROVED)
    rejected = sum(count.get(s, 0) for s in REJECTED)
    by_house = grouped("vr.house", by_key=True)
    return {
        "totals": {
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "draft": sum(count.get(s, 0) for s in DRAFT),
            "in_progress": sum(count.get(s, 0) for s in IN_PROGRESS),
            "vip": int(_fetch_all(f"SELECT COUNT(*) AS n {base} AND vr.is_vip", params)[0]["n"]),
        },
        "houses": [r["key"] for r in by_house],
        "by_day": sorted(_merge_houses(by_day), key=lambda r: r["key"]),
        "by_status": by_status,
        "by_agency": grouped(f"COALESCE(a.code, '{UNKNOWN_AGENCY}')"),
        "by_visa": grouped(_VISA_GROUP),
        "by_staff": grouped(f"COALESCE(NULLIF(vr.staff_code, ''), '{UNKNOWN_STAFF}')"),
        "by_house": by_house,
    }
