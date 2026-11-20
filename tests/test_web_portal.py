import os
import sys
import types
import unittest
from unittest import mock

from database.crud.web_user import hash_password, verify_password
from services import web_portal as wp


class FormTest(unittest.TestCase):
    def test_visa_type_join(self):
        self.assertEqual(wp.build_visa_type("L", "30"), "L30")
        self.assertEqual(wp.build_visa_type("q2", "180"), "Q2180")
        self.assertEqual(wp.build_visa_type("X1", "365"), "X1365")
        self.assertEqual(wp.build_visa_type("M", ""), "M")
        self.assertEqual(wp.build_visa_type("S2", "90"), "S290")

    def test_visa_type_rules(self):
        for code, days in [("L", ""), ("L", "60"), ("M", "45"), ("X1", "180"), ("X2", "200"), ("Z", "30"), ("Q2", "1a")]:
            with self.assertRaises(wp.FormError, msg=f"{code}{days}"):
                wp.build_visa_type(code, days)

    def test_prefix(self):
        self.assertEqual(wp.normalize_source_prefix("  /L30 - NGUYEN VAN A/ "), "L30 - NGUYEN VAN A/")
        for bad in ["", "  / ", "_archive/2026/x", "a/../b"]:
            with self.assertRaises(wp.FormError, msg=bad):
                wp.normalize_source_prefix(bad)

    def test_payload_matches_wf01_fields(self):
        p = wp.build_start_payload("bao", {"house": "phong", "visa_code": "Q2", "days": "180",
                                           "relation": "childrenSpouse", "source_prefix": "Be giau- Q2-180N"})
        self.assertRegex(p.pop("job_id"), r"^job-[a-z0-9]{8}$")
        self.assertEqual(p, {"staff": "BAO", "house": "PHONG", "bucket": "visa-data-phong", "api_port": "20000",
                             "visa_type": "Q2180", "relation": "childrenSpouse",
                             "source_prefix": "Be giau- Q2-180N/", "folder_name": "t"})

    def test_relation_rules(self):
        base = {"house": "HAI", "days": "", "source_prefix": "x"}
        with self.assertRaises(wp.FormError):
            wp.build_start_payload("BAO", {**base, "visa_code": "Q1"})  # Q needs a relation
        with self.assertRaises(wp.FormError):
            wp.build_start_payload("BAO", {**base, "visa_code": "Q1", "relation": "friend"})
        self.assertEqual(wp.build_start_payload("BAO", {**base, "visa_code": "M"})["relation"], "")
        with self.assertRaises(wp.FormError):
            wp.build_start_payload("BAO", {**base, "visa_code": "M", "house": "XYZ"})

    def test_start_case_posts_to_webhook_with_key(self):
        with mock.patch.dict(os.environ, {"N8N_START_WEBHOOK_URL": "https://n8n/webhook/visa-start", "VISA_API_KEY": "k"}), \
             mock.patch.object(wp.requests, "post", return_value=mock.Mock(status_code=200)) as post:
            self.assertEqual(wp.start_case({"job_id": "job-1"}), {"ok": True, "job_id": "job-1"})
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["headers"], {"X-Api-Key": "k"})

    def test_start_case_reports_n8n_error(self):
        with mock.patch.dict(os.environ, {"N8N_START_WEBHOOK_URL": "https://n8n/x"}), \
             mock.patch.object(wp.requests, "post", return_value=mock.Mock(status_code=500, text="boom")):
            with self.assertRaises(RuntimeError):
                wp.start_case({"job_id": "job-1"})

    def test_rerun_calls_instance_of_house(self):
        resp = mock.Mock(status_code=200, json=lambda: {"ok": True, "mode": "dry_run"})
        with mock.patch.object(wp.requests, "post", return_value=resp) as post:
            wp.rerun_prepare({"house": "TAI", "source_prefix": "A", "passport_number": "e02563363"})
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:30000/r2/folders/restore")
        self.assertEqual(post.call_args.kwargs["json"], {"prefix": "A/", "passport_number": "E02563363", "confirm": False})
        with self.assertRaises(wp.FormError):
            wp.rerun_prepare({"house": "TAI", "source_prefix": "A", "passport_number": "abc/.."})


class PasswordTest(unittest.TestCase):
    def test_hash_roundtrip(self):
        h = hash_password("bí mật 123", iterations=1000)
        self.assertTrue(verify_password("bí mật 123", h))
        self.assertFalse(verify_password("bí mật 124", h))
        self.assertFalse(verify_password("x", "garbage"))


class EndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
        from fastapi.testclient import TestClient
        import server
        cls.server = server
        cls.client = TestClient(server.app)

    def setUp(self):
        user = {"id": 1, "username": "bao", "staff_code": "BAO", "api_key": "user-key"}
        p = [
            mock.patch.dict(os.environ, {"ACCESS_GUARD": "enforce", "VISA_API_KEY": "shared"}),
            mock.patch.object(self.server, "get_web_user_by_api_key", side_effect=lambda k: user if k == "user-key" else None),
            mock.patch.object(self.server, "authenticate_web_user", side_effect=lambda u, pw: dict(user) if (u, pw) == ("bao", "pw") else None),
        ]
        for x in p:
            x.start()
            self.addCleanup(x.stop)
        self.server._login_failures.clear()

    def test_page_is_public(self):
        r = self.client.get("/web")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Khai hồ sơ visa", r.text)

    def test_login(self):
        r = self.client.post("/web/login", json={"username": "bao", "password": "pw"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.json()["api_key"], r.json()["staff"]), ("user-key", "BAO"))
        self.assertIn("visa_codes", r.json())
        self.assertEqual(self.client.post("/web/login", json={"username": "bao", "password": "no"}).status_code, 401)

    def test_login_rate_limit(self):
        for _ in range(5):
            self.client.post("/web/login", json={"username": "bao", "password": "no"})
        self.assertEqual(self.client.post("/web/login", json={"username": "bao", "password": "pw"}).status_code, 429)

    def test_start_needs_user_key_and_uses_logged_in_staff(self):
        form = {"house": "HAI", "visa_code": "L", "days": "30", "source_prefix": "L30 - A", "staff": "HANG"}
        self.assertEqual(self.client.post("/web/start", json=form).status_code, 401)
        with mock.patch.object(self.server, "start_case", side_effect=lambda c: {"ok": True, "job_id": c["job_id"]}) as sc:
            r = self.client.post("/web/start", json=form, headers={"X-Api-Key": "user-key"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(sc.call_args.args[0]["staff"], "BAO")  # not the "staff" sent by the browser
        self.assertEqual(r.json()["visa_type"], "L30")

    def test_start_form_error_is_400(self):
        r = self.client.post("/web/start", json={"house": "HAI", "visa_code": "L", "days": "60", "source_prefix": "x"},
                             headers={"X-Api-Key": "user-key"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("15 hoặc 30", r.json()["detail"]["error"])

    def test_other_paths_still_need_shared_key(self):
        self.assertEqual(self.client.post("/r2/images/delete", json={}, headers={"X-Api-Key": "user-key"}).status_code, 401)


if __name__ == "__main__":
    unittest.main()
