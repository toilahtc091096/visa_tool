from __future__ import annotations

from typing import Any

from psycopg2.extras import RealDictCursor

from database.connection import get_connection


def get_or_create_agency(code: str) -> dict[str, Any]:
    """Return the agency with this code, creating it (name = code) if new."""
    code = str(code or "").strip().upper()
    if not code:
        raise ValueError("agency code is required")

    sql = """
        INSERT INTO agencies (code, name)
        VALUES (%s, %s)
        ON CONFLICT (code) DO UPDATE SET code = EXCLUDED.code
        RETURNING id, code, name
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (code, code))
                return dict(cursor.fetchone())
    finally:
        conn.close()


def set_visa_registration_agency(
    record_id: int,
    agency_id: int,
    overwrite: bool = True,
) -> bool:
    """
    Link a registration to an agency. With overwrite=False an agency already
    set is kept (a re-run without a code must not replace the real agency).
    """
    if overwrite:
        sql = """
            UPDATE visa_registrations
            SET agency_id = %s, updated_at = NOW()
            WHERE id = %s
        """
    else:
        sql = """
            UPDATE visa_registrations
            SET agency_id = COALESCE(agency_id, %s), updated_at = NOW()
            WHERE id = %s
        """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (agency_id, record_id))
                return cursor.rowcount > 0
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
          AND NOT (a.code = ANY(%s))
        ORDER BY vr.id
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (ids, list(exclude_codes or [])))
                return list(cursor.fetchall())
    finally:
        conn.close()
