from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg2
from psycopg2.extensions import connection as PGConnection

from database.config import DatabaseConfig


def _build_dsn(config: DatabaseConfig) -> str:
    return (
        f"host={config.host} "
        f"port={config.port} "
        f"dbname={config.database} "
        f"user={config.user} "
        f"password={config.password}"
    )


def get_connection(config: DatabaseConfig | None = None) -> PGConnection:
    cfg = config or DatabaseConfig.from_env()
    return psycopg2.connect(_build_dsn(cfg))


@contextmanager
def connection_cursor(
    config: DatabaseConfig | None = None,
) -> Iterator[tuple[PGConnection, Any]]:
    conn = get_connection(config)
    try:
        with conn:
            with conn.cursor() as cursor:
                yield conn, cursor
    finally:
        conn.close()


HOUSE_TABLES = ("visa_registrations", "han_approval_jobs", "agencies")

# Rows without a house belong to the house of this instance, but only while the
# table holds no other house's rows (the database is still this house's own).
# In the shared database every row already has its house: nothing is claimed.
_CLAIM_SQL = """
    UPDATE {table} SET house = %(house)s
    WHERE house = ''
      AND NOT EXISTS (SELECT 1 FROM {table} WHERE house NOT IN ('', %(house)s))
"""

_SEED_AGENCIES_SQL = """
    INSERT INTO agencies (house, code, name) VALUES
        (%(house)s, 'MB', 'Miền Bắc'),
        (%(house)s, 'CHUNG', 'Đại lý chung')
    ON CONFLICT (house, code) DO NOTHING
"""


def init_database(config: DatabaseConfig | None = None, house: str | None = None) -> None:
    """
    Create or upgrade the tables (schema.sql). With a house (default: the
    instance's house, when known) also tag that house's untagged rows and
    create its MB and CHUNG agencies.
    """
    from database.house import current_house

    schema_path = Path(__file__).resolve().parent / "schema.sql"
    ddl = schema_path.read_text(encoding="utf-8")
    if house is None:
        house = current_house(required=False)

    conn = get_connection(config)
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(ddl)
                if house:
                    for table in HOUSE_TABLES:
                        cursor.execute(_CLAIM_SQL.format(table=table), {"house": house})
                    cursor.execute(_SEED_AGENCIES_SQL, {"house": house})
    finally:
        conn.close()
