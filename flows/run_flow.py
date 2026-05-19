import random

from datetime import date, datetime
import httpx

from generate_file import hotel_info
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
)
from constants import (
    DOCUMENT_DATA,
    ENTRIES_TYPE,
    MY_VISA_TYPE,
    SERVICE_VISA_TYPE,
    VISA_TYPE_DAY_VALUE,
    VISA_TYPE_VALUE,
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
)
from models import GetDraftListBody, GetDraftListResult, has_name, passport_ocr_result_from_dict
from utils import date_util, log_event, notify


async def run_flow(
    base_url: str,
    token: str,
    tmp_secret: str,
    visa_type: str,
    register_date: date,
    guest_name: list[str],
    file_path: str,
    province_city_code: str,
    id_card_number: str,
    entries_type: str,
    type_of_visa_sub_value: str,
    service_type: str,
    arrivedChinaFlag: bool = False,
    haveChinaVisaFlag: bool = False,
    old_visaType: str ="",
    old_visaNumber: str ="",
    old_issueDate: str ="",
    old_issuePlace: str ="",
    haveOtherVisaFlag: str ="",
    old_otherVisas: str ="",
    old_otherCountries: str ="",
) -> None:
    first_letter_visa_type = visa_type[0]
    last_letter_visa_type = visa_type[1:]
    if (
        visa_type not in MY_VISA_TYPE
        or first_letter_visa_type not in SERVICE_VISA_TYPE
        or last_letter_visa_type not in VISA_TYPE_DAY_VALUE[first_letter_visa_type]
    ):
        log_event({"step": "Visa Type", "status": visa_type + " not support"})
        return
    if entries_type not in ENTRIES_TYPE:
        log_event({"step": "ENTRIES_TYPE check", "status": ENTRIES_TYPE + " not support"})
        return
    if type_of_visa_sub_value not in VISA_TYPE_VALUE.get(first_letter_visa_type, {}):
        log_event({"step": "service type", "status": type_of_visa_sub_value + " not support"})
        return

    async with httpx.AsyncClient() as client:
        step = "get ocr"
        ok, meta = await api_passport_ocr(
            client=client,
            base_url=base_url,
            token=token,
            tmp_secret=tmp_secret,
            file_path=file_path,
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
        ok1, meta1 = await api_get_draft(client, base_url, token, tmp_secret, body_draft)
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

        if not has_name(result, full_name):
            log_event(
                {
                    "step": step,
                    "ok": False,
                    "error": "Missing user_name in response",
                    "response": resp1,
                }
            )
            await notify(f"Flow FAILED at step={step}: missing user_id in response")
            return

        obj = next(
            (
                it
                for it in result.Response.Data.list
                if (it.name or "").strip() == full_name
            ),
            None,
        )
        first_applyid = obj.applyid if obj else ""
        print("applyid=", first_applyid)
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

        step = "save_personal_information"
        body_save_person_infor = build_person_profile(
            first_applyid,
            ocr_data.Response.Data,
            province_city_code,
            id_card_number,
        )
        ok2, meta2 = await api_save_person_info(
            client, base_url, token, tmp_secret, body_save_person_infor
        )
        log_event({"step": step, "ok": ok2, **meta2})
        if not ok2:
            await notify(
                f"Flow FAILED at step={step}. status={meta2.get('status_code')} "
                f"err={meta2.get('error')}"
            )
            return

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
            base_url,
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

        # Step 4: SaveWorkInfo
        step = "save_work_info"
        body_save_work_info = build_work_info_profile(
            first_applyid,
            register_date,
            province_city_code,
        )
        ok4, meta4 = await api_save_work_info(
            client,
            base_url,
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

        # Step 5: SaveEducationInfo
        step = "save_education_info"
        body_save_education_info = build_education_info_profile(
            first_applyid,
            province_city_code,
        )
        ok5, meta5 = await api_save_education_info(
            client,
            base_url,
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

        # Step 6: SaveFamilyInfo
        step = "save_family_info"
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
            province_city_code,
            datetime.strptime(ocr_data.Response.Data.dateOfBirth, "%Y-%m-%d").date(),
            ocr_data.Response.Data.nationality
        )
        ok6, meta6 = await api_save_family_info(
            client,
            base_url,
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

        # Step 7: SaveTravelInfo
        step = "save_travel_info"
        body_save_travel_info = build_travel_info_profile(
            first_applyid,
            m,
            f,
        )
        ok7, meta7 = await api_save_travel_info(
            client,
            base_url,
            token,
            tmp_secret,
            body_save_travel_info,
        )
        log_event({"step": step, "ok": ok7, **meta7})
        if not ok7:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta7.get('status_code')} "
                f"err={meta7.get('error')}"
            )
            return

        # Step 8: SavePreviousTravelInfo
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
            old_otherCountries
        )
        ok8, meta8 = await api_save_previous_travel_info(
            client,
            base_url,
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

        first_apply_id = random.choice([0, 1])
        data = DOCUMENT_DATA[visa_type]
        hotel = data["hotel"][first_apply_id]
        await hotel_info.render_docx_template(hotel, guest_name, m, f)
 