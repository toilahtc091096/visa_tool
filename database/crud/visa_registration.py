from __future__ import annotations

from typing import Any

from psycopg2.extras import RealDictCursor, Json

from database.connection import get_connection
from database.models.visa_registration import VisaRegistration


def create_visa_registration(item: VisaRegistration) -> int:
    sql = """
        INSERT INTO visa_registrations (
            first_applyid,
            application_code,
            full_name,
            passport_number,
            visa_type,
            status,
            payload
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (first_applyid) DO UPDATE
        SET application_code = COALESCE(
                NULLIF(EXCLUDED.application_code, ''),
                visa_registrations.application_code
            ),
            full_name = EXCLUDED.full_name,
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
                        item.application_code,
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


def list_existing_visa_registration_application_codes(
    application_codes: list[str],
) -> set[str]:
    codes = [
        str(code or "").strip()
        for code in application_codes
        if str(code or "").strip()
    ]
    if not codes:
        return set()

    sql = """
        SELECT application_code
        FROM visa_registrations
        WHERE application_code = ANY(%s)
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (codes,))
                return {str(row[0]).strip() for row in cursor.fetchall() if row[0]}
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
    application_code: str | None = None,
) -> bool:
    if application_code is None:
        sql = """
            UPDATE visa_registrations
            SET status = %s,
                payload = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        params = (status, Json(payload or {}), record_id)
    else:
        sql = """
            UPDATE visa_registrations
            SET status = %s,
                payload = %s,
                application_code = COALESCE(NULLIF(%s, ''), application_code),
                updated_at = NOW()
            WHERE id = %s
        """
        params = (status, Json(payload or {}), application_code, record_id)

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.rowcount > 0
    finally:
        conn.close()


def batch_update_visa_registration_status_and_payload(
    updates: list[dict[str, Any]],
) -> int:
    if not updates:
        return 0

    sql = """
        UPDATE visa_registrations
        SET status = %s,
            payload = %s,
            application_code = COALESCE(NULLIF(%s, ''), application_code),
            updated_at = NOW()
        WHERE id = %s
    """
    params: list[tuple[Any, Any, Any, Any]] = []
    for item in updates:
        record_id = item.get("record_id")
        status = item.get("status")
        payload = item.get("payload")
        if record_id is None or status is None:
            continue
        application_code = str(item.get("application_code") or "").strip()
        params.append((status, Json(payload or {}), application_code, record_id))

    if not params:
        return 0

    updated_count = 0
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                for status, payload, application_code, record_id in params:
                    cursor.execute(sql, (status, payload, application_code, record_id))
                    if cursor.rowcount > 0:
                        updated_count += 1
        return updated_count
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


def delete_visa_registrations_by_passport_except_status(
    passport_number: str,
    status: str,
) -> int:
    sql = """
        DELETE FROM visa_registrations
        WHERE passport_number = %s
          AND status <> %s
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (passport_number, status))
                return cursor.rowcount
    finally:
        conn.close()
