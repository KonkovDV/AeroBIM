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
                "| Requirement | Status | Module |\n"
                "|-------------|--------|--------|\n"
                "| approved norm pack | done | blocked until RT-002 |\n",
                encoding="utf-8",
            )
            registry = _REPO / "audit" / "tz_matrix_blocked_registry.json"
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import matrix_guard  # type: ignore[import-not-found]

                hits = matrix_guard(tz, registry_path=registry)
            finally:
                if sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertEqual(len(hits), 1)

    def test_blocked_word_does_not_suppress_forbidden_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.md"
            path.write_text(
                "Точность более 90% — blocked wording, но в пилоте достигается.\n",
                encoding="utf-8",
            )
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

    def test_matrix_guard_catches_mep_row_marked_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tz = Path(tmp) / "TZ.md"
            tz.write_text(
                "### 3.3 Error detection\n\n"
                "| Requirement | Status | Module | Phase |\n"
                "|-------------|--------|--------|-------|\n"
                "| MEP / system intersections | done | gap | P1 |\n",
                encoding="utf-8",
            )
            registry = _REPO / "audit" / "tz_matrix_blocked_registry.json"
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import matrix_guard  # type: ignore[import-not-found]

                hits = matrix_guard(tz, registry_path=registry)
            finally:
                if sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertEqual(len(hits), 1)

    def test_customer_docs_scanned_by_default_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "docs.md"
            path.write_text("Мы production-ready для заказчика.\n", encoding="utf-8")
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

    def test_claim_needs_boundary_flags_unframed_numeric_claim(self) -> None:
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_claims import claim_needs_boundary_violations  # type: ignore[import-not-found]
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        bad = "Detection accuracy is 95% on all projects.\n"
        hits = claim_needs_boundary_violations(Path("docs/x.md"), bad)
        self.assertEqual(len(hits), 1)
        framed = (
            "Detection on open corpus n=24 claim_level: coverage_map_only — 16.7% "
            "is coverage-map only, not product accuracy (NO_GO RT-001).\n"
        )
        self.assertEqual(claim_needs_boundary_violations(Path("docs/x.md"), framed), [])


if __name__ == "__main__":
    unittest.main()
