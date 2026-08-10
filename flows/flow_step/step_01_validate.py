from constants import (
    ENTRIES_TYPE,
    SERVICE_VISA_TYPE,
    VISA_TYPE_VALUE,
)
from utils import log_event


def validate_initial_inputs(ctx) -> bool:
    visa_type = str(getattr(ctx, "visa_type", "") or "").strip().upper()
    service_key = str(
        getattr(ctx, "first_letter_visa_type", "") or ""
    ).strip().upper()
    if visa_type.startswith("Q") and len(visa_type) > 1 and visa_type[1].isdigit():
        service_key = visa_type[:2]
    elif not service_key:
        service_key = visa_type[:1]

    if service_key not in SERVICE_VISA_TYPE or not visa_type.startswith(("L", "M", "Q")):
        log_event({"step": "Visa Type", "status": visa_type + " not support"})
        return False

    if ctx.entries_type not in ENTRIES_TYPE:
        log_event({"step": "ENTRIES_TYPE check", "status": ctx.entries_type + " not support"})
        return False

    sub_value = str(getattr(ctx, "type_of_visa_sub_value", "") or "").strip().upper()
    if sub_value not in VISA_TYPE_VALUE.get(service_key, {}):
        log_event({"step": "service type", "status": sub_value + " not support"})
        return False

    return True
