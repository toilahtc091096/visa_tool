"""Signature fitted to the invitation letter's picture frame (not flat, bigger)."""

import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from generate_file.signature_fit import DEFAULT_FRAME_RATIO, fit_signature_to_frame, frame_ratio

TEMPLATES = Path(__file__).resolve().parent.parent / "resources"


def _photo(size=(1024, 1024), box=(300, 350, 700, 650), fmt="JPEG"):
    img = Image.new("RGB", size, (250, 250, 248))           # off-white paper
    ImageDraw.Draw(img).rectangle(box, outline=(30, 40, 140), width=8)
    buf = BytesIO()
    img.save(buf, fmt)
    return buf.getvalue()


class SignatureFitTest(unittest.TestCase):
    def test_frame_ratio_from_templates(self):
        for name in ("Q_Template.docx", "Q_Template_MN.docx", "Q_Template_guarantor.docx"):
            self.assertAlmostEqual(frame_ratio(TEMPLATES / name, "Image 1"), 2.555, places=2, msg=name)
        self.assertAlmostEqual(frame_ratio(TEMPLATES / "Q_Template_guarantor.docx", "Image 2"), 2.55, places=1)
        self.assertEqual(frame_ratio(TEMPLATES / "nope.docx", "Image 1"), DEFAULT_FRAME_RATIO)

    def test_cropped_padded_to_ratio_and_transparent(self):
        out = Image.open(BytesIO(fit_signature_to_frame(_photo(), 2.5)))
        self.assertEqual(out.mode, "RGBA")
        w, h = out.size
        self.assertAlmostEqual(w / h, 2.5, places=1)               # same shape as the frame: not stretched
        self.assertLess(h, 400)                                     # white around the ink cropped away (ink 300 high)
        self.assertEqual(out.getpixel((0, 0))[3], 0)                # background transparent
        ink_box = out.getchannel("A").getbbox()
        self.assertGreater(ink_box[3] - ink_box[1], h * 0.85)       # ink fills the height

    def test_wide_signature_gets_taller_canvas(self):
        out = Image.open(BytesIO(fit_signature_to_frame(_photo(box=(50, 480, 970, 540)), 2.5)))
        self.assertAlmostEqual(out.size[0] / out.size[1], 2.5, places=1)

    def test_png_with_alpha_and_bad_input(self):
        img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        ImageDraw.Draw(img).line([(50, 200), (350, 210)], fill=(0, 0, 120, 255), width=6)
        buf = BytesIO(); img.save(buf, "PNG")
        out = Image.open(BytesIO(fit_signature_to_frame(buf.getvalue(), 2.5)))
        self.assertAlmostEqual(out.size[0] / out.size[1], 2.5, places=1)
        self.assertEqual(fit_signature_to_frame(b"not an image"), b"not an image")
        blank = BytesIO(); Image.new("RGB", (50, 50), "white").save(blank, "PNG")
        self.assertEqual(fit_signature_to_frame(blank.getvalue()), blank.getvalue())   # nothing to crop


if __name__ == "__main__":
    unittest.main()
