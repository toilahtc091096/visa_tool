"""S2 letter (S_MOI_NGUOI_THAN.docx): inviter sex / birth date."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.person_name import join_person_name  # noqa: E402
from visa_types.documents import _s_relative_context  # noqa: E402

# 18-digit ID: born 1990-05-17, 17th digit 3 (odd) -> male
CHINESE_ID = "110101199005171234"


def _ctx(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(**kwargs)


class S2InviterSexBirthTest(unittest.TestCase):
    def test_from_smoi_ruot(self) -> None:
        out = _s_relative_context(_ctx(inviterSex="F", inviterBirth="1988-07-08"))
        self.assertEqual((out["inviterSex"], out["inviterBirth"]), ("女", "08/07/1988"))

    def test_smoi_ruot_wins_over_chinese_id(self) -> None:
        out = _s_relative_context(
            _ctx(inviterSex="F", inviterBirth="1988-07-08", inviterIdCard=CHINESE_ID)
        )
        self.assertEqual((out["inviterSex"], out["inviterBirth"]), ("女", "08/07/1988"))

    def test_chinese_id_when_no_smoi_ruot(self) -> None:
        out = _s_relative_context(_ctx(inviterIdCard=CHINESE_ID))
        self.assertEqual((out["inviterSex"], out["inviterBirth"]), ("男", "17/05/1990"))

    def test_blank_without_either(self) -> None:
        out = _s_relative_context(_ctx(inviterIdCard="C8469505"))
        self.assertEqual((out["inviterSex"], out["inviterBirth"]), ("", ""))


class InviterNameTest(unittest.TestCase):
    def test_chinese_name_without_space(self) -> None:
        self.assertEqual(join_person_name("余", "永飞"), "余永飞")

    def test_latin_name_with_space(self) -> None:
        self.assertEqual(join_person_name("NGUYEN", "THI NGA"), "NGUYEN THI NGA")

    def test_missing_part(self) -> None:
        self.assertEqual(join_person_name("NGUYEN", ""), "NGUYEN")
        self.assertEqual(join_person_name(None, None), "")


if __name__ == "__main__":
    unittest.main()
