"""Build resources/china_locations.json (province / city / county + postcode).

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


def main() -> None:
    zip_path = Path(sys.argv[1])
    web_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "resources" / "data-web.json"
    select = json.loads(web_path.read_text(encoding="utf-8"))["content"][0]["selectData"]
    zips = {
        row["code"]: str(row.get("zipCode") or "")
        for row in json.loads(zip_path.read_text(encoding="utf-8"))
    }

    def rows(list_name: str) -> list[dict]:
        return [
            {"id": o["id"], "code": o["value"], "parent_id": o["parentId"], "name": o["name"]}
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
