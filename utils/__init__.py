from importlib import import_module
from typing import Any

_EXPORTS = {
    "debug_asdict": ("debug", "debug_asdict"),
    "build_get_draft_headers": ("headers", "build_get_draft_headers"),
    "build_login_headers": ("headers", "build_login_headers"),
    "build_upload_headers": ("headers", "build_upload_headers"),
    "log_event": ("app_logging", "log_event"),
    "notify": ("app_logging", "notify"),
    "log_exception": ("app_logging", "log_exception"),
    "vnd": ("money_format", "vnd"),
    "cny": ("money_format", "cny"),
    "vnd_decimal": ("money_format", "vnd_decimal"),
    "get_files": ("upload_file", "get_files"),
    "api_upload_file_common": ("upload_file", "api_upload_file_common"),
    "get_passport_file_path": ("upload_file", "get_passport_file_path"),
    "ensure_data_folder_downloaded": ("upload_file", "ensure_data_folder_downloaded"),
    "cleanup_data_folder": ("upload_file", "cleanup_data_folder"),
    "generate_phone_pair": ("mobile_utils", "generate_phone_pair"),
    "format_date": ("date_util", "format_date"),
    "get_today_parts": ("date_util", "get_today_parts"),
    "build_three_stays": ("date_util", "build_three_stays"),
    "get_end_date": ("date_util", "get_end_date"),
    "load_token": ("token_store", "load_token"),
    "save_token": ("token_store", "save_token"),
    "load_login_payload": ("token_store", "load_login_payload"),
    "load_authorization": ("token_store", "load_authorization"),
    "append_authorization": ("token_store", "append_authorization"),
    "save_login_data": ("token_store", "save_login_data"),
    "convert_html_to_pdf": ("pdf_helper", "convert_html_to_pdf"),
    "remove_last_blank_page": ("pdf_helper", "remove_last_blank_page"),
    "upload_pdf_to_r2": ("upload_r2", "upload_pdf_to_r2"),
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
