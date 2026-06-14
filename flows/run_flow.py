from datetime import date

import httpx

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
from utils import cleanup_data_folder, load_login_payload, log_event


async def run_flow(
    authorization: str,
    visa_type: str,
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
    payMobile: str = "",
    payName: str = "",
    first_applyid: str = "",
    is_update_info: bool = False,
    upload_config_keys: list[str] | None = None,
) -> None:
    login_payload = load_login_payload()
    token = login_payload.get("token", "")
    tmp_secret = login_payload.get("tmpSecret", "")

    ctx = build_flow_context(
        authorization=authorization,
        visa_type=visa_type,
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
        payMobile=payMobile,
        payName=payName,
        first_applyid=first_applyid,
        token=token,
        tmp_secret=tmp_secret,
    )

    if not validate_initial_inputs(ctx):
        return

    try:
        async with httpx.AsyncClient() as client:
            if not await check_token_and_get_ocr(ctx, client):
                return
            if not await load_draft_and_prepare_person(ctx, client):
                return
            if not is_update_info:
                if not await save_person_and_apply(ctx, client):
                    return
                if not await save_family_work_education(ctx, client):
                    return
            if not await save_travel_and_generate_docs(ctx, client):
                return
            if not await upload_files(
                ctx,
                client,
                is_update_info=is_update_info,
                upload_config_keys=upload_config_keys or [],
            ):
                return
            save_draft_visa_registration(ctx)
    finally:
        cleanup_data_folder()


def get_in(d, *keys, default=None):
    from flows.flow_step.common import get_in as _get_in

    return _get_in(d, *keys, default=default)
