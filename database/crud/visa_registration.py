from __future__ import annotations

from typing import Any

from psycopg2.extras import RealDictCursor, Json

from database.connection import get_connection
from database.models.visa_registration import VisaRegistration


def create_visa_registration(item: VisaRegistration) -> int:
    sql = """
        INSERT INTO visa_registrations (
            first_applyid,
            full_name,
            passport_number,
            visa_type,
            status,
            payload
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (first_applyid) DO UPDATE
        SET full_name = EXCLUDED.full_name,
            passport_number = EXCLUDED.passport_number,
            visa_type = EXCLUDED.visa_type,
            status = EXCLUDED.status,
            payload = EXCLUDED.payload,
            updated_at = NOW()
        RETURNING id
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    (
                        item.first_applyid or None,
                        item.full_name,
                        item.passport_number,
                        item.visa_type,
                        item.status,
                        Json(item.payload),
                    ),
                )
                row = cursor.fetchone()
                return int(row[0])
    finally:
        conn.close()


def get_visa_registration_by_first_applyid(first_applyid: str) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE first_applyid = %s
        LIMIT 1
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (first_applyid,))
                return cursor.fetchone()
    finally:
        conn.close()


def get_visa_registration_by_id(record_id: int) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE id = %s
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (record_id,))
                return cursor.fetchone()
    finally:
        conn.close()


def get_visa_registration_by_passport(passport_number: str) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE passport_number = %s
        ORDER BY id DESC
        LIMIT 1
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (passport_number,))
                return cursor.fetchone()
    finally:
        conn.close()


def list_visa_registrations(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM visa_registrations
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (limit, offset))
                return list(cursor.fetchall())
    finally:
        conn.close()


def list_visa_registrations_by_status(
    status: str,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE status = %s
        ORDER BY id DESC
    """
    params: list[Any] = [status]
    if limit is not None:
        sql += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, tuple(params))
                return list(cursor.fetchall())
    finally:
        conn.close()


def update_visa_registration_status(record_id: int, status: str) -> bool:
    sql = """
        UPDATE visa_registrations
        SET status = %s,
            updated_at = NOW()
        WHERE id = %s
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (status, record_id))
                return cursor.rowcount > 0
    finally:
        conn.close()


def update_visa_registration_status_and_payload(
    record_id: int,
    status: str,
    payload: dict[str, Any] | None = None,
) -> bool:
    sql = """
        UPDATE visa_registrations
        SET status = %s,
            payload = %s,
            updated_at = NOW()
        WHERE id = %s
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (status, Json(payload or {}), record_id))
                return cursor.rowcount > 0
    finally:
        conn.close()


def delete_visa_registration(record_id: int) -> bool:
    sql = """
        DELETE FROM visa_registrations
        WHERE id = %s
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (record_id,))
                return cursor.rowcount > 0
    finally:
        conn.close()
