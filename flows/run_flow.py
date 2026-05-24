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
    api_upload_file,
    api_save_other_info,
)
from constants import (
    DOCUMENT_DATA,
    ENTRIES_TYPE,
    MY_VISA_TYPE,
    SERVICE_VISA_TYPE,
    VISA_TYPE_DAY_VALUE,
    VISA_TYPE_VALUE,
    L_15_HOTEL_INFO,
    FLIGHT_TEMPLATE,
    UPLOAD_FILE_CODE,
    UPLOAD_FILE_CODE_BY_VISA_TYPE,
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
)
from models import GetDraftListBody, GetDraftListResult, has_name, passport_ocr_result_from_dict, upload_material
from utils import date_util, log_event, notify
from utils.logging import log_exception

async def run_flow(
    token: str,
    tmp_secret: str,
    visa_type: str,
    register_date: date,
    guest_name: list[str],
    ticket_names:list[str],
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
    haveOtherVisaFlag: bool=False,
    old_otherVisas: list[str]=[],
    old_otherCountries: list[str]=[],
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
        log_event({"step": "ENTRIES_TYPE check", "status": entries_type + " not support"})
        return
    if type_of_visa_sub_value not in VISA_TYPE_VALUE.get(first_letter_visa_type, {}):
        log_event({"step": "service type", "status": type_of_visa_sub_value + " not support"})
        return

    async with httpx.AsyncClient() as client:
        step = "get ocr"
        ok, meta = await api_passport_ocr(
            client=client,
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
        hotel_type = int(first_applyid[-1]) % len(DOCUMENT_DATA[visa_type]["hotel"]);
        flight_ticket = int(first_applyid[-1]) % 2;
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
            client, token, tmp_secret, body_save_person_infor
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

        arrive_05, depature_05 = generate_phone_pair("05");
        arrive_83, depature_83 = generate_phone_pair("83");
        # Step 7: SaveTravelInfo
        step = "save_travel_info"
        body_save_travel_info = build_travel_info_profile(
            visa_type,
            first_applyid,
            m,
            f,
            hotel_type,
            arrive_05, 
            depature_05
        )
        ok7, meta7 = await api_save_travel_info(
            client,
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

        # Step 8: Save Other Info
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
        hotel = L_15_HOTEL_INFO[hotel_type].get("documentName")
        if guest_name ==[]: 
            guest_name = [vietnamese_name]
        try: 
            payload = {
               "file_name": hotel,
                "names": guest_name,
                "first": m,
                "end": f,
                "type": 'hotel'
            }
            pdf_hotel = await hotel_info.render_docx_template_output_pdf(payload)
            log_event({"step": "genenrate hotel file", "ok": "ok"})
        except Exception as e:
            log_exception(e, {"event": "render_failed", "file": hotel})
            raise

        pdf_hotels = [pdf_hotel]


        file_name = ""
        if ticket_names =='': 
            ticket_names = [vietnamese_name]
        try: 
            if visa_type in FLIGHT_TEMPLATE:
                file_name = FLIGHT_TEMPLATE[visa_type][flight_ticket]["name"]
            else:
                log_exception( KeyError(f"Key {visa_type} not found"), {"event": "not have ticket key ", "visa_type": visa_type})

            payload = {
                #fake
                "file_name": file_name,
                "arrive_flight_number_from_05": arrive_05,    
                "arrive_flight_number_from_83": arrive_83,    
                "departure_flight_number_from_05": depature_05, 
                "departure_flight_number_from_83": depature_83, 
                #fake

                "arrvied_city": L_15_HOTEL_INFO[hotel_type].get("place_city"),                   
                "names": ticket_names,  
                "arrived_iata_code": L_15_HOTEL_INFO[hotel_type].get("iata_code"),              
                "departure_iata_code": L_15_HOTEL_INFO[hotel_type].get("iata_code"),          
                "departure_city": L_15_HOTEL_INFO[hotel_type].get("place_city"),                  
                "first": m,
                "end": f,
                "type": 'flight_ticket'
            }
            log_event({"step": "genenrate flight ticket file", "ok": "ok"})
        except Exception as e:
            log_exception(e, {"event": "render_failed", "file": payload.get("file_name")})
        pdf_ticket = await hotel_info.render_docx_template_output_pdf(payload)
        step = "Step 9 Upload File"

        cfg_file_by_visa_type = UPLOAD_FILE_CODE_BY_VISA_TYPE[visa_type]     
        for group_key, group_cfg in cfg_file_by_visa_type.items():
            for doc_type, files in group_cfg.items():             
                for f in files:   
                    if doc_type == 'FLIGHT_TICKET':
                        file_name = pdf_ticket
                        await api_upload_file_common(client, token, tmp_secret, file_name, f["categoryCode"], f["materialCode"], first_applyid)
                    if doc_type == "HOTEL_RESERVATION_WITH_PAYMENT":
                        for f, file_name in zip(files, pdf_hotels):
                            await api_upload_file_common(client, token, tmp_secret, file_name, f["categoryCode"], f["materialCode"], first_applyid)


async def api_upload_file_common(
    client:str,
    token: str,
    tmp_secret: str,
    file_name:str,
    category_code:str,
    material_code:str,
    first_applyid:str,
)   -> None:
    ticket_upload_payload_body = build_upload_material_body(
        file_name,
        category_code,
        material_code,
        first_applyid,
        )
    ok9, meta9 = await api_upload_file(
        client,
        token,
        tmp_secret,
        ticket_upload_payload_body,                        
        )         
    log_event({"step": "step", "ok": ok9, **meta9})
    if not ok9:
        await notify(
            f"Flow FAILED at step={'step'}. "
            f"status={meta9.get('status_code')} "
            "err={meta9.get('error')}"
            )
        return

def generate_phone_pair(prefix: str):
    """
    Input:
        "05"

    Output:
        ("0512", "0518")
    """

    if len(prefix) != 2 or not prefix.isdigit():
        raise ValueError("prefix must be 2 digits string")

    # số đầu
    first_suffix = random.randint(10, 89)

    # số thứ 2 cách vài đơn vị
    second_suffix = first_suffix + random.randint(1, 9)

    # tránh vượt 99
    if second_suffix > 99:
        second_suffix = 99

    first_number = f"{prefix}{first_suffix:02d}"
    second_number = f"{prefix}{second_suffix:02d}"

    return first_number, second_number
