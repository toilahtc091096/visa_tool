from constants import ENTRIES_TYPE
from .common import fail_step


async def validate_initial_inputs(ctx) -> bool:
    ctx.step = "validate"
    profile = ctx.profile
    if profile is None:
        visa_type = str(getattr(ctx, "visa_type", "") or "").strip().upper()
        return await fail_step(ctx, f"visa_type {visa_type!r} not supported")

    if ctx.entries_type not in ENTRIES_TYPE:
        return await fail_step(ctx, f"entries_type {ctx.entries_type!r} not supported")

    sub_value = str(getattr(ctx, "type_of_visa_sub_value", "") or "").strip().upper()
    if sub_value not in profile.sub_types:
        return await fail_step(
            ctx,
            f"type_of_visa_sub_value {sub_value!r} not supported for {profile.service_key}",
        )

    # M (both regions): the trip dates must come with the request.
    if profile.code == "M" and not all(
        str(getattr(ctx, key, "") or "").strip() for key in ("arrivalDate", "departureDate")
    ):
        return await fail_step(
            ctx,
            'Phải điền 2 trường "arrivalDate" và "departureDate" '
            '(ví dụ: "arrivalDate": "2026-12-07", "departureDate": "2026-12-11"), '
            "hãy tìm trong file để điền",
        )

    return True
