from types import SimpleNamespace


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
    ctx.first_letter_visa_type = kwargs.get("visa_type", "")[:1]
    ctx.last_letter_visa_type = kwargs.get("visa_type", "")[1:]
    ctx.first_applyid = kwargs.get("first_applyid", "")
    ctx.passportNumber = kwargs.get("passportNumber", "")
    ctx.chinaResidenceLicenseFlag = kwargs.get("chinaResidenceLicenseFlag", False)
    ctx.collectFingerprintFlag = kwargs.get("collectFingerprintFlag", False)
    ctx.is_private = kwargs.get("is_private", False)
    ctx.addition_adults = kwargs.get("addition_adults", [])
    ctx.addition_child = kwargs.get("addition_child", [])
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
