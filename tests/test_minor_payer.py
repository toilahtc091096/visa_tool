"""Q1 / Q2 / S2 under 18: 6.4A "who pays" = other (the parent from WF-04E), both regions."""
import sys
import types
import unittest
from datetime import date
from unittest import mock

sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
import flows.flow_payloads as fp  # noqa: E402
from constants import TRAVEL_PAY_FOR_OTHER, TRAVEL_PAY_FOR_SELF  # noqa: E402
from visa_types.base import get_visa_profile  # noqa: E402


def travel(visa, *, under_18, pay_name="TRAN THI MAI", pay_mobile="0912345678"):
    profile = get_visa_profile(visa)
    return fp.build_travel_info_profile(
        profile, "A1", pay_name, pay_mobile, under_18, False, "", "", "TRAN", "THI MAI",
        date(2027, 1, 4), date(2027, 1, 8), 0, False, "", "", False,
        apply_visa_validity=12, inviterFamilyName="王", inviterGivenName="小明", inviterIdCard="110101199001011234",
        inviterRelation="CHA DUONG", inviterAddress="北京市东城区示例路1号", inviterPhone="0900000000",
        inviterProvincePinyin="BeiJing", inviterCityPinyin="Beijing", inviterDistrictPinyin="Dongcheng Qu",
        visa_duration="180",
    )


class MinorPayerTest(unittest.TestCase):
    def test_family_visas(self):
        for region in ("north", "south"):
            with mock.patch.object(fp, "REGION", region):
                for visa in ("Q2", "Q1", "S2"):
                    with self.subTest(region=region, visa=visa):
                        t = travel(visa, under_18=True)
                        self.assertEqual((t.payForTravel, t.payForTravelName, t.payForTravelPhoneNumber),
                                         (TRAVEL_PAY_FOR_OTHER, "TRAN THI MAI", "0912345678"))
                        adult = travel(visa, under_18=False)               # adults: unchanged, self
                        self.assertEqual((adult.payForTravel, adult.payForTravelName), (TRAVEL_PAY_FOR_SELF, ""))
                        no_name = travel(visa, under_18=True, pay_name="")  # payer not read: self
                        self.assertEqual(no_name.payForTravel, TRAVEL_PAY_FOR_SELF)


if __name__ == "__main__":
    unittest.main()
