"""F / X work info: the applicant's own school (name_of_institute), never the inviting school."""

import unittest
from datetime import date
from types import SimpleNamespace

from constants import JOB_TYPE_BY_LABEL
from visa_types.study import build_study_work_info_profile

# made-up values
INVITING = {"inviteSchoolName": "TRUONG MOI BEN TRUNG QUOC", "school_address": "SO 1 DUONG MAU BAC KINH"}


def _ctx(dob="1990-01-01", **extra):
    ocr = SimpleNamespace(Response=SimpleNamespace(Data=SimpleNamespace(dateOfBirth=dob)))
    base = dict(first_applyid="A1", register_date=date(2026, 11, 23), ct08_province_city_code="XA MAU, TINH MAU",
                province_city_code="TINH MAU", job_type="", experiences=[], is_retired=False,
                old_work_not_apply_items=[], ocr_data=ocr)
    base.update(extra)
    return SimpleNamespace(**base)


def _d(x):
    return x if isinstance(x, dict) else x.__dict__


class StudyWorkTest(unittest.TestCase):
    def test_academic_at_own_school_not_the_inviting_one(self):
        w = _d(build_study_work_info_profile(_ctx(name_of_institute="Đại học Mẫu", **INVITING)))
        self.assertEqual(w["jobType"], JOB_TYPE_BY_LABEL["Academic"])
        exp = _d(w["workExperience"][0])
        self.assertEqual(exp["jobName"], "DAI HOC MAU")
        self.assertEqual(exp["jobAddr"], "")      # no address of the applicant's school yet: empty, not the residence
        for field in ("jobName", "jobAddr"):
            self.assertNotIn("TRUNG QUOC", exp[field])
            self.assertNotIn("BAC KINH", exp[field])

    def test_inviting_school_alone_is_not_a_job(self):
        w = _d(build_study_work_info_profile(_ctx(**INVITING)))
        self.assertEqual(w["jobType"], JOB_TYPE_BY_LABEL["Student"])
        self.assertEqual(w["workExperience"], [])

    def test_request_work_fields_and_no_future_date(self):
        w = _d(build_study_work_info_profile(_ctx(
            name_of_institute="DAI HOC MAU", employer_address="SO 2 DUONG MAU", work_from="2024-09-01",
            work_to="2099-06-30", **INVITING)))
        exp = _d(w["workExperience"][0])
        self.assertEqual(exp["jobAddr"], "SO 2 DUONG MAU")
        self.assertEqual((exp["beginDate"], exp["endDate"]), ("2024-09-01", date.today().strftime("%Y-%m")))

    def test_under_25_student(self):
        w = _d(build_study_work_info_profile(_ctx(dob="2010-01-01", name_of_institute="DAI HOC MAU")))
        self.assertEqual(w["jobType"], JOB_TYPE_BY_LABEL["Student"])


if __name__ == "__main__":
    unittest.main()
