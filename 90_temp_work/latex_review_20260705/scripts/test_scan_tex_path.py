"""Regression test for the portable _scan_tex.py input path."""

from pathlib import Path
import subprocess
import sys
import unittest


class ScanTexPathTests(unittest.TestCase):
    def test_scan_tex_reads_the_adjacent_latex_review_project(self) -> None:
        script = Path(__file__).with_name("_scan_tex.py")
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=script.parent,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            f"_scan_tex.py failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        for label in ("chars", "sections", "figures"):
            self.assertIn(label, result.stdout)


if __name__ == "__main__":
    unittest.main()
