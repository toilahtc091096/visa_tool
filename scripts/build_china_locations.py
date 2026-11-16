"""Build resources/china_locations.json (province / city / county + postcode,
plus the Chinese name "cn" used by the n8n location matcher).

Sources:
  - COVA web metadata (resources/data-web.json): PROVINCE_LIST, CITY_LIST,
    COUNTIES_LIST -> the codes COVA accepts.
  - County postcodes: tombcato/china-zipcode-data (MIT), file
    china_zipcode_adcode.json, joined on the 6-digit county code.
    https://github.com/tombcato/china-zipcode-data

Usage:
  python scripts/build_china_locations.py <china_zipcode_adcode.json> [data-web.json]
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "resources" / "china_locations.json"


# Chinese names the postcode list does not have (Taiwan, Hong Kong, the
# county-level places COVA lists as cities, a few merged counties), by id.
CN_OVERRIDES = {
    "710000": "台湾省",
    "419001": "济源市",
    "429004": "仙桃市",
    "429005": "潜江市",
    "429006": "天门市",
    "429021": "神农架林区",
    "469001": "五指山市",
    "469002": "琼海市",
    "469005": "文昌市",
    "469006": "万宁市",
    "469007": "东方市",
    "469021": "定安县",
    "469022": "屯昌县",
    "469023": "澄迈县",
    "469024": "临高县",
    "469025": "白沙黎族自治县",
    "469026": "昌江黎族自治县",
    "469027": "乐东黎族自治县",
    "469028": "陵水黎族自治县",
    "469029": "保亭黎族苗族自治县",
    "469030": "琼中黎族苗族自治县",
    "520522": "黔西市",
    "710100": "台南市",
    "710200": "苗栗县",
    "710300": "高雄市",
    "710400": "宜兰县",
    "710500": "基隆市",
    "710600": "新竹市",
    "710700": "台中市",
    "710800": "嘉义市",
    "710900": "台北市",
    "711000": "桃园市",
    "711100": "彰化县",
    "711200": "南投县",
    "711300": "云林县",
    "711400": "屏东县",
    "711500": "台东县",
    "711600": "花莲县",
    "711700": "澎湖县",
    "810100": "香港岛",
    "810200": "九龙",
    "810300": "新界",
    "361121": "上饶县",
    "441901": "东莞市",
    "442001": "中山市",
    "620201": "嘉峪关市",
}


def main() -> None:
    zip_path = Path(sys.argv[1])
    web_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "resources" / "data-web.json"
    select = json.loads(web_path.read_text(encoding="utf-8"))["content"][0]["selectData"]
    zip_rows = json.loads(zip_path.read_text(encoding="utf-8"))
    zips = {row["code"]: str(row.get("zipCode") or "") for row in zip_rows}
    # Postcodes the current source no longer lists.
    zips.setdefault("441901", "523000")  # 东莞市
    # Chinese names by 6-digit division id (county / city / province).
    cn_names: dict[str, str] = {}
    for row in zip_rows:
        cn_names.setdefault(row["provinceCode"] + "0000", row["province"])
        cn_names.setdefault(row["cityCode"] + "00", row["city"])
        cn_names[row["code"]] = row["name"]
    cn_names.update(CN_OVERRIDES)

    def rows(list_name: str) -> list[dict]:
        return [
            {
                "id": o["id"],
                "code": o["value"],
                "parent_id": o["parentId"],
                "name": o["name"],
                "cn": cn_names.get(o["id"], ""),
            }
            for o in select[list_name]["options"]
            if o.get("name")
        ]

    counties = rows("COUNTIES_LIST")
    for county in counties:
        postcode = zips.get(county["id"], "")
        # Keep only real 6-digit postcodes (the source has a few ranges/typos).
        county["postcode"] = postcode if len(postcode) == 6 and postcode.isdigit() else ""

    data = {
        "source": {
            "codes": "COVA web metadata (data-web.json)",
            "postcodes": "github.com/tombcato/china-zipcode-data (MIT), 2023 divisions",
            "built": date.today().isoformat(),
        },
        "provinces": rows("PROVINCE_LIST"),
        "cities": rows("CITY_LIST"),
        "counties": counties,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with_zip = sum(1 for c in counties if c["postcode"])
    print(
        f"{OUT}: {len(data['provinces'])} provinces, {len(data['cities'])} cities, "
        f"{len(counties)} counties ({with_zip} with postcode)"
    )


if __name__ == "__main__":
    main()
