"""Turn a phone photo of a document into a flat "scanned" image.

Steps: fix EXIF rotation -> find the whole document (all pages) and flatten
it (perspective warp, background cut away) -> mild contrast + sharpen.
Colors are kept as in the photo.

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
_WHITE_BORDER_L = 235  # OpenCV Lab lightness (0..255) of a scanner's white margin


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


def _quad_from_hull(hull: np.ndarray) -> np.ndarray:
    """4 corners of a convex hull (falls back to the min-area rectangle)."""
    peri = cv2.arcLength(hull, True)
    for eps in (0.02, 0.03, 0.04, 0.05, 0.07):
        approx = cv2.approxPolyDP(hull, eps * peri, True)
        if len(approx) == 4:
            return approx.reshape(4, 2).astype("float32")
    return cv2.boxPoints(cv2.minAreaRect(hull)).astype("float32")


def _find_page(bgr: np.ndarray) -> np.ndarray | None:
    """Corners of the whole document (e.g. both pages of an open passport)
    in ``bgr`` coordinates, or None when it cannot be told from the background.

    The background color is read from the photo border; everything that
    differs from it is the document. Its convex hull keeps all pages together
    (an inner line such as the passport fold is ignored)."""
    h, w = bgr.shape[:2]
    ratio = min(1.0, _DETECT_SIDE / max(h, w))
    small = cv2.resize(bgr, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (7, 7), 0)
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).astype("float32")
    sh, sw = lab.shape[:2]
    b = max(4, min(sh, sw) // 50)
    border = np.concatenate(
        [lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
         lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)]
    )
    bg = np.median(border, axis=0)
    # Plain white, even border = already a scan (white margin): do not crop.
    if bg[0] > _WHITE_BORDER_L and np.median(np.linalg.norm(border - bg, axis=1)) < 8:
        return None
    dist = np.linalg.norm(lab - bg, axis=2)
    # Threshold between background noise and document (Otsu on the distance).
    dist8 = np.clip(dist * 2, 0, 255).astype(np.uint8)
    _, mask = cv2.threshold(dist8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    k = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    total = sh * sw
    # Join every big piece (pages split by a fold / shadow stay one document).
    big = [c for c in contours if cv2.contourArea(c) > 0.02 * total]
    if not big:
        return None
    hull = cv2.convexHull(np.vstack(big))
    area = cv2.contourArea(hull)
    if area < _MIN_PAGE_AREA * total or area > 0.97 * total:
        return None  # nothing found, or the photo is already just the document
    return _order_corners(_quad_from_hull(hull)) / ratio


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
    """Keep the original colors: mild local contrast on lightness + sharpen."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=1.3, tileGridSize=(8, 8)).apply(l)
    out = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
    blur = cv2.GaussianBlur(out, (0, 0), 1.2)
    return cv2.addWeighted(out, 1.4, blur, -0.4, 0)


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
