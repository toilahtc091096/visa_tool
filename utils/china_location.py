"""Chinese province / city / district codes from pinyin names.

Data: resources/china_locations.json (built by scripts/build_china_locations.py
from the COVA web metadata + a county postcode list). COVA wants:
province code (GX), city code (QZH) and county code (450703).
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

LOCATIONS_PATH = Path(__file__).resolve().parent.parent / "resources" / "china_locations.json"

# Suffixes a caller may add that COVA names leave out ("Guǎngxī Zhuàngzú
# Zìzhìqū" -> GuangXi, "Qīnzhōu Shì" -> Qinzhou). Longest first.
_PROVINCE_SUFFIXES = (
    "zhuangzuzizhiqu", "weiwuerzizhiqu", "huizuzizhiqu", "tebiexingzhengqu",
    "zizhiqu", "sheng", "shi",
)
_CITY_SUFFIXES = ("zizhizhou", "diqu", "meng", "shi")


def name_key(value: Any) -> str:
    """'Qīnběi Qū' / 'Qinbei Qu' -> 'qinbeiqu' (no tone marks, lowercase,
    letters and digits only)."""
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return "".join(ch for ch in text.lower() if ch.isascii() and ch.isalnum())


def _strip_suffix(key: str, suffixes: tuple[str, ...]) -> str:
    for suffix in suffixes:
        if key.endswith(suffix) and len(key) > len(suffix):
            return key[: -len(suffix)]
    return key


@lru_cache(maxsize=1)
def _load() -> dict[str, list[dict[str, Any]]]:
    data = json.loads(LOCATIONS_PATH.read_text(encoding="utf-8"))
    for level in ("provinces", "cities", "counties"):
        for row in data[level]:
            row["key"] = name_key(row["name"])
    return data


def _match(rows: list[dict[str, Any]], key: str, suffixes: tuple[str, ...]) -> dict | None:
    """Exact key, then key without a suffix, then a unique prefix match."""
    if not key:
        return None
    for wanted in (key, _strip_suffix(key, suffixes)):
        hits = [r for r in rows if r["key"] == wanted]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            return None  # ambiguous name, never guess
    hits = [r for r in rows if key.startswith(r["key"]) or r["key"].startswith(key)]
    return hits[0] if len(hits) == 1 else None


_COUNTY_SUFFIXES = ("zizhixian", "shi", "xian", "qu", "qi")


def _county_in_province(
    data: dict[str, list[dict[str, Any]]], province_id: str, name: str, id_card: str
) -> dict | None:
    """A county-level place given as the city ("Nánān Shì" = 南安市, under
    Quanzhou): search every county of the province. Several hits (same name)
    are told apart only by the ID card's first 6 digits; otherwise no guess."""
    key = name_key(name)
    if not key:
        return None
    city_ids = {r["id"] for r in data["cities"] if r["parent_id"] == province_id}
    rows = [r for r in data["counties"] if r["parent_id"] in city_ids]
    hits = [r for r in rows if r["key"] == key]
    if not hits:
        bare = _strip_suffix(key, _COUNTY_SUFFIXES)
        hits = [r for r in rows if _strip_suffix(r["key"], _COUNTY_SUFFIXES) == bare]
    if len(hits) > 1:
        hits = [r for r in hits if r["code"] == str(id_card or "").strip()[:6]]
    return hits[0] if len(hits) == 1 else None


def resolve_china_location(
    province: str, city: str, district: str = "", id_card: str = ""
) -> dict[str, str]:
    """Pinyin names -> COVA codes, matched level by level under the parent.

    Returns the levels found, e.g. {"province_code": "GX", "city_code": "QZH",
    "county_code": "450703", "postcode": "535000"}; a level that is not found
    (and every level below it) is left out.

    When the city name is not a prefecture-level city but a county-level one
    of the province (南安市 "Nánān Shì"), the city becomes its parent city and
    the county that place. id_card (the inviter's ID number) only breaks ties
    between counties with the same name.
    """
    data = _load()
    found: dict[str, str] = {}
    prov = _match(data["provinces"], name_key(province), _PROVINCE_SUFFIXES)
    if not prov:
        return found
    found["province_code"] = prov["code"]
    cities = [r for r in data["cities"] if r["parent_id"] == prov["id"]]
    cty = _match(cities, name_key(city), _CITY_SUFFIXES)
    if cty:
        counties = [r for r in data["counties"] if r["parent_id"] == cty["id"]]
        cnty = _match(counties, name_key(district), ())
    else:
        cnty = _county_in_province(data, prov["id"], city, id_card)
        if cnty:
            cty = next(r for r in cities if r["id"] == cnty["parent_id"])
    if not cty:
        return found
    found["city_code"] = cty["code"]
    if not cnty:
        return found
    found["county_code"] = cnty["code"]
    if cnty.get("postcode"):
        found["postcode"] = cnty["postcode"]
    return found
