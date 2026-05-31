from pathlib import Path
from typing import Any

import fitz


def _convert_pdf_to_pngs(pdf_path: Path) -> list[Path]:
    output_paths: list[Path] = []
    with fitz.open(pdf_path) as doc:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            output_path = pdf_path.with_name(f"{pdf_path.stem}_page_{page_index + 1}.png")
            pix.save(output_path)
            output_paths.append(output_path)
    pdf_path.unlink(missing_ok=True)
    return output_paths


def api_convert_input_pdfs(input_dir: str | Path | None = None) -> dict[str, Any]:
    base_dir = Path(__file__).resolve().parent.parent / "resources"
    resolved_input_dir = Path(input_dir) if input_dir is not None else base_dir / "input"

    if not resolved_input_dir.exists():
        return {
            "ok": True,
            "skipped": True,
            "reason": "resources/input does not exist",
            "input_dir": str(resolved_input_dir),
        }

    converted: list[dict[str, Any]] = []
    pdf_paths = sorted(
        path
        for path in resolved_input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    )
    for pdf_path in pdf_paths:
        png_paths = _convert_pdf_to_pngs(pdf_path)
        converted.append(
            {
                "pdf": pdf_path.name,
                "png_files": [path.name for path in png_paths],
                "page_count": len(png_paths),
            }
        )

    return {
        "ok": True,
        "input_dir": str(resolved_input_dir),
        "converted": converted,
        "pdf_count": len(pdf_paths),
    }
