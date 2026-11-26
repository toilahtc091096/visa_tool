"""travel_docs: documents rendered while the 4 COVA calls run (C), R2 sent in parallel (D)."""
import asyncio
import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest import mock

sys.modules.setdefault("weasyprint", types.SimpleNamespace(HTML=object))
from flows.flow_step import step_06_save_travel_docs as step  # noqa: E402


def make_ctx():
    profile = types.SimpleNamespace(cleans_local_common_docs=False)
    return types.SimpleNamespace(profile=profile, input_passportNumber="E1", first_applyid="A1",
                                 token="t", tmp_secret="s", step="", error=None)


class TravelDocsParallelTest(unittest.TestCase):
    def run_step(self, *, api_fail_at=None, render_error=None, render_seconds=0.3):
        events, ctx = [], make_ctx()

        def api(name):
            async def call(client, token, secret, body):
                events.append(("api", name, time.monotonic()))
                await asyncio.sleep(0.05)
                return (name != api_fail_at), {"response": {}}
            return call

        async def render(c, root):
            events.append(("render_start", threading.current_thread().name, time.monotonic()))
            time.sleep(render_seconds)      # blocking, like Word
            c.guest_name = "CHANGED"
            if render_error:
                raise render_error
            events.append(("render_end", "", time.monotonic()))

        async def check(c, ok, meta):
            if not ok:
                c.error = {"step": c.step}
            return ok

        async def sync(c, root):
            events.append(("sync", "", time.monotonic()))

        patches = [
            mock.patch.object(step, "passport_data_dir", return_value=Path("x")),
            mock.patch.object(step, "has_additional_names", return_value=False),
            mock.patch.object(step, "_plan_trip", return_value=("", "")),
            mock.patch.object(step, "build_travel_info_profile", return_value={"b": "travel"}),
            mock.patch.object(step, "build_previous_travel_info_profile", return_value={}),
            mock.patch.object(step, "build_other_info", return_value={}),
            mock.patch.object(step, "build_signature_body", return_value={}),
            mock.patch.object(step, "api_save_travel_info", api("save_travel_info")),
            mock.patch.object(step, "api_save_previous_travel_info", api("save_previous_travel_info")),
            mock.patch.object(step, "api_save_other_info", api("save_other_info")),
            mock.patch.object(step, "api_save_signature_info", api("save_signature")),
            mock.patch.object(step, "check_api_result", check),
            mock.patch.object(step, "_generate_documents", render),
            mock.patch.object(step, "_sync_common_docs_to_r2", sync),
        ]
        for p in patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in patches])
        for attr in ("payName", "payMobile", "is_under_18", "haveChildFlag", "fatherFamilyName", "fatherGivenName",
                     "motherFamilyName", "motherGivenName", "m", "f", "hotel_type", "is_private",
                     "arrivedChinaFlag", "haveChinaVisaFlag", "old_visaType", "old_visaNumber", "old_issueDate",
                     "old_issuePlace", "haveOtherVisaFlag", "old_otherVisas", "old_otherCountries",
                     "collectFingerprintFlag", "chinaResidenceLicenseFlag", "residenceLicenseNumber",
                     "residence_issueDate", "residence_issuePlace"):
            setattr(ctx, attr, "")
        started = time.monotonic()
        result = asyncio.run(step.save_travel_and_generate_docs(ctx, client=None))
        return result, ctx, events, time.monotonic() - started

    def test_documents_render_while_api_calls_run(self):
        ok, ctx, events, took = self.run_step(render_seconds=0.3)
        self.assertTrue(ok)
        kinds = [e[0] for e in events]
        self.assertEqual([e[1] for e in events if e[0] == "api"],
                         ["save_travel_info", "save_previous_travel_info", "save_other_info", "save_signature"])
        self.assertLess(kinds.index("render_start"), kinds.index("api") + 2)      # started with the first call
        self.assertNotEqual(next(e[1] for e in events if e[0] == "render_start"), threading.current_thread().name)
        self.assertEqual(kinds[-1], "sync")                                        # R2 only after both
        self.assertLess(took, 0.2 * 4 + 0.3)                                       # overlapped, not 0.2 + 0.3 + ...
        self.assertEqual(ctx.step, "generate_documents")

    def test_api_failure_waits_for_documents_then_stops(self):
        ok, ctx, events, _ = self.run_step(api_fail_at="save_other_info")
        self.assertFalse(ok)
        kinds = [e[0] for e in events]
        self.assertIn("render_end", kinds)          # thread finished before returning (folder cleanup after)
        self.assertNotIn("sync", kinds)
        self.assertEqual(ctx.error, {"step": "save_other_info"})

    def test_render_error_is_raised_after_the_api_calls(self):
        with self.assertRaises(FileNotFoundError):
            self.run_step(render_error=FileNotFoundError("no reused docs"), render_seconds=0.01)


class R2ParallelTest(unittest.TestCase):
    def test_uploads_all_files_in_order(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder in step.COMMON_DOC_FOLDERS:
                (root / folder).mkdir(parents=True)
                for i in range(3):
                    (root / folder / f"{i}.pdf").write_bytes(b"x")
            seen = []

            def upload(key, content, ctype):
                time.sleep(0.05)
                seen.append(key)
                return {"ok": True}

            step.mimetypes.guess_type("a.pdf")   # first call reads the Windows registry: not part of the timing
            with mock.patch.object(step, "api_upload_r2_object", side_effect=upload):
                t = time.monotonic()
                results = step._upload_common_docs_to_r2(local_root=root, prefix="E1")
                took = time.monotonic() - t
        keys = [r["key"] for r in results]
        self.assertEqual(len(keys), 3 * len(step.COMMON_DOC_FOLDERS))
        self.assertEqual(keys, sorted(keys, key=lambda k: (step.COMMON_DOC_FOLDERS.index("/".join(k.split("/")[1:3])), k)))
        self.assertEqual(sorted(seen), sorted(keys))
        self.assertLess(took, 0.05 * len(keys) * 0.6)    # parallel

    def test_delete_all_folders(self):
        with mock.patch.object(step, "delete_r2_folder", side_effect=lambda p: 2) as d:
            self.assertEqual(step._delete_common_docs_from_r2(prefix="E1"), 2 * len(step.COMMON_DOC_FOLDERS))
        self.assertEqual(sorted(c.args[0] for c in d.call_args_list), sorted(f"E1/{f}" for f in step.COMMON_DOC_FOLDERS))


if __name__ == "__main__":
    unittest.main()
