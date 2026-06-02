from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent


def _resolve_env_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate

    search_roots = [
        PROJECT_ROOT,
        PROJECT_ROOT.parent,
        Path.cwd(),
    ]
    for base in search_roots:
        resolved = (base / candidate).resolve()
        if resolved.exists():
            return resolved

    return (PROJECT_ROOT / candidate).resolve()


def load_dotenv(path: str | Path = PROJECT_ROOT / ".env") -> None:
    env_path = _resolve_env_path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()
