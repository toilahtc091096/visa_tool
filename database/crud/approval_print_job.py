from __future__ import annotations

from typing import Any

from psycopg2.extras import Json, RealDictCursor

from database.connection import get_connection


def get_approval_print_job_by_han_code(han_code: str) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM han_approval_jobs
        WHERE han_code = %s
        LIMIT 1
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (han_code,))
                return cursor.fetchone()
    finally:
        conn.close()


def upsert_approval_print_job_processing(
    han_code: str,
    source_email: str = "",
    message_id: str = "",
    subject: str = "",
) -> dict[str, Any]:
    sql = """
        INSERT INTO han_approval_jobs (
            han_code,
            source_email,
            message_id,
            subject,
            status,
            attempt_count,
            last_error,
            updated_at
        )
        VALUES (%s, %s, %s, %s, 'printing', 1, '', NOW())
        ON CONFLICT (han_code) DO UPDATE
        SET source_email = EXCLUDED.source_email,
            message_id = EXCLUDED.message_id,
            subject = EXCLUDED.subject,
            status = 'printing',
            attempt_count = han_approval_jobs.attempt_count + 1,
            last_error = '',
            updated_at = NOW()
        RETURNING *
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    sql,
                    (
                        han_code,
                        source_email,
                        message_id,
                        subject,
                    ),
                )
                row = cursor.fetchone()
                return dict(row) if row else {}
    finally:
        conn.close()


def update_approval_print_job_by_han_code(
    han_code: str,
    status: str,
    attachment_paths: list[str] | None = None,
    application_form_path: str = "",
    last_error: str = "",
) -> bool:
    sql = """
        UPDATE han_approval_jobs
        SET status = %s,
            attachment_paths = COALESCE(%s, attachment_paths),
            application_form_path = COALESCE(%s, application_form_path),
            last_error = %s,
            printed_at = CASE WHEN %s = 'printed' THEN NOW() ELSE printed_at END,
            updated_at = NOW()
        WHERE han_code = %s
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    (
                        status,
                        Json(attachment_paths) if attachment_paths is not None else None,
                        application_form_path or None,
                        last_error or "",
                        status,
                        han_code,
                    ),
                )
                return cursor.rowcount > 0
    finally:
        conn.close()


def update_approval_print_job_status_by_ids(
    record_ids: list[int],
    status: str,
) -> int:
    record_ids = [int(record_id) for record_id in record_ids if str(record_id).strip()]
    if not record_ids:
        return 0

    sql = """
        UPDATE han_approval_jobs
        SET status = %s,
            last_error = '',
            updated_at = NOW()
        WHERE id = ANY(%s)
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (status, record_ids))
                return cursor.rowcount
    finally:
        conn.close()


def update_approval_print_job_status_by_codes(
    han_codes: list[str],
    status: str,
) -> int:
    han_codes = [str(han_code).strip() for han_code in han_codes if str(han_code).strip()]
    if not han_codes:
        return 0

    sql = """
        UPDATE han_approval_jobs
        SET status = %s,
            last_error = '',
            updated_at = NOW()
        WHERE han_code = ANY(%s)
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (status, han_codes))
                return cursor.rowcount
    finally:
        conn.close()


def reset_approval_print_jobs_by_printed_range(
    start_dt,
    end_dt,
) -> int:
    sql = """
        UPDATE han_approval_jobs
        SET status = 'not_print',
            last_error = '',
            printed_at = NULL,
            updated_at = NOW()
        WHERE printed_at >= %s
          AND printed_at < %s
          AND status = 'printed'
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (start_dt, end_dt))
                return cursor.rowcount
    finally:
        conn.close()


def list_approval_print_jobs(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM han_approval_jobs
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
