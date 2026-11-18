"""Full name from a family name and a given name."""

from __future__ import annotations

import re
from typing import Any

_LATIN = re.compile(r"[A-Za-z]")


def join_person_name(family: Any, given: Any) -> str:
    """Chinese names are written without a space (余 + 永飞 -> 余永飞); names in
    Latin letters keep one (NGUYEN + THI NGA -> NGUYEN THI NGA)."""
    parts = [str(p or "").strip() for p in (family, given)]
    parts = [p for p in parts if p]
    separator = " " if any(_LATIN.search(p) for p in parts) else ""
    return separator.join(parts)
