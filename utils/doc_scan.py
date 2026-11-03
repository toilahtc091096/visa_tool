"""Turn a phone photo of a document into a flat "scanned" image.

Steps: fix EXIF rotation -> find the 4 paper corners and flatten the page
(perspective warp) -> remove shadows / whiten the background -> sharpen.
The result stays in color (red stamps, passport photo).

When no clear page outline is found the photo is not cropped, only cleaned.
Any error returns the original bytes, so scanning can never break a run.
The output keeps the input's file format, so the name/extension stays valid
(COVA checks the real file type).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import PurePosixPath

import cv2
import numpy as np
from PIL import Image, ImageOps

from utils.app_logging import log_event

SCAN_SUFFIX_FORMAT = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}

# Folders never scanned (matched against every folder in the path, lowercase,
# "-" treated as "_"): portrait photos and signatures.
SCAN_SKIP_FOLDER_KEYWORDS = ("anh_the", "anh_4x6", "chu_ki", "chu_ky")

SCAN_MAX_SIDE = 2000
SCAN_JPEG_QUALITY = 90
_DETECT_SIDE = 1000
_MIN_PAGE_AREA = 0.25  # page outline must cover at least 25% of the photo


def should_scan(path: str) -> bool:
    """True for an image file outside the skipped folders."""
    p = PurePosixPath(str(path).replace("\\", "/").lower())
    if p.suffix not in SCAN_SUFFIX_FORMAT:
        return False
    folders = [part.replace("-", "_") for part in p.parts[:-1]]
    return not any(key in folder for folder in folders for key in SCAN_SKIP_FOLDER_KEYWORDS)


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Top-left, top-right, bottom-right, bottom-left."""
    pts = pts.reshape(4, 2).astype("float32")
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array(
        [pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]],
        dtype="float32",
    )


def _find_page(bgr: np.ndarray) -> np.ndarray | None:
    """Corners of the page in ``bgr`` coordinates, or None."""
    h, w = bgr.shape[:2]
    ratio = min(1.0, _DETECT_SIDE / max(h, w))
    small = cv2.resize(bgr, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)
    gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    min_area = _MIN_PAGE_AREA * small.shape[0] * small.shape[1]

    edges = cv2.dilate(cv2.Canny(gray, 50, 150), np.ones((3, 3), np.uint8), iterations=2)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    for mask in (edges, otsu):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
            if cv2.contourArea(c) < min_area:
                break
            approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                return _order_corners(approx) / ratio
    return None


def _warp(bgr: np.ndarray, corners: np.ndarray) -> np.ndarray:
    tl, tr, br, bl = corners
    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    dst = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32"
    )
    matrix = cv2.getPerspectiveTransform(corners.astype("float32"), dst)
    page = cv2.warpPerspective(bgr, matrix, (width, height), flags=cv2.INTER_CUBIC)
    # Trim a thin margin so no desk edge is left around the page.
    mx, my = max(2, int(width * 0.006)), max(2, int(height * 0.006))
    return page[my : height - my, mx : width - mx]


def _enhance(bgr: np.ndarray) -> np.ndarray:
    """Color "magic" clean-up: even white background, no shadows, crisp text."""
    kernel_size = max(15, (min(bgr.shape[:2]) // 40) | 1)
    channels = []
    for ch in cv2.split(bgr):
        background = cv2.medianBlur(
            cv2.dilate(ch, np.ones((7, 7), np.uint8)), kernel_size
        )
        flat = cv2.divide(ch, background, scale=255)
        channels.append(flat)
    out = cv2.merge(channels)
    # Gentle contrast stretch, then unsharp mask.
    out = cv2.convertScaleAbs(out, alpha=1.1, beta=-15)
    blur = cv2.GaussianBlur(out, (0, 0), 1.5)
    return cv2.addWeighted(out, 1.5, blur, -0.5, 0)


def scan_image(bgr: np.ndarray) -> tuple[np.ndarray, bool]:
    """Return the scanned image and whether a page outline was found."""
    corners = _find_page(bgr)
    page = _warp(bgr, corners) if corners is not None else bgr
    page = _enhance(page)
    h, w = page.shape[:2]
    if max(h, w) > SCAN_MAX_SIDE:
        r = SCAN_MAX_SIDE / max(h, w)
        page = cv2.resize(page, (int(w * r), int(h * r)), interpolation=cv2.INTER_AREA)
    return page, corners is not None


def scan_document_bytes(path: str, content: bytes) -> bytes:
    """Scan one file; returns ``content`` unchanged when skipped or on error."""
    if not should_scan(path):
        return content
    fmt = SCAN_SUFFIX_FORMAT[PurePosixPath(path.replace("\\", "/").lower()).suffix]
    try:
        with Image.open(BytesIO(content)) as img:
            rgb = ImageOps.exif_transpose(img).convert("RGB")
        bgr = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
        scanned, cropped = scan_image(bgr)
        out = Image.fromarray(cv2.cvtColor(scanned, cv2.COLOR_BGR2RGB))
        buf = BytesIO()
        if fmt == "JPEG":
            out.save(buf, "JPEG", quality=SCAN_JPEG_QUALITY, optimize=True)
        else:
            out.save(buf, fmt)
        log_event({"step": "doc_scan", "file": path, "ok": True, "cropped": cropped})
        return buf.getvalue()
    except Exception as exc:  # never fail the download because of scanning
        log_event({"step": "doc_scan", "file": path, "ok": False, "error": repr(exc)})
        return content
