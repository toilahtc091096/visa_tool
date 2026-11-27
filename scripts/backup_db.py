"""Nightly Postgres backup: pg_dump -> local file -> R2, old copies removed.

    .venv\\Scripts\\python.exe scripts\\backup_db.py            # uses .env
    .venv\\Scripts\\python.exe scripts\\backup_db.py --env .env.phong
    .venv\\Scripts\\python.exe scripts\\backup_db.py --no-upload  # local file only

Env (from the env file):
    POSTGRES_HOST / PORT / DB / USER / PASSWORD   database to dump
    BACKUP_DB           database name, when it differs from POSTGRES_DB
    BACKUP_POSTGRES_USER / BACKUP_POSTGRES_PASSWORD   other account for the dump (e.g. postgres,
                        when POSTGRES_USER cannot read every schema)
    BACKUP_EXCLUDE_SCHEMAS  comma list of schemas left out (e.g. so_loi)
    R2_ENDPOINT_URL / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY / R2_BUCKET_NAME
    BACKUP_R2_BUCKET    bucket for the dumps (default R2_BUCKET_NAME)
    BACKUP_R2_PREFIX    key prefix (default _db-backup/)
    BACKUP_KEEP_DAYS    R2 copies older than this are deleted (default 30)
    BACKUP_LOCAL_KEEP   number of local dumps kept in backups/ (default 7)
    PG_DUMP             full path of pg_dump.exe (default: PATH, then Program Files)

Restore (custom format):
    pg_restore -h <host> -U <user> -d <empty db> --no-owner <file>.dump
Exit code 1 on any failure, so the scheduled task shows it as failed.
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from env_loader import load_dotenv  # noqa: E402

LOCAL_DIR = ROOT / "backups"


def find_pg_dump() -> str:
    explicit = os.getenv("PG_DUMP", "").strip()
    if explicit:
        return explicit
    found = shutil.which("pg_dump")
    if found:
        return found
    candidates = sorted(glob.glob(r"C:\Program Files\PostgreSQL\*\bin\pg_dump.exe"))
    if candidates:
        return candidates[-1]  # newest major version
    raise RuntimeError("pg_dump not found: set PG_DUMP=<path of pg_dump.exe> in the env file")


def backup_db_name() -> str:
    return os.getenv("BACKUP_DB", "").strip() or os.getenv("POSTGRES_DB", "visa_db")


def dump(out_file: Path) -> None:
    user = os.getenv("BACKUP_POSTGRES_USER", "").strip() or os.getenv("POSTGRES_USER", "visa_user")
    password = os.getenv("BACKUP_POSTGRES_PASSWORD", "") if os.getenv("BACKUP_POSTGRES_USER", "").strip() \
        else os.getenv("POSTGRES_PASSWORD", "")
    env = dict(os.environ, PGPASSWORD=password)
    cmd = [
        find_pg_dump(),
        "-h", os.getenv("POSTGRES_HOST", "localhost"),
        "-p", os.getenv("POSTGRES_PORT", "5432"),
        "-U", user,
        "-d", backup_db_name(),
        "-Fc", "--no-owner", "-f", str(out_file),
    ]
    for schema in filter(None, (s.strip() for s in os.getenv("BACKUP_EXCLUDE_SCHEMAS", "").split(","))):
        cmd += ["-N", schema]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        out_file.unlink(missing_ok=True)
        raise RuntimeError(f"pg_dump failed ({result.returncode}): {result.stderr.strip()}")
    if out_file.stat().st_size == 0:
        raise RuntimeError("pg_dump wrote an empty file")


def old_keys(objects: list[dict], prefix: str, keep_days: int, now: datetime) -> list[str]:
    """Keys under `prefix` older than keep_days; the newest dump is always kept."""
    dumps = [o for o in objects if o["Key"].startswith(prefix) and o["Key"].endswith(".dump")]
    if not dumps:
        return []
    newest = max(dumps, key=lambda o: o["LastModified"])["Key"]
    limit = now - timedelta(days=keep_days)
    return [o["Key"] for o in dumps if o["LastModified"] < limit and o["Key"] != newest]


def upload_and_prune(out_file: Path) -> str:
    from utils.r2_env import build_r2_client

    client, config = build_r2_client(log=False)
    bucket = os.getenv("BACKUP_R2_BUCKET", "").strip() or config.bucket_name
    prefix = os.getenv("BACKUP_R2_PREFIX", "_db-backup/").strip() or "_db-backup/"
    keep_days = int(os.getenv("BACKUP_KEEP_DAYS", "30"))
    key = prefix + out_file.name
    client.upload_file(str(out_file), bucket, key)
    client.head_object(Bucket=bucket, Key=key)  # make sure it is really there

    objects: list[dict] = []
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        objects.extend(page.get("Contents", []))
    for old in old_keys(objects, prefix, keep_days, datetime.now(timezone.utc)):
        client.delete_object(Bucket=bucket, Key=old)
        print(f"removed old R2 copy {bucket}/{old}")
    return f"{bucket}/{key}"


def prune_local(keep: int) -> None:
    files = sorted(LOCAL_DIR.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        old.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", default=".env", help="env file (default .env)")
    parser.add_argument("--no-upload", action="store_true", help="keep the dump on disk only")
    args = parser.parse_args()

    load_dotenv(args.env)
    LOCAL_DIR.mkdir(exist_ok=True)
    db = backup_db_name()
    out_file = LOCAL_DIR / f"{db}-{datetime.now():%Y%m%d-%H%M}.dump"
    try:
        dump(out_file)
        size_mb = out_file.stat().st_size / 1024 / 1024
        print(f"dumped {db} -> {out_file} ({size_mb:.1f} MB)")
        if not args.no_upload:
            print(f"uploaded -> {upload_and_prune(out_file)}")
        prune_local(int(os.getenv("BACKUP_LOCAL_KEEP", "7")))
    except Exception as exc:  # noqa: BLE001 - one line in the log, non-zero exit
        print(f"BACKUP FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
