"""Consistency checks for every registered visa profile.

    python -m unittest tests.test_visa_profiles
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import (  # noqa: E402
    APPLY_VISA_VALIDITY,
    SERVICE_VISA_TYPE,
    UPLOAD_CONFIG,
    UPLOAD_FILE_CODE_BY_VISA_TYPE,
)
from visa_types import (  # noqa: E402
    get_visa_profile,
    normalize_visa_type,
    registered_visa_types,
)


class VisaProfileTest(unittest.TestCase):
    def test_expected_types_are_registered(self) -> None:
        self.assertEqual(registered_visa_types(), ["F", "L15", "L30", "M", "Q1", "Q2"])

    def test_requested_types_resolve_to_a_profile(self) -> None:
        for raw_type, raw_duration in [
            ("L15", ""), ("l30", ""), ("L", "15"), ("M", ""), ("M90", ""),
            ("Q1", ""), ("Q2", ""), ("F", ""),
        ]:
            code, _ = normalize_visa_type(raw_type, raw_duration)
            with self.subTest(raw_type=raw_type, raw_duration=raw_duration):
                self.assertIsNotNone(get_visa_profile(code))
        self.assertIsNone(get_visa_profile(normalize_visa_type("L")[0]))

    def test_codes_exist_for_each_profile(self) -> None:
        for code in registered_visa_types():
            profile = get_visa_profile(code)
            with self.subTest(code=code):
                self.assertIn(profile.service_key, SERVICE_VISA_TYPE)
                self.assertIn(profile.service_key, APPLY_VISA_VALIDITY)
                self.assertTrue(profile.sub_types)
                self.assertIsNotNone(profile.week_skip)

    def test_every_upload_folder_has_a_cova_slot(self) -> None:
        """A folder without material codes is silently never uploaded."""
        for code in registered_visa_types():
            codes: dict = {}
            for group in UPLOAD_FILE_CODE_BY_VISA_TYPE[code].values():
                codes.update(group)
            with self.subTest(code=code):
                self.assertEqual(
                    sorted(set(UPLOAD_CONFIG[code]) - set(codes)),
                    [],
                    "UPLOAD_CONFIG entries without UPLOAD_FILE_CODE_BY_VISA_TYPE codes",
                )

    def test_reuse_rules_point_to_generated_folders(self) -> None:
        for code in registered_visa_types():
            profile = get_visa_profile(code)
            if profile.reuse is None:
                continue
            outputs = {doc.output_folder.replace("\\", "/") for doc in profile.documents}
            with self.subTest(code=code):
                self.assertTrue(set(profile.reuse.folders) & outputs)


if __name__ == "__main__":
    unittest.main()
