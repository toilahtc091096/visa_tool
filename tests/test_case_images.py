"""Case images on /web (curl tab): passport image and the edited portrait from R2."""

import os
import sys
import types
import unittest
from unittest import mock

from api import r2_archive
from services import web_portal as wp


class FindCaseImagesTest(unittest.TestCase):
    def _find(self, keys):
        client = mock.Mock()
        client.get_paginator.return_value.paginate.return_value = [{"Contents": [{"Key": k} for k in keys]}]
        cfg = mock.Mock(bucket_name="visa-data")
        with mock.patch.object(r2_archive, "_missing_r2_env_vars", return_value=[]), \
             mock.patch.object(r2_archive, "_build_r2_client", return_value=(client, cfg)):
            return r2_archive.api_find_case_images("e01234567")

    def test_passport_picked_like_run(self):
        base = ["E01234567/chung/2_trang_ho_chieu_trang/file_x_a.png", "E01234567/tham-than/cccd/a.jpg"]
        # only a file_... image right in the folder (what the bucket really has)
        r = self._find(base + ["E01234567/file_job-1-doc-0001.jpg"])
        self.assertEqual(r["passport"], "E01234567/file_job-1-doc-0001.jpg")
        self.assertEqual(r["portrait"], "")
        # passport.png wins; then passport/ folder
        self.assertEqual(self._find(base + ["E01234567/file_a.jpg", "E01234567/passport.png"])["passport"],
                         "E01234567/passport.png")
        self.assertEqual(self._find(base + ["E01234567/passport/p1.jpg", "E01234567/file_a.jpg"])["passport"],
                         "E01234567/passport/p1.jpg")
        # images only in sub folders: no passport image (not a random document)
        self.assertEqual(self._find(base)["passport"], "")
        r = self._find(base + ["E01234567/passport.png", "E01234567/anh_chan_dung/portrait.png"])
        self.assertEqual(r["portrait"], "E01234567/anh_chan_dung/portrait.png")

    def test_bad_passport(self):
        with mock.patch.object(r2_archive, "_missing_r2_env_vars", return_value=[]):
            self.assertFalse(r2_archive.api_find_case_images("../x")["ok"])


class CaseImageTest(unittest.TestCase):
    def _get(self, found):
        def get(url, params=None, timeout=None):
            if url.endswith("/r2/case-images"):
                return mock.Mock(status_code=200, json=mock.Mock(return_value={"ok": True, **found}))
            return mock.Mock(status_code=200, content=b"IMG", headers={"content-type": "image/jpeg"})
        return get

    def test_reads_found_key_from_house_bucket(self):
        found = {"passport": "E01234567/file_a.jpg", "portrait": ""}
        with mock.patch.object(wp.requests, "get", side_effect=self._get(found)) as get:
            self.assertEqual(wp.case_image("tai", " e01234567 ", "passport"),
                             (200, b"IMG", "image/jpeg", "E01234567_passport.jpg"))
        urls = [c.args[0] for c in get.call_args_list]
        self.assertEqual(urls, ["http://127.0.0.1:30000/r2/case-images", "http://127.0.0.1:30000/r2/images/get"])
        self.assertEqual(get.call_args_list[1].kwargs["params"], {"key": "E01234567/file_a.jpg"})
        with mock.patch.object(wp.requests, "get", side_effect=self._get(found)):
            self.assertEqual(wp.case_image("TAI", "E01234567", "portrait")[0], 404)   # not there

    def test_validation(self):
        for house, passport, kind in [("HAI", "../x", "passport"), ("HAI", "", "passport"), ("HAI", "E1/2", "passport"),
                                      ("HAI", "E01234567", "other"), ("XYZ", "E01234567", "passport")]:
            with self.assertRaises(wp.FormError, msg=(house, passport, kind)):
                wp.case_image(house, passport, kind)


class CaseImageEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
        from fastapi.testclient import TestClient
        import server
        cls.server = server
        cls.client = TestClient(server.app)

    def setUp(self):
        p = [mock.patch.dict(os.environ, {"ACCESS_GUARD": "enforce", "VISA_API_KEY": "shared"}),
             mock.patch.object(self.server, "get_web_user_by_api_key",
                               side_effect=lambda k: {"username": "bao", "staff_code": "BAO"} if k == "bao-key" else None)]
        for x in p:
            x.start()
            self.addCleanup(x.stop)

    def test_image_and_download(self):
        url = "/web/case-image?house=HAI&passport=E01234567&kind=passport"
        self.assertEqual(self.client.get(url).status_code, 401)
        with mock.patch.object(self.server.web_portal, "case_image", return_value=(200, b"PNG", "image/png", "E01234567_passport.png")):
            r = self.client.get(url, headers={"X-Api-Key": "bao-key"})
            self.assertEqual((r.status_code, r.content, r.headers["content-type"]), (200, b"PNG", "image/png"))
            self.assertNotIn("content-disposition", r.headers)
            r = self.client.get(url + "&download=1", headers={"X-Api-Key": "bao-key"})
            self.assertIn('filename="E01234567_passport.png"', r.headers["content-disposition"])

    def test_missing_and_bad_input(self):
        with mock.patch.object(self.server.web_portal, "case_image", return_value=(404, b"", "", "")):
            r = self.client.get("/web/case-image?house=HAI&passport=E1234567&kind=portrait", headers={"X-Api-Key": "bao-key"})
        self.assertEqual(r.status_code, 404)
        self.assertIn("Chưa có ảnh", r.json()["detail"]["error"])
        r = self.client.get("/web/case-image?house=HAI&passport=../etc&kind=passport", headers={"X-Api-Key": "bao-key"})
        self.assertEqual(r.status_code, 400)

    def test_house_endpoint_needs_key_from_outside(self):
        self.assertEqual(self.client.get("/r2/case-images?passport=E01234567").status_code, 401)


if __name__ == "__main__":
    unittest.main()
