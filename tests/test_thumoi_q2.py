"""Which Q2 box the invitation letter ticks.

    python -m unittest tests.test_thumoi_q2
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generate_file.thumoi_info import CHECKED, build_thumoi_context  # noqa: E402

BOXES = ("q2Once", "q2Twice", "q2HalfYear", "q2OneYear")


def ticked(**source) -> list[str]:
    context = build_thumoi_context({"visa_type": "Q2", **source})
    return [box for box in BOXES if context[box] == CHECKED]


class Q2BoxTest(unittest.TestCase):
    def test_entries_pick_the_box(self) -> None:
        cases = [
            # (entries_type, apply_visa_validity, expected box)
            ("S", 6, "q2Once"),
            ("S", 12, "q2Once"),
            ("S", None, "q2Once"),
            ("D", 6, "q2Twice"),
            ("D", 12, "q2Twice"),
            ("M", 6, "q2HalfYear"),
            ("M", None, "q2HalfYear"),
            ("M", 12, "q2OneYear"),
        ]
        for entries, validity, expected in cases:
            with self.subTest(entries=entries, validity=validity):
                self.assertEqual(
                    ticked(entries_type=entries, apply_visa_validity=validity),
                    [expected],
                )

    def test_explicit_box_in_request_wins(self) -> None:
        self.assertEqual(
            ticked(entries_type="S", apply_visa_validity=6, q2HalfYear="1"),
            ["q2HalfYear"],
        )

    def test_not_q2(self) -> None:
        context = build_thumoi_context({"visa_type": "Q1", "entries_type": "S"})
        self.assertEqual([b for b in BOXES if context[b] == CHECKED], [])
        self.assertEqual(context["q1"], CHECKED)


if __name__ == "__main__":
    unittest.main()
