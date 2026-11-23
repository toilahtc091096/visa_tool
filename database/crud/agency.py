from __future__ import annotations

from typing import Any

from psycopg2.extras import RealDictCursor

from database.connection import get_connection
from database.house import current_house


def get_or_create_agency(code: str) -> dict[str, Any]:
    """Return the current house's agency with this code, creating it (name = code) if new."""
    code = str(code or "").strip().upper()
    if not code:
        raise ValueError("agency code is required")

    sql = """
        INSERT INTO agencies (house, code, name)
        VALUES (%s, %s, %s)
        ON CONFLICT (house, code) DO UPDATE SET code = EXCLUDED.code
        RETURNING id, code, name
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (current_house(), code, code))
                return dict(cursor.fetchone())
    finally:
        conn.close()


def set_visa_registration_agency(
    record_id: int,
    agency_id: int,
    overwrite: bool = True,
) -> str | None:
    """
    Link a registration to an agency. With overwrite=False an agency already
    set is kept (a re-run without a code must not replace the real agency).
    Returns the previous agency code ("" when none), None if no such record.
    """
    new_agency = "%s" if overwrite else "COALESCE(vr.agency_id, %s)"
    sql = f"""
        WITH old AS (
            SELECT vr.id, a.code AS old_code
            FROM visa_registrations vr
            LEFT JOIN agencies a ON a.id = vr.agency_id
            WHERE vr.id = %s AND vr.house = %s
        )
        UPDATE visa_registrations vr
        SET agency_id = {new_agency}, updated_at = NOW()
        FROM old
        WHERE vr.id = old.id
        RETURNING old.old_code
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (record_id, current_house(), agency_id))
                row = cursor.fetchone()
                return None if row is None else (row[0] or "")
    finally:
        conn.close()


def list_visa_registrations_with_agency(
    record_ids: list[int],
    exclude_codes: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Registrations (by id) that have an agency, joined with that agency."""
    ids = [int(record_id) for record_id in record_ids if record_id is not None]
    if not ids:
        return []

    sql = """
        SELECT vr.*, a.code AS agency_code, a.name AS agency_name
        FROM visa_registrations vr
        JOIN agencies a ON a.id = vr.agency_id
        WHERE vr.id = ANY(%s)
          AND vr.house = %s
          AND NOT (a.code = ANY(%s))
        ORDER BY vr.id
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (ids, current_house(), list(exclude_codes or [])))
                return list(cursor.fetchall())
    finally:
        conn.close()


def find_visa_registrations_with_agency(
    first_applyid: str = "",
    passport_number: str = "",
) -> list[dict[str, Any]]:
    """
    The registration with this first_applyid, or else the latest one with
    this passport, with its current agency (agency_code is NULL when none).
    """
    first_applyid = str(first_applyid or "").strip()
    passport_number = str(passport_number or "").strip().upper()
    if first_applyid:
        where, param = "vr.first_applyid = %s", first_applyid
    elif passport_number:
        where, param = "UPPER(vr.passport_number) = %s", passport_number
    else:
        return []

    sql = f"""
        SELECT vr.id, vr.first_applyid, vr.full_name, vr.passport_number,
               vr.status, a.code AS agency_code
        FROM visa_registrations vr
        LEFT JOIN agencies a ON a.id = vr.agency_id
        WHERE {where} AND vr.house = %s
        ORDER BY vr.id DESC
        LIMIT 1
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (param, current_house()))
                return list(cursor.fetchall())
    finally:
        conn.close()


def update_agency_name(agency_id: int, name: str) -> None:
    sql = "UPDATE agencies SET name = %s, updated_at = NOW() WHERE id = %s AND house = %s"
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (name, agency_id, current_house()))
    finally:
        conn.close()


def list_idle_small_agencies(
    max_records: int,
    idle_days: int,
    keep_codes: list[str],
) -> list[dict[str, Any]]:
    """Agencies of the current house with fewer than ``max_records`` records and no
    new record for ``idle_days`` days (an agency without records: created that long ago).
    ``keep_codes`` (CHUNG, MB) are never listed."""
    sql = """
        SELECT a.id, a.code, a.name, COUNT(vr.id) AS records,
               MAX(vr.created_at) AS last_record_at
        FROM agencies a
        LEFT JOIN visa_registrations vr ON vr.agency_id = a.id AND vr.house = a.house
        WHERE a.house = %s AND NOT (UPPER(a.code) = ANY(%s))
        GROUP BY a.id, a.code, a.name, a.created_at
        HAVING COUNT(vr.id) < %s
           AND COALESCE(MAX(vr.created_at), a.created_at) < NOW() - make_interval(days => %s)
        ORDER BY a.code
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (current_house(), [c.upper() for c in keep_codes],
                                     int(max_records), int(idle_days)))
                rows = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()
    for r in rows:
        r["records"] = int(r["records"])
        r["last_record_at"] = r["last_record_at"].isoformat() if r.get("last_record_at") else ""
    return rows


def move_agency_records(from_agency_id: int, to_agency_id: int) -> list[int]:
    """Move every record of one agency (current house) to another; ids moved."""
    sql = """
        UPDATE visa_registrations SET agency_id = %s, updated_at = NOW()
        WHERE agency_id = %s AND house = %s
        RETURNING id
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (to_agency_id, from_agency_id, current_house()))
                return sorted(int(r[0]) for r in cursor.fetchall())
    finally:
        conn.close()


def delete_agency_if_unused(agency_id: int) -> bool:
    """Delete an agency of the current house that no record points to any more."""
    sql = """
        DELETE FROM agencies a
        WHERE a.id = %s AND a.house = %s
          AND NOT EXISTS (SELECT 1 FROM visa_registrations vr WHERE vr.agency_id = a.id)
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (agency_id, current_house()))
                return cursor.rowcount > 0
    finally:
        conn.close()
