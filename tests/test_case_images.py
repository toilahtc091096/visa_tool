"""Case images on /web (curl tab): passport.png and the edited portrait from R2."""

import os
import sys
import types
import unittest
from unittest import mock

from services import web_portal as wp


class CaseImageTest(unittest.TestCase):
    def test_keys_and_validation(self):
        resp = mock.Mock(status_code=200, content=b"PNG", headers={"content-type": "image/png"})
        with mock.patch.object(wp.requests, "get", return_value=resp) as get:
            self.assertEqual(wp.case_image("tai", " e05676804 ", "portrait"),
                             (200, b"PNG", "image/png", "E05676804_portrait.png"))
        self.assertEqual(get.call_args.args[0], "http://127.0.0.1:30000/r2/images/get")  # the house's own bucket
        self.assertEqual(get.call_args.kwargs["params"], {"key": "E05676804/anh_chan_dung/portrait.png"})
        with mock.patch.object(wp.requests, "get", return_value=resp) as get:
            wp.case_image("HAI", "E05676804", "passport")
        self.assertEqual(get.call_args.kwargs["params"], {"key": "E05676804/passport.png"})
        for house, passport, kind in [("HAI", "../x", "passport"), ("HAI", "", "passport"), ("HAI", "E1/2", "passport"),
                                      ("HAI", "E05676804", "other"), ("XYZ", "E05676804", "passport")]:
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
        url = "/web/case-image?house=HAI&passport=E05676804&kind=passport"
        self.assertEqual(self.client.get(url).status_code, 401)
        with mock.patch.object(self.server.web_portal, "case_image", return_value=(200, b"PNG", "image/png", "E05676804_passport.png")):
            r = self.client.get(url, headers={"X-Api-Key": "bao-key"})
            self.assertEqual((r.status_code, r.content, r.headers["content-type"]), (200, b"PNG", "image/png"))
            self.assertNotIn("content-disposition", r.headers)
            r = self.client.get(url + "&download=1", headers={"X-Api-Key": "bao-key"})
            self.assertIn('filename="E05676804_passport.png"', r.headers["content-disposition"])

    def test_missing_and_bad_input(self):
        with mock.patch.object(self.server.web_portal, "case_image", return_value=(404, b"", "", "x")):
            r = self.client.get("/web/case-image?house=HAI&passport=E1234567&kind=portrait", headers={"X-Api-Key": "bao-key"})
        self.assertEqual(r.status_code, 404)
        self.assertIn("Chưa có ảnh", r.json()["detail"]["error"])
        r = self.client.get("/web/case-image?house=HAI&passport=../etc&kind=passport", headers={"X-Api-Key": "bao-key"})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
