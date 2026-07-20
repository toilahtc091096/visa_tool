from constants import (
    ENTRIES_TYPE,
    SERVICE_VISA_TYPE,
    VISA_TYPE_VALUE,
)
from utils import log_event


def validate_initial_inputs(ctx) -> bool:
    visa_type = str(getattr(ctx, "visa_type", "") or "").strip().upper()
    first_letter = str(getattr(ctx, "first_letter_visa_type", "") or "").strip().upper()

    if first_letter not in SERVICE_VISA_TYPE or not visa_type.startswith(("L", "M")):
        log_event({"step": "Visa Type", "status": visa_type + " not support"})
        return False

    if ctx.entries_type not in ENTRIES_TYPE:
        log_event({"step": "ENTRIES_TYPE check", "status": ctx.entries_type + " not support"})
        return False

    if ctx.type_of_visa_sub_value not in VISA_TYPE_VALUE.get(ctx.first_letter_visa_type, {}):
        log_event({"step": "service type", "status": ctx.type_of_visa_sub_value + " not support"})
        return False

    return True
