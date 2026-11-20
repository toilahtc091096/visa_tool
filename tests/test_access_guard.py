import os
import sys
import types
import unittest
from unittest import mock

from utils.access_guard import GuardConfig, decide

CFG = GuardConfig(
    mode="enforce",
    public_paths=("/health",),
    key_paths=("/",),
    local_ips=("127.0.0.1", "::1"),
    api_key="secret-key",
)


class DecideTest(unittest.TestCase):
    def test_local_can_call_anything_without_key(self):
        for path in ["/r2/images/delete", "/r2/folders/download", "/run", "/visa-registrations/sync-draft-status"]:
            self.assertTrue(decide(CFG, path, "127.0.0.1", "").allowed, path)

    def test_outside_with_key_can_call_anything(self):
        # n8n on Railway and staff curl both come from outside with the key
        for path in ["/run", "/r2/images", "/r2/folders/archive", "/upload-html-to-pdf", "/convert-input-pdfs"]:
            self.assertTrue(decide(CFG, path, "34.1.2.3", "secret-key").allowed, path)

    def test_outside_without_or_bad_key_is_blocked(self):
        for key in ["", "wrong", "secret-key "]:
            d = decide(CFG, "/r2/folders/download", "34.1.2.3", key)
            self.assertEqual((d.allowed, d.status), (False, 401), key)

    def test_no_configured_key_blocks_outside(self):
        cfg = GuardConfig("enforce", ("/health",), ("/",), ("127.0.0.1",), "")
        self.assertFalse(decide(cfg, "/run", "34.1.2.3", "").allowed)

    def test_health_is_public_and_public_prefix_is_exact(self):
        self.assertTrue(decide(CFG, "/health", "34.1.2.3", "").allowed)
        self.assertFalse(decide(CFG, "/healthz", "34.1.2.3", "").allowed)

    def test_key_paths_can_be_narrowed(self):
        cfg = GuardConfig("enforce", ("/health",), ("/run",), ("127.0.0.1",), "k")
        self.assertTrue(decide(cfg, "/run", "34.1.2.3", "k").allowed)
        d = decide(cfg, "/r2/images/delete", "34.1.2.3", "k")
        self.assertEqual((d.allowed, d.status), (False, 403))

    def test_from_env(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = GuardConfig.from_env()
        self.assertEqual((cfg.mode, cfg.key_paths, cfg.public_paths), ("off", ("/",), ("/health", "/web")))
        env = {"ACCESS_GUARD": "ENFORCE", "VISA_API_KEY": "k", "ACCESS_PUBLIC_PATHS": "/health,/han-approval"}
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = GuardConfig.from_env()
        self.assertEqual(cfg.mode, "enforce")
        self.assertTrue(decide(cfg, "/han-approval/process", "34.1.2.3", "").allowed)
        self.assertTrue(decide(cfg, "/run", "34.1.2.3", "k").allowed)


class MiddlewareTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
        from fastapi.testclient import TestClient
        import server
        cls.client = TestClient(server.app)  # client host is "testclient" (= outside)

    def env(self, **kw):
        base = {"ACCESS_GUARD": "enforce", "VISA_API_KEY": "secret-key", "ACCESS_LOCAL_IPS": "127.0.0.1"}
        base.update(kw)
        return mock.patch.dict(os.environ, base)

    def test_enforce_blocks_without_key(self):
        with self.env():
            r = self.client.get("/r2/images/get", params={"key": "x"})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"], "missing_or_bad_api_key")

    def test_enforce_passes_with_key(self):
        with self.env():
            r = self.client.post("/r2/images/delete", json={}, headers={"X-Api-Key": "secret-key"})
        self.assertNotIn(r.status_code, (401, 403))  # reaches handler (400 missing key/prefix)

    def test_health_open(self):
        with self.env():
            self.assertEqual(self.client.get("/health").status_code, 200)

    def test_log_mode_does_not_block(self):
        with self.env(ACCESS_GUARD="log"):
            r = self.client.post("/r2/images/delete", json={})
        self.assertNotIn(r.status_code, (401, 403))

    def test_off_by_default(self):
        with mock.patch.dict(os.environ, {"ACCESS_GUARD": ""}):
            r = self.client.post("/r2/images/delete", json={})
        self.assertNotIn(r.status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
