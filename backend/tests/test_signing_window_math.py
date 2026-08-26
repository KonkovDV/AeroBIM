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

    def test_key_dir_path_match_is_exact_prefix(self) -> None:
        keys = "governance/trusted_signing_keys"
        self.assertTrue(
            _MOD._touches_trusted_keys_dir(
                ["governance/trusted_signing_keys/B5690EEEBB952194.asc"],
                keys,
            )
        )
        self.assertTrue(
            _MOD._touches_trusted_keys_dir(
                ["governance/trusted_signing_keys/platform/4AEE18F83AFDEB23.asc"],
                keys,
            )
        )
        self.assertFalse(
            _MOD._touches_trusted_keys_dir(
                ["governance/commit_signing_policy.json"],
                keys,
            )
        )
        self.assertFalse(
            _MOD._touches_trusted_keys_dir(
                ["governance/trusted_signing_keys_backup/x.asc"],
                keys,
            )
        )

    def test_author_trusted_sig_rejects_unsigned_and_platform(self) -> None:
        author = {"AAAA"}
        self.assertTrue(_MOD._is_author_trusted_sig("G", "AAAA", author))
        self.assertTrue(_MOD._is_author_trusted_sig("U", "AAAA", author))
        self.assertFalse(_MOD._is_author_trusted_sig("G", "BBBB", author))
        self.assertFalse(_MOD._is_author_trusted_sig("N", "AAAA", author))


if __name__ == "__main__":
    unittest.main()
