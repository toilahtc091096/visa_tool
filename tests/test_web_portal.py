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
                                           "relation": "CON RE", "source_prefix": "Be giau- Q2-180N",
                                           "inviter_phone": "138 0013 8000", "pay_mobile": "0912.345.678"})
        self.assertRegex(p.pop("job_id"), r"^job-[a-z0-9]{8}$")
        self.assertEqual(p, {"staff": "BAO", "house": "PHONG", "bucket": "visa-data-phong", "api_port": "20000",
                             "visa_type": "Q2180", "relation": "CON RE",
                             "inviter_phone": "13800138000", "pay_mobile": "0912345678", "phone": "0912345678",
                             "source_prefix": "Be giau- Q2-180N/", "folder_name": "t"})

    def test_relation_rules(self):
        base = {"house": "HAI", "days": "", "source_prefix": "x", "inviter_phone": "13800138000", "pay_mobile": "0912345678"}
        with self.assertRaises(wp.FormError):
            wp.build_start_payload("BAO", {**base, "visa_code": "Q1"})  # Q needs a relation
        with self.assertRaises(wp.FormError):
            wp.build_start_payload("BAO", {**base, "visa_code": "Q1", "relation": "friend"})
        self.assertEqual(wp.build_start_payload("BAO", {**base, "visa_code": "M"})["relation"], "")
        self.assertEqual(wp.build_start_payload("BAO", {**base, "visa_code": "S2", "relation": "VO SAP CUOI"})["relation"], "VO SAP CUOI")
        with self.assertRaises(wp.FormError):  # old WF-01 keys are not offered on the web form
            wp.build_start_payload("BAO", {**base, "visa_code": "Q2", "relation": "spouse"})
        with self.assertRaises(wp.FormError):
            wp.build_start_payload("BAO", {**base, "visa_code": "M", "house": "XYZ"})

    def test_phones_for_visit_visas(self):
        base = {"house": "HAI", "days": "", "source_prefix": "x", "relation": "CHONG"}
        for code in ("Q1", "Q2", "S2"):
            with self.assertRaises(wp.FormError, msg=code):
                wp.build_start_payload("BAO", {**base, "visa_code": code, "inviter_phone": "13800138000"})
        p = wp.build_start_payload("BAO", {**base, "visa_code": "S2", "inviter_phone": "+86 138-0013-8000", "pay_mobile": "0912345678"})
        self.assertEqual((p["inviter_phone"], p["pay_mobile"]), ("+8613800138000", "0912345678"))
        for bad in ("12345", "0912abc678", "1" * 16):
            with self.assertRaises(wp.FormError, msg=bad):
                wp.build_start_payload("BAO", {**base, "visa_code": "Q1", "inviter_phone": bad, "pay_mobile": "0912345678"})
        # the form now sends the applicant's phone as "phone"
        p = wp.build_start_payload("BAO", {**base, "visa_code": "Q1", "inviter_phone": "13800138000", "phone": "0912 345 678"})
        self.assertEqual((p["pay_mobile"], p["phone"]), ("0912345678", "0912345678"))
        # other visas: no inviter phone / payMobile; the applicant's phone is optional
        other = {"house": "HAI", "days": "30", "source_prefix": "x", "visa_code": "L", "inviter_phone": "x"}
        p = wp.build_start_payload("BAO", other)
        self.assertEqual((p["inviter_phone"], p["pay_mobile"], p["phone"]), ("", "", ""))
        p = wp.build_start_payload("BAO", {**other, "phone": "+84 912-345-678"})
        self.assertEqual((p["inviter_phone"], p["pay_mobile"], p["phone"]), ("", "", "+84912345678"))
        with self.assertRaises(wp.FormError):
            wp.build_start_payload("BAO", {**other, "phone": "12ab"})

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

    def test_rerun_by_passport_searches_all_houses(self):
        def fake(url, json, timeout):
            port = url.split(":")[2].split("/")[0]
            if port == "20000":
                return mock.Mock(status_code=200, json=lambda: {"ok": True, "mode": "dry_run", "prefix": "X2 - A/", "archive": "_archive/s__E1/X2 - A/"})
            return mock.Mock(status_code=400, json=lambda: {"detail": {"ok": False, "error": "archive_not_found_for_passport"}})
        with mock.patch.object(wp.requests, "post", side_effect=fake) as post:
            r = wp.rerun_prepare({"passport_number": "e02563363"})
        self.assertEqual((r["ok"], r["house"], r["prefix"]), (True, "PHONG", "X2 - A/"))
        self.assertEqual(post.call_count, 3)
        self.assertTrue(all(c.kwargs["json"]["confirm"] is False and c.kwargs["json"]["prefix"] == "" for c in post.call_args_list))
        with mock.patch.object(wp.requests, "post", side_effect=fake):
            with self.assertRaises(wp.FormError):  # confirm needs the house found by Kiểm tra
                wp.rerun_prepare({"passport_number": "E02563363", "confirm": True})
        none = mock.Mock(status_code=400, json=lambda: {"detail": {"ok": False, "error": "archive_not_found_for_passport"}})
        with mock.patch.object(wp.requests, "post", return_value=none):
            r = wp.rerun_prepare({"passport_number": "E02563363"})
        self.assertFalse(r["ok"])
        self.assertIn("Không tìm thấy", r["error"])

    def test_rerun_calls_instance_of_house(self):
        resp = mock.Mock(status_code=200, json=lambda: {"ok": True, "mode": "dry_run"})
        with mock.patch.object(wp.requests, "post", return_value=resp) as post:
            wp.rerun_prepare({"house": "TAI", "source_prefix": "A", "passport_number": "e02563363"})
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:30000/r2/folders/restore")
        self.assertEqual(post.call_args.kwargs["json"], {"prefix": "A/", "passport_number": "E02563363", "confirm": False})
        with self.assertRaises(wp.FormError):
            wp.rerun_prepare({"house": "TAI", "source_prefix": "A", "passport_number": "abc/.."})


    def test_relation_labels_known_by_server(self):
        import constants
        from visa_types.family import _relation_key
        unknown = [r["value"] for r in wp.RELATIONS if _relation_key(r["value"]) not in constants.INVITER_RELATION_ZH_SOUTH]
        self.assertEqual(unknown, ["HO HANG"])  # sent as-is, same as before
        self.assertEqual([r["value"] for r in wp.RELATIONS if "S2" in r.get("first_for", [])], ["CHONG SAP CUOI", "VO SAP CUOI"])

    def test_run_case_uses_local_instance_of_port(self):
        self.assertEqual(wp.house_by_port("20000"), "PHONG")
        with self.assertRaises(wp.FormError):
            wp.house_by_port("8080")
        resp = mock.Mock(status_code=400, json=lambda: {"detail": {"ok": False, "step": "Step 3"}})
        with mock.patch.object(wp.requests, "post", return_value=resp) as post:
            r = wp.run_case("PHONG", {"passportNumber": "E1"})
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:20000/run")
        self.assertEqual(post.call_args.kwargs["json"], {"passportNumber": "E1"})
        self.assertEqual((r["ok"], r["status_code"], r["house"]), (False, 400, "PHONG"))
        with self.assertRaises(wp.FormError):
            wp.run_case("PHONG", [])

    def test_steps(self):
        s = wp.make_step("classifying", "12 file", "2026-01-01T00:00:00+00:00")
        self.assertEqual((s["step"], s["label"]), ("classifying", "Đang phân loại tài liệu"))
        self.assertEqual([wp.step_status(x) for x in ("files_loaded", "done", "error")], ["running", "done", "error"])
        with self.assertRaises(wp.FormError):
            wp.make_step("hack")

    def test_upload_forwards_to_house_instance_with_exact_key(self):
        resp = mock.Mock(status_code=200, json=lambda: {"ok": True, "key": "L30 - Ánh/sub/hộ chiếu.jpg", "size": 3})
        with mock.patch.object(wp.requests, "post", return_value=resp) as post:
            r = wp.upload_file("phong", "L30 - Ánh", "sub/hộ chiếu.jpg", b"abc", "image/jpeg")
        self.assertTrue(r["ok"])
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:20000/r2/images")
        self.assertEqual(post.call_args.kwargs["data"]["key"], "L30 - Ánh/sub/hộ chiếu.jpg")
        for bad in ["", "../x.jpg", "a/../../b", "dir/"]:
            with self.assertRaises(wp.FormError, msg=bad):
                wp.upload_file("phong", "A", bad, b"x")
        with self.assertRaises(wp.FormError):
            wp.upload_file("phong", "A", "x.jpg", b"")

    def test_folder_stat(self):
        resp = mock.Mock(status_code=200, json=lambda: {"ok": True, "files": 3, "bytes": 10})
        with mock.patch.object(wp.requests, "post", return_value=resp) as post:
            self.assertEqual(wp.folder_stat("TAI", "A")["files"], 3)
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:30000/r2/folders/stat")


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
            mock.patch.object(self.server, "create_web_job", side_effect=lambda job, u, step: self.jobs.setdefault(job["job_id"], {"username": u, "staff": job["staff"], "steps": [step], "status": "running"})),
            mock.patch.object(self.server, "add_web_job_step", side_effect=self._add_step),
            mock.patch.object(self.server, "get_web_job", side_effect=lambda jid: self.jobs.get(jid) and {"job_id": jid, **self.jobs[jid]}),
            mock.patch.object(self.server.web_curl, "save_curl", side_effect=lambda e: self.saved.append(e) or len(self.saved)),
        ]
        self.saved = []
        self.jobs = {}
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

    def _add_step(self, job_id, step, status, curl=""):
        job = self.jobs.get(job_id)
        if not job or job["status"] != "running":
            return False
        job["steps"].append(step)
        job["status"] = status
        if curl:
            job["curl"] = curl
        return True

    def test_start_records_job_and_progress_flow(self):
        form = {"house": "HAI", "visa_code": "L", "days": "30", "source_prefix": "L30 - A"}
        with mock.patch.object(self.server, "start_case", side_effect=lambda c: {"ok": True, "job_id": c["job_id"]}):
            job_id = self.client.post("/web/start", json=form, headers={"X-Api-Key": "user-key"}).json()["job_id"]
        self.assertEqual(self.jobs[job_id]["steps"][0]["step"], "received")
        # n8n reports with the shared key only
        self.assertEqual(self.client.post("/web/progress", json={"job_id": job_id, "step": "classifying"}, headers={"X-Api-Key": "user-key"}).status_code, 401)
        r = self.client.post("/web/progress", json={"job_id": job_id, "step": "classifying", "message": "12 file"}, headers={"X-Api-Key": "shared"})
        self.assertEqual(r.json(), {"ok": True, "tracked": True})
        self.client.post("/web/progress", json={"job_id": job_id, "step": "done", "curl": "curl -X POST x -d '{}'"}, headers={"X-Api-Key": "shared"})
        self.assertEqual(self.jobs[job_id]["curl"], "curl -X POST x -d '{}'")
        # closed job does not take more steps; unknown job (started from WF-01) is ignored
        self.assertFalse(self.client.post("/web/progress", json={"job_id": job_id, "step": "error"}, headers={"X-Api-Key": "shared"}).json()["tracked"])
        self.assertFalse(self.client.post("/web/progress", json={"job_id": "job-wf01", "step": "done"}, headers={"X-Api-Key": "shared"}).json()["tracked"])
        j = self.client.get(f"/web/job/{job_id}", headers={"X-Api-Key": "user-key"}).json()["job"]
        self.assertEqual([s["step"] for s in j["steps"]], ["received", "classifying", "done"])
        self.assertEqual(j["status"], "done")

    def test_progress_with_staff_registers_wf01_run(self):
        body = {"job_id": "job-wf01", "step": "files_loaded", "message": "3 file", "staff": "long", "house": "tai",
                "visa_type": "L30", "source_prefix": "A/"}
        r = self.client.post("/web/progress", json=body, headers={"X-Api-Key": "shared"})
        self.assertEqual(r.json(), {"ok": True, "tracked": True})
        self.assertEqual((self.jobs["job-wf01"]["username"], self.jobs["job-wf01"]["staff"]), ("", "LONG"))
        self.assertEqual(self.server.create_web_job.call_args.args[0]["house"], "TAI")
        # a run from /web keeps its row (user, staff)
        form = {"house": "HAI", "visa_code": "L", "days": "30", "source_prefix": "L30 - A"}
        with mock.patch.object(self.server, "start_case", side_effect=lambda c: {"ok": True, "job_id": c["job_id"]}):
            job_id = self.client.post("/web/start", json=form, headers={"X-Api-Key": "user-key"}).json()["job_id"]
        self.client.post("/web/progress", json={**body, "job_id": job_id, "staff": "HANG"}, headers={"X-Api-Key": "shared"})
        self.assertEqual((self.jobs[job_id]["username"], self.jobs[job_id]["staff"]), ("bao", "BAO"))

    def test_run_owner_from_job_id(self):
        with mock.patch.object(self.server, "set_visa_registration_owner") as own, \
             mock.patch.object(self.server, "get_job_staff", side_effect=lambda j: {"job-1": "LONG"}.get(j, "")):
            self.server._save_owner(5, {"job_id": "job-1", "staff": "BAO"})  # job known: its staff wins
            self.assertEqual(own.call_args.args, (5, "LONG", "job-1"))
            self.server._save_owner(6, {"job_id": "job-x", "staff": "BAO"})  # unknown job: staff from /web/run
            self.assertEqual(own.call_args.args, (6, "BAO", "job-x"))
            own.reset_mock()
            self.server._save_owner(7, {"passportNumber": "E1"})  # old curl run from Postman: unknown
            self.server._save_owner(None, {"job_id": "job-1"})
            own.assert_not_called()

    def test_start_n8n_failure_marks_job_error(self):
        form = {"house": "HAI", "visa_code": "M", "days": "", "source_prefix": "A"}
        with mock.patch.object(self.server, "start_case", side_effect=RuntimeError("n8n down")):
            r = self.client.post("/web/start", json=form, headers={"X-Api-Key": "user-key"})
        self.assertEqual(r.status_code, 502)
        (job,) = self.jobs.values()
        self.assertEqual((job["status"], job["steps"][-1]["step"]), ("error", "error"))

    def test_job_of_other_user_hidden(self):
        self.jobs["job-x"] = {"username": "hang", "steps": [], "status": "running"}
        self.assertEqual(self.client.get("/web/job/job-x", headers={"X-Api-Key": "user-key"}).status_code, 404)

    def test_upload_endpoint(self):
        with mock.patch.object(self.server, "web_upload_file", return_value={"ok": True, "key": "A/x.jpg", "size": 3}) as up:
            r = self.client.post("/web/upload", data={"house": "HAI", "source_prefix": "A", "relative_path": "x.jpg"},
                                 files={"file": ("x.jpg", b"abc", "image/jpeg")}, headers={"X-Api-Key": "user-key"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(up.call_args.args[:4], ("HAI", "A", "x.jpg", b"abc"))
        r = self.client.post("/web/upload", data={"house": "HAI", "source_prefix": "A", "relative_path": "x.jpg"},
                             files={"file": ("x.jpg", b"abc", "image/jpeg")})
        self.assertEqual(r.status_code, 401)

    def test_web_run_endpoint(self):
        body = {"passportNumber": "E1"}
        self.assertEqual(self.client.post("/web/run", json={"port": "10000", "body": body}).status_code, 401)
        with mock.patch.object(self.server, "web_run_case", return_value={"ok": True, "status_code": 200, "house": "HAI", "response": {"ok": True}}) as rc:
            r = self.client.post("/web/run", json={"port": "10000", "body": body}, headers={"X-Api-Key": "user-key"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(rc.call_args.args, ("HAI", {**body, "staff": "BAO"}))  # counts for the person running it
        with mock.patch.object(self.server, "web_run_case", return_value={"ok": True, "status_code": 200, "house": "HAI", "response": {}}) as rc:
            self.client.post("/web/run", json={"port": "10000", "body": {**body, "staff": "HANG"}}, headers={"X-Api-Key": "user-key"})
        self.assertEqual(rc.call_args.args[1]["staff"], "HANG")  # staff from the curl (WF-13) is kept
        r = self.client.post("/web/run", json={"port": "8080", "body": body}, headers={"X-Api-Key": "user-key"})
        self.assertEqual(r.status_code, 400)

    def test_successful_run_goes_to_curl_history(self):
        body = {"passportNumber": "E1", "visa_type": "Q2180", "authorization": "secret-token"}
        ok = {"ok": True, "status_code": 200, "house": "TAI", "response": {"data": {"full_name": "NGUYEN VAN A"}}}
        with mock.patch.object(self.server, "web_run_case", return_value=ok):
            r = self.client.post("/web/run", json={"port": "30000", "body": body}, headers={"X-Api-Key": "user-key"})
        self.assertEqual(r.json()["history_id"], 1)
        e = self.saved[0]
        self.assertEqual((e["username"], e["house"], e["port"], e["passport_number"], e["full_name"], e["visa_type"]),
                         ("bao", "TAI", "30000", "E1", "NGUYEN VAN A", "Q2180"))
        self.assertEqual(e["body"]["authorization"], "")  # token never stored
        self.assertEqual(e["body"]["staff"], "BAO")
        bad = {"ok": False, "status_code": 500, "house": "TAI", "response": {"error": "x"}}
        with mock.patch.object(self.server, "web_run_case", return_value=bad):
            self.client.post("/web/run", json={"port": "30000", "body": body}, headers={"X-Api-Key": "user-key"})
        self.assertEqual(len(self.saved), 1)  # failed runs are not kept
        with mock.patch.object(self.server.web_curl, "save_curl", side_effect=RuntimeError("db down")),              mock.patch.object(self.server, "web_run_case", return_value=ok):
            r = self.client.post("/web/run", json={"port": "30000", "body": body}, headers={"X-Api-Key": "user-key"})
        self.assertEqual(r.status_code, 200)  # history failure never breaks the run

    def test_curl_history_own_or_all_for_admin(self):
        with mock.patch.object(self.server.web_curl, "list_curls", return_value=([], 0)) as lc:
            self.assertEqual(self.client.get("/web/curl-history").status_code, 401)
            r = self.client.get("/web/curl-history?q=E1", headers={"X-Api-Key": "user-key"})
            self.assertEqual(r.json()["keep_days"], 15)
            self.assertEqual(lc.call_args.args, ("bao", "E1", 10, 0))
            r = self.client.get("/web/curl-history?page=3", headers={"X-Api-Key": "user-key"})
            self.assertEqual(lc.call_args.args, ("bao", "", 10, 20))
            self.assertEqual((r.json()["page"], r.json()["total"]), (3, 0))
            admin = {"id": 9, "username": "boss", "staff_code": "ADMIN", "api_key": "admin-key"}
            with mock.patch.object(self.server, "get_web_user_by_api_key", side_effect=lambda k: admin if k == "admin-key" else None):
                self.client.get("/web/curl-history", headers={"X-Api-Key": "admin-key"})
                self.assertEqual(lc.call_args.args, (None, "", 10, 0))
                self.client.get("/web/curl-history?mine=1", headers={"X-Api-Key": "admin-key"})
                self.assertEqual(lc.call_args.args, ("boss", "", 10, 0))


if __name__ == "__main__":
    unittest.main()
