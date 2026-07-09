from constants import (
    ENTRIES_TYPE,
    MY_VISA_TYPE,
    SERVICE_VISA_TYPE,
    VISA_TYPE_DAY_VALUE,
    VISA_TYPE_VALUE,
)
from utils import log_event


def validate_initial_inputs(ctx) -> bool:
    visa_type = str(getattr(ctx, "visa_type", "") or "").strip().upper()
    visa_duration = str(getattr(ctx, "visa_duration", "") or "").strip().upper()
    first_letter = str(getattr(ctx, "first_letter_visa_type", "") or "").strip().upper()
    last_letter = str(getattr(ctx, "last_letter_visa_type", "") or "").strip().upper()

    if visa_type not in MY_VISA_TYPE or first_letter not in SERVICE_VISA_TYPE:
        log_event({"step": "Visa Type", "status": visa_type + " not support"})
        return False

    if first_letter == "M":
        if visa_duration not in VISA_TYPE_DAY_VALUE["M"]:
            log_event({"step": "Visa Type", "status": visa_type + " not support"})
            return False
    elif last_letter not in VISA_TYPE_DAY_VALUE[first_letter]:
        log_event({"step": "Visa Type", "status": ctx.visa_type + " not support"})
        return False

    if ctx.entries_type not in ENTRIES_TYPE:
        log_event({"step": "ENTRIES_TYPE check", "status": ctx.entries_type + " not support"})
        return False

    if ctx.type_of_visa_sub_value not in VISA_TYPE_VALUE.get(ctx.first_letter_visa_type, {}):
        log_event({"step": "service type", "status": ctx.type_of_visa_sub_value + " not support"})
        return False

    return True
