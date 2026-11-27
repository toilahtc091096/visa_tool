import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "backup_db", Path(__file__).resolve().parent.parent / "scripts" / "backup_db.py"
)
backup_db = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(backup_db)

NOW = datetime(2026, 11, 27, 2, 0, tzinfo=timezone.utc)


def obj(key, days_ago):
    return {"Key": key, "LastModified": NOW - timedelta(days=days_ago)}


class OldKeysTest(unittest.TestCase):
    def test_removes_only_dumps_older_than_limit(self):
        objects = [obj("_db-backup/a.dump", 40), obj("_db-backup/b.dump", 31),
                   obj("_db-backup/c.dump", 29), obj("_db-backup/d.dump", 0)]
        self.assertEqual(backup_db.old_keys(objects, "_db-backup/", 30, NOW),
                         ["_db-backup/a.dump", "_db-backup/b.dump"])

    def test_newest_dump_is_kept_even_if_old(self):
        objects = [obj("_db-backup/a.dump", 90), obj("_db-backup/b.dump", 60)]
        self.assertEqual(backup_db.old_keys(objects, "_db-backup/", 30, NOW), ["_db-backup/a.dump"])

    def test_ignores_other_prefixes_and_files(self):
        objects = [obj("_archive/x.dump", 90), obj("_db-backup/note.txt", 90), obj("_db-backup/d.dump", 1)]
        self.assertEqual(backup_db.old_keys(objects, "_db-backup/", 30, NOW), [])


if __name__ == "__main__":
    unittest.main()
