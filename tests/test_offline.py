"""Offline tests — no network required."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "cuevault.py"
DEMO = ROOT / "demo" / "sample_library.json"


class TestCueVaultOffline(unittest.TestCase):
    def run_cmd(self, *args, home):
        return subprocess.run(
            [sys.executable, str(PY), *args],
            capture_output=True, text=True, cwd=ROOT,
            env={**__import__("os").environ, "USERPROFILE": home, "HOME": home},
        )

    def test_search_ranks_ml_first(self):
        with tempfile.TemporaryDirectory() as td:
            lib = Path(td) / ".cuevault" / "library.json"
            lib.parent.mkdir(parents=True)
            lib.write_text(DEMO.read_text(encoding="utf-8"), encoding="utf-8")
            r = self.run_cmd("search", "machine learning", home=td)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Introduction to Machine Learning", r.stdout)

    def test_validate_passes(self):
        with tempfile.TemporaryDirectory() as td:
            lib = Path(td) / ".cuevault" / "library.json"
            lib.parent.mkdir(parents=True)
            lib.write_text(DEMO.read_text(encoding="utf-8"), encoding="utf-8")
            r = self.run_cmd("validate", home=td)
            self.assertEqual(r.returncode, 0)
            self.assertIn("2 OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
