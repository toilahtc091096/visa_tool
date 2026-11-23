"""Behind Caddy (HTTPS): every request reaches the app from 127.0.0.1. uvicorn's proxy
headers (trusted 127.0.0.1 only, as server.py runs it) must give the real caller, so
the access guard, the login limit and the local-only /bio/* stay closed to the internet."""

import asyncio
import os
import sys
import types
import unittest
from unittest import mock

import httpx
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


class BehindProxyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
        import server
        cls.server = server
        cls.app = ProxyHeadersMiddleware(server.app, trusted_hosts="127.0.0.1")   # as uvicorn.run in server.py

    def setUp(self):
        p = mock.patch.dict(os.environ, {"ACCESS_GUARD": "enforce", "VISA_API_KEY": "shared",
                                         "BIO_LOGIN_URL": "https://bio/login", "BIO_USERNAME": "u", "BIO_PASSWORD": "p"})
        p.start()
        self.addCleanup(p.stop)

    def _get(self, path, peer, headers=None):
        async def go():
            transport = httpx.ASGITransport(app=self.app, client=(peer, 50000))
            async with httpx.AsyncClient(transport=transport, base_url="http://visa.example") as c:
                return await c.get(path, headers=headers or {})
        return asyncio.run(go())

    def test_internet_through_caddy_is_not_local(self):
        via_caddy = {"X-Forwarded-For": "203.0.113.7", "X-Forwarded-Proto": "https"}
        self.assertEqual(self._get("/r2/images/get?key=x", "127.0.0.1", via_caddy).status_code, 401)   # key needed
        self.assertEqual(self._get("/bio/credentials", "127.0.0.1", via_caddy).status_code, 401)        # guard first
        # even with the shared key, the house password never leaves the VPS
        with_key = {**via_caddy, "X-Api-Key": "shared"}
        self.assertEqual(self._get("/bio/credentials", "127.0.0.1", with_key).status_code, 403)
        self.assertEqual(self._get("/health", "127.0.0.1", via_caddy).status_code, 200)

    def test_forged_header_does_not_make_a_caller_local(self):
        # straight to the port from outside, claiming to be the VPS
        self.assertEqual(self._get("/bio/credentials", "198.51.100.9", {"X-Forwarded-For": "127.0.0.1"}).status_code, 401)
        # through Caddy with a forged first hop: the real (last untrusted) address is used
        forged = {"X-Forwarded-For": "127.0.0.1, 203.0.113.7"}
        self.assertEqual(self._get("/bio/credentials", "127.0.0.1", forged).status_code, 401)
        self.assertEqual(self._get("/bio/credentials", "127.0.0.1", {**forged, "X-Api-Key": "shared"}).status_code, 403)

    def test_vps_itself_is_still_local(self):
        r = self._get("/bio/credentials", "127.0.0.1")     # 10000 instance asking a house instance, no proxy
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["username"], "u")

    def test_userscript_gets_the_https_address(self):
        r = self._get("/web/visa-token.user.js", "127.0.0.1",
                      {"X-Forwarded-For": "203.0.113.7", "X-Forwarded-Proto": "https", "Host": "visa.example"})
        self.assertIn("const BASE = 'https://visa.example';", r.text)


if __name__ == "__main__":
    unittest.main()
