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


# County postcodes fixed by hand, by id: the source has placeholders (999999),
# division codes typed as postcodes, numbers of a neighbour county, or none.
POSTCODE_OVERRIDES = {
    # placeholder 999999
    "320312": "221100",  # 江苏 徐州 铜山区
    "320612": "226300",  # 江苏 南通 通州区
    # division code instead of a postcode
    "430422": "421100",  # 湖南 衡阳 衡南县 (was 430422)
    "340202": "241000",  # 安徽 芜湖 镜湖区 (was 340202)
    # wrong number (typo, or another county's postcode)
    "430725": "415700",  # 湖南 常德 桃源县 (was 451700)
    "640502": "755000",  # 宁夏 中卫 沙坡头区 (was 524000, Zhanjiang)
    "632521": "813000",  # 青海 海南州 共和县 (was 238200 = 安徽 和县)
    "150722": "162850",  # 内蒙古 呼伦贝尔 莫力达瓦旗 (was 028000 = 通辽 科尔沁区)
    "411627": "461400",  # 河南 周口 太康县 (was 475400 = 通许县)
    "520602": "554300",  # 贵州 铜仁 碧江区 (was 551600 = 大方县)
    "520502": "551700",  # 贵州 毕节 七星关区 (was 550500 = 福泉市)
    "520304": "563100",  # 贵州 遵义 播州区 (was 553500 = 盘州市)
    "320214": "214000",  # 江苏 无锡 新吴区 (was 215300 = 昆山市)
    "621102": "743000",  # 甘肃 定西 安定区 (was 744300 = 泾川县)
    "650502": "839000",  # 新疆 哈密 伊州区 (was 835200 = 霍城县)
    "230723": "153000",  # 黑龙江 伊春 汤旺县 (was 154700 = 汤原县)
    "140215": "037300",  # 山西 大同 云州区 (was 038300 = 怀仁市)
    "152501": "011100",  # 内蒙古 二连浩特市 (was 012600)
    "650202": "833600",  # 新疆 克拉玛依 独山子区 (was 838600)
    "230751": "153000",  # 黑龙江 伊春 金林区 (was 152000 = 绥化 北林区)
    "152202": "137800",  # 内蒙古 兴安盟 阿尔山市 (was 137805)
    "152221": "137400",  # 内蒙古 兴安盟 科右前旗 (was 137423)
    "460107": "571100",  # 海南 海口 琼山区 (was 571199)
    "610923": "711600",  # 陕西 安康 宁陕县 (was 711699)
    # missing in the source
    "620201": "735100",  # 甘肃 嘉峪关市
    "442001": "528400",  # 广东 中山市
    "361121": "334100",  # 江西 上饶县 (now 广信区)
    "410704": "453011",  # 河南 新乡 凤泉区
}

# Other pinyin names a place is also found by (the COVA name is kept, n8n
# sends it): 530681 is 水富市 but COVA names it "Shuicheng Shi".
NAME_ALIASES = {
    "530681": ["Shuifu Shi"],
}


def apply_fixes(data: dict) -> None:
    """Hand fixes on top of the sources (also run on an existing file)."""
    for level in ("provinces", "cities", "counties"):
        for row in data[level]:
            if row["id"] in NAME_ALIASES:
                row["aliases"] = NAME_ALIASES[row["id"]]
    for county in data["counties"]:
        if county["id"] in POSTCODE_OVERRIDES:
            county["postcode"] = POSTCODE_OVERRIDES[county["id"]]


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
    apply_fixes(data)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with_zip = sum(1 for c in counties if c["postcode"])
    print(
        f"{OUT}: {len(data['provinces'])} provinces, {len(data['cities'])} cities, "
        f"{len(counties)} counties ({with_zip} with postcode)"
    )


if __name__ == "__main__":
    main()
