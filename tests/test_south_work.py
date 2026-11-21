"""South work info: an employer in the request fills the whole work experience (every visa type)."""

import unittest
from datetime import date
from types import SimpleNamespace
from unittest import mock

from constants import JOB_TYPE_BY_LABEL, REGION_SOUTH
from visa_types import base
from visa_types.business import BusinessVisa
from visa_types.family import Q2Visa
from visa_types.tourism import L30Visa

CURL_WORK = {   # same shape as a real L30 South curl; every value is made up
    "work_from": "2025-10-06", "work_to": "2027-10-05",
    "employer_name": "CONG TY TNHH THUC PHAM MAU VIET NAM - CHI NHANH A.",
    "employer_address": "NHA XUONG B1, KCN MAU, XA MAU, TINH MAU.",
    "employer_phone": "0280000000", "supervisor_name": "NGUYEN VAN MAU.", "supervisor_mobile": "0900000000",
    "position": "CHUYEN GIA", "duty": "CHUYEN GIA",
}


def _ctx(**work):
    return SimpleNamespace(first_applyid="A1", register_date=date(2026, 11, 21), ct08_province_city_code="TINH MAU",
                           province_city_code="TINH MAU", job_type="", experiences=[], is_under_18=False,
                           is_retired=False, old_item_id="", old_work_not_apply_items=[], **work)


def _work(profile, ctx):
    with mock.patch.object(base, "REGION", REGION_SOUTH):
        body = profile.build_work_info(ctx)
    return body if isinstance(body, dict) else body.__dict__


class NotAfterCurrentMonthTest(unittest.TestCase):
    def test_dates(self):
        from utils.date_util import not_after_current_month as f
        today = date(2026, 11, 21)
        for value, want in [("2027-10-05", "2026-11"), ("2026-12-01", "2026-11"), ("2026-11-30", "2026-11-30"),
                            ("2025-10-06", "2025-10-06"), ("2027-01", "2026-11"), ("2026-11", "2026-11"),
                            ("05/10/2027", "2026-11"), ("10/2027", "2026-11"), ("06/10/2025", "06/10/2025"),
                            ("", ""), ("HIEN TAI", "HIEN TAI")]:
            self.assertEqual(f(value, today), want, value)


class SouthWorkTest(unittest.TestCase):
    def test_l30_with_employer_fills_everything(self):
        w = _work(L30Visa(), _ctx(**CURL_WORK))
        self.assertEqual(w["notApplyItems"], [])
        self.assertEqual(w["jobType"], JOB_TYPE_BY_LABEL["Company employee"])   # always 713004
        (exp,) = [e if isinstance(e, dict) else e.__dict__ for e in w["workExperience"]]
        # end 2027-10-05 is after this month -> current year-month; the past begin date is kept
        self.assertEqual((exp["beginDate"], exp["endDate"]), ("2025-10-06", date.today().strftime("%Y-%m")))
        self.assertIn("THUC PHAM MAU", exp["jobName"])
        self.assertIn("KCN MAU", exp["jobAddr"])
        self.assertEqual((exp["jobTel"], exp["supervisorTel"]), ("0280000000", "0900000000"))
        self.assertEqual((exp["jobPosition"], exp["jobDuty"]), ("CHUYEN GIA", "CHUYEN GIA"))
        self.assertIn("NGUYEN VAN MAU", exp["supervisorName"])

    def test_other_types_too(self):
        for profile in (Q2Visa(), BusinessVisa()):
            w = _work(profile, _ctx(**CURL_WORK))
            self.assertEqual(w["notApplyItems"], [], type(profile).__name__)
            self.assertEqual(len(w["workExperience"]), 1, type(profile).__name__)

    def test_without_employer_position_stays_a_remark(self):
        w = _work(L30Visa(), _ctx(position="CONG NHAN"))
        self.assertEqual(w["workExperience"], [])
        notes = [n if isinstance(n, dict) else n.__dict__ for n in w["notApplyItems"]]
        self.assertEqual(notes[0]["remark"], "CONG NHAN")


if __name__ == "__main__":
    unittest.main()
