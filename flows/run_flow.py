import time
from datetime import date

import httpx
from typing import Any

from flows.flow_step import (
    build_flow_context,
    check_token_and_get_ocr,
    load_draft_and_prepare_person,
    save_family_work_education,
    save_person_and_apply,
    save_draft_visa_registration,
    save_travel_and_generate_docs,
    upload_files,
    validate_initial_inputs,
)
from utils import cleanup_data_folder, load_login_payload, log_event, log_exception


def _normalize_name_list(value) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        return []
    return [str(item).strip() for item in items if str(item).strip()]


async def run_flow(
    authorization: str,
    visa_type: str,
    visa_duration: str,
    passport_type_code: str,
    register_date: date,
    guest_name: list[str],
    ticket_names: list[str],
    province_city_code: str,
    id_card_number: str,
    passportNumber: str,
    entries_type: str,
    type_of_visa_sub_value: str,
    service_type: str,
    haveSpouseFlag: bool = False,
    ct08_province_city_code: str = "",
    haveChildFlag: bool = False,
    childFamilyName: str = "",
    childGivenName: str = "",
    childNationality: str = "",
    childBirthDate: str = "",
    fatherFamilyName: str = "",
    fatherGivenName: str = "",
    fatherNationality: str = "",
    fatherBirthDate: str = "",
    motherFamilyName: str = "",
    motherGivenName: str = "",
    motherNationality: str = "",
    motherBirthDate: str = "",
    arrivedChinaFlag: bool = False,
    haveChinaVisaFlag: bool = False,
    old_visaType: str = "",
    old_visaNumber: str = "",
    old_issueDate: str = "",
    old_issuePlace: str = "",
    haveOtherVisaFlag: bool = False,
    old_otherVisas: list[str] = [],
    old_otherCountries: list[str] = [],
    spouseFamilyName: str = "",
    spouseFirstName: str = "",
    spouseNationalityCountry: str = "",
    spouseBirthday: str = "",
    spouseBirthCountry: str = "",
    spouseBirthCity: str = "",
    spouseBirthCounty: str = "",
    spouseAddress: str = "",
    payMobile: str = "",
    payName: str = "",
    first_applyid: str = "",
    is_update_info: bool = False,
    upload_config_keys: list[str] | None = None,
    addition_adults: list[str] | None = None,
    addition_child: list[str] | None = None,
    chinaResidenceLicenseFlag: bool = False,
    collectFingerprintFlag: bool = False,
    is_private: bool = False,
    arrivalDate: str = "",
    departureDate: str = "",
    fixed_arrived: str = "",
    fixed_departure: str = "",
    inviteCompanyName: str = "",
    company_address: str = "",
    inviteProvince: str = "",
    companyNameVi: str = "",
    companyAddressUpperNoAccent: str = "",
    companyPhone: str = "",
    managerName: str = "",
    work_from: str = "",
    work_to: str = "",
    employer_name: str = "",
    employer_address: str = "",
    employer_phone: str = "",
    supervisor_name: str = "",
    supervisor_mobile: str = "",
    position: str = "",
    duty: str = "",
    name_of_institute: str = "",
    diploma_degree: str = "",
    major: str = "",
    children: list[dict] | None = None,
    company_passport: str = "",
    school_passport: str = "",
    inviteSchoolName: str = "",
    school_address: str = "",
    family_passport: str = "",
    passengers: list[dict] | None = None,
    arrivalCity: str = "",
    arrivalDistrict: str = "",
    stayCity: str = "",
    stayDistrict: str = "",
    departureCity: str = "",
    departureDistrict: str = "",
    apply_visa_validity: Any | None = None,
    inviterFamilyName: str = "",
    inviterGivenName: str = "",
    inviterIdCard: str = "",
    inviterPhone: str = "",
    inviterAddress: str = "",
    inviterRelation: str = "",
    inviterName: str = "",
    emergencyFamilyName: str = "",
    emergencyGivenName: str = "",
    emergencyRelationship: str = "",
    emergencyPhone: str = "",
) -> dict[str, Any]:
    login_payload = load_login_payload()
    token = login_payload.get("token", "")
    tmp_secret = login_payload.get("tmpSecret", "")

    ctx = build_flow_context(
        authorization=authorization,
        visa_type=visa_type,
        visa_duration=visa_duration,
        passport_type_code=passport_type_code,
        register_date=register_date,
        guest_name=guest_name,
        ticket_names=ticket_names,
        province_city_code=province_city_code,
        id_card_number=id_card_number,
        passportNumber=passportNumber,
        entries_type=entries_type,
        type_of_visa_sub_value=type_of_visa_sub_value,
        service_type=service_type,
        haveSpouseFlag=haveSpouseFlag,
        ct08_province_city_code=ct08_province_city_code,
        haveChildFlag=haveChildFlag,
        childFamilyName=childFamilyName,
        childGivenName=childGivenName,
        childNationality=childNationality,
        childBirthDate=childBirthDate,
        fatherFamilyName=fatherFamilyName,
        fatherGivenName=fatherGivenName,
        fatherNationality=fatherNationality,
        fatherBirthDate=fatherBirthDate,
        motherFamilyName=motherFamilyName,
        motherGivenName=motherGivenName,
        motherNationality=motherNationality,
        motherBirthDate=motherBirthDate,
        arrivedChinaFlag=arrivedChinaFlag,
        haveChinaVisaFlag=haveChinaVisaFlag,
        old_visaType=old_visaType,
        old_visaNumber=old_visaNumber,
        old_issueDate=old_issueDate,
        old_issuePlace=old_issuePlace,
        haveOtherVisaFlag=haveOtherVisaFlag,
        old_otherVisas=old_otherVisas,
        old_otherCountries=old_otherCountries,
        spouseFamilyName=spouseFamilyName,
        spouseFirstName=spouseFirstName,
        spouseNationalityCountry=spouseNationalityCountry,
        spouseBirthday=spouseBirthday,
        spouseBirthCountry=spouseBirthCountry,
        spouseBirthCity=spouseBirthCity,
        spouseBirthCounty=spouseBirthCounty,
        spouseAddress=spouseAddress,
        payMobile=payMobile,
        payName=payName,
        first_applyid=first_applyid,
        token=token,
        tmp_secret=tmp_secret,
        addition_adults=_normalize_name_list(addition_adults),
        addition_child=_normalize_name_list(addition_child),
        apply_visa_validity=apply_visa_validity,
        inviterFamilyName=inviterFamilyName,
        inviterGivenName=inviterGivenName,
        inviterIdCard=inviterIdCard,
        inviterPhone=inviterPhone,
        inviterAddress=inviterAddress,
        inviterRelation=inviterRelation,
        inviterName=inviterName,
        emergencyFamilyName=emergencyFamilyName,
        emergencyGivenName=emergencyGivenName,
        emergencyRelationship=emergencyRelationship,
        emergencyPhone=emergencyPhone,
        chinaResidenceLicenseFlag=chinaResidenceLicenseFlag,
        collectFingerprintFlag=collectFingerprintFlag,
        is_private=is_private,
        arrivalDate=arrivalDate,
        departureDate=departureDate,
        fixed_arrived=fixed_arrived,
        fixed_departure=fixed_departure,
        inviteCompanyName=inviteCompanyName,
        company_address=company_address,
        inviteProvince=inviteProvince,
        companyNameVi=companyNameVi,
        companyAddressUpperNoAccent=companyAddressUpperNoAccent,
        companyPhone=companyPhone,
        managerName=managerName,
        work_from=work_from,
        work_to=work_to,
        employer_name=employer_name,
        employer_address=employer_address,
        employer_phone=employer_phone,
        supervisor_name=supervisor_name,
        supervisor_mobile=supervisor_mobile,
        position=position,
        duty=duty,
        name_of_institute=name_of_institute,
        diploma_degree=diploma_degree,
        major=major,
        children=children or [],
        company_passport=company_passport,
        school_passport=school_passport,
        inviteSchoolName=inviteSchoolName,
        school_address=school_address,
        family_passport=family_passport,
        passengers=passengers or [],
        arrivalCity=arrivalCity,
        arrivalDistrict=arrivalDistrict,
        stayCity=stayCity,
        stayDistrict=stayDistrict,
        departureCity=departureCity,
        departureDistrict=departureDistrict,
    )

    started_at = time.perf_counter()
    try:
        await _run_steps(ctx, is_update_info, upload_config_keys or [])
    except Exception as exc:
        log_exception(exc, {"event": "flow_exception", "step": ctx.step})
        ctx.error = {
            "step": ctx.step,
            "status_code": None,
            "error": f"{type(exc).__name__}: {exc}",
            "response": None,
        }
    finally:
        cleanup_data_folder()
        ctx.timings["total"] = round(time.perf_counter() - started_at, 2)
        log_event({"step": "timing", "phase": "total", "seconds": ctx.timings["total"]})

    if ctx.error:
        return {"ok": False, **ctx.error, "timings": ctx.timings}
    return {
        "ok": True,
        "first_applyid": ctx.first_applyid,
        "record_id": getattr(ctx, "record_id", None),
        "timings": ctx.timings,
    }


async def _timed(ctx, phase: str, awaitable):
    """Await ``awaitable`` and record how long it took in ``ctx.timings``."""
    started_at = time.perf_counter()
    try:
        return await awaitable
    finally:
        ctx.timings[phase] = round(time.perf_counter() - started_at, 2)
        log_event({"step": "timing", "phase": phase, "seconds": ctx.timings[phase]})


async def _log_request_start(request: httpx.Request) -> None:
    request.extensions["started_at"] = time.perf_counter()


async def _log_response_time(response: httpx.Response) -> None:
    started_at = response.request.extensions.get("started_at")
    if started_at is None:
        return
    log_event(
        {
            "step": "http",
            "method": response.request.method,
            "path": response.request.url.path,
            "status": response.status_code,
            "seconds": round(time.perf_counter() - started_at, 2),
        }
    )


async def _run_steps(ctx, is_update_info: bool, upload_config_keys: list[str]) -> None:
    """Run the steps in order; a step returning False has set ``ctx.error``."""
    if not await _timed(ctx, "validate", validate_initial_inputs(ctx)):
        return
    async with httpx.AsyncClient(
        event_hooks={"request": [_log_request_start], "response": [_log_response_time]}
    ) as client:
        if not await _timed(ctx, "token_ocr", check_token_and_get_ocr(ctx, client)):
            return
        if not await _timed(
            ctx, "draft_person", load_draft_and_prepare_person(ctx, client)
        ):
            return

        if not await _timed(ctx, "person_apply", save_person_and_apply(ctx, client)):
            return
        if not await _timed(
            ctx, "family_work_education", save_family_work_education(ctx, client)
        ):
            return
        if not await _timed(
            ctx, "travel_docs", save_travel_and_generate_docs(ctx, client)
        ):
            return
        if not await _timed(
            ctx,
            "upload_files",
            upload_files(
                ctx,
                client,
                is_update_info=is_update_info,
                upload_config_keys=upload_config_keys,
            ),
        ):
            return
        ctx.step = "save_visa_registration_to_db"
        ctx.record_id = save_draft_visa_registration(ctx)
