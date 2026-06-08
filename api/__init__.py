from importlib import import_module
from typing import Any

_EXPORTS = {
    "api_passport_ocr": ("passport", "api_passport_ocr"),
    "api_get_draft": ("draft", "api_get_draft"),
    "api_save_apply_info": ("apply", "api_save_apply_info"),
    "api_save_education_info": ("education", "api_save_education_info"),
    "api_save_family_info": ("family", "api_save_family_info"),
    "api_save_person_info": ("person", "api_save_person_info"),
    "api_save_previous_travel_info": ("previous_travel", "api_save_previous_travel_info"),
    "api_save_travel_info": ("travel", "api_save_travel_info"),
    "api_save_work_info": ("work", "api_save_work_info"),
    "api_upload_file": ("upload_file_materia", "api_upload_file"),
    "api_remove_upload_file": ("remove_upload_file", "api_remove_upload_file"),
    "api_save_other_info": ("other_info", "api_save_other_info"),
    "api_save_signature_info": ("signature", "api_save_signature_info"),
    "api_list_online_applications": ("get_list_old_by_visa_number", "api_list_online_applications"),
    "api_get_online_application_list_by_passport": ("get_list_old_by_visa_number", "api_get_online_application_list_by_passport"),
    "api_get_work_info": ("get_work_by_app_id", "api_get_work_info"),
    "api_get_education_info": ("api_get_education_info_by_app_id", "api_get_education_info"),
    "api_get_family_info": ("api_get_family_info", "api_get_family_info"),
    "api_convert_input_pdfs": ("convert_input_pdfs", "api_convert_input_pdfs"),
    "api_download_r2_object": ("r2_download", "api_download_r2_object"),
    "api_download_r2_object_bytes": ("r2_download", "api_download_r2_object_bytes"),
    "api_upload_r2_object": ("r2_upload", "api_upload_r2_object"),
    "login": ("api_login", "login"),
    "needs_relogin": ("api_login", "needs_relogin"),
    "api_get_person_info": ("get_person_info", "api_get_person_info"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    module = import_module(f".{module_name}", __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


__all__ = list(_EXPORTS)
