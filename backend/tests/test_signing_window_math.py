"""Unit checks for signature-window arithmetic (N-55 / foreign FP)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_commit_signatures.py"
_SPEC = importlib.util.spec_from_file_location("verify_commit_signatures", _SCRIPT)
assert _SPEC and _SPEC.loader
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


class SigningWindowMathTests(unittest.TestCase):
    def test_needed_signed_for_three_percent_of_fifty(self) -> None:
        self.assertEqual(_MOD._needed_signed(0.03, 50), 2)

    def test_commits_until_break_uses_needed_th_newest(self) -> None:
        author = {"AAAA"}
        rows: list[tuple[str, str, str, str]] = [("N", "", f"{i}", "x") for i in range(50)]
        for idx, fpr in ((15, "AAAA"), (18, "AAAA"), (28, "AAAA")):
            rows[idx] = ("G", fpr, f"c{idx}", f"sig-{idx}")
        until = _MOD._commits_until_ratio_break(rows, author, min_ratio=0.03, depth=50)
        self.assertEqual(until, 50 - 18)

    def test_foreign_good_signature_is_unverifiable_not_signed(self) -> None:
        author = {"AAAA"}
        platform = {"BBBB"}
        rows = [
            ("G", "CCCC", "f1", "foreign"),
            ("G", "BBBB", "p1", "platform"),
            ("G", "AAAA", "a1", "author"),
            ("N", "", "n1", "unsigned"),
        ]
        signed, unverifiable, _bad, total, named = _MOD._classify(rows, author, platform)
        self.assertEqual(total, 4)
        self.assertEqual(signed, 1)
        self.assertEqual(unverifiable, 1)
        self.assertEqual(named, [("a1", "author")])


if __name__ == "__main__":
    unittest.main()
