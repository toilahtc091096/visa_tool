import os
import sys
import types
import unittest
from datetime import date
from unittest import mock

from database.crud import admin_report


class AgencyVipFilterTest(unittest.TestCase):
    def test_agency_by_code_across_houses(self):
        where, params = admin_report.build_filters({"agency": "abc"})
        self.assertIn("vr.agency_id IN (SELECT id FROM agencies WHERE code = %s)", where)
        self.assertEqual(params, ["ABC"])

    def test_agency_none(self):
        where, params = admin_report.build_filters({"agency": admin_report.UNKNOWN_AGENCY})
        self.assertIn("vr.agency_id IS NULL", where)
        self.assertEqual(params, [])

    def test_vip(self):
        self.assertIn("AND vr.is_vip", admin_report.build_filters({"vip": "1"})[0])
        self.assertIn("NOT vr.is_vip", admin_report.build_filters({"vip": "0"})[0])
        self.assertEqual(admin_report.build_filters({"vip": "x"}), ("WHERE TRUE", []))


class ChartSummaryTest(unittest.TestCase):
    def test_summary_shapes_and_totals(self):
        calls = []

        def fake_fetch(sql, params):
            calls.append((sql, params))
            if "::date AS key" in sql:
                return [{"key": date(2026, 11, 22), "house": "TAI", "n": 2},
                        {"key": date(2026, 11, 20), "house": "HAI", "n": 2},
                        {"key": date(2026, 11, 20), "house": "TAI", "n": 1}]
            if "COUNT(*) AS n FROM" in sql and "is_vip" in sql:
                return [{"n": 1}]
            if "vr.status AS key" in sql:
                return [{"key": "approved", "house": "HAI", "n": 1, "approved": 1, "rejected": 0},
                        {"key": "approved", "house": "TAI", "n": 1, "approved": 1, "rejected": 0},
                        {"key": "rejected", "house": "TAI", "n": 1, "approved": 0, "rejected": 1},
                        {"key": "under_review", "house": "HAI", "n": 1, "approved": 0, "rejected": 0},
                        {"key": "draft", "house": "HAI", "n": 1, "approved": 0, "rejected": 0}]
            if "vr.house AS key" in sql:
                return [{"key": "TAI", "house": "TAI", "n": 3, "approved": 1, "rejected": 1},
                        {"key": "HAI", "house": "HAI", "n": 2, "approved": 1, "rejected": 0}]
            return [{"key": "ABC", "house": "HAI", "n": 2, "approved": 1, "rejected": 0},
                    {"key": "ABC", "house": "TAI", "n": 3, "approved": 1, "rejected": 1}]

        with mock.patch.object(admin_report, "_fetch_all", side_effect=fake_fetch):
            s = admin_report.chart_summary({"agency": "ABC", "house": "HAI"})
        self.assertEqual(s["totals"], {"total": 5, "approved": 2, "rejected": 1, "draft": 1, "in_progress": 1, "vip": 1})
        self.assertEqual(s["by_day"], [{"key": "2026-11-20", "n": 3, "houses": {"HAI": 2, "TAI": 1}},
                                       {"key": "2026-11-22", "n": 2, "houses": {"TAI": 2}}])
        self.assertEqual(s["by_status"][0], {"key": "approved", "n": 2, "approved": 2, "rejected": 0, "houses": {"HAI": 1, "TAI": 1}})
        self.assertEqual(s["by_agency"], [{"key": "ABC", "n": 5, "approved": 2, "rejected": 1, "houses": {"HAI": 2, "TAI": 3}}])
        self.assertEqual(s["houses"], ["HAI", "TAI"])  # by_house sorted by name
        for k in ("by_agency", "by_visa", "by_staff", "by_house", "by_status"):
            self.assertIn(k, s)
        # every query is scoped by the same filters
        for sql, params in calls:
            self.assertIn("vr.house = %s", sql)
            self.assertIn("HAI", params)
            self.assertIn("ABC", params)


class ChartEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
        from fastapi.testclient import TestClient
        import server
        cls.server = server
        cls.client = TestClient(server.app)

    def setUp(self):
        users = {"admin-key": {"id": 1, "username": "admin", "staff_code": "ADMIN", "api_key": "admin-key"},
                 "bao-key": {"id": 2, "username": "bao", "staff_code": "BAO", "api_key": "bao-key"}}
        for p in [
            mock.patch.dict(os.environ, {"ACCESS_GUARD": "enforce", "VISA_API_KEY": "shared"}),
            mock.patch.object(self.server, "get_web_user_by_api_key", side_effect=lambda k: users.get(k)),
            mock.patch.object(admin_report, "chart_summary", return_value={"totals": {"total": 0}, "by_day": []}),
            mock.patch.object(admin_report, "list_agencies", return_value=[{"code": "ABC", "name": "Đại lý A", "houses": ["TAI"]}]),
            mock.patch.object(admin_report, "list_staff_codes", return_value=["BAO"]),
        ]:
            p.start()
            self.addCleanup(p.stop)

    def test_stats_page_is_served(self):
        r = self.client.get("/web/stats")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Thống kê hồ sơ", r.text)

    def test_charts_admin_only_and_filters(self):
        self.assertEqual(self.client.get("/web/admin/charts").status_code, 401)
        self.assertEqual(self.client.get("/web/admin/charts", headers={"X-Api-Key": "bao-key"}).status_code, 403)
        r = self.client.get("/web/admin/charts?agency=ABC&vip=1&house=TAI&date_from=2026-11-01",
                            headers={"X-Api-Key": "admin-key"})
        self.assertEqual(r.status_code, 200, r.text)
        f = admin_report.chart_summary.call_args.args[0]
        self.assertEqual((f["agency"], f["vip"], f["house"], f["date_from"]), ("ABC", "1", "TAI", "2026-11-01"))

    def test_options_list_agencies(self):
        r = self.client.get("/web/admin/options", headers={"X-Api-Key": "admin-key"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["agencies"][0]["code"], "ABC")
        self.assertEqual(r.json()["unknown_agency"], admin_report.UNKNOWN_AGENCY)


if __name__ == "__main__":
    unittest.main()
