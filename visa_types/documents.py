"""Documents generated for an application (hotel, flight ticket, CV...).

Each DocumentStep renders one document into ``output_folder`` of the
applicant's data folder. A profile lists the steps it needs, in order.
"""

from __future__ import annotations

import random
from typing import Any

from constants import (
    CV_DATA,
    L_15_HOTEL_INFO,
    L_15_HOTEL_OUTPUT_PATH,
    L_15_TICKET_OUTPUT_PATH,
    L_15_TRAVEL_PLAN_OUTPUT_PATH,
    L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH,
    L_30_HOTEL_INFO,
    NATIONALITY_MAP,
    SEX_MAP,
    TRAVEL_PLAN_21D,
    UNDER_18_HOTEL_INFO,
    VIETNAMESE_NAMES,
)
from flows.flow_payloads import build_L30_guest_names
from generate_file import cv_info, file_init_info, flight_info, hotel_info, thumoi_info
from utils import format_date, get_today_parts, log_event, log_exception


# R2/local folders shared between applicants of the same family/company/school.
COMMON_DOC_FOLDERS = (
    "chung/khach_san",
    "chung/ve_may_bay",
    "chung/xac_nhan_tu_trung_tam_visa",
)
CV_DOC_FOLDERS = ("chung/xac_nhan_tu_trung_tam_visa",)


def has_additional_names(ctx) -> bool:
    return bool(getattr(ctx, "addition_adults", []) or getattr(ctx, "addition_child", []))


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


def _companion_name(ctx) -> str:
    """Adult travelling with a minor: the payer, or a random Vietnamese name."""
    return ctx.payName if ctx.payName else random.choice(VIETNAMESE_NAMES).upper()


class DocumentStep:
    output_folder: str = ""

    async def render(self, ctx) -> None:
        raise NotImplementedError


class L15HotelBooking(DocumentStep):
    output_folder = L_15_HOTEL_OUTPUT_PATH

    async def render(self, ctx) -> None:
        additional = has_additional_names(ctx)
        adult_number = 0 if ctx.is_under_18 else 1
        child_number = 1 if ctx.is_under_18 else 0
        if additional:
            if not ctx.guest_name:
                ctx.guest_name = [ctx.vietnamese_name]
            adult_number += len(getattr(ctx, "addition_adults", []))
            child_number += len(getattr(ctx, "addition_child", []))
            _extend_unique_names(ctx.guest_name, ctx.addition_adults)
            _extend_unique_names(ctx.guest_name, ctx.addition_child)
            _extend_unique_names(ctx.guest_name, _child_names(ctx))
        elif ctx.is_under_18:
            print("under 18, generate hotel file with payName or random name")
            adult = _companion_name(ctx)
            if not ctx.guest_name:
                ctx.guest_name = [ctx.vietnamese_name, adult]
                print(f"guest_name: {ctx.guest_name}")
        if ctx.is_under_18 or additional:
            hotel = UNDER_18_HOTEL_INFO[0]["documentName"]
        else:
            hotel = L_15_HOTEL_INFO[ctx.hotel_type]["documentName"]
        if not ctx.guest_name:
            ctx.guest_name = [ctx.vietnamese_name]

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
            "has_additional_names": additional,
        }
        print(f"payload for hotel file: {payload}")
        try:
            await hotel_info.render_docx_template_output_pdf(
                payload, self.output_folder, ctx.input_passportNumber
            )
        except Exception as e:
            log_exception(e, {"event": "render_failed", "file": hotel})
            raise
        log_event({"step": "genenrate hotel file", "ok": "ok"})


class L30HotelBooking(DocumentStep):
    output_folder = L_15_HOTEL_OUTPUT_PATH

    async def render(self, ctx) -> None:
        ctx.guest_name = build_L30_guest_names(
            ctx.guest_name,
            ctx.vietnamese_name,
            ctx.addition_adults,
            ctx.addition_child,
        )
        payload = {
            "names": ctx.guest_name,
            "addition_adults": ctx.addition_adults,
            "addition_child": ctx.addition_child,
            "first": ctx.m,
            "type": "hotel",
            "is_under_18": ctx.is_under_18,
            "haveChildFlag": ctx.haveChildFlag,
        }
        try:
            await hotel_info.render_L30_hotel(
                payload, self.output_folder, ctx.input_passportNumber
            )
        except Exception as e:
            log_exception(e, {"event": "render_failed_L30"})
            raise
        log_event({"step": "genenrate hotel file", "ok": "ok"})


class FlightTicket(DocumentStep):
    """Round-trip ticket landing next to the hotel(s) of the travel info.

    ``three_cities``: arrive at the first L30 hotel city, leave from the last.
    """

    output_folder = L_15_TICKET_OUTPUT_PATH

    def __init__(self, three_cities: bool = False) -> None:
        self.three_cities = three_cities

    async def render(self, ctx) -> None:
        additional = has_additional_names(ctx)
        if ctx.ticket_names == []:
            ctx.ticket_names = self._passenger_names(ctx, additional)

        template = ctx.profile.flight_templates[ctx.flight_ticket]
        if self.three_cities:
            arrival_info = L_30_HOTEL_INFO[0]
            departure_info = L_30_HOTEL_INFO[-1]
        elif ctx.is_under_18 or additional:
            arrival_info = departure_info = UNDER_18_HOTEL_INFO[0]
        else:
            arrival_info = departure_info = L_15_HOTEL_INFO[ctx.hotel_type]
        if ctx.is_under_18 or additional:
            ctx.arrive_flight_number = ctx.arrive_flight_number[-4:]
            ctx.departure_flight_number = ctx.departure_flight_number[-4:]
        payload = {
            "file_name": template["name"],
            "arrive_flight_number": ctx.arrive_flight_number,
            "departure_flight_number": ctx.departure_flight_number,
            "arrvied_city": arrival_info.get("place_city"),
            "names": ctx.ticket_names,
            "arrived_iata_code": arrival_info.get("iata_code"),
            "first": ctx.m,
            "departure_iata_code": departure_info.get("iata_code"),
            "departure_city": departure_info.get("place_city"),
            "end": ctx.f,
            "type": "flight_ticket",
            "visa_type": ctx.visa_type,
        }
        await flight_info.render_flight_ticket_output_pdf(
            payload, self.output_folder, ctx.input_passportNumber
        )
        log_event({"step": "genenrate flight ticket file", "ok": "ok"})

    @staticmethod
    def _passenger_names(ctx, additional: bool) -> list[str]:
        if not additional:
            names = [ctx.vietnamese_name]
            if ctx.is_under_18:
                names.append(_companion_name(ctx))
            return names
        names = _sorted_unique_names(ctx.addition_adults)
        if ctx.vietnamese_name and ctx.vietnamese_name not in names:
            names.append(ctx.vietnamese_name)
        _extend_unique_names(names, _sorted_unique_names(ctx.addition_child))
        _extend_unique_names(names, _child_names(ctx))
        return names


class VisaCenterConfirmation(DocumentStep):
    """The "CV" confirmation form of the visa center, for the applicant only."""

    output_folder = L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH

    async def render(self, ctx) -> None:
        ctx.ticket_names = [ctx.vietnamese_name]
        ocr = ctx.ocr_data.Response.Data
        today_yyyy, today_mm, today_dd = get_today_parts()
        payload = {
            "file_name": CV_DATA,
            "names": ctx.ticket_names,
            "visa_type_first": ctx.first_letter_visa_type,
            "visa_type_number": ctx.last_letter_visa_type,
            "submit_year_yyyy": today_yyyy,
            "submit_month_mm": today_mm,
            "submit_day_dd": today_dd,
            "sex": SEX_MAP.get(ocr.sex, ""),
            "nationality": NATIONALITY_MAP.get(ocr.nationality, ""),
            "passportNo": ocr.passportNumber,
            "birth_date_dd_mm_yyyy": format_date(ocr.dateOfBirth),
            "expired_day_dd_mm_yyyy": format_date(ocr.dateOfExpiration),
            "passengers": getattr(ctx, "passengers", []),
            "passportNumber": ctx.passportNumber,
            "entries_type": ctx.entries_type,
        }
        await cv_info.render_docx_template_output_pdf(
            payload, self.output_folder, ctx.input_passportNumber
        )
        log_event({"step": "genenrate CV file", "ok": "ok"})


class InvitationLetter(DocumentStep):
    """Invitation letter (thu moi) from the inviter given in the request."""

    template_name = "Q_Template.docx"

    def __init__(self, output_folder: str) -> None:
        self.output_folder = output_folder

    async def render(self, ctx) -> None:
        log_event(
            {
                "step": "generate invitation letter file",
                "ok": "ok",
                "file": self.template_name,
            }
        )
        try:
            await thumoi_info.render_thumoi_docx_output_pdf(
                ctx, self.output_folder, ctx.input_passportNumber
            )
        except Exception as e:
            log_exception(e, {"event": "render_failed", "file": self.template_name})
            raise


class Itinerary(DocumentStep):
    """Day-by-day travel plan matching the three L30 hotel stays."""

    output_folder = L_15_TRAVEL_PLAN_OUTPUT_PATH

    async def render(self, ctx) -> None:
        await file_init_info.render_init_pdf(
            {"file_name": TRAVEL_PLAN_21D, "first": ctx.m},
            self.output_folder,
            ctx.input_passportNumber,
        )
        log_event(
            {
                "step": "generate travel itinerary file",
                "ok": "ok",
                "file": TRAVEL_PLAN_21D,
            }
        )
