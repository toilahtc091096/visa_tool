"""web/file_check.js (update.md K1 + K2): the folder check of the /web start form.

The cases are in tests/file_check_cases.js (Node); this runs them inside unittest.
Skipped when Node is not installed.
"""

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class FileCheckTest(unittest.TestCase):
    def test_cases(self):
        proc = subprocess.run(
            ["node", str(ROOT / "tests" / "file_check_cases.js")],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_script_served_with_the_page(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('src="/web/file_check.js"', html)


if __name__ == "__main__":
    unittest.main()
