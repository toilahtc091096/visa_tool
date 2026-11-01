"""Keep an image's file extension in line with its real format.

COVA checks the file content (error FileRealTypeInvalid / 文件真实格式非法),
so a JPEG named ``.png`` is rejected. These helpers fix the name (and convert
uncommon image formats to JPEG) before a file is stored or sent.
"""

from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

_JPEG_FORMATS = {"JPEG", "MPO"}  # MPO: multi-picture JPEG from phone cameras
_JPEG_SUFFIXES = {".jpg", ".jpeg"}


def real_image_format(content: bytes) -> str:
    """Return "JPEG", "PNG", "WEBP"... read from the content, "" if not an image."""
    try:
        with Image.open(BytesIO(content)) as img:
            fmt = (img.format or "").upper()
    except (UnidentifiedImageError, OSError):
        return ""
    return "JPEG" if fmt in _JPEG_FORMATS else fmt


def fix_image_name(file_name: str, content: bytes) -> str:
    """Rename ``file_name`` so a JPEG ends in .jpg and a PNG in .png."""
    # Plain string ops: file_name may be an R2 key ("folder/x.png") and must
    # keep its "/" separators on Windows.
    base, suffix = os.path.splitext(file_name)
    suffix = suffix.lower()
    fmt = real_image_format(content)
    if fmt == "JPEG" and suffix not in _JPEG_SUFFIXES:
        return f"{base}.jpg"
    if fmt == "PNG" and suffix != ".png":
        return f"{base}.png"
    return file_name


def prepare_upload_file(file_path: str, file_name: str) -> tuple[str, bytes]:
    """Return ``(file_name, content)`` ready to send to COVA.

    JPEG/PNG keep their bytes and get the matching extension; other image
    formats (webp, bmp...) are converted to JPEG; non-images (pdf...) are
    returned unchanged.
    """
    with open(file_path, "rb") as f:
        content = f.read()
    fmt = real_image_format(content)
    if fmt in ("", "JPEG", "PNG"):
        return fix_image_name(file_name, content), content
    with Image.open(BytesIO(content)) as img:
        out = BytesIO()
        img.convert("RGB").save(out, format="JPEG", quality=92)
    return f"{Path(file_name).stem}.jpg", out.getvalue()
