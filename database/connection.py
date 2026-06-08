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


def init_database(config: DatabaseConfig | None = None) -> None:
    """
    Create the visa registration table if it does not already exist.
    """
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    ddl = schema_path.read_text(encoding="utf-8")

    conn = get_connection(config)
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(ddl)
    finally:
        conn.close()
