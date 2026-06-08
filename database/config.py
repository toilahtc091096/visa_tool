from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    user: str = ""
    password: str = ""

    @staticmethod
    def from_env() -> "DatabaseConfig":
        return DatabaseConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "visa_db"),
            user=os.getenv("POSTGRES_USER", "visa_user"),
            password=os.getenv("POSTGRES_PASSWORD", "123456"),
        )
