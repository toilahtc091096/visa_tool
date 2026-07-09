from pathlib import Path


def sanitize_path_suffix(value: str) -> str:
    text = str(value or "").strip().strip('"').strip("'")
    text = "".join(ch for ch in text if ch.isalnum() or ch in {"_", "-"})
    return text or "default"


def passport_data_dir(passport_number: str) -> Path:
    base = Path(__file__).resolve().parent / ".." / "resources"
    return base / f"data_{sanitize_path_suffix(passport_number)}"
