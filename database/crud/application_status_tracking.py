from __future__ import annotations

from typing import Any

from psycopg2.extras import Json, RealDictCursor

from database.connection import get_connection


_UPDATABLE_COLUMNS = {
    "first_applyid",
    "application_code",
    "full_name",
    "initial_status",
    "current_status",
    "apply_status_raw",
    "is_active",
    "note",
    "payload",
    "status_changed_at",
    "last_checked_at",
}


def get_active_tracking_by_passport(passport_number: str) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM application_status_trackings
        WHERE passport_number = %s AND is_active
        LIMIT 1
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (passport_number,))
                row = cursor.fetchone()
                return dict(row) if row else None
    finally:
        conn.close()


def create_tracking(
    passport_number: str,
    group_id: str = "",
    sender_id: str = "",
    sender_name: str = "",
) -> dict[str, Any] | None:
    """Insert a new active tracking; return ``None`` if one is already active."""
    sql = """
        INSERT INTO application_status_trackings (
            passport_number,
            group_id,
            sender_id,
            sender_name
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (passport_number) WHERE is_active DO NOTHING
        RETURNING *
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    sql,
                    (passport_number, group_id, sender_id, sender_name),
                )
                row = cursor.fetchone()
                return dict(row) if row else None
    finally:
        conn.close()


def list_active_trackings() -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM application_status_trackings
        WHERE is_active
        ORDER BY id ASC
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql)
                return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def list_finished_tracking_applyids(passport_number: str) -> set[str]:
    sql = """
        SELECT first_applyid
        FROM application_status_trackings
        WHERE passport_number = %s AND NOT is_active AND first_applyid <> ''
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (passport_number,))
                return {str(row[0]) for row in cursor.fetchall()}
    finally:
        conn.close()


def update_tracking(record_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
    columns = [key for key in fields if key in _UPDATABLE_COLUMNS]
    if not columns:
        return None

    assignments = ", ".join(f"{column} = %s" for column in columns)
    values = [
        Json(fields[column]) if column == "payload" else fields[column]
        for column in columns
    ]
    sql = f"""
        UPDATE application_status_trackings
        SET {assignments}, updated_at = NOW()
        WHERE id = %s
        RETURNING *
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (*values, record_id))
                row = cursor.fetchone()
                return dict(row) if row else None
    finally:
        conn.close()
