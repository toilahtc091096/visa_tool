"""'Ảnh yêu cầu ban đầu' of a web job (start form -> curl tab), kept KEEP_DAYS days."""

from __future__ import annotations

from database.connection import get_connection

KEEP_DAYS = 30
MAX_BYTES = 5 * 1024 * 1024
_PURGE = f"DELETE FROM web_request_images WHERE created_at < NOW() - INTERVAL '{KEEP_DAYS} days'"


def save_request_image(job_id: str, username: str, content_type: str, data: bytes) -> None:
    """Store (or replace) the image of one job and drop images older than KEEP_DAYS."""
    sql = """
        INSERT INTO web_request_images (job_id, username, content_type, data)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (job_id) DO UPDATE SET username = EXCLUDED.username, content_type = EXCLUDED.content_type,
                                           data = EXCLUDED.data, created_at = NOW()
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(_PURGE)
                cursor.execute(sql, (job_id, username, content_type, data))
    finally:
        conn.close()


def get_request_image(job_id: str) -> tuple[str, bytes] | None:
    """(content_type, bytes) of the job's image, None when there is none (or it is too old)."""
    sql = f"""
        SELECT content_type, data FROM web_request_images
        WHERE job_id = %s AND created_at >= NOW() - INTERVAL '{KEEP_DAYS} days'
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (job_id,))
                row = cursor.fetchone()
    finally:
        conn.close()
    return (row[0], bytes(row[1])) if row else None
