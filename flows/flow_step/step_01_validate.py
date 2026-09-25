from constants import (
    ENTRIES_TYPE,
    SERVICE_VISA_TYPE,
    VISA_TYPE_VALUE,
)
from .common import fail_step


async def validate_initial_inputs(ctx) -> bool:
    ctx.step = "validate"
    visa_type = str(getattr(ctx, "visa_type", "") or "").strip().upper()
    service_key = str(
        getattr(ctx, "first_letter_visa_type", "") or ""
    ).strip().upper()
    if visa_type.startswith("Q") and len(visa_type) > 1 and visa_type[1].isdigit():
        service_key = visa_type[:2]
    elif not service_key:
        service_key = visa_type[:1]

    if service_key not in SERVICE_VISA_TYPE or not visa_type.startswith(("L", "M", "Q","F")):
        return await fail_step(ctx, f"visa_type {visa_type!r} not supported")

    if ctx.entries_type not in ENTRIES_TYPE:
        return await fail_step(ctx, f"entries_type {ctx.entries_type!r} not supported")

    sub_value = str(getattr(ctx, "type_of_visa_sub_value", "") or "").strip().upper()
    if sub_value not in VISA_TYPE_VALUE.get(service_key, {}):
        return await fail_step(
            ctx, f"type_of_visa_sub_value {sub_value!r} not supported for {service_key}"
        )

    return True
