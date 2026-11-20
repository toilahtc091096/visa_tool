"""Manage /web accounts. Run on the VPS from the repo folder, with the same .env as the server:

    $env:ENV_FILE = ".env"; python scripts\\web_user.py add bao BAO          # asks for the password
    $env:ENV_FILE = ".env"; python scripts\\web_user.py add bao BAO --reset-key
    $env:ENV_FILE = ".env"; python scripts\\web_user.py disable bao

staff_code must match the Railway Telegram variables (TELE_<STAFF>_<HOUSE>_TOKEN).
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import env_loader  # noqa: F401,E402  (loads ENV_FILE like the server)
from database.connection import init_database  # noqa: E402
from database.crud.web_user import set_web_user_active, upsert_web_user  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage /web accounts")
    sub = parser.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add", help="create or update an account (password asked)")
    add.add_argument("username")
    add.add_argument("staff_code", help="BAO / HANG / LONG / ADMIN ...")
    add.add_argument("--reset-key", action="store_true", help="issue a new api key (logs the person out)")
    for name in ("disable", "enable"):
        p = sub.add_parser(name)
        p.add_argument("username")
    args = parser.parse_args()

    init_database()
    if args.cmd == "add":
        password = getpass.getpass("Mật khẩu: ")
        if len(password) < 6 or password != getpass.getpass("Nhập lại: "):
            print("Mật khẩu phải từ 6 ký tự và hai lần nhập phải giống nhau")
            return 1
        user = upsert_web_user(args.username, password, args.staff_code, reset_key=args.reset_key)
        print(f"OK: {user['username']} ({user['staff_code']})")
        return 0
    ok = set_web_user_active(args.username, args.cmd == "enable")
    print("OK" if ok else "Không có tài khoản này")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
