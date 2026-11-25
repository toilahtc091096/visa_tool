"""South S2 to get married (inviter CHONG SAP CUOI): SaveApplyInfo uses SPM (710021) + 登记结婚."""

import sys
import types
import unittest
from unittest import mock

sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))

from flows import flow_payloads as fp  # noqa: E402


def apply(region, visa="S2", relation="CHONG SAP CUOI", sub="SFM"):
    with mock.patch.object(fp, "REGION", region):
        body = fp.build_apply_info_profile("A1", visa, "30", "S", sub, "N", 3, "王", "小明",
                                           "110101199001011234", relation)
    d = body.to_dict() if hasattr(body, "to_dict") else vars(body)
    return d


def reason(d):
    r = d["applyReason"]
    return r if isinstance(r, dict) else vars(r)


class SouthS2MarriageTest(unittest.TestCase):
    def test_south_fiance(self):
        d = apply(fp.REGION_SOUTH)
        self.assertEqual((d["visaType"], d["visaPurpose"]), (710021, 709007))
        self.assertEqual(reason(d)["personalMatters"], "登记结婚")
        self.assertEqual(reason(d)["relation"], "未婚夫")
        self.assertEqual(reason(d)["residencePermit"], "110101199001011234")
        d = apply(fp.REGION_SOUTH, relation="Chồng sắp cưới")
        self.assertEqual(reason(d)["personalMatters"], "登记结婚")

    def test_unchanged_otherwise(self):
        for kw in (dict(region="north"), dict(region=fp.REGION_SOUTH, relation="CHONG"),
                   dict(region=fp.REGION_SOUTH, visa="Q2", sub="QCV")):
            d = apply(**kw)
            self.assertEqual(reason(d)["personalMatters"], "", kw)
            self.assertNotEqual(d["visaType"], 710021, kw)


if __name__ == "__main__":
    unittest.main()
