import mimetypes
import shutil
from pathlib import Path

from api import (
    api_save_other_info,
    api_save_previous_travel_info,
    api_save_signature_info,
    api_save_travel_info,
)
from api import api_upload_r2_object
from flows.flow_payloads import (
    build_other_info,
    build_previous_travel_info_profile,
    build_signature_body,
    build_travel_info_profile,
)
from generate_file.path_utils import passport_data_dir
from utils import date_util, generate_phone_pair
from utils.remove_r2 import delete_r2_folder
from utils.download_r2 import download_r2_folder
from visa_types.documents import COMMON_DOC_FOLDERS, has_additional_names
from .common import check_api_result


def _maybe_parse_date(value):
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return value
    if isinstance(value, str) and value.strip():
        return date_util.parse_date(value.strip())
    return None


def _normalize_r2_prefix(value: str, fallback: str) -> str:
    text = str(value or "").strip().strip('"').strip("'")
    if not text:
        text = str(fallback or "").strip().strip('"').strip("'")
    return text.lstrip("/")


def _as_r2_folder(folder: str) -> str:
    return folder.replace("\\", "/")


def _upload_file_preserve_local(
    file_path: str | Path,
    *,
    local_root: Path,
    prefix: str,
) -> dict:
    path = Path(file_path).resolve()
    root = local_root.resolve()
    if not path.exists():
        return {"ok": False, "error": "missing_file", "file_path": str(path)}
    try:
        relative_path = path.relative_to(root).as_posix()
    except ValueError as exc:
        return {
            "ok": False,
            "error": f"file_outside_root: {exc}",
            "file_path": str(path),
            "local_root": str(root),
        }

    normalized_prefix = _normalize_r2_prefix(prefix, "")
    key = f"{normalized_prefix}/{relative_path}" if normalized_prefix else relative_path
    result = api_upload_r2_object(
        key,
        path.read_bytes(),
        mimetypes.guess_type(path.name)[0] or "application/octet-stream",
    )
    if not result.get("ok"):
        return result
    result["key"] = key
    result["local_path"] = str(path)
    return result


def _download_folders_from_r2(
    *,
    prefix: str,
    folders: tuple[str, ...],
    local_root: Path,
) -> int:
    normalized_prefix = _normalize_r2_prefix(prefix, "")
    if not normalized_prefix:
        return 0

    total = 0
    for folder in folders:
        total += download_r2_folder(
            prefix=f"{normalized_prefix.rstrip('/')}/{folder}",
            local_dir=str(local_root / Path(folder)),
        )
    return total


def _cleanup_common_docs_local(*, local_root: Path) -> int:
    deleted_count = 0
    for folder in COMMON_DOC_FOLDERS:
        folder_path = local_root / Path(folder)
        if not folder_path.exists():
            print(
                f"[LOCAL][COMMON_DOCS] skip missing folder={folder_path}",
                flush=True,
            )
            continue
        print(
            f"[LOCAL][COMMON_DOCS] deleting folder={folder_path}",
            flush=True,
        )
        shutil.rmtree(folder_path)
        deleted_count += 1
        print(
            f"[LOCAL][COMMON_DOCS] deleted folder={folder_path}",
            flush=True,
        )
    print(
        f"[LOCAL][COMMON_DOCS] cleanup finished root={local_root} "
        f"deleted_folders={deleted_count}",
        flush=True,
    )
    return deleted_count


def _upload_common_docs_to_r2(*, local_root: Path, prefix: str) -> list[dict]:
    results: list[dict] = []
    for folder in COMMON_DOC_FOLDERS:
        folder_path = local_root / Path(folder)
        if not folder_path.is_dir():
            continue
        for file_path in sorted(folder_path.rglob("*")):
            if file_path.is_file():
                results.append(
                    _upload_file_preserve_local(
                        file_path,
                        local_root=local_root,
                        prefix=prefix,
                    )
                )
    return results


def _delete_common_docs_from_r2(*, prefix: str) -> int:
    normalized_prefix = _normalize_r2_prefix(prefix, "")
    if not normalized_prefix:
        print(
            "[R2][COMMON_DOCS] skip delete because prefix is empty",
            flush=True,
        )
        return 0

    deleted_count = 0
    for folder in COMMON_DOC_FOLDERS:
        folder_prefix = f"{normalized_prefix.rstrip('/')}/{folder}"
        print(
            f"[R2][COMMON_DOCS] deleting folder_prefix={folder_prefix}",
            flush=True,
        )
        folder_deleted = delete_r2_folder(folder_prefix)
        deleted_count += folder_deleted
        print(
            f"[R2][COMMON_DOCS] deleted folder_prefix={folder_prefix} "
            f"count={folder_deleted}",
            flush=True,
        )
    print(
        f"[R2][COMMON_DOCS] delete finished prefix={normalized_prefix} "
        f"total_deleted={deleted_count}",
        flush=True,
    )
    return deleted_count


def _plan_trip(ctx, has_additional: bool) -> tuple[str, str]:
    """Pick hotel/flight, travel dates and flight numbers on ``ctx``.

    Returns the arrival and departure flight numbers written in the travel info.
    """
    profile = ctx.profile
    profile.choose_hotel_and_flight(ctx, has_additional)

    requested_arrival = _maybe_parse_date(getattr(ctx, "arrivalDate", ""))
    requested_departure = _maybe_parse_date(getattr(ctx, "departureDate", ""))
    if profile.accepts_requested_dates and requested_arrival and requested_departure:
        ctx.m, ctx.f = requested_arrival, requested_departure
    else:
        ctx.m, ctx.f = date_util.monday_and_friday_skip_x_weeks(
            ctx.register_date, profile.week_skip
        )

    template = None
    if profile.flight_templates:
        template = profile.flight_templates[ctx.flight_ticket]
        ctx.prefix_flight_text = template["prefix_flight_text"]
        ctx.arrive_flight_number, ctx.departure_flight_number = generate_phone_pair(
            template["prefix_number"]
        )
    else:
        ctx.prefix_flight_text = ""
        ctx.arrive_flight_number = ""
        ctx.departure_flight_number = ""
    arrive_flight = ctx.prefix_flight_text + " " + ctx.arrive_flight_number
    departure_flight = ctx.prefix_flight_text + " " + ctx.departure_flight_number

    if template and (ctx.is_under_18 or has_additional):
        ctx.m, ctx.f = date_util.monday_and_friday_skip_x_weeks(ctx.register_date, 5)
        arrive_flight = f"{ctx.prefix_flight_text} {template['prefix_number']}21"
        departure_flight = f"{ctx.prefix_flight_text} {template['prefix_number']}23"
        ctx.arrive_flight_number = arrive_flight
        ctx.departure_flight_number = departure_flight

    fixed_arrived = _maybe_parse_date(getattr(ctx, "fixed_arrived", ""))
    fixed_departure = _maybe_parse_date(getattr(ctx, "fixed_departure", ""))
    if fixed_arrived is not None:
        ctx.m = fixed_arrived
    if fixed_departure is not None:
        ctx.f = fixed_departure
    return arrive_flight, departure_flight


async def _generate_documents(ctx, passport_root: Path) -> None:
    """Render the profile's documents, taking reusable ones from R2 instead."""
    profile = ctx.profile
    reused_folders: set[str] = set()
    reuse_prefix = profile.reuse_prefix(ctx)
    if reuse_prefix:
        downloaded = _download_folders_from_r2(
            prefix=reuse_prefix,
            folders=profile.reuse.folders,
            local_root=passport_root,
        )
        if downloaded == 0:
            raise FileNotFoundError(
                profile.reuse.missing_message.format(prefix=reuse_prefix)
            )
        print(
            f"downloaded reused docs from R2 prefix={reuse_prefix} "
            f"folders={profile.reuse.folders} into={passport_root}"
        )
        reused_folders = set(profile.reuse.folders)

    for document in profile.documents:
        if _as_r2_folder(document.output_folder) in reused_folders:
            continue
        await document.render(ctx)


async def _sync_common_docs_to_r2(ctx, passport_root: Path) -> None:
    """Replace the shared ``chung/*`` folders on R2 with the local ones."""
    family_passport = str(getattr(ctx, "family_passport", "") or "").strip()
    upload_prefix = _normalize_r2_prefix(family_passport, ctx.input_passportNumber)
    print(
        f"[R2][COMMON_DOCS] start cleanup+upload prefix={upload_prefix} "
        f"folders={COMMON_DOC_FOLDERS}",
        flush=True,
    )
    deleted_common_docs = _delete_common_docs_from_r2(prefix=upload_prefix)
    print(
        f"[R2][COMMON_DOCS] cleanup done prefix={upload_prefix} "
        f"deleted={deleted_common_docs}",
        flush=True,
    )
    common_doc_uploads = _upload_common_docs_to_r2(
        local_root=passport_root,
        prefix=upload_prefix,
    )
    failed_uploads = [result for result in common_doc_uploads if not result.get("ok")]
    if failed_uploads:
        raise RuntimeError(
            "Failed to upload common documents to R2: "
            f"{failed_uploads[0].get('error')}"
        )
    print(
        f"uploaded common docs to R2 prefix={upload_prefix} "
        f"files={len(common_doc_uploads)} folders={COMMON_DOC_FOLDERS}"
    )


async def save_travel_and_generate_docs(ctx, client) -> bool:
    profile = ctx.profile
    passport_root = passport_data_dir(ctx.input_passportNumber)
    has_additional = has_additional_names(ctx)
    if profile.cleans_local_common_docs:
        print(
            f"[LOCAL][COMMON_DOCS] start cleanup root={passport_root} "
            f"folders={COMMON_DOC_FOLDERS}",
            flush=True,
        )
        _cleanup_common_docs_local(local_root=passport_root)
    arrive_flight, departure_flight = _plan_trip(ctx, has_additional)

    ctx.step = "save_travel_info"
    body_save_travel_info = build_travel_info_profile(
        profile,
        ctx.first_applyid,
        ctx.payName,
        ctx.payMobile,
        ctx.is_under_18,
        ctx.haveChildFlag,
        ctx.fatherFamilyName,
        ctx.fatherGivenName,
        ctx.motherFamilyName,
        ctx.motherGivenName,
        ctx.m,
        ctx.f,
        ctx.hotel_type,
        has_additional,
        arrive_flight,
        departure_flight,
        ctx.is_private,
        getattr(ctx, "inviteCompanyName", ""),
        getattr(ctx, "company_address", ""),
        getattr(ctx, "inviteSchoolName", ""),
        getattr(ctx, "school_address", ""),
        getattr(ctx, "inviteProvince", ""),
        getattr(ctx, "arrivalCity", ""),
        getattr(ctx, "arrivalDistrict", ""),
        getattr(ctx, "stayCity", ""),
        getattr(ctx, "stayDistrict", ""),
        getattr(ctx, "departureCity", ""),
        getattr(ctx, "departureDistrict", ""),
        getattr(ctx, "companyPhone", ""),
        getattr(ctx, "managerName", ""),
        apply_visa_validity=getattr(ctx, "apply_visa_validity", None),
        inviterFamilyName=getattr(ctx, "inviterFamilyName", ""),
        inviterGivenName=getattr(ctx, "inviterGivenName", ""),
        inviterIdCard=getattr(ctx, "inviterIdCard", ""),
        inviterRelation=getattr(ctx, "inviterRelation", ""),
        inviterAddress=getattr(ctx, "inviterAddress", ""),
        inviterPhone=getattr(ctx, "inviterPhone", ""),
        emergencyFamilyName=getattr(ctx, "emergencyFamilyName", ""),
        emergencyGivenName=getattr(ctx, "emergencyGivenName", ""),
        emergencyRelationship=getattr(ctx, "emergencyRelationship", ""),
        emergencyPhone=getattr(ctx, "emergencyPhone", ""),
    )
    ok7, meta7 = await api_save_travel_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_save_travel_info,
    )
    if not await check_api_result(ctx, ok7, meta7):
        return False

    ctx.step = "save_previous_travel_info"
    body_save_previous_travel_info = build_previous_travel_info_profile(
        ctx.first_applyid,
        ctx.arrivedChinaFlag,
        ctx.haveChinaVisaFlag,
        ctx.old_visaType,
        ctx.old_visaNumber,
        ctx.old_issueDate,
        ctx.old_issuePlace,
        ctx.haveOtherVisaFlag,
        ctx.old_otherVisas,
        ctx.old_otherCountries,
        ctx.collectFingerprintFlag,
        ctx.chinaResidenceLicenseFlag,
    )
    ok8, meta8 = await api_save_previous_travel_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_save_previous_travel_info,
    )
    if not await check_api_result(ctx, ok8, meta8):
        return False

    ctx.step = "save_other_info"
    body_other_info = build_other_info(ctx.first_applyid)
    ok8, meta8 = await api_save_other_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_other_info,
    )
    if not await check_api_result(ctx, ok8, meta8):
        return False

    ctx.step = "save_signature"
    body_signature_info = build_signature_body(ctx.first_applyid)
    ok8, meta8 = await api_save_signature_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_signature_info,
    )
    if not await check_api_result(ctx, ok8, meta8):
        return False

    ctx.step = "generate_documents"
    await _generate_documents(ctx, passport_root)
    await _sync_common_docs_to_r2(ctx, passport_root)
    return True
