"""WP-R10 claims linter tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_LINT = _REPO / "scripts" / "lint_claims.py"


class LintClaimsTests(unittest.TestCase):
    def test_detects_forbidden_production_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.md"
            path.write_text("We are production-ready for Samolet.\n", encoding="utf-8")
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import lint_claims  # type: ignore[import-not-found]

                hits = lint_claims(
                    matrix_path=_REPO / "docs" / "capability-claim-matrix-2026.md", roots=[path]
                )
            finally:
                if sys.path and sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertTrue(hits)
            self.assertTrue(any("production" in hit.lower() for hit in hits))

    def test_allowlist_with_reason_suppresses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.md"
            allow = (
                '# claims-lint: allow reason="quoted forbidden term in TZ audit, not product claim"'
            )
            path.write_text(f"production-ready  {allow}\n", encoding="utf-8")
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import lint_claims  # type: ignore[import-not-found]

                hits = lint_claims(
                    matrix_path=_REPO / "docs" / "capability-claim-matrix-2026.md", roots=[path]
                )
            finally:
                if sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertEqual(hits, [])

    def test_matrix_guard_flags_blocked_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tz = Path(tmp) / "TZ.md"
            tz.write_text(
                "| Row | partial | RT-001 customer corpus blocked |\n"
                "| Bad | done | approved norm pack delivered |\n",
                encoding="utf-8",
            )
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import matrix_guard  # type: ignore[import-not-found]

                hits = matrix_guard(tz)
            finally:
                if sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertEqual(len(hits), 1)


if __name__ == "__main__":
    unittest.main()
