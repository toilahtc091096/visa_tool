from database.crud.visa_registration import create_visa_registration
from database.models.visa_registration import VisaRegistration
from utils import log_event


def save_draft_visa_registration(ctx) -> int | None:
    first_applyid = (getattr(ctx, "first_applyid", "") or "").strip()
    full_name = (getattr(ctx, "full_name", "") or "").strip()
    if not full_name and getattr(ctx, "ocr_data", None):
        ocr = ctx.ocr_data.Response.Data
        full_name = " ".join(
            part
            for part in [
                getattr(ocr, "passportFirstName", "") or "",
                getattr(ocr, "passportFamilyName", "") or "",
            ]
            if part.strip()
        ).strip()

    passport_number = ""
    if getattr(ctx, "ocr_data", None):
        passport_number = (
            getattr(ctx.ocr_data.Response.Data, "passportNumber", "") or ""
        ).strip()

    visa_type = (getattr(ctx, "visa_type", "") or "").strip()

    if not first_applyid or not full_name or not passport_number or not visa_type:
        log_event(
            {
                "step": "save_visa_registration_to_db",
                "ok": False,
                "error": "missing required fields",
                "first_applyid": first_applyid,
                "full_name": full_name,
                "passport_number": passport_number,
                "visa_type": visa_type,
            }
        )
        return None

    record_id = create_visa_registration(
        VisaRegistration(
            first_applyid=first_applyid,
            full_name=full_name,
            passport_number=passport_number,
            visa_type=visa_type,
            status="draft",
        )
    )
    log_event(
        {
            "step": "save_visa_registration_to_db",
            "ok": True,
            "record_id": record_id,
            "first_applyid": first_applyid,
            "full_name": full_name,
            "passport_number": passport_number,
            "visa_type": visa_type,
        }
    )
    return record_id
