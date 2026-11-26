"""Q1 North, Q2 both regions: every file of the under-18 folder -> mfa-039 _1.._5.
South Q1 keeps its guardian slots. REGION is read at import: one process per region."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = r"""
import json, sys, types
sys.modules['weasyprint'] = types.SimpleNamespace(HTML=object)
from visa_types.base import get_visa_profile
out = {}
for v in ('Q1', 'Q2'):
    for it in get_visa_profile(v).upload_plan():
        if it.doc_type in ('UNDER_18', 'GUARDIAN_DOCUMENTS'):
            out[v] = [it.doc_type, [c['materialCode'] for c in it.codes], it.configs]
print('RESULT' + json.dumps(out))
"""


def plan(region):
    env = {**os.environ, "REGION": region}
    proc = subprocess.run([sys.executable, "-c", SCRIPT], cwd=ROOT, env=env, capture_output=True, text=True)
    line = next(l for l in proc.stdout.splitlines() if l.startswith("RESULT"))
    return json.loads(line[len("RESULT"):])


SLOTS = [f"mfa-039_{i}" for i in range(1, 6)]
ALL_FILES = [{"folder": "duoi_18_tuoi\\giay_to_cho_nguoi_duoi_18", "limit": 5}]   # no exclude


class QUnder18UploadTest(unittest.TestCase):
    def test_north(self):
        p = plan("north")
        self.assertEqual(p["Q1"], ["UNDER_18", SLOTS, ALL_FILES])
        self.assertEqual(p["Q2"], ["UNDER_18", SLOTS, ALL_FILES])

    def test_south(self):
        p = plan("south")
        self.assertEqual(p["Q2"], ["UNDER_18", SLOTS, ALL_FILES])
        self.assertEqual(p["Q1"][0], "GUARDIAN_DOCUMENTS")   # unchanged


if __name__ == "__main__":
    unittest.main()
