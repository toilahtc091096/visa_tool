"""S2 letter (S_MOI_NGUOI_THAN.docx): inviter sex / birth date."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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


if __name__ == "__main__":
    unittest.main()
