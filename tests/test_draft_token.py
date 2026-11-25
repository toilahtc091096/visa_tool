"""Step get_draft: an expired token must stop the run with a clear message
(before: COVA's Response.Error was dropped, the run made a new profile and lost the old information)."""
import asyncio
import sys
import unittest
from pathlib import Path
from unittest import mock

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.draft import api_get_draft  # noqa: E402
from flows.flow_step import step_03_draft_person as step  # noqa: E402
from models import GetDraftListBody  # noqa: E402

EXPIRED = {"Response": {"Error": {"Code": "AuthFailure.TokenExpired", "Message": "token expired"}}}


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class _Ctx:
    def __init__(self):
        self.token, self.tmp_secret, self.first_applyid = "t", "s", ""
        self.step, self.error, self.ocr_data = "", None, None


def _run(coro):
    return asyncio.run(coro)


class DraftTokenTest(unittest.TestCase):
    def test_api_keeps_business_error(self):
        async def go():
            async with _client(lambda r: httpx.Response(200, json=EXPIRED)) as c:
                return await api_get_draft(c, "t", "s", GetDraftListBody())
        ok, meta = _run(go())
        self.assertTrue(ok)
        self.assertEqual(meta["response"]["Response"]["Error"]["Code"], "AuthFailure.TokenExpired")

    def test_api_ok_list_unchanged(self):
        body = {"Response": {"Data": {"list": [{"name": "NGUYEN VAN A", "applyid": "A1"}]}}}

        async def go():
            async with _client(lambda r: httpx.Response(200, json=body)) as c:
                return await api_get_draft(c, "t", "s", GetDraftListBody())
        ok, meta = _run(go())
        self.assertTrue(ok)
        self.assertNotIn("Error", meta["response"]["Response"])
        self.assertNotIn("_no_data", meta["response"]["Response"])
        self.assertEqual(meta["response"]["Response"]["Data"]["list"][0]["applyid"], "A1")

    def _flow(self, handler):
        ctx = _Ctx()

        async def go():
            async with _client(handler) as c:
                with mock.patch("utils.notify", new=mock.AsyncMock()):
                    return await step.load_draft_and_prepare_person(ctx, c)
        return _run(go()), ctx

    def test_flow_stops_on_expired_token(self):
        calls = []

        def handler(r):
            calls.append(r.url.path)
            return httpx.Response(200, json=EXPIRED)
        ok, ctx = self._flow(handler)
        self.assertFalse(ok)
        self.assertEqual(ctx.error["step"], "get_draft")
        self.assertIn("token", ctx.error["error"])
        self.assertIn("TokenExpired", ctx.error["error"])
        self.assertFalse(any(p.endswith("/SavePersonInfo") for p in calls), "must not create a new profile")

    def test_flow_stops_on_http_401(self):
        ok, ctx = self._flow(lambda r: httpx.Response(401, json={"message": "Unauthorized"}))
        self.assertFalse(ok)
        self.assertIn("HTTP 401", ctx.error["error"])

    def test_flow_stops_when_no_data(self):
        ok, ctx = self._flow(lambda r: httpx.Response(200, json={"Response": {"RequestId": "R"}}))
        self.assertFalse(ok)
        self.assertIn("không trả về Data", ctx.error["error"])

    def test_flow_stops_when_old_info_unreadable(self):
        def handler(r):
            if r.url.path.endswith("/GetDraftList"):
                return httpx.Response(200, json={"Response": {"Data": {"list": []}}})
            return httpx.Response(200, json=EXPIRED)  # GetPersonInfo
        ctx = _Ctx()
        ctx.first_applyid = "APPLY-1"
        with mock.patch.object(step, "full_name_from_ocr", return_value="NGUYEN VAN A"), \
             mock.patch.object(step, "vietnamese_name_from_ocr", return_value="Nguyễn Văn A"):
            async def go():
                async with _client(handler) as c:
                    with mock.patch("utils.notify", new=mock.AsyncMock()):
                        return await step.load_draft_and_prepare_person(ctx, c)
            ok = _run(go())
        self.assertFalse(ok)
        self.assertEqual(ctx.error["step"], "get_current_draft_personal_information")
        self.assertIn("APPLY-1", ctx.error["error"])


if __name__ == "__main__":
    unittest.main()
