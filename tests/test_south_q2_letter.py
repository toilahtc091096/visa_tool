"""Q2 invitation letter (North and South): the applicant's qthumoi_* letter wins, the
template letter becomes <name>_backup.pdf on R2; South puts the letter into 3 COVA slots.

    python -m unittest tests.test_south_q2_letter
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object, CSS=object))

import constants  # noqa: E402
from flows.flow_step import step_07_upload_files as step07  # noqa: E402
from utils import upload_file  # noqa: E402
from visa_types import documents  # noqa: E402

LETTER_CATEGORY = "12025062617423948560682"
INVITER_ID_CATEGORY = "12025062617342103276497"


class SlotsTest(unittest.TestCase):
    def test_letter_in_three_slots(self):
        codes = constants.UPLOAD_FILE_CODE_SOUTH["Q2"]["COMMON"]
        cfg = constants.UPLOAD_CONFIG_SOUTH_Q2
        self.assertNotIn("CHUNG_MINH_QUAN_HE", codes)
        self.assertNotIn("CHUNG_MINH_QUAN_HE", cfg)
        self.assertEqual(codes["THU_MOI_3"], [{"categoryCode": LETTER_CATEGORY, "materialCode": "mfa-015_3"}])
        self.assertEqual(codes["CCCD_NGUOI_MOI_THU_MOI"], [{"categoryCode": INVITER_ID_CATEGORY, "materialCode": "mfa-015_2"}])
        for key in ("THU_MOI", "CCCD_NGUOI_MOI_THU_MOI", "THU_MOI_3"):
            self.assertIn("first_of", cfg[key], key)
        # qcm_ proof stays in the inviter ID category _3
        self.assertEqual(cfg["CCCD_NGUOI_MOI_QUAN_HE"]["name"], "quan_he_qcm.pdf")


class SourceFilesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.letters = self.root / "tham-than" / "thumoi"
        self.letters.mkdir(parents=True)
        p = mock.patch.object(upload_file, "_CURRENT_DATA_FOLDER", self.root)
        p.start()
        self.addCleanup(p.stop)
        self.merged = []

        def fake_merge(files, name):
            self.merged.append(sorted(f.name for f in files))
            return self.root / "_merged" / name

        p = mock.patch.object(step07, "merge_files_to_pdf", side_effect=fake_merge)
        p.start()
        self.addCleanup(p.stop)

    def resolve(self, key, cfg=None):
        cfg = cfg or constants.UPLOAD_CONFIG_SOUTH_Q2
        return [f.name for f in step07._source_files(cfg[key], "P1")]

    def test_template_letter_when_no_qthumoi(self):
        (self.letters / "Q_Template_MN_A_B.pdf").write_bytes(b"%PDF")
        for key in ("THU_MOI", "CCCD_NGUOI_MOI_THU_MOI", "THU_MOI_3"):
            self.assertEqual(self.resolve(key), ["Q_Template_MN_A_B.pdf"], key)
        self.assertEqual(self.merged, [])

    def test_qthumoi_wins_and_is_merged(self):
        (self.letters / "Q_Template_MN_A_B_backup.pdf").write_bytes(b"%PDF")
        (self.letters / "qthumoi_2.jpg").write_bytes(b"x")
        (self.letters / "QTHUMOI_1.jpg").write_bytes(b"x")
        for key in ("THU_MOI", "CCCD_NGUOI_MOI_THU_MOI", "THU_MOI_3"):
            self.assertEqual(self.resolve(key), ["thu_moi_qthumoi.pdf"], key)
        self.assertEqual(self.merged[0], ["QTHUMOI_1.jpg", "qthumoi_2.jpg"])  # the backup is never used

    def test_north_q2_same_logic(self):
        north = constants.UPLOAD_CONFIG["Q2"]
        (self.letters / "Q_Template_A_B.pdf").write_bytes(b"%PDF")
        self.assertEqual(self.resolve("THU_MOI", north), ["Q_Template_A_B.pdf"])
        (self.letters / "Q_Template_A_B.pdf").rename(self.letters / "Q_Template_A_B_backup.pdf")
        (self.letters / "qthumoi_1.pdf").write_bytes(b"%PDF")
        self.assertEqual(self.resolve("THU_MOI", north), ["thu_moi_qthumoi.pdf"])
        self.assertEqual(self.merged, [["qthumoi_1.pdf"]])


class BackupLetterTest(unittest.TestCase):
    def run_render(self, own_files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name) / "tham-than" / "thumoi"
        folder.mkdir(parents=True)
        for name in own_files:
            (folder / name).write_bytes(b"own")

        async def fake_render(ctx, output_path, passport, template_name, **kw):
            out = folder / "Q_Template_MN_LI_NGUYEN.pdf"
            out.write_bytes(b"%PDF template")
            return str(out)

        uploads = []
        with mock.patch.object(documents.thumoi_info, "render_thumoi_docx_output_pdf", side_effect=fake_render), \
             mock.patch.object(documents, "ensure_data_folder_downloaded"), \
             mock.patch.object(documents, "api_upload_r2_object",
                               side_effect=lambda k, data, ct: uploads.append((k, data)) or {"ok": True}):
            letter = documents.Q2InvitationLetter(constants.Q2_THU_MOI_OUTPUT_PATH, "Q_Template_MN.docx")
            asyncio.run(letter.render(SimpleNamespace(input_passportNumber="C123")))
        return sorted(f.name for f in folder.iterdir()), uploads

    def test_no_qthumoi_keeps_template_letter(self):
        files, uploads = self.run_render([])
        self.assertEqual(files, ["Q_Template_MN_LI_NGUYEN.pdf"])
        self.assertEqual(uploads, [])

    def test_qthumoi_makes_template_a_backup_on_r2(self):
        files, uploads = self.run_render(["qthumoi_1.jpg"])
        self.assertEqual(files, ["Q_Template_MN_LI_NGUYEN_backup.pdf", "qthumoi_1.jpg"])
        self.assertEqual(uploads, [("C123/tham-than/thumoi/Q_Template_MN_LI_NGUYEN_backup.pdf", b"%PDF template")])


class NorthQ2ProfileTest(unittest.TestCase):
    def test_north_q2_uses_the_same_letter_step(self):
        from visa_types import family
        letters = [d for d in family.Q2Visa.documents if isinstance(d, documents.InvitationLetter)]
        self.assertEqual([type(d) for d in letters], [documents.Q2InvitationLetter])
        self.assertEqual(letters[0].template_name, "")   # North template (Q_Template.docx)


if __name__ == "__main__":
    unittest.main()
