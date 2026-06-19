import random

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
)
from flows.flow_payloads import (
    build_L30_guest_names,
    build_other_info,
    build_previous_travel_info_profile,
    build_signature_body,
    build_travel_info_profile,
)
from generate_file import cv_info, hotel_info, flight_info, file_init_info
from utils import (
    date_util,
    format_date,
    generate_phone_pair,
    get_today_parts,
    log_event,
    log_exception,
    notify,
)


async def save_travel_and_generate_docs(ctx, client) -> bool:
    if ctx.visa_type == "L15":
        ctx.hotel_type = random.randint(0, 100) % len(
            HOTEL_DATA[ctx.visa_type]["hotel"]
        )
    ctx.flight_ticket = random.randint(0, 100) % len(FLIGHT_TEMPLATE[ctx.visa_type])
    ctx.m, ctx.f = date_util.monday_and_friday_skip_x_weeks(
        ctx.register_date, WEEK_SKIP_BY_TYPE.get(ctx.visa_type)
    )
    ctx.prefix_flight_text = FLIGHT_TEMPLATE[ctx.visa_type][ctx.flight_ticket][
        "prefix_flight_text"
    ]
    ctx.arrive_flight_number, ctx.departure_flight_number = generate_phone_pair(
        FLIGHT_TEMPLATE[ctx.visa_type][ctx.flight_ticket]["prefix_number"]
    )

    ctx.step = "save_travel_info"
    arrive_flight_number_full_info = (
        ctx.prefix_flight_text + " " + ctx.arrive_flight_number
    )
    departure_flight_number_full_info = (
        ctx.prefix_flight_text + " " + ctx.departure_flight_number
    )

    if ctx.is_under_18 or (ctx.haveChildFlag and not ctx.is_private): #todo: them and is_private  (haveChildFlag and is_private)
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

    if ctx.visa_type == "L15":
        if ctx.is_under_18:
            print("under 18, generate hotel file with payName or random name")
            hotel = UNDER_18_HOTEL_INFO[0]["documentName"]
            adult = (
                ctx.payName if ctx.payName else random.choice(VIETNAMESE_NAMES).upper()
            )
            if not ctx.guest_name:
                ctx.guest_name = [ctx.vietnamese_name, adult]
                print(f"guest_name: {ctx.guest_name}")
        elif (ctx.haveChildFlag and not ctx.is_private): #todo: them and is_private  (haveChildFlag and is_private)
            hotel = UNDER_18_HOTEL_INFO[0]["documentName"]
            child = (
                f"{ctx.childFamilyName} {ctx.childGivenName}"
                if (ctx.childGivenName and ctx.childFamilyName)
                else random.choice(VIETNAMESE_NAMES).upper()
            )
            if not ctx.guest_name:
                ctx.guest_name = [ctx.vietnamese_name, child]
        else:
            hotel = L_15_HOTEL_INFO[ctx.hotel_type]["documentName"]
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
            }
            print(f"payload for hotel file: {payload}")
            await hotel_info.render_docx_template_output_pdf(
                payload, L_15_HOTEL_OUTPUT_PATH
            )
            log_event({"step": "genenrate hotel file", "ok": "ok"})
        except Exception as e:
            log_exception(e, {"event": "render_failed", "file": hotel})
            raise
    elif ctx.visa_type == "L30":
        ctx.guest_name = build_L30_guest_names(ctx.guest_name, ctx.vietnamese_name)
        try:
            payload = {
                "names": ctx.guest_name,
                "first": ctx.m,
                "type": "hotel",
                "is_under_18": ctx.is_under_18,
                "haveChildFlag": ctx.haveChildFlag,
            }
            await hotel_info.render_L30_hotel(payload, L_15_HOTEL_OUTPUT_PATH)
            log_event({"step": "genenrate hotel file", "ok": "ok"})
        except Exception as e:
            log_exception(e, {"event": "render_failed_L30"})
            raise

    file_name = ""
    if ctx.ticket_names == []:
        ctx.ticket_names = [ctx.vietnamese_name]
        if ctx.is_under_18:
            ctx.ticket_names.append(
                ctx.payName if ctx.payName else random.choice(VIETNAMESE_NAMES).upper()
            )
        if (ctx.haveChildFlag and not ctx.is_private): #todo: them and is_private  (haveChildFlag and is_private)
            ctx.ticket_names.append(
                f"{ctx.childFamilyName} {ctx.childGivenName}"
                if (ctx.childGivenName and ctx.childFamilyName)
                else random.choice(VIETNAMESE_NAMES).upper()
            )
    try:
        if ctx.visa_type in FLIGHT_TEMPLATE:
            file_name = FLIGHT_TEMPLATE[ctx.visa_type][ctx.flight_ticket]["name"]
        else:
            log_exception(
                KeyError(f"Key {ctx.visa_type} not found"),
                {"event": "not have ticket key ", "visa_type": ctx.visa_type},
            )
        if ctx.visa_type == "L30":
            hotel_info_item = L_30_HOTEL_INFO[0]
            hotel_departure_info_item = L_30_HOTEL_INFO[-1]
        else:
            hotel_info_item = L_15_HOTEL_INFO[ctx.hotel_type]
        if ctx.is_under_18 or (ctx.haveChildFlag and not ctx.is_private): #todo: them and is_private  (haveChildFlag and is_private)
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
        if ctx.visa_type == "L30":
            payload.update(
                {
                    "departure_iata_code": hotel_departure_info_item.get("iata_code"),
                    "departure_city": hotel_departure_info_item.get("place_city"),
                }
            )
        log_event({"step": "genenrate flight ticket file", "ok": "ok"})
    except Exception as e:
        log_exception(e, {"event": "render_failed", "file": payload.get("file_name")})
    await flight_info.render_flight_ticket_output_pdf(payload, L_15_TICKET_OUTPUT_PATH)

    ctx.ticket_names = [ctx.vietnamese_name]
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
            "passportNumber": ctx.passportNumber,
        }
        log_event({"step": "genenrate flight ticket file", "ok": "ok"})
    except Exception as e:
        log_exception(e, {"event": "render_failed", "file": payload.get("file_name")})
    await cv_info.render_docx_template_output_pdf(
        payload, L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH
    )
    ctx.ticket_names = [ctx.vietnamese_name]

    try:
        file_name = TRAVEL_PLAN_21D

        payload = {
            "file_name": file_name,
            "names": ctx.ticket_names,
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
    )

    return True
