"""NDA gate: operator patterns stay out of git; synthetic token must fail the scan."""

from __future__ import annotations

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "scripts"))
_nda = importlib.import_module("scan_nda_gate_patterns")

_SELFTEST = "NDA-GATE-SELFTEST-TOKEN"


class NdaGatePatternTests(unittest.TestCase):
    def test_missing_operator_file_skips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.txt"
            self.assertIsNone(_nda.load_patterns(missing))
            self.assertEqual(_nda.main(["--patterns", str(missing)]), 0)

    def test_empty_operator_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.txt"
            empty.write_text("# only comments\n\n", encoding="utf-8")
            self.assertEqual(_nda.main(["--patterns", str(empty)]), 1)

    def test_synthetic_token_in_bytes_is_a_hit(self) -> None:
        encoded = (_SELFTEST.encode("utf-8"),)
        self.assertTrue(_nda.bytes_contain_tokens(b"prefix " + encoded[0] + b" suffix", encoded))
        self.assertFalse(_nda.bytes_contain_tokens(b"clean fixture bytes", encoded))

    def test_injected_file_fails_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patterns = root / "patterns.txt"
            patterns.write_text(_SELFTEST + "\n", encoding="utf-8")
            planted = root / "planted.txt"
            planted.write_text(f"leak {_SELFTEST} here\n", encoding="utf-8")
            encoded = (_SELFTEST.encode("utf-8"),)
            self.assertTrue(_nda.file_contains_tokens(planted, encoded))
            self.assertEqual(
                _nda.main(["--patterns", str(patterns), "--scan-root", str(root)]),
                1,
            )
            clean_root = root / "clean"
            clean_root.mkdir()
            (clean_root / "ok.txt").write_text("no operator token\n", encoding="utf-8")
            self.assertEqual(
                _nda.main(["--patterns", str(patterns), "--scan-root", str(clean_root)]),
                0,
            )
