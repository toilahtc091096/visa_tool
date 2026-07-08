from __future__ import annotations

import asyncio
import email
import imaplib
import mimetypes
import os
import re
import shutil
import smtplib
import traceback
import unicodedata
import zipfile
from datetime import date, datetime, time as dt_time, timedelta, timezone, tzinfo
from email.header import decode_header, make_header
from email.message import EmailMessage, Message
from email.policy import default as email_default_policy
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo
from api import get_list_old_by_visa_number
import httpx
from utils.token_store import load_token, load_tmpSecret

from api import api_download_application_form
from database.crud.approval_print_job import (
    get_approval_print_job_by_han_code,
    list_approval_print_jobs,
    update_approval_print_job_by_han_code,
    update_approval_print_job_status_by_codes,
    update_approval_print_job_status_by_ids,
    upsert_approval_print_job_processing,
)
from database.crud.visa_registration import (
    get_visa_registration_by_application_code,
    list_existing_visa_registration_application_codes,
)
from utils import append_authorization, log_exception, load_login_payload, log_event


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    value = _env(name, "1" if default else "0").lower()
    return value in {"1", "true", "yes", "on"}


def _is_match_with_database_enabled() -> bool:
    return _env_bool("IS_MATCH_WITH_DATABASE", False)


def _env_int(name: str, default: int) -> int:
    raw = _env(name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFD", value or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.casefold()


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _sanitize_filename(name: str) -> str:
    candidate = os.path.basename((name or "").strip())
    candidate = re.sub(r"[^A-Za-z0-9._-]+", "_", candidate)
    return candidate or "attachment.pdf"


def _extract_message_text(message: Message) -> str:
    if message.is_multipart():
        parts: list[str] = []
        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            if content_type not in {"text/plain", "text/html"}:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                text = payload.decode(charset, errors="replace")
            except LookupError:
                text = payload.decode("utf-8", errors="replace")
            parts.append(text)
        return "\n".join(parts)

    payload = message.get_payload(decode=True)
    if not payload:
        raw_payload = message.get_payload()
        return raw_payload if isinstance(raw_payload, str) else ""

    charset = message.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _iter_pdf_attachments(message: Message) -> Iterable[tuple[str, bytes]]:
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        filename = part.get_filename()
        content_type = (part.get_content_type() or "").lower()
        disposition = (part.get_content_disposition() or "").lower()
        if (
            not filename
            and disposition != "attachment"
            and content_type != "application/pdf"
        ):
            continue
        if (
            filename
            and not filename.lower().endswith(".pdf")
            and content_type != "application/pdf"
        ):
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        safe_name = _sanitize_filename(
            _decode_header_value(filename) or "attachment.pdf"
        )
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"
        yield safe_name, payload


def _extract_han_codes(text: str) -> list[str]:
    if not text:
        return []
    matches = re.findall(r"\bHAN[A-Z0-9_-]+\b", text.upper())
    seen: set[str] = set()
    ordered: list[str] = []
    for item in matches:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _extract_applyid_by_al_form_id(
    list_result: dict[str, Any],
    al_form_id: str,
) -> str:
    target = str(al_form_id or "").strip()
    response = list_result.get("response") if isinstance(list_result, dict) else {}
    rows = response.get("rows") if isinstance(response, dict) else None
    if not target or not isinstance(rows, list):
        return ""

    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("alFormId") or "").strip() == target:
            return str(row.get("applyid") or "").strip()
    return ""


def _subject_or_body_has_keyword(subject: str, body: str) -> bool:
    keyword = _env("EMAIL_APPROVAL_KEYWORD", "chấp thuận")
    if not keyword:
        return True
    combined = f"{subject}\n{body}"
    return _normalize_text(keyword) in _normalize_text(combined)


def _download_root() -> Path:
    base = _env("HAN_DOWNLOAD_DIR", "").strip() or "resources/han_approval_downloads"
    return Path(base).resolve()


def _zip_download_root(download_root: Path) -> Path:
    zip_path = download_root.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()

    log_event(
        {
            "level": "info",
            "component": "han_approval",
            "state": "download_folder_zip_start",
            "download_root": str(download_root),
            "zip_path": str(zip_path),
        }
    )
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in sorted(download_root.rglob("*")):
            if path.is_file():
                zip_file.write(path, path.relative_to(download_root))
    log_event(
        {
            "level": "info",
            "component": "han_approval",
            "state": "download_folder_zip_done",
            "download_root": str(download_root),
            "zip_path": str(zip_path),
            "byte_size": zip_path.stat().st_size if zip_path.exists() else 0,
        }
    )
    return zip_path


def _zip_download_folders(download_root: Path, folder_names: list[str]) -> Path:
    zip_path = download_root.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()

    normalized_folder_names = [
        str(folder_name).strip()
        for folder_name in folder_names
        if str(folder_name).strip()
    ]
    log_event(
        {
            "level": "info",
            "component": "han_approval",
            "state": "download_folder_batch_zip_start",
            "download_root": str(download_root),
            "zip_path": str(zip_path),
            "folder_names": normalized_folder_names,
        }
    )
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for folder_name in normalized_folder_names:
            folder_path = download_root / folder_name
            if not folder_path.exists() or not folder_path.is_dir():
                continue
            for path in sorted(folder_path.rglob("*")):
                if path.is_file():
                    zip_file.write(path, path.relative_to(download_root))
    log_event(
        {
            "level": "info",
            "component": "han_approval",
            "state": "download_folder_batch_zip_done",
            "download_root": str(download_root),
            "zip_path": str(zip_path),
            "folder_count": len(normalized_folder_names),
            "byte_size": zip_path.stat().st_size if zip_path.exists() else 0,
        }
    )
    return zip_path


def _cleanup_download_artifacts(download_root: Path, zip_path: Path) -> None:
    errors: list[str] = []
    for path in (download_root, zip_path):
        try:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        except Exception as exc:
            errors.append(f"{path}: {type(exc).__name__}: {exc}")

    log_event(
        {
            "level": "error" if errors else "info",
            "component": "han_approval",
            "state": "download_artifacts_cleanup_done",
            "download_root": str(download_root),
            "zip_path": str(zip_path),
            "errors": errors,
        }
    )


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    if size <= 0:
        return [items]
    return [items[index : index + size] for index in range(0, len(items), size)]


def _parse_scan_day(value: str | None) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None

    raw = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(_get_local_timezone())
        return parsed.date()
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
    return None


def _get_local_timezone() -> tzinfo:
    tz_name = _env("APP_TIMEZONE", "Asia/Bangkok")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone(timedelta(hours=7))


def _default_start_scan() -> datetime:
    tz = _get_local_timezone()
    now = datetime.now(tz)
    return datetime.combine(now.date(), dt_time.min, tzinfo=tz)


def _parse_start_scan(value: str | None) -> datetime:
    tz = _get_local_timezone()
    raw = str(value or "").strip()
    if not raw:
        return _default_start_scan()

    raw = raw.replace("Z", "+00:00")
    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                parsed = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
    if parsed is None:
        return _default_start_scan()

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def _parse_allowed_sender_addresses() -> set[str]:
    raw = _env("EMAIL_IMAP_FROM", "")
    if not raw:
        return set()
    return {
        address.strip().casefold()
        for _name, address in getaddresses([raw])
        if address.strip()
    }


def _extract_sender_addresses(message: Message) -> set[str]:
    from_header = message.get("From", "") or ""
    return {
        address.strip().casefold()
        for _name, address in getaddresses([from_header])
        if address.strip()
    }


def _extract_message_datetime(message: Message) -> datetime | None:
    date_header = message.get("Date", "") or ""
    if not date_header:
        return None
    try:
        parsed = parsedate_to_datetime(date_header)
    except Exception:
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=_get_local_timezone())
    return parsed.astimezone(_get_local_timezone())


def _imap_date(value: datetime) -> str:
    return value.strftime("%d-%b-%Y")


def _imap_connect() -> imaplib.IMAP4_SSL | imaplib.IMAP4:
    host = _env("EMAIL_IMAP_HOST")
    if not host:
        raise RuntimeError("Missing env EMAIL_IMAP_HOST")
    user = _env("EMAIL_IMAP_USER")
    password = _env("EMAIL_IMAP_PASSWORD")
    if not user or not password:
        raise RuntimeError("Missing env EMAIL_IMAP_USER or EMAIL_IMAP_PASSWORD")

    port = _env_int("EMAIL_IMAP_PORT", 993)
    use_ssl = _env_bool("EMAIL_IMAP_USE_SSL", True)
    if use_ssl:
        client: imaplib.IMAP4_SSL | imaplib.IMAP4 = imaplib.IMAP4_SSL(host, port)
    else:
        client = imaplib.IMAP4(host, port)
    client.login(user, password)
    return client


def _smtp_send(
    subject: str,
    body: str,
    attachments: list[str] | None = None,
) -> dict[str, Any]:
    log_event(
        {
            "level": "info",
            "component": "han_approval",
            "state": "smtp_prepare_start",
            "subject": subject,
            "attachment_count": len(attachments or []),
        }
    )
    smtp_host = _env("EMAIL_SMTP_HOST")
    smtp_user = _env("EMAIL_SMTP_USER")
    smtp_password = _env("EMAIL_SMTP_PASSWORD")
    if not smtp_host or not smtp_user or not smtp_password:
        missing = [
            name
            for name, value in (
                ("EMAIL_SMTP_HOST", smtp_host),
                ("EMAIL_SMTP_USER", smtp_user),
                ("EMAIL_SMTP_PASSWORD", smtp_password),
            )
            if not value
        ]
        log_event(
            {
                "level": "error",
                "component": "han_approval",
                "state": "smtp_missing_env",
                "missing": missing,
            }
        )
        return {
            "ok": False,
            "error": "missing_smtp_env",
            "missing": missing,
        }

    smtp_port = _env_int("EMAIL_SMTP_PORT", 465)
    use_ssl = _env_bool("EMAIL_SMTP_USE_SSL", True)
    use_starttls = _env_bool("EMAIL_SMTP_USE_STARTTLS", False)
    email_from = _env("EMAIL_SMTP_FROM", smtp_user)
    email_to = _env("EMAIL_TO")
    if not email_to:
        log_event(
            {
                "level": "error",
                "component": "han_approval",
                "state": "smtp_missing_email_to",
            }
        )
        return {
            "ok": False,
            "error": "missing_email_to",
        }

    recipients = [
        address for _name, address in getaddresses([email_to]) if address.strip()
    ]
    if not recipients:
        recipients = [email_to]

    log_event(
        {
            "level": "info",
            "component": "han_approval",
            "state": "smtp_recipients_resolved",
            "from": email_from,
            "recipients": recipients,
            "raw_email_to": email_to,
        }
    )

    msg = EmailMessage()
    msg["From"] = email_from
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    attached_files: list[str] = []
    missing_attachments: list[str] = []
    for attachment_path in attachments or []:
        path = Path(attachment_path)
        if not path.exists() or not path.is_file():
            missing_attachments.append(str(path))
            continue
        mime_type, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
        msg.add_attachment(
            path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )
        attached_files.append(str(path))

    log_event(
        {
            "level": "info",
            "component": "han_approval",
            "state": "smtp_attachments_prepared",
            "attached_count": len(attached_files),
            "missing_count": len(missing_attachments),
            "attached_files": attached_files,
            "missing_attachments": missing_attachments,
        }
    )

    client: smtplib.SMTP | smtplib.SMTP_SSL | None = None
    try:
        log_event(
            {
                "level": "info",
                "component": "han_approval",
                "state": "smtp_connect_start",
                "host": smtp_host,
                "port": smtp_port,
                "use_ssl": use_ssl,
                "use_starttls": use_starttls,
            }
        )
        if use_ssl:
            client = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            client = smtplib.SMTP(smtp_host, smtp_port)
        client.ehlo()
        if use_starttls and not use_ssl:
            log_event(
                {
                    "level": "info",
                    "component": "han_approval",
                    "state": "smtp_starttls_start",
                    "host": smtp_host,
                    "port": smtp_port,
                }
            )
            client.starttls()
            client.ehlo()
        log_event(
            {
                "level": "info",
                "component": "han_approval",
                "state": "smtp_login_start",
                "host": smtp_host,
                "user": smtp_user,
            }
        )
        client.login(smtp_user, smtp_password)
        log_event(
            {
                "level": "info",
                "component": "han_approval",
                "state": "smtp_send_start",
                "from": email_from,
                "recipients": recipients,
                "subject": subject,
                "attached_count": len(attached_files),
            }
        )
        client.send_message(msg)
        log_event(
            {
                "level": "info",
                "component": "han_approval",
                "state": "smtp_send_done",
                "recipients": recipients,
                "subject": subject,
            }
        )
    except Exception as exc:
        log_event(
            {
                "level": "error",
                "component": "han_approval",
                "state": "smtp_send_failed",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "host": smtp_host,
                "port": smtp_port,
                "use_ssl": use_ssl,
                "use_starttls": use_starttls,
                "from": email_from,
                "recipients": recipients,
            }
        )
        raise
    finally:
        if client is not None:
            client.quit()

    return {
        "ok": True,
        "recipients": recipients,
        "attached_count": len(attached_files),
        "missing_attachments": missing_attachments,
    }


def _save_email_attachments(
    message: Message,
    code_dir: Path,
    han_code: str,
) -> list[str]:
    return _save_pdf_attachments(list(_iter_pdf_attachments(message)), code_dir, han_code)


def _save_pdf_attachments(
    pdf_attachments: list[tuple[str, bytes]],
    code_dir: Path,
    han_code: str,
) -> list[str]:
    saved_paths: list[str] = []
    for index, (_filename, content) in enumerate(pdf_attachments, start=1):
        if index == 1:
            target_name = f"{han_code}.pdf"
        else:
            target_name = f"{han_code}_{index}.pdf"
        target_path = code_dir / target_name
        target_path.write_bytes(content)
        saved_paths.append(str(target_path))
    return saved_paths


async def process_han_approval_inbox(
    start_scan: str = "",
    end_scan: str = "",
    authorization: str = "",
) -> dict[str, Any]:
    has_explicit_start = bool(str(start_scan or "").strip())
    start_scan_dt = _parse_start_scan(start_scan)
    scan_start_day = start_scan_dt.date()
    end_scan_day = _parse_scan_day(end_scan)
    scan_end_day = end_scan_day if has_explicit_start and end_scan_day else scan_start_day
    if authorization.strip():
        append_authorization(authorization)
    allowed_senders = _parse_allowed_sender_addresses()
    log_event(
        {
            "level": "info",
            "component": "han_approval",
            "state": "process_start",
            "start_scan": start_scan_dt.isoformat(),
            "end_scan": scan_end_day.isoformat() if scan_end_day else "",
            "allowed_senders": sorted(allowed_senders),
        }
    )
    summary: dict[str, Any] = {
        "ok": True,
        "checked_messages": 0,
        "matched_messages": 0,
        "processed": 0,
        "printed": 0,
        "skipped": 0,
        "failed": 0,
        "items": [],
    }
    pending_email_items: list[dict[str, Any]] = []
    han_jobs: list[dict[str, Any]] = []
    inbox_folder = _env("EMAIL_IMAP_FOLDER", "completed")
    search_criteria = _env("EMAIL_IMAP_SEARCH_CRITERIA", "ALL")
    download_root = _download_root()
    download_root.mkdir(parents=True, exist_ok=True)
    client = _imap_connect()
    payload = load_login_payload()
    credential_key = str(
        payload.get("xCredentialKey", "") or payload.get("x_credential_key", "") or ""
    ).strip()
    try:
        select_status, _ = client.select(inbox_folder)
        if select_status != "OK":
            raise RuntimeError(f"Unable to select mailbox: {inbox_folder}")
        log_event(
            {
                "level": "info",
                "component": "han_approval",
                "state": "mailbox_selected",
                "folder": inbox_folder,
            }
        )

        imap_search_terms = [term for term in search_criteria.split() if term]
        imap_search_terms.extend(["SINCE", _imap_date(start_scan_dt)])
        imap_search_terms.extend(
            [
                "BEFORE",
                _imap_date(
                    datetime.combine(
                        scan_end_day + timedelta(days=1),
                        dt_time.min,
                        tzinfo=_get_local_timezone(),
                    )
                ),
            ]
        )
        log_event(
            {
                "level": "info",
                "component": "han_approval",
                "state": "search_begin",
                "criteria": " ".join(imap_search_terms),
            }
        )

        search_status, data = client.search(None, *imap_search_terms)
        if search_status != "OK":
            raise RuntimeError("Unable to search inbox")

        message_ids = data[0].split() if data and data[0] else []
        summary["checked_messages"] = len(message_ids)
        log_event(
            {
                "level": "info",
                "component": "han_approval",
                "state": "search_completed",
                "search_criteria": " ".join(imap_search_terms),
                "checked_messages": len(message_ids),
            }
        )

        for raw_message_id in message_ids:
            fetch_status, fetch_data = client.fetch(raw_message_id, "(RFC822)")
            if fetch_status != "OK" or not fetch_data:
                summary["failed"] += 1
                summary["items"].append(
                    {
                        "message_id": raw_message_id.decode(errors="ignore"),
                        "ok": False,
                        "reason": "fetch_failed",
                    }
                )
                continue

            raw_bytes = None
            for item in fetch_data:
                if isinstance(item, tuple) and len(item) >= 2:
                    raw_bytes = item[1]
                    break
            if not raw_bytes:
                summary["failed"] += 1
                summary["items"].append(
                    {
                        "message_id": raw_message_id.decode(errors="ignore"),
                        "ok": False,
                        "reason": "empty_message",
                    }
                )
                continue

            message = email.message_from_bytes(raw_bytes, policy=email_default_policy)
            subject = _decode_header_value(message.get("Subject"))
            from_email = _decode_header_value(message.get("From"))
            message_id = _decode_header_value(message.get("Message-ID"))
            body = _extract_message_text(message)
            message_dt = _extract_message_datetime(message)
            sender_addresses = _extract_sender_addresses(message)
            if allowed_senders and not (sender_addresses & allowed_senders):
                summary["skipped"] += 1
                continue

            if message_dt is not None and message_dt < start_scan_dt:
                summary["skipped"] += 1
                continue

            if not _subject_or_body_has_keyword(subject, body):
                summary["skipped"] += 1
                continue

            codes = _extract_han_codes(f"{subject}\n{body}")
            if not codes:
                summary["failed"] += 1
                summary["items"].append(
                    {
                        "message_id": message_id,
                        "subject": subject,
                        "ok": False,
                        "reason": "han_code_not_found",
                    }
                )
                continue

            if _is_match_with_database_enabled():
                existing_application_codes = (
                    list_existing_visa_registration_application_codes(codes)
                )
                matched_codes = [
                    code for code in codes if code in existing_application_codes
                ]
                if not matched_codes:
                    summary["skipped"] += 1
                    summary["items"].append(
                        {
                            "message_id": message_id,
                            "subject": subject,
                            "ok": False,
                            "reason": "han_code_not_in_application_code",
                            "han_codes": codes,
                        }
                    )
                    continue
                codes = matched_codes

            summary["matched_messages"] += 1
            log_event(
                {
                    "level": "info",
                    "component": "han_approval",
                    "state": "message_accepted",
                    "message_id": message_id,
                    "from_email": from_email,
                    "message_dt": message_dt.isoformat() if message_dt else "",
                    "han_codes": codes,
                }
            )
            pdf_attachments = list(_iter_pdf_attachments(message))
            for han_code in codes:
                log_event(
                    {
                        "level": "info",
                        "component": "han_approval",
                        "state": "han_job_queued",
                        "han_code": han_code,
                    }
                )
                existing = get_approval_print_job_by_han_code(han_code)
                if (
                    existing
                    and str(existing.get("status", "")).strip().lower() == "printed"
                ):
                    summary["skipped"] += 1
                    log_event(
                        {
                            "level": "info",
                            "component": "han_approval",
                            "state": "already_printed",
                            "han_code": han_code,
                        }
                    )
                    summary["items"].append(
                        {
                            "han_code": han_code,
                            "ok": True,
                            "skipped": True,
                            "reason": "already_printed",
                        }
                    )
                    continue

                han_jobs.append(
                    {
                        "han_code": han_code,
                        "from_email": from_email,
                        "message_id": message_id,
                        "subject": subject,
                        "pdf_attachments": pdf_attachments,
                    }
                )

        if han_jobs:
            concurrency = max(1, _env_int("HAN_APPROVAL_CONCURRENCY", 5))
            semaphore = asyncio.Semaphore(concurrency)
            log_event(
                {
                    "level": "info",
                    "component": "han_approval",
                    "state": "han_jobs_parallel_start",
                    "count": len(han_jobs),
                    "concurrency": concurrency,
                }
            )

            async def process_han_job(job: dict[str, Any]) -> dict[str, Any]:
                han_code = str(job.get("han_code") or "")
                processing_row: dict[str, Any] | None = None
                async with semaphore:
                    log_event(
                        {
                            "level": "info",
                            "component": "han_approval",
                            "state": "han_processing_start",
                            "han_code": han_code,
                        }
                    )
                    processing_row = upsert_approval_print_job_processing(
                        han_code=han_code,
                        source_email=str(job.get("from_email") or ""),
                        message_id=str(job.get("message_id") or ""),
                        subject=str(job.get("subject") or ""),
                    )
                    code_dir = download_root / han_code
                    code_dir.mkdir(parents=True, exist_ok=True)

                    try:
                        visa_registration = get_visa_registration_by_application_code(
                            han_code
                        )
                        applyid = (
                            str(visa_registration.get("first_applyid") or "").strip()
                            if visa_registration
                            else ""
                        )
                        pdf_attachments = job.get("pdf_attachments")
                        attachment_paths = _save_pdf_attachments(
                            pdf_attachments if isinstance(pdf_attachments, list) else [],
                            code_dir,
                            han_code,
                        )
                        if not attachment_paths:
                            raise RuntimeError("No pdf attachment found")
                        log_event(
                            {
                                "level": "info",
                                "component": "han_approval",
                                "state": "attachments_saved",
                                "han_code": han_code,
                                "count": len(attachment_paths),
                            }
                        )
                        async with httpx.AsyncClient(timeout=60) as http_client:
                            if not applyid:
                                list_ok, list_result = (
                                    await get_list_old_by_visa_number.api_get_list_by_han_code(
                                        client=http_client,
                                        token=load_token(),
                                        tmp_secret=load_tmpSecret(),
                                        han_code=han_code,
                                    )
                                )
                                if not list_ok:
                                    raise RuntimeError(
                                        f"get_list_by_han_code_failed: {list_result}"
                                    )

                                applyid = _extract_applyid_by_al_form_id(
                                    list_result=list_result,
                                    al_form_id=han_code,
                                )
                            if not applyid:
                                raise RuntimeError(
                                    f"applyid_not_found_for_alFormId: {han_code}"
                                )

                            ok, application_form_result = (
                                await api_download_application_form(
                                    client=http_client,
                                    applyid=applyid,
                                    credential_key=credential_key,
                                    authorization=authorization,
                                    output_dir=code_dir,
                                )
                            )
                        log_event(
                            {
                                "level": "info",
                                "component": "han_approval",
                                "state": "application_form_download_result",
                                "han_code": han_code,
                                "applyid": applyid,
                                "ok": ok,
                                "status_code": application_form_result.get("status_code"),
                                "content_type": application_form_result.get(
                                    "content_type", ""
                                ),
                                "file_path": application_form_result.get("file_path", ""),
                                "error": application_form_result.get("error", ""),
                            }
                        )
                        if not ok:
                            safe_application_form_result = {
                                key: value
                                for key, value in application_form_result.items()
                                if key not in {"response"}
                            }
                            raise RuntimeError(
                                f"download_application_form_failed: {safe_application_form_result}"
                            )

                        application_form_path = str(
                            application_form_result.get("file_path", "")
                        )
                        if not application_form_path:
                            raise RuntimeError(
                                "download_application_form_missing_file_path"
                            )
                        log_event(
                            {
                                "level": "info",
                                "component": "han_approval",
                                "state": "application_form_downloaded",
                                "han_code": han_code,
                                "file_path": application_form_path,
                            }
                        )
                        log_event(
                            {
                                "level": "info",
                                "component": "han_approval",
                                "state": "email_batch_item_ready",
                                "han_code": han_code,
                                "attachment_paths": attachment_paths,
                                "application_form_path": application_form_path,
                            }
                        )
                        return {
                            "ok": True,
                            "han_code": han_code,
                            "record": processing_row,
                            "source_email": str(job.get("from_email") or ""),
                            "subject": str(job.get("subject") or ""),
                            "attachment_paths": attachment_paths,
                            "application_form_path": application_form_path,
                        }
                    except Exception as exc:
                        error_text = f"{type(exc).__name__}: {exc}"
                        log_event(
                            {
                                "level": "error",
                                "component": "han_approval",
                                "state": "han_processing_failed",
                                "han_code": han_code,
                                "error": error_text,
                            }
                        )
                        update_approval_print_job_by_han_code(
                            han_code=han_code,
                            status="not_print",
                            attachment_paths=None,
                            application_form_path="",
                            last_error=error_text,
                        )
                        log_exception(
                            exc,
                            {
                                "path": "process_han_approval_inbox",
                                "han_code": han_code,
                            },
                        )
                        return {
                            "ok": False,
                            "han_code": han_code,
                            "status": "not_print",
                            "record": processing_row,
                            "error": error_text,
                        }

            han_results = await asyncio.gather(
                *(process_han_job(job) for job in han_jobs)
            )
            for result in han_results:
                if result.get("ok"):
                    pending_email_items.append(result)
                    log_event(
                        {
                            "level": "info",
                            "component": "han_approval",
                            "state": "han_processing_waiting_email_batch",
                            "han_code": result.get("han_code"),
                            "status": "pending_email",
                        }
                    )
                else:
                    summary["failed"] += 1
                    summary["items"].append(result)

            log_event(
                {
                    "level": "info",
                    "component": "han_approval",
                    "state": "han_jobs_parallel_done",
                    "count": len(han_jobs),
                    "ready_for_email": len(pending_email_items),
                }
            )

        if pending_email_items:
            batch_size = max(1, _env_int("HAN_APPROVAL_EMAIL_BATCH_SIZE", 10))
            email_batches = _chunked(pending_email_items, batch_size)
            log_event(
                {
                    "level": "info",
                    "component": "han_approval",
                    "state": "email_batch_split",
                    "total_items": len(pending_email_items),
                    "batch_size": batch_size,
                    "batch_count": len(email_batches),
                }
            )
            for batch_index, batch_items in enumerate(email_batches, start=1):
                zip_path: Path | None = None
                try:
                    batch_han_codes = [str(item.get("han_code", "")) for item in batch_items]
                    zip_path = _zip_download_folders(
                        download_root,
                        batch_han_codes,
                    )
                    log_event(
                        {
                            "level": "info",
                            "component": "han_approval",
                            "state": "email_batch_send_prepare",
                            "batch_index": batch_index,
                            "batch_count": len(email_batches),
                            "han_codes": batch_han_codes,
                            "count": len(batch_items),
                            "download_root": str(download_root),
                            "zip_path": str(zip_path),
                        }
                    )
                    notify_result = _smtp_send(
                        subject=(
                            f"HAN approvals printed: "
                            f"{len(batch_items)} (batch {batch_index}/{len(email_batches)})"
                        ),
                        body=(
                            "HAN approval files are attached as one batch zip.\n\n"
                            "HAN codes:\n"
                            + "\n".join(f"- {code}" for code in batch_han_codes)
                            + "\n\n"
                            f"Download folder: {download_root}\n"
                            f"Zip file: {zip_path}\n"
                        ),
                        attachments=[str(zip_path)],
                    )
                    if not notify_result.get("ok"):
                        raise RuntimeError(f"send_email_failed: {notify_result}")

                    for item in batch_items:
                        han_code = str(item.get("han_code", ""))
                        attachment_paths = item.get("attachment_paths")
                        application_form_path = str(item.get("application_form_path", ""))
                        update_approval_print_job_by_han_code(
                            han_code=han_code,
                            status="printed",
                            attachment_paths=(
                                attachment_paths if isinstance(attachment_paths, list) else []
                            ),
                            application_form_path=application_form_path,
                            last_error="",
                        )
                        summary["printed"] += 1
                        summary["processed"] += 1
                        summary["items"].append(
                            {
                                "han_code": han_code,
                                "ok": True,
                                "status": "printed",
                                "record": item.get("record"),
                                "attachment_paths": attachment_paths,
                                "application_form_path": application_form_path,
                                "email_sent_to": notify_result.get("recipients", []),
                                "email_attachment": str(zip_path),
                            }
                        )
                        log_event(
                            {
                                "level": "info",
                                "component": "han_approval",
                                "state": "han_processing_done",
                                "han_code": han_code,
                                "status": "printed",
                                "batch_index": batch_index,
                            }
                        )

                    log_event(
                        {
                            "level": "info",
                            "component": "han_approval",
                            "state": "email_batch_sent",
                            "batch_index": batch_index,
                            "batch_count": len(email_batches),
                            "recipients": notify_result.get("recipients", []),
                            "han_codes": batch_han_codes,
                            "zip_path": str(zip_path),
                        }
                    )
                except Exception as exc:
                    error_text = f"{type(exc).__name__}: {exc}"
                    log_event(
                        {
                            "level": "error",
                            "component": "han_approval",
                            "state": "email_batch_failed",
                            "batch_index": batch_index,
                            "error": error_text,
                            "zip_path": str(zip_path) if zip_path else "",
                        }
                    )
                    for item in batch_items:
                        han_code = str(item.get("han_code", ""))
                        update_approval_print_job_by_han_code(
                            han_code=han_code,
                            status="not_print",
                            attachment_paths=None,
                            application_form_path=str(item.get("application_form_path", "")),
                            last_error=error_text,
                        )
                        summary["failed"] += 1
                        summary["items"].append(
                            {
                                "han_code": han_code,
                                "ok": False,
                                "status": "not_print",
                                "record": item.get("record"),
                                "error": error_text,
                            }
                        )
                    log_exception(
                        exc,
                        {
                            "path": "process_han_approval_inbox_batch_email",
                            "batch_index": batch_index,
                        },
                    )
                    break
                finally:
                    if zip_path is not None and zip_path.exists():
                        try:
                            zip_path.unlink()
                        except Exception:
                            pass
            _cleanup_download_artifacts(download_root, download_root.with_suffix(".zip"))
    except Exception as exc:
        summary["ok"] = False
        summary["error"] = f"{type(exc).__name__}: {exc}"
        log_exception(exc, {"path": "process_han_approval_inbox"})
    finally:
        try:
            client.logout()
        except Exception:
            pass
        log_event(
            {
                "level": "info",
                "component": "han_approval",
                "state": "process_end",
                "ok": summary.get("ok", False),
                "checked_messages": summary.get("checked_messages", 0),
                "matched_messages": summary.get("matched_messages", 0),
                "processed": summary.get("processed", 0),
                "printed": summary.get("printed", 0),
                "skipped": summary.get("skipped", 0),
                "failed": summary.get("failed", 0),
            }
        )

    return summary


def retry_han_approval_jobs(
    record_ids: list[int] | None = None,
    han_codes: list[str] | None = None,
) -> dict[str, Any]:
    record_ids = [
        int(record_id) for record_id in (record_ids or []) if str(record_id).strip()
    ]
    han_codes = [
        str(han_code).strip() for han_code in (han_codes or []) if str(han_code).strip()
    ]
    updated = 0
    if record_ids:
        updated += update_approval_print_job_status_by_ids(record_ids, "not_print")
    if han_codes:
        updated += update_approval_print_job_status_by_codes(han_codes, "not_print")
    return {
        "ok": True,
        "updated": updated,
        "record_ids": record_ids,
        "han_codes": han_codes,
    }


def list_han_approval_jobs(limit: int = 100, offset: int = 0) -> dict[str, Any]:
    return {
        "ok": True,
        "items": list_approval_print_jobs(limit=limit, offset=offset),
    }
