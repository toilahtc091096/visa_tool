"""House (nhà) served by this server instance.

All houses share one Postgres database; every row of visa_registrations,
han_approval_jobs and agencies carries the house it belongs to, and every
query of database/crud filters on the current house (except the admin
reports in database/crud/admin_report.py, which read all houses on purpose).

HOUSE in the instance's .env names the house. Without it the house comes from
PORT (one instance per house on the VPS).
"""

from __future__ import annotations

import os

import env_loader  # noqa: F401  (loads .env before reading HOUSE/PORT)

HOUSE_BY_PORT = {"10000": "HAI", "20000": "PHONG", "30000": "TAI"}
HOUSES = tuple(HOUSE_BY_PORT.values())


def current_house(required: bool = True) -> str:
    house = os.getenv("HOUSE", "").strip().upper()
    if not house:
        house = HOUSE_BY_PORT.get(os.getenv("PORT", "").strip(), "")
    if house and house not in HOUSES:
        raise RuntimeError(f"HOUSE must be one of {', '.join(HOUSES)}, got {house!r}")
    if required and not house:
        raise RuntimeError("Set HOUSE (HAI, PHONG or TAI) or PORT in .env: the database is shared by all houses")
    return house
