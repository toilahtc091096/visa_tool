"""Merge the per-house databases into one shared database (W3).

Each house (HAI, PHONG, TAI) had its own database. This copies all of them into
one target database, tagging every row with its house:

  - visa_registrations, han_approval_jobs, agencies: house = the source's house,
    new ids (agency_id is remapped through the agency code).
  - web_users, web_jobs: copied as they are (only the 10000 instance has rows).

The source databases are only read, never changed. Default is a dry run: the
whole copy runs inside a transaction on the target, is checked, then rolled
back. Add --apply to commit.

Run on the VPS from the repo folder (credentials come from ENV_FILE, all houses
use the same Postgres user):

    # 1. dry run (--create makes the empty target database if missing):
    $env:ENV_FILE = ".env"; python scripts\\merge_databases.py --target visa_main --create
    #    stop the 3 instances and their watchdogs, then:
    $env:ENV_FILE = ".env"; python scripts\\merge_databases.py --target visa_main --apply
    # 2. set POSTGRES_DB=visa_main (and HOUSE=...) in the 3 .env files, start the instances.

Sources default to HAI=visa_db, PHONG=visa_db_phong, TAI=visa_db_tai; override with
--source HOUSE=DBNAME (repeatable).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import env_loader  # noqa: F401,E402
import psycopg2  # noqa: E402
from psycopg2.extras import Json, RealDictCursor  # noqa: E402

from database.config import DatabaseConfig  # noqa: E402
from database.connection import get_connection  # noqa: E402
from database.house import HOUSES  # noqa: E402

DEFAULT_SOURCES = {"HAI": "visa_db", "PHONG": "visa_db_phong", "TAI": "visa_db_tai"}
HOUSE_TABLES = ("visa_registrations", "han_approval_jobs")
SHARED_TABLES = ("web_users", "web_jobs")
# (table, column, condition): values that must be unique across all houses.
UNIQUE_KEYS = [
    ("visa_registrations", "first_applyid", "first_applyid IS NOT NULL AND first_applyid <> ''"),
    ("visa_registrations", "application_code", "application_code <> ''"),
    ("han_approval_jobs", "han_code", "TRUE"),
    ("web_users", "username", "TRUE"),
    ("web_users", "api_key", "TRUE"),
    ("web_jobs", "job_id", "TRUE"),
]


def parse_sources(items: list[str] | None) -> dict[str, str]:
    sources = dict(DEFAULT_SOURCES)
    for item in items or []:
        house, sep, db = item.partition("=")
        house = house.strip().upper()
        if not sep or house not in HOUSES or not db.strip():
            raise SystemExit(f"--source must be HOUSE=DBNAME with HOUSE in {HOUSES}: {item!r}")
        sources[house] = db.strip()
    return sources


def table_columns(cursor, table: str) -> list[str]:
    cursor.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position",
        (table,),
    )
    return [row[0] if not isinstance(row, dict) else row["column_name"] for row in cursor.fetchall()]


def read_table(conn, table: str) -> tuple[list[str], list[dict[str, Any]]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cols = table_columns(cursor, table)
        if not cols:
            return [], []
        cursor.execute(f'SELECT * FROM "{table}" ORDER BY 1')
        return cols, [dict(row) for row in cursor.fetchall()]


def find_duplicates(data: dict[str, dict[str, list[dict[str, Any]]]]) -> list[str]:
    """Values of UNIQUE_KEYS found in more than one row across all sources."""
    problems = []
    for table, column, _ in UNIQUE_KEYS:
        seen: dict[str, str] = {}
        for house, tables in data.items():
            for row in tables.get(table, []):
                value = row.get(column)
                if value is None or str(value).strip() == "":
                    continue
                value = str(value).strip()
                if value in seen:
                    problems.append(f"{table}.{column} = {value!r} có ở cả {seen[value]} và {house}")
                else:
                    seen[value] = house
    return problems


def drop_duplicate_han_jobs(data: dict[str, dict[str, list[dict[str, Any]]]], keep: str) -> list[tuple[str, str]]:
    """han_approval_jobs rows of other houses whose han_code the `keep` house also has: removed
    from `data` (not from the source databases). Returns (house, han_code) of the dropped rows."""
    kept = {str(r.get("han_code") or "").strip() for r in data.get(keep, {}).get("han_approval_jobs", [])}
    dropped = []
    for house, tables in data.items():
        if house == keep:
            continue
        rows = tables.get("han_approval_jobs", [])
        tables["han_approval_jobs"] = [r for r in rows if str(r.get("han_code") or "").strip() not in kept]
        dropped += [(house, str(r.get("han_code")).strip()) for r in rows
                    if str(r.get("han_code") or "").strip() in kept]
    return dropped


def wrong_house_rows(house: str, tables: dict[str, list[dict[str, Any]]]) -> list[str]:
    problems = []
    for table in (*HOUSE_TABLES, "agencies"):
        for row in tables.get(table, []):
            tagged = str(row.get("house") or "").strip().upper()
            if tagged and tagged != house:
                problems.append(f"{table} id={row.get('id')} của DB nhà {house} lại ghi house={tagged}")
    return problems


def _value(v: Any) -> Any:
    return Json(v) if isinstance(v, (dict, list)) else v


def insert_rows(cursor, table: str, target_cols: list[str], rows: list[dict[str, Any]],
                skip: tuple[str, ...] = ("id",), overrides: dict[str, Any] | None = None,
                returning: str = "") -> list[Any]:
    """Insert rows keeping the columns the target has. Returns RETURNING values."""
    out = []
    for row in rows:
        values = {k: v for k, v in row.items() if k in target_cols and k not in skip}
        values.update(overrides(row) if callable(overrides) else (overrides or {}))
        cols = list(values)
        sql = (f'INSERT INTO "{table}" ({", ".join(cols)}) VALUES ({", ".join(["%s"] * len(cols))})'
               + (f" RETURNING {returning}" if returning else ""))
        cursor.execute(sql, [_value(values[c]) for c in cols])
        if returning:
            out.append(cursor.fetchone()[0])
    return out


def create_database(base: DatabaseConfig, name: str) -> bool:
    """CREATE DATABASE name (connected through the ENV_FILE database). False if it already exists."""
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", name):
        raise SystemExit(f"Tên DB chỉ gồm chữ thường, số, dấu _: {name!r}")
    conn = get_connection(base)
    try:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
            if cursor.fetchone():
                return False
            cursor.execute(f'CREATE DATABASE "{name}"')
            return True
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge the per-house databases into one")
    parser.add_argument("--target", required=True, help="target database (empty; see --create)")
    parser.add_argument("--create", action="store_true", help="create the target database if it does not exist")
    parser.add_argument("--source", action="append", help="HOUSE=DBNAME (default: HAI=visa_db, PHONG=visa_db_phong, TAI=visa_db_tai)")
    parser.add_argument("--apply", action="store_true", help="commit (default: dry run, rolled back)")
    parser.add_argument("--han-keep", metavar="HOUSE",
                        help="han_code found in several houses: keep this house's row, drop the others")
    args = parser.parse_args()
    han_keep = (args.han_keep or "").strip().upper()
    if han_keep and han_keep not in HOUSES:
        raise SystemExit(f"--han-keep must be one of {HOUSES}")

    base = DatabaseConfig.from_env()
    sources = parse_sources(args.source)
    if args.target in sources.values():
        raise SystemExit("Target must be a new database, not one of the sources")
    if args.create:
        created = create_database(base, args.target)
        print(f"[create] {args.target}: {'đã tạo' if created else 'đã có sẵn'}")

    # ---- read every source (read only) ----
    data: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for house, db in sources.items():
        conn = get_connection(replace(base, database=db))
        try:
            conn.set_session(readonly=True)
            data[house] = {}
            for table in (*HOUSE_TABLES, "agencies", *SHARED_TABLES):
                cols, rows = read_table(conn, table)
                data[house][table] = rows
                print(f"[read] {house:5} {db:15} {table:20} {len(rows):6} rows" + ("" if cols else "  (no table)"))
        finally:
            conn.close()

    if han_keep:
        for house, code in drop_duplicate_han_jobs(data, han_keep):
            print(f"[han-keep] bỏ han_code {code} của {house}, giữ bản của {han_keep}")

    problems = find_duplicates(data)
    for house, tables in data.items():
        problems += wrong_house_rows(house, tables)
    if problems:
        print("\nKHÔNG GỘP ĐƯỢC, cần xử lý trước:")
        for p in problems:
            print("  -", p)
        return 1

    # ---- copy into the target, in one transaction ----
    schema = (Path(__file__).resolve().parent.parent / "database" / "schema.sql").read_text(encoding="utf-8")
    conn = get_connection(replace(base, database=args.target))
    try:
        with conn.cursor() as cursor:
            cursor.execute(schema)
            cursor.execute("SELECT (SELECT COUNT(*) FROM visa_registrations) + (SELECT COUNT(*) FROM han_approval_jobs)"
                           " + (SELECT COUNT(*) FROM web_users)")
            if cursor.fetchone()[0]:
                raise SystemExit(f"Target {args.target} already has data: use a new empty database")
            target_cols = {t: table_columns(cursor, t) for t in (*HOUSE_TABLES, "agencies", *SHARED_TABLES)}

            for house, tables in data.items():
                # agencies: old id -> new id (MB and CHUNG are created for every house)
                agency_map: dict[Any, int] = {}
                for row in tables["agencies"]:
                    cursor.execute(
                        "INSERT INTO agencies (house, code, name, created_at, updated_at) VALUES (%s, %s, %s, %s, %s) "
                        "ON CONFLICT (house, code) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                        (house, row["code"], row.get("name") or "", row["created_at"], row["updated_at"]),
                    )
                    agency_map[row["id"]] = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO agencies (house, code, name) VALUES (%s, 'MB', 'Miền Bắc'), (%s, 'CHUNG', 'Đại lý chung') "
                    "ON CONFLICT (house, code) DO NOTHING",
                    (house, house),
                )
                missing = {r.get("agency_id") for r in tables["visa_registrations"]} - set(agency_map) - {None}
                if missing:
                    raise SystemExit(f"{house}: visa_registrations point to unknown agency ids {sorted(missing)}")

                insert_rows(cursor, "visa_registrations", target_cols["visa_registrations"], tables["visa_registrations"],
                            overrides=lambda r, h=house, m=agency_map: {
                                "house": h, "agency_id": m.get(r.get("agency_id")) if r.get("agency_id") else None})
                insert_rows(cursor, "han_approval_jobs", target_cols["han_approval_jobs"], tables["han_approval_jobs"],
                            overrides={"house": house})
                insert_rows(cursor, "web_users", target_cols["web_users"], tables["web_users"])
                insert_rows(cursor, "web_jobs", target_cols["web_jobs"], tables["web_jobs"], skip=())

            # ---- check: counts per house in the target match the sources ----
            ok = True
            print()
            for house, tables in data.items():
                for table in HOUSE_TABLES:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE house = %s", (house,))
                    got, want = cursor.fetchone()[0], len(tables[table])
                    ok &= got == want
                    print(f"[check] {house:5} {table:20} source {want:6}  target {got:6}  {'OK' if got == want else 'SAI'}")
            for table in SHARED_TABLES:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                got, want = cursor.fetchone()[0], sum(len(t[table]) for t in data.values())
                ok &= got == want
                print(f"[check] all   {table:20} source {want:6}  target {got:6}  {'OK' if got == want else 'SAI'}")
            cursor.execute("SELECT COUNT(*) FROM visa_registrations WHERE house = ''")
            ok &= cursor.fetchone()[0] == 0

        if not ok:
            conn.rollback()
            print("\nSố dòng không khớp: đã huỷ, target không đổi")
            return 1
        if args.apply:
            conn.commit()
            print(f"\nĐÃ GỘP vào {args.target}. Đổi POSTGRES_DB={args.target} trong .env của cả 3 nhà rồi khởi động lại.")
        else:
            conn.rollback()
            print(f"\nChạy thử xong, mọi thứ khớp. Đã huỷ (target {args.target} vẫn trống). Thêm --apply để gộp thật.")
        return 0
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
