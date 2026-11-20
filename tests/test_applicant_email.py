"""Applicant phone/email from the /run body (n8n reads them from the INFO file)."""

import unittest

from flows.flow_step.common import build_flow_context, normalize_email
from tests.test_flow_snapshots import BASE_CASE, run_case


def _family_info_bodies(events):
    return [e["body"] for e in events["http"] if str(e["path"]).endswith("/SaveFamilyInfo")]


class NormalizeEmailTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(normalize_email("  Nguyen.Van_A+1@Gmail.COM "), "nguyen.van_a+1@gmail.com")
        self.assertEqual(normalize_email("abc @ yahoo.com.vn"), "abc@yahoo.com.vn")

    def test_invalid_is_empty(self):
        for bad in ["", None, "abc", "abc@", "abc@gmail", "a@b.c", "khong co", "x@@y.com"]:
            self.assertEqual(normalize_email(bad), "", bad)

    def test_context(self):
        self.assertEqual(build_flow_context(email=" A@B.COM ").email, "a@b.com")
        self.assertEqual(build_flow_context().email, "")


class RunFlowEmailTest(unittest.TestCase):
    """Whole /run flow with every outside call faked (same harness as the snapshot test)."""

    def test_email_and_phone_from_body_go_to_save_family_info(self):
        events = run_case("L30_email", {"visa_type": "L30", "type_of_visa_sub_value": "I",
                                        "phone": "0912345678", "email": "Khach.Hang@Gmail.com"})
        bodies = _family_info_bodies(events)
        self.assertTrue(bodies, "SaveFamilyInfo not called")
        body = bodies[-1]
        self.assertEqual(body["email"], "khach.hang@gmail.com")
        self.assertEqual(body["mobilePhoneNumber"], "0912345678")

    def test_without_email_it_is_generated_as_before(self):
        events = run_case("L30_no_email", {"visa_type": "L30", "type_of_visa_sub_value": "I"})
        body = _family_info_bodies(events)[-1]
        self.assertRegex(body["email"], r"^nguyenvanan_\d{3}@gmail\.com$")
        events = run_case("L30_bad_email", {"visa_type": "L30", "type_of_visa_sub_value": "I", "email": "khong co"})
        self.assertRegex(_family_info_bodies(events)[-1]["email"], r"@gmail\.com$")


if __name__ == "__main__":
    unittest.main()
