"""Archive / restore an input folder on R2 instead of deleting it.

WF14 (after the curl is sent) moves `<prefix>/` to `_archive/<stamp>/<prefix>/`.
An R2 lifecycle rule on `_archive/` removes it after 7 days. To re-run a case,
`restore` moves the latest archive back and clears the `<passport>/` output
folder so files from the previous run cannot mix into the new one.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from api.r2_image import _build_r2_client, _missing_r2_env_vars

ARCHIVE_ROOT = "_archive/"
_VN_TZ = timezone(timedelta(hours=7))
_PASSPORT_RE = re.compile(r"^[A-Z0-9]{6,12}$")


def _folder(prefix: str) -> str:
    """'a/b' or '/a/b/' -> 'a/b/'; '' stays ''."""
    text = str(prefix or "").strip().strip("/")
    return f"{text}/" if text else ""


def _list(client, bucket: str, prefix: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects.extend(page.get("Contents", []))
    return objects


def _summary(objects: list[dict[str, Any]]) -> dict[str, int]:
    return {"files": len(objects), "bytes": sum(int(o.get("Size", 0)) for o in objects)}


def _delete_keys(client, bucket: str, keys: list[str]) -> list[Any]:
    errors: list[Any] = []
    for i in range(0, len(keys), 1000):
        chunk = [{"Key": k} for k in keys[i : i + 1000]]
        resp = client.delete_objects(Bucket=bucket, Delete={"Objects": chunk, "Quiet": True})
        errors.extend(resp.get("Errors", []))
    return errors


def _move(client, bucket: str, src: str, dst: str) -> dict[str, Any]:
    """Copy every object under src to dst, check counts and sizes, then delete src."""
    source = _list(client, bucket, src)
    if not source:
        return {"ok": False, "error": "source_not_found", "source": src}
    if _list(client, bucket, dst):
        return {"ok": False, "error": "destination_not_empty", "destination": dst}

    for obj in source:
        new_key = dst + obj["Key"][len(src) :]
        client.copy_object(
            Bucket=bucket,
            Key=new_key,
            CopySource={"Bucket": bucket, "Key": obj["Key"]},
        )

    before, after = _summary(source), _summary(_list(client, bucket, dst))
    if before != after:
        # Source is kept untouched; the partial copy can be inspected or removed.
        return {
            "ok": False,
            "error": "copy_mismatch",
            "source": src,
            "destination": dst,
            "source_summary": before,
            "destination_summary": after,
        }

    errors = _delete_keys(client, bucket, [o["Key"] for o in source])
    if errors:
        return {"ok": False, "error": "delete_source_errors", "errors": errors, "destination": dst}
    return {"ok": True, "source": src, "destination": dst, **before}


def _latest_archive(client, bucket: str, folder: str) -> str:
    """Newest `_archive/<stamp>/<folder>` that holds files, or ''."""
    paginator = client.get_paginator("list_objects_v2")
    stamps: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=ARCHIVE_ROOT, Delimiter="/"):
        stamps.extend(p["Prefix"] for p in page.get("CommonPrefixes", []))
    for stamp in sorted(stamps, reverse=True):
        candidate = stamp + folder
        resp = client.list_objects_v2(Bucket=bucket, Prefix=candidate, MaxKeys=1)
        if resp.get("KeyCount", 0):
            return candidate
    return ""


def api_archive_r2_folder(prefix: str, *, now: datetime | None = None) -> dict[str, Any]:
    missing = _missing_r2_env_vars()
    if missing:
        return {"ok": False, "error": "missing_r2_env_vars", "missing": missing}
    folder = _folder(prefix)
    if not folder:
        return {"ok": False, "error": "missing_prefix"}
    if folder.startswith(ARCHIVE_ROOT):
        return {"ok": False, "error": "already_archived", "prefix": folder}

    stamp = (now or datetime.now(_VN_TZ)).strftime("%Y-%m-%d_%H%M%S")
    try:
        client, config = _build_r2_client()
        result = _move(client, config.bucket_name, folder, f"{ARCHIVE_ROOT}{stamp}/{folder}")
        result["bucket"] = config.bucket_name
        return result
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "message": str(exc)}


def api_restore_r2_folder(
    prefix: str,
    passport_number: str,
    *,
    confirm: bool = False,
) -> dict[str, Any]:
    """Re-run preparation. confirm=False only reports what would happen."""
    missing = _missing_r2_env_vars()
    if missing:
        return {"ok": False, "error": "missing_r2_env_vars", "missing": missing}
    folder = _folder(prefix)
    if not folder or folder.startswith(ARCHIVE_ROOT):
        return {"ok": False, "error": "invalid_prefix", "prefix": folder}
    passport = str(passport_number or "").strip().upper()
    if not _PASSPORT_RE.fullmatch(passport):
        # Guards the delete below: a wrong value must never widen it.
        return {"ok": False, "error": "invalid_passport_number", "passport_number": passport}
    output = f"{passport}/"

    try:
        client, config = _build_r2_client()
        bucket = config.bucket_name
        source_now = _list(client, bucket, folder)
        archive = _latest_archive(client, bucket, folder)
        output_objects = _list(client, bucket, output)

        if source_now and archive:
            return {"ok": False, "error": "source_and_archive_both_exist", "prefix": folder, "archive": archive}

        plan = {
            "bucket": bucket,
            "prefix": folder,
            "archive": archive,
            "restore": _summary(_list(client, bucket, archive)) if archive else None,
            "source_already_present": _summary(source_now) if source_now else None,
            "delete_output": {"prefix": output, **_summary(output_objects)},
        }
        if not source_now and not archive:
            return {"ok": False, "error": "nothing_to_restore", **plan}
        if not confirm:
            return {"ok": True, "mode": "dry_run", **plan}

        errors = _delete_keys(client, bucket, [o["Key"] for o in output_objects])
        if errors:
            return {"ok": False, "error": "delete_output_errors", "errors": errors, **plan}
        if archive:
            moved = _move(client, bucket, archive, folder)
            if not moved.get("ok"):
                return {**moved, **plan, "output_deleted": True}
        return {"ok": True, "mode": "done", **plan}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "message": str(exc)}
