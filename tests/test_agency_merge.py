"""South: small idle agencies merged into CHUNG (DB + agency sheet).

    python -m unittest tests.test_agency_merge
"""

from __future__ import annotations

import re
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object, CSS=object))

from database.crud import agency as agency_crud  # noqa: E402
from services import agency_merge, agency_sheets  # noqa: E402


def _cell(ref: str) -> tuple[int, int]:
    m = re.match(r"([A-Z]+)(\d+)", ref)
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return int(m.group(2)) - 1, col - 1


class FakeWorksheet:
    def __init__(self, title, values):
        self.title = title
        self.values = [list(r) for r in values]
        self.row_count, self.col_count = 1000, 26

    def get_all_values(self):
        return [list(r) for r in self.values]

    def _set(self, r, c, v):
        while len(self.values) <= r:
            self.values.append([])
        row = self.values[r]
        while len(row) <= c:
            row.append("")
        row[c] = v

    def batch_update(self, updates, value_input_option=None):
        for u in updates:
            start = u["range"].split(":")[0]
            r, c = _cell(start)
            for i, row in enumerate(u["values"]):
                for j, v in enumerate(row):
                    self._set(r + i, c + j, v)

    def update(self, values, range_name, value_input_option=None):
        self.batch_update([{"range": range_name, "values": values}])

    def add_cols(self, n):
        self.col_count += n

    def add_rows(self, n):
        self.row_count += n

    def insert_row(self, row, index, value_input_option=None):
        self.values.insert(index - 1, list(row))

    def delete_rows(self, row_num):
        del self.values[row_num - 1]


class FakeSpreadsheet:
    def __init__(self, tabs):
        self.tabs = {t.title: t for t in tabs}

    def worksheet(self, title):
        if title not in self.tabs:
            raise KeyError(title)
        return self.tabs[title]

    def add_worksheet(self, title, rows, cols):
        self.tabs[title] = FakeWorksheet(title, [])
        return self.tabs[title]

    def del_worksheet(self, ws):
        del self.tabs[ws.title]

    def worksheets(self):
        return list(self.tabs.values())


H = agency_sheets.AGENCY_SHEET_HEADER


def sheet_row(key, agency, passport):
    row = {name: "" for name in H}
    row.update({"visa_apply_id": key, "agency_code": agency, "passport_no": passport})
    return row


def as_values(row, header=H):
    return [row.get(name, "") for name in header]


class SheetTest(unittest.TestCase):
    def test_note_added_on_new_rows_only(self):
        header = [*H, "note"]
        chung = FakeWorksheet("CHUNG", [header, as_values({**sheet_row("1", "CHUNG", "P1"), "note": "khach quen"}, header)])
        ss = FakeSpreadsheet([chung])
        rows = [{**sheet_row("1", "CHUNG", "P1"), "note": "Từ đại lý ABC"},
                {**sheet_row("2", "CHUNG", "P2"), "note": "Từ đại lý ABC"}]
        agency_sheets._upsert_worksheet(ss, "CHUNG", rows)
        note = header.index("note")
        self.assertEqual(chung.values[1][note], "khach quen")      # people's note kept
        self.assertEqual(chung.values[2][note], "Từ đại lý ABC")  # new row gets the old agency

    def test_note_column_created_when_missing(self):
        chung = FakeWorksheet("CHUNG", [list(H)])
        agency_sheets._upsert_worksheet(FakeSpreadsheet([chung]), "CHUNG", [{**sheet_row("9", "CHUNG", "P9"), "note": "Từ đại lý X"}])
        self.assertEqual(chung.values[0][-1], "note")
        self.assertEqual(chung.values[1][-1], "Từ đại lý X")

    def test_sync_rows_never_touch_note(self):
        header = [*H, "note"]
        chung = FakeWorksheet("CHUNG", [header, as_values({**sheet_row("1", "CHUNG", "P1"), "note": "Từ đại lý ABC"}, header)])
        agency_sheets._upsert_worksheet(FakeSpreadsheet([chung]), "CHUNG", [sheet_row("1", "CHUNG", "P1")])
        self.assertEqual(chung.values[1][header.index("note")], "Từ đại lý ABC")

    def test_old_tab_deleted_only_when_empty(self):
        old = FakeWorksheet("ABC", [list(H), as_values(sheet_row("1", "ABC", "P1")), as_values(sheet_row("2", "ABC", "P2"))])
        ss = FakeSpreadsheet([old])
        self.assertEqual(agency_sheets._clear_old_tab(ss, "ABC", {"1", "2"}), {"deleted": True, "rows": 2})
        self.assertNotIn("ABC", ss.tabs)
        other = FakeWorksheet("XYZ", [list(H), as_values(sheet_row("1", "XYZ", "P1")), as_values(sheet_row("7", "XYZ", "P7"))])
        ss = FakeSpreadsheet([other])
        self.assertEqual(agency_sheets._clear_old_tab(ss, "XYZ", {"1"}), {"deleted": False, "removed": 1, "kept": 1})
        self.assertEqual([r[0] for r in other.values[1:]], ["7"])

    def test_move_records_to_agency_tab(self):
        old = FakeWorksheet("ABC", [list(H), as_values(sheet_row("11", "ABC", "P1"))])
        ss = FakeSpreadsheet([old])
        record = {"id": 5, "first_applyid": "11", "agency_code": "CHUNG", "agency_name": "CHUNG", "passport_number": "P1"}
        with mock.patch.object(agency_sheets, "is_agency_sheet_enabled", return_value=True), \
             mock.patch.object(agency_sheets, "list_visa_registrations_with_agency", return_value=[record]), \
             mock.patch.object(agency_sheets, "_load_service_account_client") as client, \
             mock.patch.object(agency_sheets, "extract_spreadsheet_id", return_value="id"), \
             mock.patch.object(agency_sheets, "_rebuild_vip_summary", return_value={"vip_rows": 0}):
            client.return_value.open_by_key.return_value = ss
            r = agency_sheets.move_records_to_agency_tab("ABC", "CHUNG", [5], "Từ đại lý ABC (Đại lý A)")
        self.assertTrue(r["ok"], r)
        self.assertNotIn("ABC", ss.tabs)
        chung = ss.tabs["CHUNG"].values
        self.assertEqual(chung[1][0], "11")
        self.assertEqual(chung[1][chung[0].index("note")], "Từ đại lý ABC (Đại lý A)")


class MergeTest(unittest.TestCase):
    def patches(self, candidates):
        calls = {"moved": [], "sheet": [], "deleted": []}
        ps = [
            mock.patch.object(agency_merge, "REGION", "south"),
            mock.patch.object(agency_merge, "list_idle_small_agencies", return_value=candidates),
            mock.patch.object(agency_merge, "get_or_create_agency", return_value={"id": 1, "code": "CHUNG", "name": "CHUNG"}),
            mock.patch.object(agency_merge, "move_agency_records",
                              side_effect=lambda a, b: calls["moved"].append((a, b)) or [10 + a]),
            mock.patch.object(agency_sheets, "move_records_to_agency_tab",
                              side_effect=lambda *a: calls["sheet"].append(a) or {"ok": True}),
            mock.patch.object(agency_merge, "delete_agency_if_unused",
                              side_effect=lambda a: calls["deleted"].append(a) or True),
        ]
        for p in ps:
            p.start()
            self.addCleanup(p.stop)
        return calls

    def test_merge(self):
        calls = self.patches([{"id": 4, "code": "ABC", "name": "Đại lý A", "records": 3, "last_record_at": "2026-11-01"},
                              {"id": 6, "code": "XYZ", "name": "XYZ", "records": 0, "last_record_at": ""}])
        r = agency_merge.merge_small_agencies()
        self.assertTrue(r["ok"])
        self.assertEqual(calls["moved"], [(4, 1), (6, 1)])
        self.assertEqual(calls["sheet"], [("ABC", "CHUNG", [14], "Từ đại lý ABC (Đại lý A)"),
                                          ("XYZ", "CHUNG", [16], "Từ đại lý XYZ")])
        self.assertEqual(calls["deleted"], [4, 6])
        args = agency_merge.list_idle_small_agencies.call_args.args
        self.assertEqual(args, (5, 14, ["CHUNG", "MB"]))

    def test_dry_run_moves_nothing(self):
        calls = self.patches([{"id": 4, "code": "ABC", "name": "", "records": 1, "last_record_at": ""}])
        r = agency_merge.merge_small_agencies(dry_run=True)
        self.assertEqual([a["code"] for a in r["agencies"]], ["ABC"])
        self.assertEqual(calls["moved"], [])

    def test_north_does_nothing(self):
        with mock.patch.object(agency_merge, "REGION", "north"), \
             mock.patch.object(agency_merge, "list_idle_small_agencies") as lst:
            self.assertEqual(agency_merge.merge_small_agencies()["skipped"], "north")
            lst.assert_not_called()


class SqlTest(unittest.TestCase):
    def test_idle_query(self):
        cur = mock.MagicMock()
        cur.fetchall.return_value = []
        conn = mock.MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur
        with mock.patch.object(agency_crud, "get_connection", return_value=conn), \
             mock.patch.object(agency_crud, "current_house", return_value="TAI"):
            agency_crud.list_idle_small_agencies(5, 14, ["CHUNG", "mb"])
        sql, params = cur.execute.call_args.args
        self.assertIn("HAVING COUNT(vr.id) < %s", sql)
        self.assertIn("make_interval(days => %s)", sql)
        self.assertEqual(params, ("TAI", ["CHUNG", "MB"], 5, 14))


if __name__ == "__main__":
    unittest.main()
