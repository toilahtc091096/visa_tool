"""Mô phỏng luồng theo dõi trạng thái hồ sơ (không gọi DB/API/Zalo thật).

    python -m unittest tests.test_application_status_tracker
"""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import application_status_tracker as tracker  # noqa: E402


def _remote_row(applyid: str, status: str, update_time: str, passport: str = "E21321321") -> dict:
    return {
        "applyid": applyid,
        "passportNo": passport,
        "applyStatus": status,
        "alFormId": f"HAN{applyid}",
        "updateTime": update_time,
    }


def _tracking(**overrides) -> dict:
    row = {
        "id": 1,
        "passport_number": "E21321321",
        "first_applyid": "",
        "full_name": "",
        "initial_status": "",
        "current_status": "not_checked",
        "is_active": True,
        "group_id": "g1",
        "payload": {},
    }
    row.update(overrides)
    return row


class ParseTest(unittest.TestCase):
    def test_passports_only_from_valid_codes(self) -> None:
        self.assertEqual(
            tracker.parse_passport_numbers("E21321321,P12321321; e21321321 sđt 0912345678"),
            ["E21321321", "P12321321"],
        )
        self.assertEqual(tracker.parse_passport_numbers("ok chị, mai em gửi tiếp"), [])

    def test_token_and_done(self) -> None:
        self.assertEqual(tracker.parse_token_message("Token: abc.def"), "abc.def")
        self.assertEqual(tracker.parse_token_message("token hết hạn rồi"), "")
        self.assertTrue(tracker.is_done_message("xong"))
        self.assertTrue(tracker.is_done_message("xong rồi nhé"))
        self.assertTrue(tracker.is_done_message("E21321321 xong!"))
        self.assertFalse(tracker.is_done_message("chưa xong đâu"))


class PickRemoteRowTest(unittest.TestCase):
    rows = [
        _remote_row("A1", "审核通过", "2026-01-01 10:00:00"),
        _remote_row("A2", "初审中", "2026-10-20 09:00:00"),
    ]

    def test_match_by_first_applyid(self) -> None:
        row = tracker._pick_remote_row(self.rows, "E21321321", "A1", set())
        self.assertEqual(row["applyid"], "A1")
        self.assertIsNone(tracker._pick_remote_row(self.rows, "E21321321", "ZZ", set()))

    def test_newest_skips_finished_trip(self) -> None:
        self.assertEqual(
            tracker._pick_remote_row(self.rows, "E21321321", "", set())["applyid"], "A2"
        )
        self.assertIsNone(
            tracker._pick_remote_row(self.rows, "E21321321", "", {"A1", "A2"})
        )


class CheckOneTest(unittest.TestCase):
    def _run(self, tracking: dict, remote_rows: list[dict], registration: dict | None):
        async def fake_api(**_kwargs):
            return True, {"status_code": 200, "response": {"code": 200, "rows": remote_rows}}

        with mock.patch.object(tracker, "api_list_online_applications", fake_api), \
             mock.patch.object(tracker, "list_finished_tracking_applyids", return_value=set()), \
             mock.patch.object(tracker, "get_visa_registration_by_passport", return_value=registration), \
             mock.patch.object(tracker, "update_tracking", side_effect=lambda _id, f: {**tracking, **f}):
            return asyncio.run(
                tracker._check_one(None, asyncio.Semaphore(1), tracking, "t", "s", "auth")
            )

    def test_first_check_sets_initial_status_without_notify(self) -> None:
        result = self._run(
            _tracking(),
            [_remote_row("A2", "初审中", "2026-10-20 09:00:00")],
            {"first_applyid": "A2", "full_name": "NGUYEN VAN A"},
        )
        row = result["tracking"]
        self.assertIsNone(result["change"])
        self.assertEqual(row["initial_status"], "under_review")
        self.assertEqual(row["current_status"], "under_review")
        self.assertEqual(row["full_name"], "NGUYEN VAN A")
        self.assertTrue(row["is_active"])

    def test_under_review_to_approved_notifies_and_stops_tracking(self) -> None:
        result = self._run(
            _tracking(first_applyid="A2", initial_status="under_review", current_status="under_review", full_name="X"),
            [_remote_row("A2", "审核通过", "2026-10-22 14:12:00")],
            None,
        )
        change = result["change"]
        self.assertEqual((change["from"], change["to"]), ("under_review", "approved"))
        self.assertFalse(result["tracking"]["is_active"])
        message = tracker._format_change_message(result["tracking"], change)
        print("\n--- tin nhắn nhóm ---\n" + message)
        self.assertIn("Under review → Approved", message)
        self.assertIn("2026-10-22 14:12:00", message)

    def test_token_error_in_response(self) -> None:
        async def fake_api(**_kwargs):
            return True, {"status_code": 200, "response": {"code": 401, "msg": "token expired"}}

        with mock.patch.object(tracker, "api_list_online_applications", fake_api):
            result = asyncio.run(
                tracker._check_one(None, asyncio.Semaphore(1), _tracking(), "t", "s", "a")
            )
        self.assertIn("401", result["token_error"])


class BatchTest(unittest.TestCase):
    def test_skip_active_and_add_new(self) -> None:
        active = _tracking(id=9, passport_number="P12321321", current_status="under_review")
        created = _tracking(id=10, passport_number="E21321321")
        sent: list[str] = []

        async def fake_check(trackings):
            return {
                "ok": True,
                "results": [
                    {"tracking": {**row, "current_status": "under_review"}, "change": None}
                    for row in trackings
                ],
            }

        async def fake_notify(text, group_id=""):
            sent.append(text)
            return {"ok": True}

        with mock.patch.object(
            tracker, "get_active_tracking_by_passport",
            side_effect=lambda p: active if p == "P12321321" else None,
        ), mock.patch.object(tracker, "create_tracking", return_value=created), \
             mock.patch.object(tracker, "_check_trackings", fake_check), \
             mock.patch.object(tracker, "sync_trackings_to_sheet", return_value={"ok": True}), \
             mock.patch.object(tracker, "notify_group", fake_notify):
            result = asyncio.run(
                tracker.process_passport_batch(["E21321321", "P12321321"], "g1", "u1", "Chị A")
            )

        self.assertEqual(result["added"], ["E21321321"])
        self.assertEqual(result["skipped"], ["P12321321"])
        print("\n--- trả lời nhóm ---\n" + sent[0])


class InboxTest(unittest.TestCase):
    def test_buffer_then_flush_on_done(self) -> None:
        calls: list[tuple] = []

        async def fake_run_in_thread(func, *args):
            calls.append((func.__name__, args))
            return {}

        async def scenario():
            inbox = tracker.ZaloInbox()
            base = {"thread_id": "g1", "sender_id": "u1", "sender_name": "Chị A"}
            self.assertEqual(inbox.handle({**base, "text": "chào cả nhà"})["action"], "ignored")
            self.assertEqual(inbox.handle({**base, "text": "E21321321,P12321321"})["action"], "buffered")
            inbox.handle({**base, "text": "e21321321; C1234567"})
            self.assertEqual(inbox.handle({**base, "text": "xong"})["action"], "flush")
            self.assertEqual(inbox.handle({**base, "sender_id": "u2", "text": "token: abc"})["action"], "token")
            await asyncio.sleep(0.05)

        with mock.patch.object(tracker, "_run_in_thread", fake_run_in_thread), \
             mock.patch.dict("os.environ", {"TRACKER_ZALO_GROUP_ID": "g1", "TRACKER_ZALO_SENDER_IDS": "u1"}):
            asyncio.run(scenario())

        self.assertEqual(calls[0][0], "process_passport_batch")
        self.assertEqual(calls[0][1][0], ["E21321321", "P12321321", "C1234567"])
        self.assertEqual(calls[1], ("update_authorization", ("abc", "g1", "Chị A")))

    def test_sender_not_allowed_cannot_add_passports(self) -> None:
        with mock.patch.dict("os.environ", {"TRACKER_ZALO_SENDER_IDS": "u1"}):
            result = tracker.ZaloInbox().handle(
                {"thread_id": "g1", "sender_id": "u9", "text": "E21321321"}
            )
        self.assertEqual(result["reason"], "sender_not_allowed")


if __name__ == "__main__":
    unittest.main()
