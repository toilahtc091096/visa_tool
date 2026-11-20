"""Accounts for the /web input form."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

from psycopg2.extras import RealDictCursor

from database.connection import get_connection

_ITERATIONS = 200_000


def hash_password(password: str, *, salt: bytes | None = None, iterations: int = _ITERATIONS) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, digest_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, AttributeError):
        return False


def new_api_key() -> str:
    return secrets.token_hex(24)


def upsert_web_user(username: str, password: str, staff_code: str, *, reset_key: bool = False) -> dict[str, Any]:
    """Create the account, or update password/staff (and the key if reset_key)."""
    username = str(username or "").strip().lower()
    staff_code = str(staff_code or "").strip().upper()
    if not username or not password or not staff_code:
        raise ValueError("username, password and staff_code are required")
    sql = """
        INSERT INTO web_users (username, password_hash, staff_code, api_key)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (username) DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            staff_code = EXCLUDED.staff_code,
            api_key = CASE WHEN %s THEN EXCLUDED.api_key ELSE web_users.api_key END,
            active = TRUE,
            updated_at = NOW()
        RETURNING id, username, staff_code, api_key, active
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, (username, hash_password(password), staff_code, new_api_key(), reset_key))
                return dict(cursor.fetchone())
    finally:
        conn.close()


def set_web_user_active(username: str, active: bool) -> bool:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE web_users SET active = %s, updated_at = NOW() WHERE username = %s",
                    (active, str(username or "").strip().lower()),
                )
                return cursor.rowcount > 0
    finally:
        conn.close()


def _fetch_one(sql: str, params: tuple) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def authenticate_web_user(username: str, password: str) -> dict[str, Any] | None:
    row = _fetch_one(
        "SELECT id, username, staff_code, api_key, password_hash FROM web_users WHERE username = %s AND active",
        (str(username or "").strip().lower(),),
    )
    if not row or not verify_password(password or "", row.pop("password_hash")):
        return None
    return row


def get_web_user_by_api_key(api_key: str) -> dict[str, Any] | None:
    key = str(api_key or "").strip()
    if not key:
        return None
    return _fetch_one(
        "SELECT id, username, staff_code, api_key FROM web_users WHERE api_key = %s AND active",
        (key,),
    )
