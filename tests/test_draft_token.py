"""Step get_draft: when the token cannot read the drafts / old information the run goes on
but returns a warning (before: COVA's Response.Error was dropped silently)."""
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

    def _flow(self, handler, first_applyid="APPLY-1"):
        ctx = _Ctx()
        ctx.warnings = []
        ctx.first_applyid = first_applyid

        async def go():
            async with _client(handler) as c:
                with mock.patch("utils.notify", new=mock.AsyncMock()),                      mock.patch.object(step, "full_name_from_ocr", return_value="NGUYEN VAN A"),                      mock.patch.object(step, "vietnamese_name_from_ocr", return_value="Nguyen Van A"):
                    return await step.load_draft_and_prepare_person(ctx, c)
        return _run(go()), ctx

    @staticmethod
    def _draft(draft_resp, info_resp=None):
        info_resp = info_resp or httpx.Response(200, json={"Response": {"Data": {"applyid": "APPLY-1"}}})

        def handler(r):
            return draft_resp if r.url.path.endswith("/GetDraftList") else info_resp
        return handler

    def test_expired_token_warns_and_goes_on(self):
        ok, ctx = self._flow(self._draft(httpx.Response(200, json=EXPIRED)))
        self.assertTrue(ok, ctx.error)
        self.assertEqual(len(ctx.warnings), 1)
        w = ctx.warnings[0]
        self.assertEqual(w["step"], "get_draft")
        self.assertIn("token", w["message"])
        self.assertIn("TokenExpired", w["message"])
        self.assertEqual(ctx.first_applyid, "APPLY-1")

    def test_http_401_warns(self):
        ok, ctx = self._flow(self._draft(httpx.Response(401, json={"message": "Unauthorized"})))
        self.assertTrue(ok, ctx.error)
        self.assertIn("HTTP 401", ctx.warnings[0]["message"])

    def test_no_data_warns(self):
        ok, ctx = self._flow(self._draft(httpx.Response(200, json={"Response": {"RequestId": "R"}})))
        self.assertTrue(ok, ctx.error)
        self.assertIn("không trả về Data", ctx.warnings[0]["message"])

    def test_old_info_unreadable_warns(self):
        handler = self._draft(httpx.Response(200, json={"Response": {"Data": {"list": []}}}),
                              httpx.Response(200, json=EXPIRED))
        ok, ctx = self._flow(handler)
        self.assertTrue(ok, ctx.error)
        self.assertEqual(ctx.warnings[0]["step"], "get_current_draft_personal_information")
        self.assertIn("APPLY-1", ctx.warnings[0]["message"])
        self.assertEqual(ctx.data_obj, {})

    def test_all_fine_no_warning(self):
        ok, ctx = self._flow(self._draft(httpx.Response(200, json={"Response": {"Data": {"list": []}}})))
        self.assertTrue(ok, ctx.error)
        self.assertEqual(ctx.warnings, [])


if __name__ == "__main__":
    unittest.main()
