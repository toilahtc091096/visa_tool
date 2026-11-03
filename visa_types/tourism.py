"""L visas (tourism): L15 and L30."""

from __future__ import annotations

import random
from typing import Any

from constants import (
    L_15_HOTEL_INFO,
    REGION,
    REGION_SOUTH,
    SOUTH_FLIGHT_TEMPLATE,
    SOUTH_L30_HOTEL_INFO,
    WEEK_SKIP_BY_TYPE,
)
from flows.flow_payloads import getL15TravelInfo, getL30TravelInfo

from .base import ReuseRule, VisaProfile, register
from .documents import (
    COMMON_DOC_FOLDERS,
    FlightTicket,
    Itinerary,
    L15HotelBooking,
    L30HotelBooking,
    SouthItinerary,
    VisaCenterConfirmation,
)

FAMILY_REUSE = ReuseRule(
    source_field="family_passport",
    folders=COMMON_DOC_FOLDERS,
    missing_message="No family common documents found on R2 for prefix: {prefix}",
)


class TourismVisa(VisaProfile):
    service_key = "L"
    reuse = FAMILY_REUSE
    cleans_local_common_docs = True


@register
class L15Visa(TourismVisa):
    """15 days, one hotel, generated hotel booking + flight ticket."""

    code = "L15"
    hotels = L_15_HOTEL_INFO
    documents = (L15HotelBooking(), FlightTicket(), VisaCenterConfirmation())

    def choose_hotel(self, ctx) -> None:
        ctx.hotel_type = random.randrange(len(self.hotels))

    def build_travel_json(self, travel) -> dict[str, Any]:
        travel_json = getL15TravelInfo(
            **travel.emergency(),
            is_under_18=travel.is_under_18,
            has_additional_names=travel.has_additional_names,
            haveChildFlag=travel.haveChildFlag,
            hotel_type=travel.hotel_type,
            arrival_str=travel.arrival_str,
            leave_str=travel.leave_str,
            arrivalVehicleType=travel.arrivalVehicleType,
            leaveVehicleType=travel.leaveVehicleType,
            is_private=travel.is_private,
            hotels=self.hotels,
        )
        if REGION == REGION_SOUTH:
            # South L15 / L30: no invitation letter.
            travel_json["notApplyItems"] = [
                {"notApplyCode": "invitation", "remark": "N/A"}
            ]
            # One hotel: arrive at and leave from the same county.
            travel_json["leaveCounty"] = travel_json.get("arrivalCounty") or ""
        return travel_json


class L30Visa(TourismVisa):
    """30 days over three cities, with a day-by-day itinerary."""

    code = "L30"
    documents = (
        L30HotelBooking(),
        FlightTicket(three_cities=True),
        VisaCenterConfirmation(),
        Itinerary(),
    )

    def build_travel_json(self, travel) -> dict[str, Any]:
        return getL30TravelInfo(
            **travel.emergency(),
            is_under_18=travel.is_under_18,
            haveChildFlag=travel.haveChildFlag,
            arrival_date=travel.arrival_date,
            arrivalVehicleType=travel.arrivalVehicleType,
            leaveVehicleType=travel.leaveVehicleType,
            is_private=travel.is_private,
        )


class SouthL30Visa(L15Visa):
    """South (HCMC) L30: works exactly like the north L15 (one hotel, same
    dates and flight tickets), with the South hotel."""

    code = "L30"
    hotels = SOUTH_L30_HOTEL_INFO
    flight_visa_type = "L15"
    documents = (
        L15HotelBooking(),
        FlightTicket(),
        VisaCenterConfirmation(),
        SouthItinerary(),
    )

    @property
    def flight_templates(self) -> list[dict[str, str]]:
        return SOUTH_FLIGHT_TEMPLATE

    @property
    def week_skip(self) -> int | None:
        return WEEK_SKIP_BY_TYPE["L15"]


register(SouthL30Visa if REGION == REGION_SOUTH else L30Visa)
