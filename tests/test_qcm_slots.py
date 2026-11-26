"""North Q1 relationship proof (qcm): which file goes into _1.._4, by the number of files."""
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
from flows.flow_step import step_07_upload_files as step  # noqa: E402


def slots(names):
    files = [Path(n) for n in names]
    with mock.patch.object(step, "get_files", return_value=list(reversed(files))):   # any order in, by name out
        out = step._source_files({"folder": "tham-than\\quan-he", "qcm_slots": True}, "E1")
    return [f.name if f else None for f in out]


class QcmSlotsTest(unittest.TestCase):
    def test_by_file_count(self):
        self.assertEqual(slots(["qcm_1.jpg", "qcm_2.jpg", "qcm_3.jpg", "qcm_4.jpg", "qcm_5.jpg"]),
                         ["qcm_1.jpg", "qcm_2.jpg", "qcm_3.jpg", "qcm_4.jpg"])
        self.assertEqual(slots(["qcm_1.jpg", "qcm_2.jpg", "qcm_3.jpg", "qcm_4.jpg"]),
                         ["qcm_1.jpg", "qcm_2.jpg", "qcm_3.jpg", "qcm_4.jpg"])
        self.assertEqual(slots(["qcm_1.jpg", "qcm_2.jpg", "qcm_3.jpg"]),
                         [None, "qcm_1.jpg", "qcm_2.jpg", "qcm_3.jpg"])          # _1 skipped
        self.assertEqual(slots(["qcm_1.jpg", "qcm_2.jpg"]),
                         [None, "qcm_1.jpg", "qcm_2.jpg", "qcm_1.jpg"])          # one file again
        self.assertEqual(slots(["qcm_1.jpg"]), [None, "qcm_1.jpg", "qcm_1.jpg", "qcm_1.jpg"])
        self.assertEqual(slots([]), [])

    def test_north_q1_uses_it(self):
        from constants import REGION, REGION_NORTH, UPLOAD_CONFIG
        if REGION != REGION_NORTH:
            self.skipTest("North table")
        self.assertTrue(UPLOAD_CONFIG["Q1"]["CHUNG_MINH_QUAN_HE"]["qcm_slots"])


if __name__ == "__main__":
    unittest.main()
