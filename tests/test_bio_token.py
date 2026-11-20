"""Bio token: /web "Lấy token" + Tampermonkey script (services/bio_token.py)."""

import os
import sys
import time
import types
import unittest
from unittest import mock

from services import bio_token


class CheckAuthorizationTest(unittest.TestCase):
    def _resp(self, status, data):
        r = mock.Mock(status_code=status)
        r.json.return_value = data
        return r

    def test_valid_and_invalid(self):
        with mock.patch.object(bio_token.requests, "post", return_value=self._resp(200, {"code": 200, "rows": []})) as post:
            self.assertEqual(bio_token.check_authorization("Bearer eyJabc"), (True, "Token hợp lệ"))
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "eyJabc")  # "Bearer " dropped
        with mock.patch.object(bio_token.requests, "post", return_value=self._resp(200, {"code": 401, "msg": "expired"})):
            ok, msg = bio_token.check_authorization("eyJold")
        self.assertFalse(ok)
        self.assertIn("401", msg)
        self.assertEqual(bio_token.check_authorization(""), (False, "Token rỗng"))

    def test_network_error(self):
        with mock.patch.object(bio_token.requests, "post", side_effect=bio_token.requests.ConnectionError("down")):
            ok, msg = bio_token.check_authorization("eyJx")
        self.assertFalse(ok)
        self.assertIn("down", msg)


class TicketTest(unittest.TestCase):
    def test_lifecycle_and_expiry(self):
        t = bio_token.new_ticket("bao", "HAI", "https://bio/login")
        self.assertEqual(bio_token.get_ticket(t)["house"], "HAI")
        bio_token.set_ticket_state(t, "done", "ok")
        self.assertIsNone(bio_token.get_ticket(t))  # done: no more credentials / token
        self.assertEqual(bio_token.ticket_status(t)["state"], "done")
        old = bio_token.new_ticket("bao", "TAI", "u")
        bio_token._tickets[old]["created"] = time.time() - bio_token.TICKET_TTL - 1
        self.assertIsNone(bio_token.get_ticket(old))
        self.assertEqual(bio_token.ticket_status(old)["state"], "expired")
        self.assertIsNone(bio_token.get_ticket("nope"))

    def test_userscript(self):
        js = bio_token.userscript("http://160.250.5.191:10000/")
        self.assertIn("// @match        https://*.visaforchina.cn/*", js)
        self.assertIn("// @match        http://160.250.5.191/*", js)  # no port: not matched by every version
        for value, token in [("https://bio.visaforchina.cn/x?site=HAN4_VI&token=eyJa.b.c&username=a", "eyJa.b.c"),
                             ("curl -H 'Authorization: eyJa.b.c' -H 'X: y'", "eyJa.b.c"), (" eyJa.b.c ", "eyJa.b.c"),
                             ("xin chao", "")]:
            self.assertEqual(bio_token.extract_token(value), token, value)
        self.assertIn("// @connect      160.250.5.191", js)
        self.assertIn("const BASE = 'http://160.250.5.191:10000';", js)
        self.assertNotIn("__", js.replace("__proto__", ""))


class BioEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
        from fastapi.testclient import TestClient
        import server
        cls.server = server
        cls.client = TestClient(server.app)

    def setUp(self):
        users = {"bao-key": {"username": "bao", "staff_code": "BAO"}, "hang-key": {"username": "hang", "staff_code": "HANG"}}
        self.cred = {"ok": True, "login_url": "https://bio.visaforchina.cn/login", "username": "a@b.com", "password": "pw"}
        p = [
            mock.patch.dict(os.environ, {"ACCESS_GUARD": "enforce", "VISA_API_KEY": "shared"}),
            mock.patch.object(self.server, "get_web_user_by_api_key", side_effect=users.get),
            mock.patch.object(self.server.web_portal, "bio_credentials", side_effect=lambda h: dict(self.cred)),
        ]
        for x in p:
            x.start()
            self.addCleanup(x.stop)

    def test_full_flow(self):
        r = self.client.post("/web/bio/start", json={"house": "phong"}, headers={"X-Api-Key": "bao-key"})
        self.assertEqual(r.status_code, 200, r.text)
        d = r.json()
        self.assertEqual(d["house"], "PHONG")
        self.assertEqual(d["open_url"], f"https://bio.visaforchina.cn/login#visa_tool={d['ticket']}")
        t = d["ticket"]
        # the userscript (no user key) gets the account with the ticket
        acc = self.client.get(f"/web/bio/ticket/{t}").json()
        self.assertEqual((acc["house"], acc["username"], acc["password"]), ("PHONG", "a@b.com", "pw"))
        # a token the bio site does not accept: still waiting
        with mock.patch.object(self.server.web_portal, "bio_save_authorization", return_value={"ok": False, "error": "Token không dùng được"}):
            self.assertEqual(self.client.post(f"/web/bio/ticket/{t}/token", json={"authorization": "eyJold"}).status_code, 400)
        st = self.client.get(f"/web/bio/ticket/{t}/status", headers={"X-Api-Key": "bao-key"}).json()
        self.assertEqual(st["state"], "waiting")
        with mock.patch.object(self.server.web_portal, "bio_save_authorization", return_value={"ok": True}) as save:
            r = self.client.post(f"/web/bio/ticket/{t}/token", json={"authorization": "eyJnew"})
        self.assertEqual(r.json(), {"ok": True, "house": "PHONG"})
        self.assertEqual(save.call_args.args, ("PHONG", "eyJnew"))
        st = self.client.get(f"/web/bio/ticket/{t}/status", headers={"X-Api-Key": "bao-key"}).json()
        self.assertEqual(st["state"], "done")
        # used ticket: no credentials anymore; other users cannot see its status
        self.assertEqual(self.client.get(f"/web/bio/ticket/{t}").status_code, 404)
        self.assertEqual(self.client.get(f"/web/bio/ticket/{t}/status", headers={"X-Api-Key": "hang-key"}).status_code, 404)

    def test_start_needs_login_and_account(self):
        self.assertEqual(self.client.post("/web/bio/start", json={"house": "HAI"}).status_code, 401)
        self.assertEqual(self.client.post("/web/bio/start", json={"house": "XYZ"}, headers={"X-Api-Key": "bao-key"}).status_code, 400)
        self.cred = {"ok": False, "error": "Thiếu biến trong .env của nhà: BIO_PASSWORD"}
        r = self.client.post("/web/bio/start", json={"house": "HAI"}, headers={"X-Api-Key": "bao-key"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("BIO_PASSWORD", r.json()["detail"]["error"])

    def test_house_endpoints_are_not_open_from_outside(self):
        # credentials: only from the VPS itself, even with the shared key
        self.assertEqual(self.client.get("/bio/credentials", headers={"X-Api-Key": "shared"}).status_code, 403)
        self.assertEqual(self.client.post("/bio/authorization", json={"authorization": "x"}).status_code, 401)

    def test_save_authorization_checks_then_stores(self):
        with mock.patch.object(self.server.bio_token, "check_authorization", return_value=(True, "Token hợp lệ")), \
             mock.patch.object(self.server, "append_authorization") as app_:
            r = self.client.post("/bio/authorization", json={"authorization": "Bearer eyJnew"}, headers={"X-Api-Key": "shared"})
        self.assertEqual(r.status_code, 200, r.text)
        app_.assert_called_once_with("eyJnew")
        with mock.patch.object(self.server.bio_token, "check_authorization", return_value=(False, "hết hạn")), \
             mock.patch.object(self.server, "append_authorization") as app_:
            r = self.client.post("/bio/authorization", json={"authorization": "eyJold"}, headers={"X-Api-Key": "shared"})
        self.assertEqual(r.status_code, 400)
        app_.assert_not_called()  # a bad token never replaces the stored one

    def test_current_token(self):
        self.assertEqual(self.client.get("/bio/authorization/current", headers={"X-Api-Key": "shared"}).status_code, 403)
        self.assertEqual(self.client.get("/web/bio/token?house=HAI").status_code, 401)
        with mock.patch.object(self.server.web_portal, "bio_current_authorization", return_value={"ok": True, "authorization": "eyJcur"}):
            r = self.client.get("/web/bio/token?house=hai", headers={"X-Api-Key": "bao-key"})
        self.assertEqual(r.json(), {"ok": True, "house": "HAI", "authorization": "eyJcur"})

    def test_run_authorization(self):
        s = self.server
        with mock.patch.object(s, "load_authorization", return_value="eyJstored"), \
             mock.patch.object(s, "append_authorization") as save, \
             mock.patch.object(s.bio_token, "check_authorization", return_value=(False, "expired")) as check:
            # empty: unchanged (main() loads the stored token)
            self.assertEqual(s._authorization_for_run({"authorization": ""}), {"authorization": ""})
            # same as stored: no check
            self.assertEqual(s._authorization_for_run({"authorization": "eyJstored"})["authorization"], "eyJstored")
            check.assert_not_called()
            # an old token in an old curl: refused, the stored one is used and kept
            self.assertEqual(s._authorization_for_run({"authorization": "eyJold", "x": 1}), {"authorization": "eyJstored", "x": 1})
            save.assert_not_called()
        with mock.patch.object(s, "load_authorization", return_value="eyJstored"), \
             mock.patch.object(s, "append_authorization") as save, \
             mock.patch.object(s.bio_token, "check_authorization", return_value=(True, "ok")):
            # a newer valid token pasted in the curl: used and stored
            self.assertEqual(s._authorization_for_run({"authorization": "Bearer eyJnew"})["authorization"], "eyJnew")
            save.assert_called_once_with("eyJnew")
        with mock.patch.object(s, "load_authorization", return_value=""), \
             mock.patch.object(s, "append_authorization") as save, \
             mock.patch.object(s.bio_token, "check_authorization") as check:
            # nothing stored yet: as before, stored without a check
            s._authorization_for_run({"authorization": "eyJfirst"})
            save.assert_called_once_with("eyJfirst")
            check.assert_not_called()

    def test_manual_paste(self):
        url = "https://bio.visaforchina.cn/onlineWeb/x?site=HAN4_VI&token=eyJa.b.c&username=a"
        self.assertEqual(self.client.post("/web/bio/manual", json={"house": "TAI", "value": url}).status_code, 401)
        with mock.patch.object(self.server.web_portal, "bio_save_authorization", return_value={"ok": True}) as save:
            r = self.client.post("/web/bio/manual", json={"house": "tai", "value": url}, headers={"X-Api-Key": "bao-key"})
        self.assertEqual(r.json(), {"ok": True, "house": "TAI"})
        self.assertEqual(save.call_args.args, ("TAI", "eyJa.b.c"))
        r = self.client.post("/web/bio/manual", json={"house": "TAI", "value": "abc"}, headers={"X-Api-Key": "bao-key"})
        self.assertEqual(r.status_code, 400)

    def test_userscript_served(self):
        r = self.client.get("/web/visa-token.user.js")
        self.assertEqual(r.status_code, 200)
        self.assertIn("==UserScript==", r.text)
        self.assertIn("http://testserver/web/visa-token.user.js", r.text)


if __name__ == "__main__":
    unittest.main()
