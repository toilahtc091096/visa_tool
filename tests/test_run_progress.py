import asyncio
import sys
import types
import unittest
from unittest import mock

sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
from utils import run_progress as rp  # noqa: E402  (after the weasyprint stub: utils imports it)


class RunProgressTest(unittest.TestCase):
    def test_phases_and_finish(self):
        rp.begin("run-abc123")
        token = rp.current_run_id.set("run-abc123")
        try:
            ctx = types.SimpleNamespace(step="get ocr")
            rp.phase_start("token_ocr", ctx)
            s = rp.snapshot("run-abc123")
            self.assertEqual((s["status"], s["phase"], s["step"], s["done"]), ("running", "token_ocr", "get ocr", []))
            ctx.step = "get_draft"   # the step is read live from ctx
            self.assertEqual(rp.snapshot("run-abc123")["step"], "get_draft")
            rp.phase_end("token_ocr", 3.5)
            s = rp.snapshot("run-abc123")
            self.assertEqual((s["phase"], s["step"], s["done"]), ("", "", [["token_ocr", 3.5]]))
        finally:
            rp.current_run_id.reset(token)
        rp.finish("run-abc123", False)
        self.assertEqual(rp.snapshot("run-abc123")["status"], "error")

    def test_no_run_id_records_nothing(self):
        rp.phase_start("validate")   # no current run id: ignored
        self.assertIsNone(rp.snapshot("unknown-run"))
        self.assertEqual(rp.valid_run_id("../x"), "")
        self.assertEqual(rp.valid_run_id("r1abcdef"), "r1abcdef")

    def test_run_id_reaches_the_flow_through_asyncio_run(self):
        # /run sets the context var, main() calls asyncio.run: the flow must still see it
        rp.begin("run-ctx0001")
        token = rp.current_run_id.set("run-ctx0001")
        try:
            async def flow():
                rp.phase_start("validate")
            asyncio.run(flow())
        finally:
            rp.current_run_id.reset(token)
        self.assertEqual(rp.snapshot("run-ctx0001")["phase"], "validate")


class RunProgressEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
        from fastapi.testclient import TestClient
        import server
        cls.server = server
        cls.client = TestClient(server.app)

    def test_run_records_progress_and_strips_run_id(self):
        seen = {}

        def fake_run_case(payload):
            seen["payload"] = dict(payload)
            rp.phase_start("validate")
            rp.phase_end("validate", 0.1)
            return self.server.JSONResponse(status_code=200, content={"ok": True})

        with mock.patch.object(self.server, "_run_case", side_effect=fake_run_case):
            r = self.client.post("/run", json={"passportNumber": "E1", "run_id": "web-run-001"})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("run_id", seen["payload"])
        p = self.client.get("/run/progress/web-run-001").json()
        self.assertEqual((p["status"], p["done"]), ("done", [["validate", 0.1]]))
        self.assertEqual(self.client.get("/run/progress/nope-0000").status_code, 404)

    def test_web_run_forwards_run_id(self):
        import services.web_portal as wp
        resp = mock.Mock(status_code=200, json=lambda: {"ok": True})
        with mock.patch.object(wp.requests, "post", return_value=resp) as post:
            wp.run_case("PHONG", {"passportNumber": "E1"}, "web-run-002")
        self.assertEqual(post.call_args.kwargs["json"], {"passportNumber": "E1", "run_id": "web-run-002"})
        with mock.patch.object(wp.requests, "get", return_value=mock.Mock(status_code=404)):
            self.assertEqual(wp.run_progress("PHONG", "web-run-002"), {"ok": True, "found": False})


if __name__ == "__main__":
    unittest.main()
