from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


WINDOWS_FONT_DIRS: tuple[Path, ...] = (
    Path(r"C:\Windows\Fonts"),
    Path(r"C:\WINNT\Fonts"),
)

DEFAULT_FONT_CANDIDATES: tuple[str, ...] = (
    "KaiTi.ttf",
    "stkaiti.ttf",
    "simkai.ttf",
    "SIMKAI.TTF",
    "kaiu.ttf",
    "STKAITI.TTF",
    "FangSong.ttf",
    "simfang.ttf",
    "STFANGS.TTF",
    "MSYH.TTC",
    "msyh.ttc",
    "microsoft yahei.ttf",
    "SIMSUN.TTC",
    "simsun.ttc",
)


def _iter_font_candidates(font_name: str | None = None) -> Iterable[Path]:
    if font_name:
        candidate = Path(font_name)
        if candidate.is_file():
            yield candidate
        else:
            for font_dir in WINDOWS_FONT_DIRS:
                yield font_dir / font_name
        return

    for font_dir in WINDOWS_FONT_DIRS:
        for font_file in DEFAULT_FONT_CANDIDATES:
            yield font_dir / font_file


def resolve_chinese_font(font_name: str | None = None) -> str:
    """
    Find a usable Chinese font path on Windows.

    Priority:
    1. `font_name` if it is a real path
    2. `font_name` inside common Windows font directories
    3. Known calligraphy-like/system Chinese fonts
    4. Pillow default font as final fallback
    """

    for candidate in _iter_font_candidates(font_name):
        if candidate.is_file():
            return str(candidate)

    return ""


def _sanitize_text(value: str) -> str:
    return str(value or "").strip()


def render_chinese_name_signature_png(
    name: str,
    *,
    font_name: str | None = None,
    font_size: int = 64,
    padding_x: int = 18,
    padding_y: int = 12,
    text_color: tuple[int, int, int, int] = (0, 0, 0, 255),
    background: tuple[int, int, int, int] = (255, 255, 255, 0),
    min_width: int = 260,
    min_height: int = 90,
) -> bytes:
    """
    Render a Chinese name as a transparent PNG.

    Returns raw PNG bytes so it can be embedded directly into a DOCX flow
    or saved to disk.
    """

    text = _sanitize_text(name)
    if not text:
        raise ValueError("name is required")

    font_path = resolve_chinese_font(font_name)
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        raise RuntimeError(
            "No Chinese font found. Pass `font_name` or install a font such as "
            "KaiTi, STKaiti, FangSong, or Microsoft YaHei in C:\\Windows\\Fonts."
        )

    probe = Image.new("RGBA", (1, 1), background)
    probe_draw = ImageDraw.Draw(probe)
    bbox = probe_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    width = max(min_width, text_width + padding_x * 2)
    height = max(min_height, text_height + padding_y * 2)

    image = Image.new("RGBA", (width, height), background)
    draw = ImageDraw.Draw(image)

    x = padding_x - bbox[0]
    y = (height - text_height) // 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=text_color)

    import io

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def save_chinese_name_signature_png(
    name: str,
    output_path: str | Path,
    *,
    font_name: str | None = None,
    font_size: int = 64,
    padding_x: int = 18,
    padding_y: int = 12,
    text_color: tuple[int, int, int, int] = (0, 0, 0, 255),
    background: tuple[int, int, int, int] = (255, 255, 255, 0),
    min_width: int = 260,
    min_height: int = 90,
) -> str:
    """
    Save the rendered PNG to disk and return the resolved file path.
    """

    png_bytes = render_chinese_name_signature_png(
        name,
        font_name=font_name,
        font_size=font_size,
        padding_x=padding_x,
        padding_y=padding_y,
        text_color=text_color,
        background=background,
        min_width=min_width,
        min_height=min_height,
    )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(png_bytes)
    return str(target.resolve())
