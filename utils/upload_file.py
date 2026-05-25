from pathlib import Path


def get_files(folder_path, x):
    base = Path(__file__).resolve().parent / ".." / "resources"

    folder = base / folder_path.lstrip("/")

    files = [f for f in folder.iterdir() if f.is_file()]

    return files[:x]
