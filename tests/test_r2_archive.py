import unittest
from datetime import datetime
from unittest import mock

from api import r2_archive


class FakeR2:
    """In-memory stand-in for the boto3 S3 client calls used by r2_archive."""

    def __init__(self, files):
        self.objects = dict(files)  # key -> bytes size

    def get_paginator(self, _name):
        return self

    def paginate(self, Bucket, Prefix, Delimiter=None):
        keys = sorted(k for k in self.objects if k.startswith(Prefix))
        if Delimiter:
            subs = sorted({Prefix + k[len(Prefix):].split(Delimiter)[0] + Delimiter
                           for k in keys if Delimiter in k[len(Prefix):]})
            return [{"CommonPrefixes": [{"Prefix": s} for s in subs]}]
        return [{"Contents": [{"Key": k, "Size": self.objects[k]} for k in keys]}]

    def list_objects_v2(self, Bucket, Prefix, MaxKeys=1000):
        n = sum(1 for k in self.objects if k.startswith(Prefix))
        return {"KeyCount": min(n, MaxKeys)}

    def copy_object(self, Bucket, Key, CopySource):
        self.objects[Key] = self.objects[CopySource["Key"]]

    def delete_objects(self, Bucket, Delete, ):
        for o in Delete["Objects"]:
            self.objects.pop(o["Key"], None)
        return {"Deleted": Delete["Objects"]}


class R2ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.r2 = FakeR2({
            "L15 - A/1.jpg": 10,
            "L15 - A/2.pdf": 20,
            "L15 - AB/x.jpg": 5,  # must not be touched (shares a name prefix)
            "C1234567/chung/passport.png": 7,
            "C12345678/other.png": 3,  # must not be touched
        })
        cfg = mock.Mock(bucket_name="visa-data")
        patches = [
            mock.patch.object(r2_archive, "_build_r2_client", return_value=(self.r2, cfg)),
            mock.patch.object(r2_archive, "_missing_r2_env_vars", return_value=[]),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def archive(self, when="2026-11-20 10:00:00"):
        return r2_archive.api_archive_r2_folder(
            "L15 - A/", now=datetime.strptime(when, "%Y-%m-%d %H:%M:%S"))

    def test_archive_moves_folder_and_keeps_neighbours(self):
        res = self.archive()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["files"], 2)
        self.assertEqual(res["destination"], "_archive/2026-11-20_100000/L15 - A/")
        self.assertNotIn("L15 - A/1.jpg", self.r2.objects)
        self.assertIn("_archive/2026-11-20_100000/L15 - A/2.pdf", self.r2.objects)
        self.assertIn("L15 - AB/x.jpg", self.r2.objects)

    def test_archive_rejects_empty_or_missing(self):
        self.assertEqual(r2_archive.api_archive_r2_folder("")["error"], "missing_prefix")
        self.assertEqual(r2_archive.api_archive_r2_folder("nope/")["error"], "source_not_found")
        self.assertEqual(r2_archive.api_archive_r2_folder("_archive/x/")["error"], "already_archived")

    def test_restore_dry_run_changes_nothing(self):
        self.archive()
        before = dict(self.r2.objects)
        res = r2_archive.api_restore_r2_folder("L15 - A", "c1234567")
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["mode"], "dry_run")
        self.assertEqual(res["restore"], {"files": 2, "bytes": 30})
        self.assertEqual(res["delete_output"]["files"], 1)
        self.assertEqual(self.r2.objects, before)

    def test_restore_uses_latest_archive_and_clears_output_only(self):
        self.archive("2026-11-19 09:00:00")
        self.r2.objects["L15 - A/new.jpg"] = 1
        self.archive("2026-11-20 10:00:00")
        res = r2_archive.api_restore_r2_folder("L15 - A/", "C1234567", confirm=True)
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["archive"], "_archive/2026-11-20_100000/L15 - A/")
        self.assertIn("L15 - A/new.jpg", self.r2.objects)
        self.assertNotIn("C1234567/chung/passport.png", self.r2.objects)
        self.assertIn("C12345678/other.png", self.r2.objects)
        self.assertIn("_archive/2026-11-19_090000/L15 - A/1.jpg", self.r2.objects)

    def test_restore_when_failed_before_archive_only_clears_output(self):
        res = r2_archive.api_restore_r2_folder("L15 - A/", "C1234567", confirm=True)
        self.assertTrue(res["ok"], res)
        self.assertIn("L15 - A/1.jpg", self.r2.objects)
        self.assertNotIn("C1234567/chung/passport.png", self.r2.objects)

    def test_restore_rejects_bad_passport(self):
        self.archive()
        for bad in ["", "C123", "C1234567/..", "*", "C 1234567"]:
            res = r2_archive.api_restore_r2_folder("L15 - A/", bad, confirm=True)
            self.assertEqual(res["error"], "invalid_passport_number", bad)
        self.assertIn("C1234567/chung/passport.png", self.r2.objects)

    def test_restore_refuses_when_source_and_archive_both_exist(self):
        self.archive()
        self.r2.objects["L15 - A/again.jpg"] = 1
        res = r2_archive.api_restore_r2_folder("L15 - A/", "C1234567", confirm=True)
        self.assertEqual(res["error"], "source_and_archive_both_exist")
        self.assertIn("C1234567/chung/passport.png", self.r2.objects)


if __name__ == "__main__":
    unittest.main()
