"""One database for all houses (W3) and the admin report (W2)."""

import inspect
import os
import sys
import types
import unittest
from datetime import date
from unittest import mock

from database import house as house_mod
from database.crud import admin_report
from database.crud import agency as agency_crud
from database.crud import approval_print_job as han_crud
from database.crud import visa_registration as vr_crud
from database.models.visa_registration import VisaRegistration


class Row(dict):
    """Fake DB row usable as a tuple (row[0]) or a RealDictCursor dict."""

    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


class FakeCursor:
    def __init__(self, log, row=(1,)):
        self.log, self.row, self.rowcount = log, row, 1

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql, params))

    def fetchone(self):
        return self.row

    def fetchall(self):
        return []


class FakeConn:
    def __init__(self, log, row=(1,)):
        self.log, self.row = log, row

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self, cursor_factory=None):
        return FakeCursor(self.log, self.row)

    def close(self):
        pass


def _dummy_args(fn):
    args = []
    for name, p in inspect.signature(fn).parameters.items():
        if p.default is not inspect.Parameter.empty:
            continue
        if name == "item":
            args.append(VisaRegistration(first_applyid="A1", full_name="N", passport_number="P1", visa_type="L30"))
        elif name in ("updates",):
            args.append([{"record_id": 1, "status": "draft"}])
        elif name.endswith("_ids") or name.endswith("codes") or name == "record_ids":
            args.append([1] if "id" in name else ["X"])
        elif name in ("record_id", "agency_id"):
            args.append(1)
        elif name in ("start_dt", "end_dt"):
            args.append(date(2026, 11, 1))
        elif name == "is_vip":
            args.append(True)
        else:
            args.append("X")
    return args


class CurrentHouseTest(unittest.TestCase):
    def test_house_from_env_or_port(self):
        with mock.patch.dict(os.environ, {"HOUSE": "phong", "PORT": "10000"}):
            self.assertEqual(house_mod.current_house(), "PHONG")
        with mock.patch.dict(os.environ, {"HOUSE": "", "PORT": "30000"}):
            self.assertEqual(house_mod.current_house(), "TAI")

    def test_unknown_or_missing_house(self):
        with mock.patch.dict(os.environ, {"HOUSE": "XYZ"}):
            with self.assertRaises(RuntimeError):
                house_mod.current_house()
        with mock.patch.dict(os.environ, {"HOUSE": "", "PORT": "8080"}):
            self.assertEqual(house_mod.current_house(required=False), "")
            with self.assertRaises(RuntimeError):
                house_mod.current_house()


class HouseScopeTest(unittest.TestCase):
    """Every query of the house-scoped CRUD filters on (or writes) the current house."""

    def _run_all(self, module, row=(1,)):
        calls = {}
        fns = [f for n, f in inspect.getmembers(module, inspect.isfunction)
               if f.__module__ == module.__name__ and not n.startswith("_")]
        self.assertTrue(fns)
        for fn in fns:
            log = []
            with mock.patch.dict(os.environ, {"HOUSE": "PHONG"}), \
                 mock.patch.object(module, "get_connection", return_value=FakeConn(log, row)):
                # find_* look up by an optional key: give one so the query runs
                fn(*_dummy_args(fn), **({"first_applyid": "X"} if fn.__name__.startswith("find_") else {}))
            calls[fn.__name__] = log
        return calls

    def _assert_scoped(self, calls):
        for name, log in calls.items():
            self.assertTrue(log, f"{name} ran no SQL")
            for sql, params in log:
                self.assertIn("house", sql, f"{name}: SQL without house\n{sql}")
                self.assertIn("PHONG", list(params or []), f"{name}: house value not passed")

    def test_visa_registration_crud(self):
        self._assert_scoped(self._run_all(vr_crud))

    def test_agency_crud(self):
        self._assert_scoped(self._run_all(agency_crud, row=Row(id=1, code="X", name="X")))

    def test_han_job_crud(self):
        self._assert_scoped(self._run_all(han_crud, row=Row(id=1)))

    def test_create_refuses_record_of_other_house(self):
        log = []
        item = VisaRegistration(first_applyid="A1", full_name="N", passport_number="P1", visa_type="L30", staff_code="bao")
        with mock.patch.dict(os.environ, {"HOUSE": "HAI"}), \
             mock.patch.object(vr_crud, "get_connection", return_value=FakeConn(log, None)):
            with self.assertRaises(RuntimeError):
                vr_crud.create_visa_registration(item)
        sql, params = log[0]
        self.assertIn("WHERE visa_registrations.house = EXCLUDED.house", sql)
        self.assertIn("staff_code = COALESCE(NULLIF(visa_registrations.staff_code, ''), EXCLUDED.staff_code)", sql)
        self.assertEqual(params[-3:], ("HAI", "BAO", ""))

    def test_owner_first_run_wins(self):
        log = []
        with mock.patch.dict(os.environ, {"HOUSE": "TAI"}), \
             mock.patch.object(vr_crud, "get_connection", return_value=FakeConn(log)):
            vr_crud.set_visa_registration_owner(5, " long ", "job-1")
        sql, params = log[0]
        self.assertIn("COALESCE(NULLIF(staff_code, ''), %s)", sql)
        self.assertEqual(params, ("LONG", "job-1", 5, "TAI"))


class InitDatabaseTest(unittest.TestCase):
    def test_claims_untagged_rows_only_for_own_db_and_seeds_agencies(self):
        from database import connection
        log = []
        with mock.patch.object(connection, "get_connection", return_value=FakeConn(log)):
            connection.init_database(house="TAI")
        claims = [(sql, p) for sql, p in log if "SET house" in sql]
        self.assertEqual(len(claims), 3)
        for sql, p in claims:
            self.assertIn("NOT EXISTS", sql)  # never claims rows once another house is present
            self.assertEqual(p, {"house": "TAI"})
        self.assertIn("ON CONFLICT (house, code)", log[-1][0])

    def test_no_house_no_claim(self):
        from database import connection
        log = []
        with mock.patch.object(connection, "get_connection", return_value=FakeConn(log)):
            connection.init_database(house="")
        self.assertEqual(len(log), 1)  # schema only


class AdminFilterTest(unittest.TestCase):
    def test_all_filters(self):
        where, params = admin_report.build_filters({
            "date_from": "2026-11-01", "date_to": date(2026, 11, 20), "staff": "bao", "house": "hai",
            "visa_code": "l", "status": "approved", "q": "e12_%"})
        self.assertTrue(where.startswith("WHERE TRUE AND "))
        self.assertEqual(where.count("%s"), len(params))
        self.assertIn(date(2026, 11, 1), params)
        self.assertIn("BAO", params)
        self.assertIn("HAI", params)
        self.assertIn("L%", params)
        self.assertIn("%e12%", params)  # wildcards typed by the user are dropped

    def test_unknown_staff_and_empty(self):
        where, params = admin_report.build_filters({"staff": admin_report.UNKNOWN_STAFF})
        self.assertIn("vr.staff_code = ''", where)
        self.assertEqual(params, [])
        self.assertEqual(admin_report.build_filters({}), ("WHERE TRUE", []))

    def test_bad_date(self):
        with self.assertRaises(ValueError):
            admin_report.build_filters({"date_from": "20/11/2026"})


class MergeScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        import merge_databases
        cls.m = merge_databases

    def test_sources(self):
        self.assertEqual(self.m.parse_sources(None), {"HAI": "visa_db", "PHONG": "visa_db_phong", "TAI": "visa_db_tai"})
        self.assertEqual(self.m.parse_sources(["tai=x"])["TAI"], "x")
        with self.assertRaises(SystemExit):
            self.m.parse_sources(["NAM=x"])

    def test_duplicates_across_houses(self):
        data = {
            "HAI": {"visa_registrations": [{"first_applyid": "1", "application_code": ""}], "web_users": [{"username": "bao"}]},
            "PHONG": {"visa_registrations": [{"first_applyid": "1", "application_code": ""}, {"first_applyid": None, "application_code": ""}],
                      "web_users": []},
        }
        problems = self.m.find_duplicates(data)
        self.assertEqual(len(problems), 1)
        self.assertIn("first_applyid", problems[0])

    def test_han_keep_drops_other_house_copies(self):
        data = {
            "HAI": {"han_approval_jobs": [{"han_code": "HAN1"}, {"han_code": "HAN2"}]},
            "PHONG": {"han_approval_jobs": [{"han_code": "HAN1"}, {"han_code": "HAN3"}]},
            "TAI": {"han_approval_jobs": []},
        }
        self.assertEqual(self.m.drop_duplicate_han_jobs(data, "HAI"), [("PHONG", "HAN1")])
        self.assertEqual(data["PHONG"]["han_approval_jobs"], [{"han_code": "HAN3"}])
        self.assertEqual(len(data["HAI"]["han_approval_jobs"]), 2)
        self.assertEqual(self.m.find_duplicates(data), [])

    def test_rows_tagged_with_other_house(self):
        tables = {"visa_registrations": [{"id": 1, "house": "PHONG"}, {"id": 2, "house": ""}, {"id": 3, "house": "HAI"}]}
        self.assertEqual(len(self.m.wrong_house_rows("HAI", tables)), 1)


class AdminEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
        from fastapi.testclient import TestClient
        import server
        cls.server = server
        cls.client = TestClient(server.app)

    def setUp(self):
        users = {"admin-key": {"username": "chu", "staff_code": "ADMIN"}, "bao-key": {"username": "bao", "staff_code": "BAO"}}
        p = [
            mock.patch.dict(os.environ, {"ACCESS_GUARD": "enforce", "VISA_API_KEY": "shared"}),
            mock.patch.object(self.server, "get_web_user_by_api_key", side_effect=users.get),
            mock.patch.object(admin_report, "count_by_staff_day", return_value=[{"day": "2026-11-20", "staff_code": "BAO", "house": "HAI", "total": 2}]),
            mock.patch.object(admin_report, "list_records", return_value={"total": 0, "items": [], "limit": 50, "offset": 0}),
            mock.patch.object(admin_report, "list_staff_codes", return_value=["BAO"]),
        ]
        for x in p:
            x.start()
            self.addCleanup(x.stop)

    def test_admin_only(self):
        for path in ("/web/admin/options", "/web/admin/stats", "/web/admin/records"):
            self.assertEqual(self.client.get(path).status_code, 401, path)
            self.assertEqual(self.client.get(path, headers={"X-Api-Key": "bao-key"}).status_code, 403, path)
            self.assertEqual(self.client.get(path, headers={"X-Api-Key": "admin-key"}).status_code, 200, path)

    def test_filters_passed(self):
        self.client.get("/web/admin/stats?date_from=2026-11-01&staff=BAO&house=HAI", headers={"X-Api-Key": "admin-key"})
        f = admin_report.count_by_staff_day.call_args.args[0]
        self.assertEqual((f["date_from"], f["staff"], f["house"], f["date_to"]), ("2026-11-01", "BAO", "HAI", ""))
        r = self.client.get("/web/admin/stats?date_from=1/11/2026", headers={"X-Api-Key": "admin-key"})
        self.assertEqual(r.status_code, 400)
        self.client.get("/web/admin/records?q=E1&limit=20&offset=40", headers={"X-Api-Key": "admin-key"})
        self.assertEqual(admin_report.list_records.call_args.kwargs, {"limit": 20, "offset": 40})


if __name__ == "__main__":
    unittest.main()
