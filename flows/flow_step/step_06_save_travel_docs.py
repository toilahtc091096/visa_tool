import mimetypes
import random
import shutil
from pathlib import Path
from typing import Any

from api import (
    api_save_other_info,
    api_save_previous_travel_info,
    api_save_signature_info,
    api_save_travel_info,
)
from constants import (
    FLIGHT_TEMPLATE,
    HOTEL_DATA,
    L_15_HOTEL_INFO,
    L_15_HOTEL_OUTPUT_PATH,
    L_15_TICKET_OUTPUT_PATH,
    L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH,
    L_30_HOTEL_INFO,
    CV_DATA,
    SEX_MAP,
    NATIONALITY_MAP,
    WEEK_SKIP_BY_TYPE,
    UNDER_18_HOTEL_INFO,
    VIETNAMESE_NAMES,
    L_15_TRAVEL_PLAN_OUTPUT_PATH,
    TRAVEL_PLAN_21D,
    Q1_THU_MOI_OUTPUT_PATH,
)
from generate_file.path_utils import passport_data_dir
from api import api_upload_r2_object
from flows.flow_payloads import (
    build_L30_guest_names,
    build_other_info,
    build_previous_travel_info_profile,
    build_signature_body,
    build_travel_info_profile,
)
from generate_file import cv_info, hotel_info, flight_info, file_init_info, thumoi_info
from generate_file.path_utils import passport_data_dir
from utils import (
    date_util,
    format_date,
    generate_phone_pair,
    get_today_parts,
    log_event,
    log_exception,
    notify,
    save_chinese_name_signature_png,
)
from utils.remove_r2 import delete_r2_folder
from utils.download_r2 import download_r2_folder


def _extend_unique_names(names: list[str], additions: list[str] | None) -> None:
    for name in additions or []:
        if name and name not in names:
            names.append(name)


def _sorted_unique_names(additions: list[str] | None) -> list[str]:
    return sorted({name.strip() for name in (additions or []) if name and name.strip()})


def _child_full_name(child: dict[str, Any]) -> str:
    family = str(
        child.get("childFamilyName", child.get("familyName", "")) or ""
    ).strip()
    given = str(child.get("childGivenName", child.get("firstName", "")) or "").strip()
    return " ".join(part for part in [family, given] if part).strip()


def _child_names(ctx) -> list[str]:
    names: list[str] = []
    for child in getattr(ctx, "children", []) or []:
        if isinstance(child, dict):
            full_name = _child_full_name(child)
            if full_name and full_name not in names:
                names.append(full_name)
    legacy_name = " ".join(
        part
        for part in [
            str(getattr(ctx, "childFamilyName", "") or "").strip(),
            str(getattr(ctx, "childGivenName", "") or "").strip(),
        ]
        if part
    ).strip()
    if legacy_name and legacy_name not in names:
        names.append(legacy_name)
    return names


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


COMMON_DOC_FOLDERS = (
    "chung/khach_san",
    "chung/ve_may_bay",
    "chung/xac_nhan_tu_trung_tam_visa",
)


def _download_family_common_docs_from_r2(
    *,
    prefix: str,
    local_root: Path,
) -> int:
    normalized_prefix = _normalize_r2_prefix(prefix, "")
    if not normalized_prefix:
        return 0

    total = 0
    for folder in COMMON_DOC_FOLDERS:
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


async def save_travel_and_generate_docs(ctx, client) -> bool:
    passport_root = passport_data_dir(ctx.input_passportNumber)
    family_passport = str(getattr(ctx, "family_passport", "") or "").strip()

    reuse_l_docs = bool(ctx.visa_type.startswith("L") and family_passport)
    is_q_visa = ctx.visa_type.startswith("Q")
    if ctx.visa_type.startswith("L"):
        print(
            f"[LOCAL][COMMON_DOCS] start cleanup root={passport_root} "
            f"folders={COMMON_DOC_FOLDERS}",
            flush=True,
        )
        _cleanup_common_docs_local(local_root=passport_root)
    if not is_q_visa and ctx.visa_type == "L15":
        ctx.hotel_type = random.randint(0, 100) % len(
            HOTEL_DATA[ctx.visa_type]["hotel"]
        )
    if not is_q_visa and ctx.visa_type in FLIGHT_TEMPLATE:
        ctx.flight_ticket = random.randint(0, 100) % len(FLIGHT_TEMPLATE[ctx.visa_type])
    else:
        ctx.flight_ticket = 0
    if not is_q_visa and (ctx.is_under_18 or ctx.haveChildFlag):
        ctx.flight_ticket = 0
    arrival_date_override = _maybe_parse_date(getattr(ctx, "arrivalDate", ""))
    departure_date_override = _maybe_parse_date(getattr(ctx, "departureDate", ""))
    if (
        (ctx.visa_type.startswith("Q") or ctx.visa_type.startswith("M"))
        and arrival_date_override
        and departure_date_override
    ):
        ctx.m, ctx.f = arrival_date_override, departure_date_override
    else:
        ctx.m, ctx.f = date_util.monday_and_friday_skip_x_weeks(
            ctx.register_date, WEEK_SKIP_BY_TYPE.get(ctx.visa_type)
        )
    if not is_q_visa and ctx.visa_type in FLIGHT_TEMPLATE:
        ctx.prefix_flight_text = FLIGHT_TEMPLATE[ctx.visa_type][ctx.flight_ticket][
            "prefix_flight_text"
        ]
        ctx.arrive_flight_number, ctx.departure_flight_number = generate_phone_pair(
            FLIGHT_TEMPLATE[ctx.visa_type][ctx.flight_ticket]["prefix_number"]
        )
    else:
        ctx.prefix_flight_text = ""
        ctx.arrive_flight_number = ""
        ctx.departure_flight_number = ""

    ctx.step = "save_travel_info"
    arrive_flight_number_full_info = (
        ctx.prefix_flight_text + " " + ctx.arrive_flight_number
    )
    departure_flight_number_full_info = (
        ctx.prefix_flight_text + " " + ctx.departure_flight_number
    )

    if not is_q_visa and (
        ctx.is_under_18 or (ctx.haveChildFlag and not ctx.is_private)
    ):  # todo: them and is_private  (haveChildFlag and is_private)
        ctx.m, ctx.f = date_util.monday_and_friday_skip_x_weeks(ctx.register_date, 5)
        arrive_flight_number_full_info = (
            ctx.prefix_flight_text
            + " "
            + FLIGHT_TEMPLATE[ctx.visa_type][ctx.flight_ticket]["prefix_number"]
            + "21"
        )
        departure_flight_number_full_info = (
            ctx.prefix_flight_text
            + " "
            + FLIGHT_TEMPLATE[ctx.visa_type][ctx.flight_ticket]["prefix_number"]
            + "23"
        )
        ctx.arrive_flight_number = arrive_flight_number_full_info
        ctx.departure_flight_number = departure_flight_number_full_info
    fixed_arrived = _maybe_parse_date(getattr(ctx, "fixed_arrived", ""))
    fixed_departure = _maybe_parse_date(getattr(ctx, "fixed_departure", ""))
    if fixed_arrived is not None:
        ctx.m = fixed_arrived
    if fixed_departure is not None:
        ctx.f = fixed_departure
    body_save_travel_info = build_travel_info_profile(
        ctx.visa_type,
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
        arrive_flight_number_full_info,
        departure_flight_number_full_info,
        ctx.is_private,
        getattr(ctx, "inviteCompanyName", ""),
        getattr(ctx, "company_address", ""),
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
    )
    ok7, meta7 = await api_save_travel_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_save_travel_info,
    )
    log_event({"step": ctx.step, "ok": ok7, **meta7})
    if not ok7:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            f"status={meta7.get('status_code')} "
            f"err={meta7.get('error')}"
        )
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
    log_event({"step": ctx.step, "ok": ok8, **meta8})
    if not ok8:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            f"status={meta8.get('status_code')} "
            f"err={meta8.get('error')}"
        )
        return False

    ctx.step = "save_other_info"
    body_other_info = build_other_info(ctx.first_applyid)
    ok8, meta8 = await api_save_other_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_other_info,
    )
    log_event({"step": ctx.step, "ok": ok8, **meta8})
    if not ok8:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            f"status={meta8.get('status_code')} "
            f"err={meta8.get('error')}"
        )
        return False

    ctx.step = "save_signature"
    body_signature_info = build_signature_body(ctx.first_applyid)
    ok8, meta8 = await api_save_signature_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_signature_info,
    )
    log_event({"step": ctx.step, "ok": ok8, **meta8})
    if not ok8:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            f"status={meta8.get('status_code')} "
            f"err={meta8.get('error')}"
        )
        return False

    ctx.signature_image_path = ""
    signature_name = str(getattr(ctx, "inviterName", "") or "").strip()
    if signature_name:
        try:
            signature_dir = (
                passport_data_dir(ctx.input_passportNumber) / Q1_THU_MOI_OUTPUT_PATH
            )
            signature_path = signature_dir / "signature.png"
            ctx.signature_image_path = save_chinese_name_signature_png(
                signature_name,
                signature_path,
            )
        except Exception as e:
            log_exception(
                e,
                {
                    "event": "render_failed",
                    "file": "signature.png",
                },
            )
    adult_number = 0
    child_number = 0

    if ctx.is_under_18:
        child_number += 1
    else:
        adult_number += 1
    if not is_q_visa and ctx.visa_type == "L15":
        hotel = ""
        if not reuse_l_docs:
            child_names = _child_names(ctx)
            if ctx.is_under_18 or (
                ctx.haveChildFlag and not ctx.is_private
            ):  # todo: them and is_private  (haveChildFlag and is_private)
                hotel = UNDER_18_HOTEL_INFO[0]["documentName"]
            else:
                hotel = L_15_HOTEL_INFO[ctx.hotel_type]["documentName"]
                if not ctx.guest_name:
                    ctx.guest_name = [ctx.vietnamese_name]
            has_additional_names = bool(
                getattr(ctx, "addition_adults", [])
                or getattr(ctx, "addition_child", [])
            )
            if has_additional_names:
                if not ctx.guest_name:
                    ctx.guest_name = [ctx.vietnamese_name]
                adult_number += len(getattr(ctx, "addition_adults", []))
                child_number += len(getattr(ctx, "addition_child", []))
                _extend_unique_names(ctx.guest_name, ctx.addition_adults)
                _extend_unique_names(ctx.guest_name, ctx.addition_child)
                _extend_unique_names(ctx.guest_name, child_names)
            else:
                if ctx.is_under_18:
                    print("under 18, generate hotel file with payName or random name")
                    adult = (
                        ctx.payName
                        if ctx.payName
                        else random.choice(VIETNAMESE_NAMES).upper()
                    )
                    if not ctx.guest_name:
                        ctx.guest_name = [ctx.vietnamese_name, adult]
                        print(f"guest_name: {ctx.guest_name}")

            if not ctx.guest_name:
                ctx.guest_name = [ctx.vietnamese_name]

            try:
                payload = {
                    "file_name": hotel,
                    "names": ctx.guest_name,
                    "first": ctx.m,
                    "end": ctx.f,
                    "type": "hotel",
                    "is_under_18": ctx.is_under_18,
                    "haveChildFlag": ctx.haveChildFlag,
                    "adults_number": adult_number,
                    "child_number": child_number,
                }
                print(f"payload for hotel file: {payload}")
                await hotel_info.render_docx_template_output_pdf(
                    payload, L_15_HOTEL_OUTPUT_PATH, ctx.input_passportNumber
                )
                log_event({"step": "genenrate hotel file", "ok": "ok"})
            except Exception as e:
                log_exception(e, {"event": "render_failed", "file": hotel})
                raise
    elif not is_q_visa and ctx.visa_type == "L30":
        if not reuse_l_docs:
            ctx.guest_name = build_L30_guest_names(
                ctx.guest_name,
                ctx.vietnamese_name,
                ctx.addition_adults,
                ctx.addition_child,
            )
            try:
                payload = {
                    "names": ctx.guest_name,
                    "addition_adults": ctx.addition_adults,
                    "addition_child": ctx.addition_child,
                    "first": ctx.m,
                    "type": "hotel",
                    "is_under_18": ctx.is_under_18,
                    "haveChildFlag": ctx.haveChildFlag,
                }
                await hotel_info.render_L30_hotel(
                    payload, L_15_HOTEL_OUTPUT_PATH, ctx.input_passportNumber
                )
                log_event({"step": "genenrate hotel file", "ok": "ok"})
            except Exception as e:
                log_exception(e, {"event": "render_failed_L30"})
                raise

    file_name = ""
    if ctx.ticket_names == []:
        has_additional_names = bool(
            getattr(ctx, "addition_adults", []) or getattr(ctx, "addition_child", [])
        )
        child_names = _child_names(ctx)
        if has_additional_names:
            ctx.ticket_names = _sorted_unique_names(ctx.addition_adults)
            if ctx.vietnamese_name and ctx.vietnamese_name not in ctx.ticket_names:
                ctx.ticket_names.append(ctx.vietnamese_name)
            _extend_unique_names(
                ctx.ticket_names, _sorted_unique_names(ctx.addition_child)
            )
            _extend_unique_names(ctx.ticket_names, child_names)
        else:
            ctx.ticket_names = [ctx.vietnamese_name]
            if ctx.is_under_18:
                ctx.ticket_names.append(
                    ctx.payName
                    if ctx.payName
                    else random.choice(VIETNAMESE_NAMES).upper()
                )
    if not is_q_visa and ctx.visa_type.startswith("L"):
        try:
            if ctx.visa_type in FLIGHT_TEMPLATE:
                file_name = FLIGHT_TEMPLATE[ctx.visa_type][ctx.flight_ticket]["name"]
            else:
                log_exception(
                    KeyError(f"Key {ctx.visa_type} not found"),
                    {"event": "not have ticket key ", "visa_type": ctx.visa_type},
                )
            if ctx.visa_type in {"L30"}:
                hotel_info_item = L_30_HOTEL_INFO[0]
                hotel_departure_info_item = L_30_HOTEL_INFO[-1]
            else:
                hotel_info_item = L_15_HOTEL_INFO[ctx.hotel_type]
            if ctx.is_under_18 or (
                ctx.haveChildFlag and not ctx.is_private
            ):  # todo: them and is_private  (haveChildFlag and is_private)
                ctx.arrive_flight_number = ctx.arrive_flight_number[-4:]
                ctx.departure_flight_number = ctx.departure_flight_number[-4:]
            payload = {
                "file_name": file_name,
                "arrive_flight_number": ctx.arrive_flight_number,
                "departure_flight_number": ctx.departure_flight_number,
                "arrvied_city": hotel_info_item.get("place_city"),
                "names": ctx.ticket_names,
                "arrived_iata_code": hotel_info_item.get("iata_code"),
                "first": ctx.m,
                "departure_iata_code": hotel_info_item.get("iata_code"),
                "departure_city": hotel_info_item.get("place_city"),
                "end": ctx.f,
                "type": "flight_ticket",
                "visa_type": ctx.visa_type,
            }
            if ctx.visa_type in {"L30"}:
                payload.update(
                    {
                        "departure_iata_code": hotel_departure_info_item.get(
                            "iata_code"
                        ),
                        "departure_city": hotel_departure_info_item.get("place_city"),
                    }
                )
            log_event({"step": "genenrate flight ticket file", "ok": "ok"})
        except Exception as e:
            log_exception(
                e, {"event": "render_failed", "file": payload.get("file_name")}
            )
        if not reuse_l_docs:
            await flight_info.render_flight_ticket_output_pdf(
                payload, L_15_TICKET_OUTPUT_PATH, ctx.input_passportNumber
            )
        if reuse_l_docs:
            downloaded = _download_family_common_docs_from_r2(
                prefix=family_passport,
                local_root=passport_root,
            )
            if downloaded == 0:
                raise FileNotFoundError(
                    "No family common documents found on R2 for prefix: "
                    f"{family_passport}"
                )
            print(
                f"downloaded family common docs from R2 prefix={family_passport} "
                f"folders={COMMON_DOC_FOLDERS} into={passport_root}"
            )

    ctx.ticket_names = [ctx.vietnamese_name]
    if not (ctx.visa_type.startswith("L") and reuse_l_docs):
        try:
            today_yyyy, today_mm, today_dd = get_today_parts()
            file_name = CV_DATA
            payload = {
                "file_name": file_name,
                "names": ctx.ticket_names,
                "visa_type_first": ctx.first_letter_visa_type,
                "visa_type_number": ctx.last_letter_visa_type,
                "submit_year_yyyy": today_yyyy,
                "submit_month_mm": today_mm,
                "submit_day_dd": today_dd,
                "sex": SEX_MAP.get(ctx.ocr_data.Response.Data.sex, ""),
                "nationality": NATIONALITY_MAP.get(
                    ctx.ocr_data.Response.Data.nationality, ""
                ),
                "passportNo": ctx.ocr_data.Response.Data.passportNumber,
                "birth_date_dd_mm_yyyy": format_date(
                    ctx.ocr_data.Response.Data.dateOfBirth
                ),
                "expired_day_dd_mm_yyyy": format_date(
                    ctx.ocr_data.Response.Data.dateOfExpiration
                ),
                "passengers": getattr(ctx, "passengers", []),
                "passportNumber": ctx.passportNumber,
                "entries_type": ctx.entries_type,
            }
            log_event({"step": "genenrate CV file", "ok": "ok"})
        except Exception as e:
            log_exception(
                e, {"event": "render_failed", "file": payload.get("file_name")}
            )
        await cv_info.render_docx_template_output_pdf(
            payload, L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH, ctx.input_passportNumber
        )

    if ctx.visa_type.startswith("Q"):
        try:
            file_name = "Q_Template.docx"
            log_event(
                {
                    "step": "generate invitation letter file",
                    "ok": "ok",
                    "file": file_name,
                }
            )
            await thumoi_info.render_thumoi_docx_output_pdf(
                ctx,
                Q1_THU_MOI_OUTPUT_PATH,
                ctx.input_passportNumber,
            )
        except Exception as e:
            log_exception(
                e,
                {
                    "event": "render_failed",
                    "file": "Q_Template.docx",
                },
            )
            raise

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

    if ctx.visa_type == "L30":
        try:
            file_name = TRAVEL_PLAN_21D

            payload = {
                "file_name": file_name,
                "first": ctx.m,
            }

            log_event(
                {
                    "step": "generate travel itinerary file",
                    "ok": "ok",
                    "file": file_name,
                }
            )

        except Exception as e:
            log_exception(
                e,
                {
                    "event": "render_failed",
                    "file": file_name,
                },
            )

        await file_init_info.render_init_pdf(
            payload,
            L_15_TRAVEL_PLAN_OUTPUT_PATH,
            ctx.input_passportNumber,
        )

    return True
