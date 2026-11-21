"""R2 cleanup after approval, decided from status = 'approved' in the DB."""

import os
import unittest
from unittest import mock

from database.crud import visa_registration as vr_crud
from services import visa_registration_sync as sync


class CleanupApprovedR2Test(unittest.TestCase):
    def test_deletes_marks_and_never_raises(self):
        rows = [
            {"id": 1, "passport_number": "E1111111"},
            {"id": 2, "passport_number": "E2222222"},   # R2 error: not marked, tried next run
            {"id": 3, "passport_number": "E1111111"},   # same passport: folder deleted once
        ]

        def delete(folder):
            if folder == "E2222222":
                raise RuntimeError("Delete errors: [...]")
            return 7

        with mock.patch.object(sync, "list_approved_pending_r2_cleanup", return_value=rows), \
             mock.patch.object(sync.remove_r2, "delete_r2_folder", side_effect=delete) as d, \
             mock.patch.object(sync, "mark_r2_deleted", side_effect=lambda ids: len(ids)) as mark:
            result = sync.cleanup_approved_r2()
        self.assertEqual([c.args[0] for c in d.call_args_list], ["E1111111", "E2222222"])
        mark.assert_called_once_with([1, 3])
        self.assertEqual((result["checked"], result["cleaned"], result["objects"]), (3, 2, 7))
        self.assertEqual(result["failed"][0]["id"], 2)

    def test_db_error_does_not_stop_the_sync(self):
        with mock.patch.object(sync, "list_approved_pending_r2_cleanup", side_effect=RuntimeError("db down")), \
             mock.patch.object(sync.remove_r2, "delete_r2_folder") as d:
            result = sync.cleanup_approved_r2()
        d.assert_not_called()
        self.assertIn("db down", result["error"])

    def test_query_uses_db_status_house_and_guard(self):
        captured = {}

        def fake_execute(sql, params, fetch="", dict_rows=False):
            captured.update(sql=sql, params=params)
            return []

        with mock.patch.dict(os.environ, {"HOUSE": "TAI"}), mock.patch.object(vr_crud, "_execute", side_effect=fake_execute):
            vr_crud.list_approved_pending_r2_cleanup(50)
        sql = " ".join(captured["sql"].split())
        self.assertIn("vr.status = 'approved'", sql)
        self.assertIn("vr.r2_deleted_at IS NULL", sql)
        self.assertIn("vr.house = %s", sql)
        # a newer case of the same passport still in progress keeps the folder
        self.assertIn("o.status NOT IN ('approved', 'rejected', 'cancelled') AND o.created_at > vr.created_at", sql)
        self.assertEqual(captured["params"], ("TAI", 50))

    def test_sync_no_longer_deletes_r2_inline(self):
        import inspect
        src = inspect.getsource(sync.sync_draft_visa_registrations)
        self.assertNotIn("delete_r2_folder", src)
        self.assertIn("cleanup_approved_r2", src)


if __name__ == "__main__":
    unittest.main()
