"""SavePreviousTravelInfo body with a Chinese residence permit (both regions)."""

from __future__ import annotations

import sys
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import (  # noqa: E402
    CHINA_RESIDENCE_PERMIT_VISA_TYPE,
    REGION_NORTH,
    REGION_SOUTH,
)
import flows.flow_payloads as fp  # noqa: E402

PERMIT = {
    "chinaResidenceLicenseFlag": True,
    "residenceLicenseNumber": "102856209",
    "residence_issueDate": "2023-11-22",
    "residence_issuePlace": "fujian",
}


def _body(region: str, **kwargs) -> dict:
    with mock.patch.object(fp, "REGION", region):
        return asdict(fp.build_previous_travel_info_profile("APPLY-1", **kwargs))


class ResidencePermitBodyTest(unittest.TestCase):
    def test_permit_only_matches_cova_form(self) -> None:
        for region in (REGION_NORTH, REGION_SOUTH):
            with self.subTest(region=region):
                self._check_permit_only(_body(region, **PERMIT))

    def _check_permit_only(self, body: dict) -> None:
        expected = {
            "arrivedChinaFlag": False,
            "chinaResidenceLicenseFlag": True,
            "haveChinaVisaFlag": True,
            "firstApplyChinaVisaFlag": False,
            "visaType": CHINA_RESIDENCE_PERMIT_VISA_TYPE,
            "visaNumber": "102856209",
            "residenceLicenseNumber": "102856209",
            "issueDate": "2023-11-22",
            "issuePlace": "FUJIAN",
            "previousTravelInChinaInfos": [],
            "lostChinaVisaFlag": "",
            "provideChinaVisaDetailFlag": "",
        }
        self.assertEqual({k: body[k] for k in expected}, expected)

    def test_permit_with_old_visa_keeps_visa_and_adds_number(self) -> None:
        for region in (REGION_NORTH, REGION_SOUTH):
            with self.subTest(region=region):
                self._check_with_old_visa(region)

    def _check_with_old_visa(self, region: str) -> None:
        body = _body(
            region,
            arrivedChinaFlag=True,
            haveChinaVisaFlag=True,
            old_visaType="L",
            old_visaNumber="AH669238",
            old_issueDate="2026-03-09",
            old_issuePlace="TP HO CHI MINH",
            **PERMIT,
        )
        self.assertTrue(body["arrivedChinaFlag"])
        self.assertTrue(body["chinaResidenceLicenseFlag"])
        self.assertEqual(body["residenceLicenseNumber"], "102856209")
        self.assertEqual(body["visaType"], "L")
        self.assertEqual(body["visaNumber"], "AH669238")
        self.assertEqual(body["issueDate"], "2026-03-09")
        self.assertEqual(body["issuePlace"], "TP HO CHI MINH")

    def test_no_permit_keeps_no_travel_body(self) -> None:
        body = _body(REGION_NORTH)
        self.assertFalse(body["chinaResidenceLicenseFlag"])
        self.assertFalse(body["haveChinaVisaFlag"])
        self.assertEqual(body["residenceLicenseNumber"], "")
        self.assertEqual(body["visaType"], "")

    def test_permit_type_passes_validation(self) -> None:
        errors = fp.validate_payload(
            {
                "arrivedChinaFlag": False,
                "haveChinaVisaFlag": True,
                "chinaResidenceLicenseFlag": True,
                "visaType": CHINA_RESIDENCE_PERMIT_VISA_TYPE,
            }
        )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
