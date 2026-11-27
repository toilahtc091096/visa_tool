"""ADMIN sync buttons: /sync/start + /sync/status on a house, /web/admin/sync on the web."""
import sys
import threading
import types
import unittest
from unittest import mock

sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))

FAKE_RESULT = {
    "ok": True, "total": 4, "matched": 3, "updated": 2, "skipped": 1, "display_only": 0,
    "items": [{"ok": True}, {"ok": False, "reason": "missing_first_applyid"}],
}


class SyncEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        import server
        cls.server = server
        cls.client = TestClient(server.app)

    def setUp(self):
        # the local .env may enforce the access guard: the test client is not 127.0.0.1
        env = mock.patch.dict("os.environ", {"ACCESS_GUARD": "off"})
        env.start()
        self.addCleanup(env.stop)
        self.server._sync_after_run_state.update(running=False, pending=False, source="", started_at="", last=None)

    def _local(self, yes=True):
        return mock.patch.object(self.server, "_is_local_request", return_value=yes)

    def _enabled(self, yes=True):
        return mock.patch.object(self.server, "_is_sync_draft_enabled", return_value=yes)

    def test_local_only(self):
        with self._local(False):
            self.assertEqual(self.client.get("/sync/status").status_code, 403)
            self.assertEqual(self.client.post("/sync/start").status_code, 403)

    def test_disabled_house_says_so(self):
        with self._local(), self._enabled(False):
            r = self.client.post("/sync/start")
        self.assertEqual(r.status_code, 400)
        self.assertIn("SYNC_DRAFT_ENABLED", r.json()["detail"]["error"])

    def test_start_runs_and_keeps_last_result(self):
        done = threading.Event()

        async def fake_sync(**kwargs):
            return FAKE_RESULT

        real_record = self.server._record_sync

        def record(summary):
            real_record(summary)
            done.set()

        with self._local(), self._enabled(), \
             mock.patch.object(self.server, "sync_draft_visa_registrations", side_effect=fake_sync), \
             mock.patch.object(self.server, "_record_sync", side_effect=record):
            r = self.client.post("/sync/start").json()
            self.assertTrue(r["started"])
            self.assertTrue(done.wait(5))
            for _ in range(50):  # the worker clears "running" right after recording
                if not self.server._sync_after_run_state["running"]:
                    break
                threading.Event().wait(0.02)
            s = self.client.get("/sync/status").json()
        self.assertFalse(s["running"])
        last = s["last"]
        self.assertEqual((last["source"], last["ok"], last["updated"], last["total"]), ("admin", True, 2, 4))
        self.assertEqual(last["skip_reasons"], {"missing_first_applyid": 1})

    def test_second_press_while_running_is_queued(self):
        self.server._sync_after_run_state.update(running=True, source="scheduler")
        with self._local(), self._enabled():
            r = self.client.post("/sync/start").json()
        self.assertEqual((r["started"], r["queued"]), (False, True))
        self.assertTrue(self.server._sync_after_run_state["pending"])
        self.server._sync_after_run_state.update(running=False, pending=False)

    def test_failed_sync_is_shown(self):
        s = self.server._sync_summary(None, "admin", "2026-01-01 00:00:00", 1.0, error="RuntimeError: boom")
        self.assertFalse(s["ok"])
        self.assertEqual(s["error"], "RuntimeError: boom")

    def test_web_admin_sync_asks_every_house(self):
        with mock.patch.object(self.server, "_web_admin", return_value={"staff_code": "ADMIN"}), \
             mock.patch.object(self.server.web_portal, "sync_status", side_effect=lambda h: {"ok": True, "running": h == "TAI"}):
            d = self.client.get("/web/admin/sync").json()
        self.assertEqual([h["house"] for h in d["houses"]], list(self.server.WEB_HOUSES))
        self.assertTrue(next(h for h in d["houses"] if h["house"] == "TAI")["running"])

    def test_web_admin_sync_start_and_bad_house(self):
        with mock.patch.object(self.server, "_web_admin", return_value={"staff_code": "ADMIN"}), \
             mock.patch.object(self.server.web_portal, "sync_start", return_value={"ok": True, "started": True}) as start:
            d = self.client.post("/web/admin/sync/phong").json()
        start.assert_called_once_with("PHONG")
        self.assertEqual((d["house"], d["started"]), ("PHONG", True))
        with mock.patch.object(self.server, "_web_admin", return_value={"staff_code": "ADMIN"}):
            r = self.client.post("/web/admin/sync/NOPE")
        self.assertEqual(r.status_code, 400)


class WebPortalSyncTest(unittest.TestCase):
    def test_status_never_raises(self):
        import services.web_portal as wp
        with mock.patch.object(wp.requests, "get", side_effect=wp.requests.ConnectionError("down")):
            s = wp.sync_status("HAI")
        self.assertFalse(s["ok"])
        self.assertIn("HAI", s["error"])

    def test_start_calls_house_port(self):
        import services.web_portal as wp
        resp = mock.Mock(status_code=200, json=lambda: {"ok": True, "started": True})
        with mock.patch.object(wp.requests, "post", return_value=resp) as post:
            self.assertTrue(wp.sync_start("TAI")["started"])
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:30000/sync/start")


if __name__ == "__main__":
    unittest.main()
