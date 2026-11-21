"""Fit a signature photo to the picture frame of a .docx template.

docxtpl's replace_pic keeps the template picture's frame size and stretches the
new image into it: a square signature photo in the 4.92 x 1.93 cm frame of
Q_Template*.docx came out flat (2.5x squashed) and small (much white around).

fit_signature_to_frame(): crop to the ink, make the white background
transparent, pad (centered) to the frame's width/height ratio. The frame stays
the same; the signature keeps its shape and fills it.
"""

from __future__ import annotations

import re
import zipfile
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

DEFAULT_FRAME_RATIO = 4.92125 / 1.9261666  # Q_Template*.docx "Image 1" (width / height)
_WHITE = 225          # a pixel brighter than this on every channel is background
_MARGIN = 0.04        # blank kept around the ink, share of the ink box size


def frame_ratio(docx_path: str | Path, picture_name: str) -> float:
    """width / height of the picture named ``picture_name`` (docPr name) in the template."""
    try:
        with zipfile.ZipFile(docx_path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
    except (OSError, KeyError, zipfile.BadZipFile):
        return DEFAULT_FRAME_RATIO
    for m in re.finditer(r"<wp:(inline|anchor)\b.*?</wp:\1>", xml, re.S):
        block = m.group(0)
        if re.search(r'<wp:docPr [^>]*name="%s"' % re.escape(picture_name), block):
            ext = re.search(r'<wp:extent cx="(\d+)" cy="(\d+)"', block)
            if ext and int(ext.group(2)) > 0:
                return int(ext.group(1)) / int(ext.group(2))
    return DEFAULT_FRAME_RATIO


def fit_signature_to_frame(image_bytes: bytes, ratio: float = DEFAULT_FRAME_RATIO) -> bytes:
    """PNG bytes: the signature cropped to its ink, transparent background,
    padded to ``ratio`` (width / height). The original bytes when it cannot be read."""
    try:
        img = ImageOps.exif_transpose(Image.open(BytesIO(image_bytes))).convert("RGBA")
    except Exception:
        return image_bytes
    # background -> transparent (white paper of a photo or scan, or already transparent)
    arr = np.array(img)
    background = (arr[..., 3] < 20) | np.all(arr[..., :3] > _WHITE, axis=-1)
    arr[background] = (255, 255, 255, 0)
    img = Image.fromarray(arr, "RGBA")
    w, h = img.size
    box = img.getchannel("A").getbbox()
    if not box:
        return image_bytes   # nothing but background: leave it as it is
    left, top, right, bottom = box
    mx, my = int((right - left) * _MARGIN) + 2, int((bottom - top) * _MARGIN) + 2
    ink = img.crop((max(0, left - mx), max(0, top - my), min(w, right + mx), min(h, bottom + my)))

    iw, ih = ink.size
    if iw / ih < ratio:      # too tall for the frame: widen
        cw, ch = round(ih * ratio), ih
    else:                    # too wide: heighten
        cw, ch = iw, round(iw / ratio)
    canvas = Image.new("RGBA", (cw, ch), (255, 255, 255, 0))
    canvas.paste(ink, ((cw - iw) // 2, (ch - ih) // 2), ink)
    out = BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue()
