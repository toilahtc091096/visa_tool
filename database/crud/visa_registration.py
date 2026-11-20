"""visa_registrations of the current house (database/house.py).

Every query filters on house: the database is shared by all houses, and the
sync, HAN approval and agency jobs of one instance must never touch another
house's records (they run with that house's account and token).
"""

from __future__ import annotations

from typing import Any

from psycopg2.extras import RealDictCursor, Json

from database.connection import get_connection
from database.house import current_house
from database.models.visa_registration import VisaRegistration


def _execute(sql: str, params: tuple, fetch: str = "", dict_rows: bool = False) -> Any:
    """Run one statement. fetch: "" -> rowcount, "one" -> one row, "all" -> rows."""
    conn = get_connection()
    try:
        with conn:
            factory = RealDictCursor if dict_rows else None
            with conn.cursor(cursor_factory=factory) as cursor:
                cursor.execute(sql, params)
                if fetch == "one":
                    return cursor.fetchone()
                if fetch == "all":
                    return list(cursor.fetchall())
                return cursor.rowcount
    finally:
        conn.close()


def create_visa_registration(item: VisaRegistration) -> int:
    # house, staff_code and job_id of an existing record are kept: the
    # record belongs to whoever ran it first.
    sql = """
        INSERT INTO visa_registrations (
            first_applyid,
            application_code,
            full_name,
            passport_number,
            visa_type,
            status,
            payload,
            house,
            staff_code,
            job_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            skip = FALSE,
            staff_code = COALESCE(NULLIF(visa_registrations.staff_code, ''), EXCLUDED.staff_code),
            job_id = COALESCE(NULLIF(visa_registrations.job_id, ''), EXCLUDED.job_id),
            updated_at = NOW()
        WHERE visa_registrations.house = EXCLUDED.house
        RETURNING id
    """
    house = current_house()
    row = _execute(
        sql,
        (
            item.first_applyid or None,
            item.application_code,
            item.full_name,
            item.passport_number,
            item.visa_type,
            item.status,
            Json(item.payload),
            house,
            (item.staff_code or "").strip().upper(),
            (item.job_id or "").strip(),
        ),
        fetch="one",
    )
    if row is None:
        raise RuntimeError(
            f"first_applyid {item.first_applyid} already belongs to another house, not {house}"
        )
    return int(row[0])


def set_visa_registration_owner(record_id: int, staff_code: str, job_id: str = "") -> bool:
    """Record who started the registration; an owner already set is kept (first run wins)."""
    sql = """
        UPDATE visa_registrations
        SET staff_code = COALESCE(NULLIF(staff_code, ''), %s),
            job_id = COALESCE(NULLIF(job_id, ''), %s),
            updated_at = NOW()
        WHERE id = %s AND house = %s
    """
    params = (str(staff_code or "").strip().upper(), str(job_id or "").strip(), record_id, current_house())
    return _execute(sql, params) > 0


def get_visa_registration_by_first_applyid(first_applyid: str) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE first_applyid = %s AND house = %s
        LIMIT 1
    """
    return _execute(sql, (first_applyid, current_house()), fetch="one", dict_rows=True)


def get_visa_registration_by_id(record_id: int) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE id = %s AND house = %s
    """
    return _execute(sql, (record_id, current_house()), fetch="one", dict_rows=True)


def get_visa_registration_by_passport(passport_number: str) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE passport_number = %s AND house = %s
        ORDER BY id DESC
        LIMIT 1
    """
    return _execute(sql, (passport_number, current_house()), fetch="one", dict_rows=True)


def get_visa_registration_by_application_code(
    application_code: str,
) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE application_code = %s AND house = %s
        ORDER BY id DESC
        LIMIT 1
    """
    return _execute(sql, (application_code, current_house()), fetch="one", dict_rows=True)


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
        WHERE application_code = ANY(%s) AND house = %s
    """
    rows = _execute(sql, (codes, current_house()), fetch="all")
    return {str(row[0]).strip() for row in rows if row[0]}


def list_visa_registrations(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE house = %s
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """
    return _execute(sql, (current_house(), limit, offset), fetch="all", dict_rows=True)


def list_visa_registrations_by_status(
    status: str,
    limit: int | None = None,
    offset: int = 0,
    include_skipped: bool = True,
) -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM visa_registrations
        WHERE status = %s AND house = %s
    """
    if not include_skipped:
        sql += " AND NOT skip"
    sql += " ORDER BY id DESC"
    params: list[Any] = [status, current_house()]
    if limit is not None:
        sql += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
    return _execute(sql, tuple(params), fetch="all", dict_rows=True)


def update_visa_registration_status(record_id: int, status: str) -> bool:
    sql = """
        UPDATE visa_registrations
        SET status = %s,
            updated_at = NOW()
        WHERE id = %s AND house = %s
    """
    return _execute(sql, (status, record_id, current_house())) > 0


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
            WHERE id = %s AND house = %s
        """
        params = (status, Json(payload or {}), record_id, current_house())
    else:
        sql = """
            UPDATE visa_registrations
            SET status = %s,
                payload = %s,
                application_code = COALESCE(NULLIF(%s, ''), application_code),
                updated_at = NOW()
            WHERE id = %s AND house = %s
        """
        params = (status, Json(payload or {}), application_code, record_id, current_house())
    return _execute(sql, params) > 0


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
        WHERE id = %s AND house = %s
    """
    house = current_house()
    params: list[tuple[Any, ...]] = []
    for item in updates:
        record_id = item.get("record_id")
        status = item.get("status")
        payload = item.get("payload")
        if record_id is None or status is None:
            continue
        application_code = str(item.get("application_code") or "").strip()
        params.append((status, Json(payload or {}), application_code, record_id, house))

    if not params:
        return 0

    updated_count = 0
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                for row_params in params:
                    cursor.execute(sql, row_params)
                    if cursor.rowcount > 0:
                        updated_count += 1
        return updated_count
    finally:
        conn.close()


def delete_visa_registration(record_id: int) -> bool:
    sql = """
        DELETE FROM visa_registrations
        WHERE id = %s AND house = %s
    """
    return _execute(sql, (record_id, current_house())) > 0


def delete_visa_registrations_by_passport_except_status(
    passport_number: str,
    status: str,
) -> int:
    sql = """
        DELETE FROM visa_registrations
        WHERE passport_number = %s
          AND status <> %s
          AND house = %s
    """
    return _execute(sql, (passport_number, status, current_house()))


def set_visa_registration_vip(record_id: int, is_vip: bool) -> None:
    sql = """
        UPDATE visa_registrations
        SET is_vip = %s, updated_at = NOW()
        WHERE id = %s AND house = %s
    """
    _execute(sql, (bool(is_vip), record_id, current_house()))
