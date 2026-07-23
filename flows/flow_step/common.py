from types import SimpleNamespace


def normalize_visa_type(visa_type: str, visa_duration: str = "") -> tuple[str, str]:
    raw_type = str(visa_type or "").strip().upper()
    raw_duration = str(visa_duration or "").strip().upper()

    if raw_type.startswith("M"):
        if raw_type == "M":
            if raw_duration in {"15", "30", "90", "MT", "MP", "MO"}:
                return "M", raw_duration
            return "M", "90"
        return "M", raw_type[1:] or raw_duration

    if raw_type.startswith("L"):
        if raw_type[1:] in {"15", "30"}:
            return raw_type, raw_type[1:]
        if raw_duration in {"15", "30"}:
            return f"L{raw_duration}", raw_duration

    if raw_duration in {"15", "30", "90"}:
        return raw_type, raw_duration

    return raw_type, ""


def get_in(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def build_flow_context(**kwargs):
    ctx = SimpleNamespace(**kwargs)
    ctx.token = kwargs.get("token", "")
    ctx.tmp_secret = kwargs.get("tmp_secret", "")
    raw_visa_type = str(kwargs.get("visa_type", "") or "").strip().upper()
    raw_visa_duration = str(kwargs.get("visa_duration", "") or "").strip().upper()
    ctx.visa_type_raw = raw_visa_type
    ctx.visa_type, ctx.visa_duration = normalize_visa_type(
        raw_visa_type,
        raw_visa_duration,
    )
    ctx.first_letter_visa_type = ctx.visa_type[:1]
    ctx.last_letter_visa_type = ctx.visa_duration or ctx.visa_type[1:]
    ctx.first_applyid = kwargs.get("first_applyid", "")
    ctx.passportNumber = kwargs.get("passportNumber", "")
    ctx.input_passportNumber = ctx.passportNumber
    ctx.chinaResidenceLicenseFlag = kwargs.get("chinaResidenceLicenseFlag", False)
    ctx.collectFingerprintFlag = kwargs.get("collectFingerprintFlag", False)
    ctx.is_private = kwargs.get("is_private", False)
    ctx.family_passport = kwargs.get("family_passport", "")
    ctx.arrivalDate = kwargs.get("arrivalDate", "")
    ctx.departureDate = kwargs.get("departureDate", "")
    ctx.fixed_arrived = kwargs.get("fixed_arrived", "")
    ctx.fixed_departure = kwargs.get("fixed_departure", "")
    ctx.inviteCompanyName = kwargs.get("inviteCompanyName", "")
    ctx.company_address = kwargs.get("company_address", "")
    ctx.inviteProvince = kwargs.get("inviteProvince", "")
    ctx.companyNameVi = kwargs.get("companyNameVi", "")
    ctx.companyAddressUpperNoAccent = kwargs.get("companyAddressUpperNoAccent", "")
    ctx.companyPhone = kwargs.get("companyPhone", "")
    ctx.managerName = kwargs.get("managerName", "")
    ctx.company_passport = kwargs.get("company_passport", "")
    ctx.arrivalCity = kwargs.get("arrivalCity", "")
    ctx.arrivalDistrict = kwargs.get("arrivalDistrict", "")
    ctx.stayCity = kwargs.get("stayCity", "")
    ctx.stayDistrict = kwargs.get("stayDistrict", "")
    ctx.departureCity = kwargs.get("departureCity", "")
    ctx.departureDistrict = kwargs.get("departureDistrict", "")
    ctx.addition_adults = kwargs.get("addition_adults", [])
    ctx.addition_child = kwargs.get("addition_child", [])
    ctx.passengers = kwargs.get("passengers", [])
    ctx.step = ""
    ctx.ocr_data = None
    ctx.data_obj = {}
    ctx.old_item_id = ""
    ctx.job_type = ""
    ctx.experiences = []
    ctx.educationExperience = []
    ctx.old_notApplyItems = []
    ctx.old_streetAddr = ""
    ctx.old_phoneNumber = ""
    ctx.old_mobilePhoneNumber = ""
    ctx.old_parents = []
    ctx.old_children = []
    ctx.old_relatives = []
    ctx.old_haveSpouseFlag = False
    ctx.old_spouses = []
    ctx.fileId = ""
    ctx.hotel_type = 0
    ctx.flight_ticket = 0
    ctx.m = None
    ctx.f = None
    ctx.prefix_flight_text = ""
    ctx.arrive_flight_number = ""
    ctx.departure_flight_number = ""
    ctx.vietnamese_name = ""
    ctx.full_name = ""
    return ctx
