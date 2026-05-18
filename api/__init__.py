from .apply import api_save_apply_info
from .draft import api_get_draft
from .passport import api_passport_ocr
from .person import api_save_person_info
from .education import api_save_education_info
from .family import api_save_family_info
from .previous_travel import api_save_previous_travel_info
from .travel import api_save_travel_info
from .work import api_save_work_info

__all__ = [
    "api_get_draft",
    "api_passport_ocr",
    "api_save_apply_info",
    "api_save_education_info",
    "api_save_family_info",
    "api_save_person_info",
    "api_save_previous_travel_info",
    "api_save_travel_info",
    "api_save_work_info",
]
