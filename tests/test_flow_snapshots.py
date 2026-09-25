"""Golden-master tests for the whole /run flow, one case per visa type.

Every outside effect is faked and recorded: HTTP calls to COVA (bodies),
rendered documents (payloads), R2 downloads/uploads/deletes, material uploads
and the DB insert. The recording of each case is compared with
tests/snapshots/flow_snapshots.json, so a refactor that changes what gets sent
anywhere shows up as a diff.

    python -m unittest tests.test_flow_snapshots                 # compare
    set SNAPSHOT_UPDATE=1 && python -m unittest tests.test_flow_snapshots   # rewrite

Snapshots contain date-dependent values (Q arrival dates, CV submit date...),
so regenerate the baseline on the same day you compare against it.
"""

from __future__ import annotations

import contextlib
import copy
import difflib
import io
import json
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import constants  # noqa: E402
import main as main_module  # noqa: E402
import utils.upload_file  # noqa: E402
import utils.download_r2  # noqa: E402
import utils.remove_r2  # noqa: E402
import utils.token_store  # noqa: E402
from api import api_upload_r2_object  # noqa: E402
from api.api_login import login  # noqa: E402
from api.upload_file_materia import api_upload_file  # noqa: E402
from flows.flow_step import save_draft_visa_registration  # noqa: E402
from generate_file import (  # noqa: E402
    cv_info,
    file_init_info,
    flight_info,
    hotel_info,
    thumoi_info,
)

SNAPSHOT_PATH = Path(__file__).resolve().parent / "snapshots" / "flow_snapshots.json"
REGISTER_DATE = "2026-09-07"
APPLY_ID = "APPLY-0001"

BASE_CASE: dict[str, Any] = {
    "authorization": "AUTH",
    "first_applyid": APPLY_ID,
    "passportNumber": "SNAP0001",
    "register_date": REGISTER_DATE,
    "province_city_code": "HA NOI",
    "id_card_number": "001090000001",
    "entries_type": "S",
    "service_type": "N",
}

CASES: dict[str, dict[str, Any]] = {
    "L15_adult": {"visa_type": "L15", "type_of_visa_sub_value": "I"},
    "L15_under18": {
        "visa_type": "L15",
        "type_of_visa_sub_value": "I",
        "_dob": "2015-05-05",
    },
    "L15_additional_names": {
        "visa_type": "L15",
        "type_of_visa_sub_value": "I",
        "addition_adults": ["TRAN VAN B"],
        "addition_child": ["TRAN THI C"],
    },
    "L15_family_reuse": {
        "visa_type": "L15",
        "type_of_visa_sub_value": "I",
        "family_passport": "FAMILY0001",
    },
    "L15_prev_china_visa": {
        "visa_type": "L15",
        "type_of_visa_sub_value": "I",
        "arrivedChinaFlag": True,
        "haveChinaVisaFlag": True,
        "old_visaType": "L",
        "old_visaNumber": "V1234567",
        "old_issueDate": "2024-01-10",
        "old_issuePlace": "HANOI",
    },
    "L30_adult": {"visa_type": "L30", "type_of_visa_sub_value": "I"},
    "M_company": {
        "visa_type": "M",
        "visa_duration": "90",
        "type_of_visa_sub_value": "T",
        "arrivalDate": "2026-10-05",
        "departureDate": "2026-10-20",
        "inviteCompanyName": "SHENZHEN TRADING CO",
        "company_address": "1 NANSHAN ROAD",
        "inviteProvince": "GUANGDONG",
        "arrivalCity": "SHENZHEN",
        "arrivalDistrict": "NANSHAN",
        "companyNameVi": "Công ty TNHH ABC (Việt Nam)",
        "companyAddressUpperNoAccent": "SO 1 PHO HUE HA NOI",
        "companyPhone": "0901234567",
        "managerName": "Nguyễn Văn Giám",
    },
    "M_company_reuse": {
        "visa_type": "M",
        "visa_duration": "90",
        "type_of_visa_sub_value": "T",
        "arrivalDate": "2026-10-05",
        "departureDate": "2026-10-20",
        "company_passport": "COMPANY0001",
    },
    "Q1_family": {
        "visa_type": "Q1",
        "type_of_visa_sub_value": "QCN",
        "inviterFamilyName": "王",
        "inviterGivenName": "伟",
        "inviterIdCard": "110101199001011234",
        "inviterPhone": "13800000000",
        "inviterAddress": "BEIJING CHAOYANG",
        "inviterRelation": "SPOUSE",
        "inviteProvince": "BEIJING",
        "arrivalCity": "BEIJING",
        "arrivalDistrict": "CHAOYANG",
    },
    "Q2_family": {
        "visa_type": "Q2",
        "type_of_visa_sub_value": "QCV",
        "apply_visa_validity": 6,
        "inviterFamilyName": "李",
        "inviterGivenName": "娜",
        "inviterRelation": "SISTER",
        "arrivalCity": "SHANGHAI",
    },
    "F_school": {
        "visa_type": "F",
        "type_of_visa_sub_value": "AE",
        "inviteSchoolName": "PEKING UNIVERSITY",
        "school_address": "5 YIHEYUAN ROAD",
        "fixed_arrived": "2026-10-05",
        "fixed_departure": "2026-10-19",
    },
    "F_school_reuse": {
        "visa_type": "F",
        "type_of_visa_sub_value": "AE",
        "school_passport": "SCHOOL0001",
    },
    "L15_update_info": {
        "visa_type": "L15",
        "type_of_visa_sub_value": "I",
        "is_update_info": True,
        "upload_config_keys": ["FLIGHT_TICKET", "HOTEL_RESERVATION_WITH_PAYMENT"],
    },
    "invalid_visa_type": {"visa_type": "X15", "type_of_visa_sub_value": "I"},
    "invalid_sub_type": {"visa_type": "M", "type_of_visa_sub_value": "ZZ"},
}


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str, ensure_ascii=False))


class Recorder:
    def __init__(self, dob: str) -> None:
        self.dob = dob
        self.events: dict[str, list[Any]] = {
            "http": [],
            "renders": [],
            "r2": [],
            "uploads": [],
            "db": [],
        }

    def add(self, kind: str, item: Any) -> None:
        self.events[kind].append(_jsonable(item))

    # ---- HTTP ---------------------------------------------------------
    def handle(self, request: httpx.Request) -> httpx.Response:
        content_type = request.headers.get("content-type", "")
        body: Any
        if content_type.startswith("application/json"):
            body = json.loads(request.content or b"null")
        elif content_type.startswith("application/x-www-form-urlencoded"):
            form = parse_qs(request.content.decode())
            body = {k: v for k, v in sorted(form.items()) if k != "_t"}
        elif content_type.startswith("multipart/"):
            body = "<multipart>"
        else:
            body = request.content.decode() or None
        self.add("http", {"method": request.method, "path": request.url.path, "body": body})

        path = request.url.path
        if path.endswith("/PassportOCR"):
            data = {
                "fileId": "FILE-1",
                "passportNumber": "SNAP0001",
                "passportFamilyName": "NGUYEN",
                "passportFirstName": "VAN AN",
                "dateOfBirth": self.dob,
                "dateOfExpiration": "2032-01-01",
                "sex": "1",
                "nationality": "VNM",
                "issuingCountry": "VNM",
            }
            return httpx.Response(200, json={"Response": {"Data": data}})
        if path.endswith("/GetDraftList"):
            return httpx.Response(200, json={"Response": {"Data": {"list": []}}})
        if path.endswith("/online/list"):
            return httpx.Response(200, json={"code": 200, "rows": [], "total": 0})
        if path.endswith("/GetPersonInfo") or path.endswith("/SavePersonInfo"):
            return httpx.Response(200, json={"Response": {"Data": {"applyid": APPLY_ID}}})
        return httpx.Response(200, json={"Response": {"Data": {}, "RequestId": "R"}})


def _patch_everywhere(original: Any, replacement: Any, patches: list) -> None:
    """Replace every module-level reference to ``original`` in project modules."""
    for module in list(sys.modules.values()):
        module_file = getattr(module, "__file__", None) or ""
        if not module_file or not str(Path(module_file).resolve()).startswith(
            str(PROJECT_ROOT)
        ):
            continue
        if "tests" in Path(module_file).parts:
            continue
        for name, value in list(vars(module).items()):
            if value is original:
                patches.append((module, name, value))
                setattr(module, name, replacement)


def run_case(name: str, overrides: dict[str, Any]) -> dict[str, Any]:
    overrides = dict(overrides)
    rec = Recorder(overrides.pop("_dob", "1990-01-01"))
    patches: list = []
    tmp_dir = Path(tempfile.mkdtemp(prefix="visa_snapshot_"))
    passport_image = tmp_dir / "passport.jpg"
    passport_image.write_bytes(b"fake")

    def fake_get_files(folder_path, limit):
        return [Path(str(folder_path)) / f"file{i}.jpg" for i in range(limit)]

    async def fake_api_upload_file(client, token, tmp_secret, body):
        rec.add(
            "uploads",
            {
                "file": Path(body.filePath).as_posix(),
                "categoryCode": body.categoryCode,
                "materialCode": body.materialCode,
                "businessId": body.businessId,
            },
        )
        return True, {"status_code": 200, "response": {"Response": {"Data": {}}}}

    def render_recorder(kind):
        async def fake(payload, output_path="", passport_number="", *args, **kwargs):
            if kind == "invitation_letter":
                payload = thumoi_info.build_thumoi_context(payload)
            rec.add(
                "renders",
                {"kind": kind, "output_path": output_path, "payload": payload},
            )
            return ""

        return fake

    def fake_save_draft(ctx):
        rec.add(
            "db",
            {
                "first_applyid": ctx.first_applyid,
                "full_name": ctx.full_name,
                "visa_type": getattr(ctx, "visa_type_raw", ""),
            },
        )
        return 1

    replacements = [
        (utils.token_store.load_login_payload, lambda: {"token": "T", "tmpSecret": "S"}),
        (utils.token_store.save_login_data, lambda *a, **k: None),
        (login, lambda *a, **k: (_ for _ in ()).throw(AssertionError("login called"))),
        (utils.upload_file.cleanup_data_folder, lambda: None),
        (utils.upload_file.ensure_data_folder_downloaded,
         lambda prefix="", extra_prefixes=None: rec.add("r2", ["data_folder", prefix])),
        (utils.upload_file.ensure_company_doanh_nghiep_downloaded,
         lambda value: rec.add("r2", ["company_folder", value])),
        (utils.upload_file.ensure_school_downloaded,
         lambda value: rec.add("r2", ["school_folder", value])),
        (utils.upload_file.get_passport_file_path, lambda folder, prefix: str(passport_image)),
        (utils.upload_file.get_files, fake_get_files),
        (utils.download_r2.download_r2_folder,
         lambda prefix, local_dir: rec.add("r2", ["download", prefix]) or 2),
        (utils.remove_r2.delete_r2_folder,
         lambda prefix: rec.add("r2", ["delete", prefix]) or 0),
        (api_upload_r2_object,
         lambda key, body, content_type: rec.add("r2", ["upload", key]) or {"ok": True}),
        (api_upload_file, fake_api_upload_file),
        (save_draft_visa_registration, fake_save_draft),
    ]
    for original, replacement in replacements:
        _patch_everywhere(original, replacement, patches)
    render_patches = [
        (hotel_info, "render_docx_template_output_pdf", "hotel"),
        (hotel_info, "render_L30_hotel", "hotel_l30"),
        (flight_info, "render_flight_ticket_output_pdf", "flight_ticket"),
        (cv_info, "render_docx_template_output_pdf", "visa_center_confirmation"),
        (thumoi_info, "render_thumoi_docx_output_pdf", "invitation_letter"),
        (file_init_info, "render_init_pdf", "itinerary"),
    ]
    for module, attr, kind in render_patches:
        patches.append((module, attr, getattr(module, attr)))
        setattr(module, attr, render_recorder(kind))

    original_client = httpx.AsyncClient
    transport = httpx.MockTransport(rec.handle)

    class FakeAsyncClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    httpx.AsyncClient = FakeAsyncClient
    saved_week_skip = dict(constants.WEEK_SKIP_BY_TYPE)
    # constants picks these with random.randint at import time; pin them.
    constants.WEEK_SKIP_BY_TYPE.update(
        {"L15": 5, "L30": 10, "M": 10, "M30": 10, "M90": 10, "F": 10}
    )
    random.seed(20260907)
    try:
        payload = {**BASE_CASE, **overrides}
        case = main_module.build_case(copy.deepcopy(payload))
        with contextlib.redirect_stdout(io.StringIO()):
            result = main_module.main(
                case,
                first_applyid=case.get("first_applyid", ""),
                is_update_info=case.get("is_update_info", False),
                upload_config_keys=case.get("upload_config_keys", []),
                apply_visa_validity=case.get("apply_visa_validity"),
            )
    finally:
        httpx.AsyncClient = original_client
        constants.WEEK_SKIP_BY_TYPE.clear()
        constants.WEEK_SKIP_BY_TYPE.update(saved_week_skip)
        for module, attr, value in reversed(patches):
            setattr(module, attr, value)

    result = dict(result or {})
    result.pop("timings", None)
    return {"result": _jsonable(result), **rec.events}


class FlowSnapshotTest(unittest.TestCase):
    maxDiff = None

    def test_flow_snapshots(self) -> None:
        actual = {name: run_case(name, case) for name, case in CASES.items()}
        if os.getenv("SNAPSHOT_UPDATE") == "1" or not SNAPSHOT_PATH.exists():
            SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            SNAPSHOT_PATH.write_text(
                json.dumps(actual, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            self.skipTest(f"snapshot written to {SNAPSHOT_PATH}")

        expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        failures = []
        for name in sorted(set(expected) | set(actual)):
            if expected.get(name) == actual.get(name):
                continue
            want = json.dumps(expected.get(name), indent=1, sort_keys=True, ensure_ascii=False)
            got = json.dumps(actual.get(name), indent=1, sort_keys=True, ensure_ascii=False)
            diff = "\n".join(
                difflib.unified_diff(
                    want.splitlines(), got.splitlines(), "expected", "actual", lineterm=""
                )
            )
            failures.append(f"=== {name}\n{diff}")
        if failures:
            self.fail("Flow output changed:\n" + "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
