import threading
import time
import unittest
from pathlib import Path

from generate_file.docx_to_pdf import WordKeeper


class FakeWord:
    def __init__(self):
        self.quit_called = False


class FakeKeeper(WordKeeper):
    """WordKeeper with Word replaced: counts opens / quits, can fail or hang."""
    poll_seconds = 0.02

    def __init__(self, **kw):
        super().__init__(**{"idle_seconds": 60, "max_conversions": 50, "timeout_seconds": 5, **kw})
        self.opened, self.exported, self.quits = 0, [], 0
        self.fail_next = False
        self.hang = threading.Event()
        self.hang_next = False

    def _com_init(self): pass
    def _com_uninit(self): pass
    def _pump(self): pass

    def _open_word(self):
        self.opened += 1
        return FakeWord()

    def _alive(self, word):
        return not word.quit_called

    def _export(self, word, source, target):
        if self.hang_next:
            self.hang_next = False
            self.hang.wait(5)            # released by kill()
            raise RuntimeError("killed")
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("com_error: call was rejected by callee")
        self.exported.append(source.name)

    def _quit(self, word):
        word.quit_called = True
        self.quits += 1

    def kill(self):
        self.hang.set()


def wait_until(cond, seconds=2.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return False


class WordKeeperTest(unittest.TestCase):
    def tearDown(self):
        self.k.shutdown()

    def test_one_word_for_many_files(self):
        self.k = FakeKeeper()
        for i in range(6):
            self.k.convert(Path(f"f{i}.docx"), Path(f"f{i}.pdf"))
        self.assertEqual((self.k.opened, len(self.k.exported), self.k.quits), (1, 6, 0))
        self.assertTrue(self.k.is_open)

    def test_closes_when_idle_and_reopens_for_next_case(self):
        self.k = FakeKeeper(idle_seconds=0.15)
        self.k.convert(Path("a.docx"), Path("a.pdf"))
        self.k.convert(Path("b.docx"), Path("b.pdf"))
        self.assertTrue(wait_until(lambda: not self.k.is_open))   # idle -> closed
        self.assertEqual((self.k.opened, self.k.quits), (1, 1))
        self.k.convert(Path("c.docx"), Path("c.pdf"))             # new case -> opened again
        self.assertEqual((self.k.opened, self.k.is_open), (2, True))

    def test_each_file_restarts_the_idle_clock(self):
        self.k = FakeKeeper(idle_seconds=0.3)
        for i in range(5):
            self.k.convert(Path(f"f{i}.docx"), Path(f"f{i}.pdf"))
            time.sleep(0.15)
        self.assertEqual((self.k.opened, self.k.quits), (1, 0))

    def test_error_resets_word(self):
        self.k = FakeKeeper()
        self.k.convert(Path("a.docx"), Path("a.pdf"))
        self.k.fail_next = True
        with self.assertRaises(RuntimeError):
            self.k.convert(Path("b.docx"), Path("b.pdf"))
        self.k.convert(Path("c.docx"), Path("c.pdf"))
        self.assertEqual((self.k.opened, self.k.quits), (2, 1))

    def test_recycle_after_max_conversions(self):
        self.k = FakeKeeper(max_conversions=2)
        for i in range(5):
            self.k.convert(Path(f"f{i}.docx"), Path(f"f{i}.pdf"))
        self.assertEqual(self.k.opened, 3)

    def test_timeout_kills_word_and_next_file_works(self):
        self.k = FakeKeeper(timeout_seconds=0.2)
        self.k.hang_next = True
        with self.assertRaises(RuntimeError) as cm:
            self.k.convert(Path("stuck.docx"), Path("stuck.pdf"))
        self.assertIn("did not finish", str(cm.exception))
        self.k.convert(Path("ok.docx"), Path("ok.pdf"))
        self.assertEqual(self.k.exported, ["ok.docx"])
        self.assertEqual(self.k.opened, 2)


if __name__ == "__main__":
    unittest.main()
