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
        # A place with aliases (another pinyin name) is also listed under each
        # alias, as the same place.
        extra = []
        for row in data[level]:
            row["key"] = name_key(row["name"])
            for alias in row.get("aliases") or ():
                extra.append({**row, "key": name_key(alias)})
        data[level].extend(extra)
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


# ---------------------------------------------------------------------------
# From the Chinese address (the source of truth). The province / city / district
# pinyin come from an AI reading the ID card and can be a guess that does not
# match the address (广西宁明县明江镇… came with Bose / Tiandong Xian).
# ---------------------------------------------------------------------------

_PROVINCE_CN_SUFFIXES = ("壮族自治区", "回族自治区", "维吾尔自治区", "特别行政区", "自治区", "省", "市")
_CITY_CN_SUFFIXES = ("自治州", "地区", "盟", "市")
_COUNTY_CN_SUFFIXES = "县区市旗"


def _cn_short(name: str, suffixes: tuple[str, ...]) -> str:
    for suffix in suffixes:
        if name.endswith(suffix) and len(name) - len(suffix) >= 2:
            return name[: -len(suffix)]
    return name


def _is_subsequence(short: str, long: str) -> bool:
    it = iter(long)
    return all(ch in it for ch in short)


def resolve_from_address(address: str, id_card: str = "") -> dict[str, str]:
    """COVA codes + pinyin names of the place written in a Chinese address.

    Province: the one the address starts with (full or short name: 广西 /
    广西壮族自治区), else the ID card's (first 2 digits). County: a county of
    that province whose full name is in the address (the earliest one; one
    under the city found wins). City: the county's city, else a city named in
    the address. No county in the address: the ID card's county (first 6
    digits) when it is in that province and city. When the address has a
    county-like word that is not a real county but whose characters are all in
    the ID card's county name (宁县 for 宁明县: a character missed by OCR),
    "fixed_address" is the address with that word replaced.

    Returns the levels found: province_code, city_code, county_code, postcode,
    province / city / county (COVA pinyin), source ("address" / "id_card" for
    the county) and maybe fixed_address."""
    data = _load()
    text = "".join(str(address or "").split())
    id_card = str(id_card or "").strip().upper()
    found: dict[str, str] = {}
    if not text:
        return found
    provinces = [r for r in data["provinces"] if r["key"] == name_key(r["name"])]  # no alias rows
    prov = next((r for r in provinces
                 if text.startswith(r["cn"]) or text.startswith(_cn_short(r["cn"], _PROVINCE_CN_SUFFIXES))), None)
    if not prov and len(id_card) >= 2:
        prov = next((r for r in provinces if r["id"][:2] == id_card[:2]), None)
    if not prov:
        return found
    found.update(province_code=prov["code"], province=prov["name"])
    cities = [r for r in data["cities"] if r["parent_id"] == prov["id"] and r["key"] == name_key(r["name"])]
    city_ids = {r["id"] for r in cities}
    counties = [r for r in data["counties"] if r["parent_id"] in city_ids and r["key"] == name_key(r["name"])]

    def first_pos(names: list[str]) -> int:
        pos = [text.find(n) for n in names if n and text.find(n) >= 0]
        return min(pos) if pos else -1

    city_hits = sorted(((first_pos([r["cn"], _cn_short(r["cn"], _CITY_CN_SUFFIXES)]), r) for r in cities),
                       key=lambda x: x[0])
    city_hits = [(p, r) for p, r in city_hits if p >= 0]
    city = city_hits[0][1] if city_hits else None
    county_hits = [(text.find(r["cn"]), r) for r in counties if text.find(r["cn"]) >= 0]
    if city:
        under = [(p, r) for p, r in county_hits if r["parent_id"] == city["id"]]
        county_hits = under or county_hits
    county_hits.sort(key=lambda x: (x[0], -len(x[1]["cn"])))
    county = county_hits[0][1] if county_hits else None
    if county and len({r["id"] for p, r in county_hits if p == county_hits[0][0]}) > 1:
        same = [r for p, r in county_hits if p == county_hits[0][0] and r["code"] == id_card[:6]]
        county = same[0] if same else None   # same name, same place in the text: only the ID card can tell
    source = "address"
    if not county and len(id_card) >= 6:
        by_id = next((r for r in counties if r["code"] == id_card[:6]), None)
        if by_id and (not city or by_id["parent_id"] == city["id"]):
            county, source = by_id, "id_card"
            # a county-like word right after the province / city that misses characters
            start = 0
            for name in (prov["cn"], _cn_short(prov["cn"], _PROVINCE_CN_SUFFIXES)):
                if text.startswith(name):
                    start = len(name)
                    break
            if city:
                end = text.find(city["cn"], start)
                if end >= 0:
                    start = end + len(city["cn"])
            m = next((i for i in range(start + 1, min(len(text), start + 8)) if text[i] in _COUNTY_CN_SUFFIXES), -1)
            word = text[start:m + 1] if m > start else ""
            if word and word != by_id["cn"] and word[-1] == by_id["cn"][-1] and _is_subsequence(word, by_id["cn"]):
                raw = str(address)
                found["fixed_address"] = raw.replace(word, by_id["cn"], 1) if word in raw else text.replace(word, by_id["cn"], 1)
    if county and not city:
        city = next(r for r in cities if r["id"] == county["parent_id"])
    if not city:
        return found
    found.update(city_code=city["code"], city=city["name"])
    if county:
        found.update(county_code=county["code"], county=county["name"], source=source)
        if county.get("postcode"):
            found["postcode"] = county["postcode"]
    return found
