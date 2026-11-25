"""The inviter's place (COVA codes) follows the Chinese address, not the AI's pinyin guess."""

import sys
import types
import unittest
from types import SimpleNamespace
from unittest import mock

sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))

from utils.china_location import resolve_from_address  # noqa: E402
from visa_types.base import china_place_from_pinyin  # noqa: E402

BAD = "广西宁县明江镇峙利村峙垌屯24号"          # OCR missed 明 (宁明县)
GOOD = "广西宁明县明江镇峙利村峙垌屯24号"
NINGMING_ID = "451422199001011234"


def travel(**kw):
    base = dict(inviterProvincePinyin="GuangXi", inviterCityPinyin="Bose", inviterDistrictPinyin="Tiandong  Xian",
                inviterIdCard="", inviterAddress=GOOD)
    return SimpleNamespace(**{**base, **kw})


class ResolveFromAddressTest(unittest.TestCase):
    def test_places(self):
        for address, county in [(GOOD, "451422"), ("广西壮族自治区崇左市宁明县明江镇", "451422"),
                                ("福建省泉州市南安市溪美街道", "350583"), ("北京市朝阳区建国路88号", "110105"),
                                ("甘肃省庆阳市宁县新宁镇", "621026")]:
            self.assertEqual(resolve_from_address(address).get("county_code"), county, address)
        r = resolve_from_address(GOOD)
        self.assertEqual((r["city"], r["county"], r["city_code"]), ("Chongzuo", "Ningming Xian", "COZ"))

    def test_missing_character_fixed_from_id_card(self):
        r = resolve_from_address(BAD, NINGMING_ID)
        self.assertEqual((r["county_code"], r["source"], r["fixed_address"]), ("451422", "id_card", GOOD))
        self.assertNotIn("city_code", resolve_from_address(BAD))   # no ID card: no guess below the province

    def test_id_card_of_another_province_is_not_used(self):
        self.assertNotIn("county_code", resolve_from_address(BAD, "621026199001011234"))


class ChinaPlaceTest(unittest.TestCase):
    def test_address_wins_over_wrong_pinyin(self):
        t = travel()
        with mock.patch("utils.log_event") as log:
            place = china_place_from_pinyin(t)
        self.assertEqual((place.province, place.city, place.county, place.postcode), ("GX", "COZ", "451422", "532500"))
        self.assertEqual((t.inviterCityPinyin, t.inviterDistrictPinyin), ("Chongzuo", "Ningming Xian"))
        self.assertIn("warning", log.call_args.args[0])

    def test_bad_address_fixed(self):
        t = travel(inviterAddress=BAD, inviterIdCard=NINGMING_ID)
        with mock.patch("utils.log_event"):
            place = china_place_from_pinyin(t)
        self.assertEqual((place.city, place.county, t.inviterAddress), ("COZ", "451422", GOOD))

    def test_pinyin_kept_when_address_says_nothing(self):
        t = travel(inviterAddress="", inviterCityPinyin="Chongzuo", inviterDistrictPinyin="Ningming Xian")
        with mock.patch("utils.log_event"):
            self.assertEqual(china_place_from_pinyin(t).county, "451422")
        t = travel(inviterAddress="")   # old behaviour: the pinyin as given
        with mock.patch("utils.log_event"):
            self.assertEqual(china_place_from_pinyin(t).city, "BSS")

    def test_company_address_not_rewritten(self):
        t = travel(inviterAddress="")
        with mock.patch("utils.log_event"):
            place = china_place_from_pinyin(t, address=GOOD)
        self.assertEqual(place.county, "451422")
        self.assertEqual(t.inviterAddress, "")


if __name__ == "__main__":
    unittest.main()
