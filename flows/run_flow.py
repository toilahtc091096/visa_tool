from datetime import date, datetime
import httpx
import random

from generate_file import hotel_info, cv_info
from api import (
    api_get_draft,
    api_passport_ocr,
    api_save_apply_info,
    api_save_person_info,
    api_save_education_info,
    api_save_family_info,
    api_save_previous_travel_info,
    api_save_travel_info,
    api_save_work_info,
    api_upload_file,
    api_save_other_info,
    api_save_signature_info,
    api_list_online_applications,
    api_get_work_info,
    api_get_education_info,
    api_get_family_info,
    api_login,
    api_get_person_info,
)
from constants import (
    HOTEL_DATA,
    ENTRIES_TYPE,
    MY_VISA_TYPE,
    SERVICE_VISA_TYPE,
    VISA_TYPE_DAY_VALUE,
    VISA_TYPE_VALUE,
    L_15_HOTEL_INFO,
    FLIGHT_TEMPLATE,
    UPLOAD_FILE_CODE_BY_VISA_TYPE,
    L_15_HOTEL_OUTPUT_PATH,
    L_15_TICKET_OUTPUT_PATH,
    L_15_HOTEL_OUTPUT_PATH,
    L_15_TICKET_OUTPUT_PATH,
    UPLOAD_CONFIG,
    OLD_APPLY_STATUS_APPROVED,
    CV_DATA,
    L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH,
    SEX_MAP,
    NATIONALITY_MAP,
    OLD_APPLY_ID_FOR_TEST_TOKEN,
)
from flows.flow_payloads import (
    build_apply_info_profile,
    build_person_profile,
    build_education_info_profile,
    build_family_info_profile,
    build_previous_travel_info_profile,
    build_travel_info_profile,
    build_work_info_profile,
    full_name_from_ocr,
    vietnamese_name_from_ocr,
    build_upload_material_body,
    build_other_info,
    build_signature_body,
)
from models import (
    GetDraftListBody,
    GetDraftListResult,
    has_name,
    passport_ocr_result_from_dict,
    upload_material,
    OnlineApplicationListResponse,
    GetWorkInfoResponse,
    GetWorkInfoResponseWrapper,
    GetWorkInfoData,
    WorkExperienceItem,
    GetEducationInfoResponse,
    GetFamilyInfoResponse,
    LoginApiResponse,
    LoginData,
    person_info_result_from_dict,
    PersonInfoData,
)
from utils import (
    date_util,
    generate_phone_pair,
    log_event,
    log_exception,
    notify,
    get_files,
    api_upload_file_common,
    format_date,
    get_today_parts,
    load_login_payload,
    save_login_data,
    get_passport_file_path,
)


async def run_flow(
    authorization: str,
    visa_type: str,
    register_date: date,
    guest_name: list[str],
    ticket_names: list[str],
    province_city_code: str,
    id_card_number: str,
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
    payMobile: str = "",
    payName: str = "",
) -> None:

    login_payload = load_login_payload()
    token = login_payload.get("token", "")
    # uid = login_payload.get("uid", "")
    tmp_secret = login_payload.get("tmpSecret", "")
    first_letter_visa_type = visa_type[0]
    last_letter_visa_type = visa_type[1:]
    first_applyid = ""
    if (
        visa_type not in MY_VISA_TYPE
        or first_letter_visa_type not in SERVICE_VISA_TYPE
        or last_letter_visa_type not in VISA_TYPE_DAY_VALUE[first_letter_visa_type]
    ):
        log_event({"step": "Visa Type", "status": visa_type + " not support"})
        return
    if entries_type not in ENTRIES_TYPE:
        log_event(
            {"step": "ENTRIES_TYPE check", "status": entries_type + " not support"}
        )
        return
    if type_of_visa_sub_value not in VISA_TYPE_VALUE.get(first_letter_visa_type, {}):
        log_event(
            {"step": "service type", "status": type_of_visa_sub_value + " not support"}
        )
        return

    async with httpx.AsyncClient() as client:
        step = "check token"
        ok, res = await api_get_education_info(
            client=client,
            token=token,
            tmp_secret=tmp_secret,
            applyid=OLD_APPLY_ID_FOR_TEST_TOKEN,
        )
        if not ok:
            parsed = GetEducationInfoResponse.from_dict(res)
            # if api_login.needs_relogin(parsed):
            print("call login")
            login_response = api_login.login(authorization)
            print(login_response)
            save_login_data(login_response.data)
        else:
            print("token ok ")
        step = "get ocr"
        passport_file_path = get_passport_file_path()
        if passport_file_path == "":
            await notify(
                f"Flow FAILED at step={step}. status={meta.get('status_code')} "
                f"err={meta.get('error')}"
            )
            log_event({"step": step, "ok": False, **{"status": "not have file"}})

            return

        ok, meta = await api_passport_ocr(
            client=client,
            token=token,
            tmp_secret=tmp_secret,
            file_path=get_passport_file_path(),
            form_field_name="file",
        )
        log_event({"step": step, "ok": ok, **meta})
        resp = meta.get("response")
        if isinstance(resp, dict):
            ocr_data = passport_ocr_result_from_dict(resp)
        else:
            await notify(
                f"Flow FAILED at step={step}. status={meta.get('status_code')} "
                f"err={meta.get('error')}"
            )
            return
        step = "get_draft"
        body_draft = GetDraftListBody()
        ok1, meta1 = await api_get_draft(client, token, tmp_secret, body_draft)
        log_event({"step": step, "ok": ok1, **meta1})
        if not ok1:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta1.get('status_code')} "
                f"err={meta1.get('error')}"
            )
            return

        resp1 = meta1.get("response", {})
        result = GetDraftListResult.from_dict(resp1)
        full_name = full_name_from_ocr(ocr_data)
        vietnamese_name = vietnamese_name_from_ocr(ocr_data)
        if not has_name(result, full_name):
            log_event(
                {
                    "step": step,
                    "ok": False,
                    "error": "Missing user_name in draft, create new",
                    "response": resp1,
                }
            )
            # todo: api create new
            step = "save_personal_information_first"
            body_save_person_infor = build_person_profile(
                "", ocr_data.Response.Data, province_city_code, id_card_number, {}
            )
            ok2, meta2 = await api_save_person_info(
                client, token, tmp_secret, body_save_person_infor
            )
            log_event({"step": step, "ok": ok2, **meta2})
            if not ok2:
                await notify(
                    f"Flow FAILED at step={step}. status={meta2.get('status_code')} "
                    f"err={meta2.get('error')}"
                )
                return
            first_applyid = get_in(meta2, "response", "Response", "Data", "applyid")
        obj = next(
            (
                it
                for it in result.Response.Data.list
                if (it.name or "").strip() == full_name
            ),
            None,
        )
        if first_applyid is None or first_applyid == "":
            first_applyid = obj.applyid if obj else ""
        print("applyid=", first_applyid)
        hotel_type = random.randint(0, 100) % len(HOTEL_DATA[visa_type]["hotel"])
        flight_ticket = random.randint(0, 100) % len(FLIGHT_TEMPLATE[visa_type])
        if not first_applyid:
            log_event(
                {
                    "step": step,
                    "ok": False,
                    "error": "Missing applyid in response",
                    "response": resp1,
                }
            )
            await notify(f"Flow FAILED at step={step}: missing applyid in response")
            return

        step = "get_current_draft_personal_information"
        data_obj = {}
        if first_applyid is None or first_applyid == "":
            ok, result = await api_get_person_info(
                client, token, tmp_secret, first_applyid
            )
            if ok:
                parsed = person_info_result_from_dict(result.get("response") or {})
                data_obj = parsed.Response.Data

        # step = "save_personal_information"
        # body_save_person_infor = build_person_profile(
        #     first_applyid,
        #     ocr_data.Response.Data,
        #     province_city_code,
        #     id_card_number,
        #     data_obj,
        # )
        # ok2, meta2 = await api_save_person_info(
        #     client, token, tmp_secret, body_save_person_infor
        # )
        # log_event({"step": step, "ok": ok2, **meta2})
        # if not ok2:
        #     await notify(
        #         f"Flow FAILED at step={step}. status={meta2.get('status_code')} "
        #         f"err={meta2.get('error')}"
        #     )
        #     return

        step = "save_type_of_visa"
        body_save_apply_info = build_apply_info_profile(
            first_applyid,
            first_letter_visa_type,
            last_letter_visa_type,
            entries_type,
            type_of_visa_sub_value,
            service_type,
        )
        ok3, meta3 = await api_save_apply_info(
            client,
            token,
            tmp_secret,
            body_save_apply_info,
        )
        log_event({"step": step, "ok": ok3, **meta3})
        if not ok3:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta3.get('status_code')} "
                f"err={meta3.get('error')}"
            )
            return

        step = "get_old_list"
        old_item_id = ""
        if haveChinaVisaFlag:
            okList, metaList = await api_list_online_applications(
                client,
                token,
                tmp_secret,
                ocr_data.Response.Data.passportNumber,
            )
            if okList:
                model = OnlineApplicationListResponse.from_dict(metaList["response"])
                for item in model.rows:
                    if item.applyStatus == OLD_APPLY_STATUS_APPROVED:
                        old_item_id = item.applyid
            log_event({"step": step, "ok": okList, **metaList})
            if not okList:
                await notify(
                    f"Flow FAILED at step={step}. "
                    f"status={metaList.get('status_code')} "
                    f"err={metaList.get('error')}"
                )
                return
        step = "save_work_info"
        # todo: if under 10 ages, ignore
        # todo: if have old old_item_id
        job_type = ""
        experiences: list[WorkExperienceItem] = []
        if old_item_id != "":
            ok, res = await api_get_work_info(
                client=client,
                token=token,
                tmp_secret=tmp_secret,
                applyid=old_item_id,
            )
            if ok:
                model = GetWorkInfoResponse.from_dict(res["response"])
                data = model.data  # Optional[GetWorkInfoData]
                if data:
                    job_type = data.jobType
                    experiences = data.workExperience
                    # model.raw is the full original dict
        body_save_work_info = build_work_info_profile(
            first_applyid,
            register_date,
            (
                ct08_province_city_code
                if ct08_province_city_code != ""
                else province_city_code
            ),
            job_type,
            experiences,
        )
        ok4, meta4 = await api_save_work_info(
            client,
            token,
            tmp_secret,
            body_save_work_info,
        )
        log_event({"step": step, "ok": ok4, **meta4})
        if not ok4:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta4.get('status_code')} "
                f"err={meta4.get('error')}"
            )
            return

        step = "save_education_info"
        # todo:  if under 10 ages, ignore
        educationExperience = []
        if old_item_id != "":
            ok, res = await api_get_education_info(
                client=client,
                token=token,
                tmp_secret=tmp_secret,
                applyid=old_item_id,
            )
            if ok:
                model = GetEducationInfoResponse.from_dict(res["response"])
                data = model.data  # Optional[GetWorkInfoData]
                if data:
                    educationExperience = data.educationExperience
        body_save_education_info = build_education_info_profile(
            first_applyid,
            (
                ct08_province_city_code
                if ct08_province_city_code != ""
                else province_city_code
            ),
            educationExperience,
        )
        ok5, meta5 = await api_save_education_info(
            client,
            token,
            tmp_secret,
            body_save_education_info,
        )
        log_event({"step": step, "ok": ok5, **meta5})
        if not ok5:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta5.get('status_code')} "
                f"err={meta5.get('error')}"
            )
            return

        step = "save_family_info"
        old_notApplyItems = []
        old_streetAddr = ""
        old_phoneNumber = ""
        old_mobilePhoneNumber = ""
        old_parents = []
        old_children = []
        old_relatives = []
        old_haveSpouseFlag = False
        old_spouses = []
        if old_item_id != "":
            ok, res = await api_get_family_info(
                client=client,
                token=token,
                tmp_secret=tmp_secret,
                applyid=old_item_id,
            )
            if ok:
                model = GetFamilyInfoResponse.from_dict(res["response"])
                data = model.data  # Optional[GetWorkInfoData]
                if data:
                    old_notApplyItems = data.notApplyItems
                    old_streetAddr = data.streetAddr
                    old_phoneNumber = data.phoneNumber
                    old_mobilePhoneNumber = data.mobilePhoneNumber
                    old_parents = data.parents
                    old_children = data.children
                    old_relatives = data.relatives
                    old_haveSpouseFlag = data.haveSpouseFlag
                    old_spouses = data.spouses
        dob = date_util.parse_date(ocr_data.Response.Data.dateOfBirth)

        if dob is None:
            await notify(
                f"Flow FAILED at step={step}. "
                "status={('data is not valid')} "
                "err={('step 6 cannot parse date')}"
            )
            return
        body_save_family_info = build_family_info_profile(
            first_applyid,
            (
                ct08_province_city_code
                if ct08_province_city_code != ""
                else province_city_code
            ),
            datetime.strptime(ocr_data.Response.Data.dateOfBirth, "%Y-%m-%d").date(),
            ocr_data.Response.Data.nationality,
            haveSpouseFlag,
            haveChildFlag,
            childFamilyName,
            childGivenName,
            childNationality,
            childBirthDate,
            fatherFamilyName,
            fatherGivenName,
            fatherNationality,
            fatherBirthDate,
            motherFamilyName,
            motherGivenName,
            motherNationality,
            motherBirthDate,
            ocr_data.Response.Data.passportFamilyName,
            old_notApplyItems,
            old_streetAddr,
            old_phoneNumber,
            old_mobilePhoneNumber,
            old_parents,
            old_children,
            old_relatives,
            old_haveSpouseFlag,
            old_spouses,
        )
        ok6, meta6 = await api_save_family_info(
            client,
            token,
            tmp_secret,
            body_save_family_info,
        )
        log_event({"step": step, "ok": ok6, **meta6})
        if not ok6:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta6.get('status_code')} "
                f"err={meta6.get('error')}"
            )
            return

        m, f = date_util.monday_and_friday_skip_4_weeks(register_date)

        prefix_flight_text = FLIGHT_TEMPLATE[visa_type][flight_ticket][
            "prefix_flight_text"
        ]
        arrive_flight_number, departure_flight_number = generate_phone_pair(
            FLIGHT_TEMPLATE[visa_type][flight_ticket]["prefix_number"]
        )
        step = "save_travel_info"
        arrive_flight_number_full_info = prefix_flight_text + " " + arrive_flight_number
        departure_flight_number_full_info = (
            prefix_flight_text + " " + departure_flight_number
        )
        body_save_travel_info = build_travel_info_profile(
            visa_type,
            first_applyid,
            dob,
            fatherFamilyName,
            fatherGivenName,
            motherFamilyName,
            motherGivenName,
            payName,
            payMobile,
            m,
            f,
            hotel_type,
            arrive_flight_number_full_info,
            departure_flight_number_full_info,
        )
        ok7, meta7 = await api_save_travel_info(
            client,
            token,
            tmp_secret,
            body_save_travel_info,
        )
        print(body_save_travel_info)
        log_event({"step": step, "ok": ok7, **meta7})
        if not ok7:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta7.get('status_code')} "
                f"err={meta7.get('error')}"
            )
            return

        step = "save_previous_travel_info"
        body_save_previous_travel_info = build_previous_travel_info_profile(
            first_applyid,
            arrivedChinaFlag,
            haveChinaVisaFlag,
            old_visaType,
            old_visaNumber,
            old_issueDate,
            old_issuePlace,
            haveOtherVisaFlag,
            old_otherVisas,
            old_otherCountries,
        )
        ok8, meta8 = await api_save_previous_travel_info(
            client,
            token,
            tmp_secret,
            body_save_previous_travel_info,
        )
        log_event({"step": step, "ok": ok8, **meta8})
        if not ok8:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta8.get('status_code')} "
                f"err={meta8.get('error')}"
            )
            return

        step = "save_other_info"
        body_other_info = build_other_info(
            first_applyid,
        )
        ok8, meta8 = await api_save_other_info(
            client,
            token,
            tmp_secret,
            body_other_info,
        )
        log_event({"step": step, "ok": ok8, **meta8})
        if not ok8:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta8.get('status_code')} "
                f"err={meta8.get('error')}"
            )
            return
        step = "save_signature"
        body_signature_info = build_signature_body(
            first_applyid,
        )
        ok8, meta8 = await api_save_signature_info(
            client,
            token,
            tmp_secret,
            body_signature_info,
        )
        log_event({"step": step, "ok": ok8, **meta8})
        if not ok8:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta8.get('status_code')} "
                f"err={meta8.get('error')}"
            )
            return
        hotel = L_15_HOTEL_INFO[hotel_type].get("documentName")
        if guest_name == []:
            guest_name = [vietnamese_name]
        try:
            payload = {
                "file_name": hotel,
                "names": guest_name,
                "first": m,
                "end": f,
                "type": "hotel",
            }
            await hotel_info.render_docx_template_output_pdf(
                payload, L_15_HOTEL_OUTPUT_PATH
            )
            log_event({"step": "genenrate hotel file", "ok": "ok"})
        except Exception as e:
            log_exception(e, {"event": "render_failed", "file": hotel})
            raise

        file_name = ""
        if ticket_names == []:
            ticket_names = [vietnamese_name]
        try:
            if visa_type in FLIGHT_TEMPLATE:
                file_name = FLIGHT_TEMPLATE[visa_type][flight_ticket]["name"]
            else:
                log_exception(
                    KeyError(f"Key {visa_type} not found"),
                    {"event": "not have ticket key ", "visa_type": visa_type},
                )
            payload = {
                "file_name": file_name,
                "arrive_flight_number": arrive_flight_number,
                "departure_flight_number": departure_flight_number,
                "arrvied_city": L_15_HOTEL_INFO[hotel_type].get("place_city"),
                "names": ticket_names,
                "arrived_iata_code": L_15_HOTEL_INFO[hotel_type].get("iata_code"),
                "departure_iata_code": L_15_HOTEL_INFO[hotel_type].get("iata_code"),
                "departure_city": L_15_HOTEL_INFO[hotel_type].get("place_city"),
                "first": m,
                "end": f,
                "type": "flight_ticket",
            }
            log_event({"step": "genenrate flight ticket file", "ok": "ok"})
        except Exception as e:
            log_exception(
                e, {"event": "render_failed", "file": payload.get("file_name")}
            )
        await hotel_info.render_docx_template_output_pdf(
            payload, L_15_TICKET_OUTPUT_PATH
        )

        # CV FILE
        if ticket_names == []:
            ticket_names = [vietnamese_name]
        try:

            today_yyyy, today_mm, today_dd = get_today_parts()
            file_name = CV_DATA

            payload = {
                "file_name": file_name,
                "names": ticket_names,
                "visa_type_first": first_letter_visa_type,
                "visa_type_number": last_letter_visa_type,
                "submit_year_yyyy": today_yyyy,
                "submit_month_mm": today_mm,
                "submit_day_dd": today_dd,
                "sex": SEX_MAP.get(ocr_data.Response.Data.sex, ""),
                "nationality": NATIONALITY_MAP.get(
                    ocr_data.Response.Data.nationality, ""
                ),
                "passportNo": ocr_data.Response.Data.passportNumber,
                "birth_date_dd_mm_yyyy": format_date(
                    ocr_data.Response.Data.dateOfBirth
                ),
                "expired_day_dd_mm_yyyy": format_date(
                    ocr_data.Response.Data.dateOfExpiration
                ),
            }
            log_event({"step": "genenrate flight ticket file", "ok": "ok"})
        except Exception as e:
            log_exception(
                e, {"event": "render_failed", "file": payload.get("file_name")}
            )
        await cv_info.render_docx_template_output_pdf(
            payload, L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH
        )
        # END
        step = "Step 9 Upload File"

        cfg_file_by_visa_type = UPLOAD_FILE_CODE_BY_VISA_TYPE[visa_type]

        for group_key, group_cfg in cfg_file_by_visa_type.items():
            for doc_type, files in group_cfg.items():

                config = UPLOAD_CONFIG[visa_type].get(doc_type)

                if not config:
                    continue

                # Support both:
                # {}  -> single config
                # []  -> multiple configs
                configs = config if isinstance(config, list) else [config]

                all_upload_files = []

                for cfg in configs:
                    upload_files = get_files(
                        cfg["folder"],
                        cfg["limit"],
                    )

                    all_upload_files.extend(upload_files)

                for f_doc, upload_file in zip(files, all_upload_files):

                    if not upload_file:
                        continue

                    print(upload_file, f_doc["categoryCode"], f_doc["materialCode"])

                    await api_upload_file_common(
                        client,
                        token,
                        tmp_secret,
                        upload_file,
                        f_doc["categoryCode"],
                        f_doc["materialCode"],
                        first_applyid,
                    )


def get_in(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur
