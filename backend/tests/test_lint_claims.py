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
            from lint_claims import (
                claim_needs_boundary_violations,  # type: ignore[import-not-found]
            )
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

    def test_claim_needs_boundary_checks_markdown_table_rows(self) -> None:
        """N-28: metrics hidden in table cells must still require a boundary marker."""
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_claims import (
                claim_needs_boundary_violations,  # type: ignore[import-not-found]
            )
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        table = "| Metric | Value |\n|---|---|\n| detection accuracy | 95% |\n"
        hits = claim_needs_boundary_violations(Path("docs/x.md"), table)
        self.assertTrue(hits)
        self.assertTrue(any("table-row" in h for h in hits))

    def test_allow_file_without_registry_is_not_amnesty(self) -> None:
        """N-29 / A8: allow-file header on an unregistered path must still lint."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.md"
            path.write_text(
                '<!-- claims-lint: allow-file reason="legacy honesty quote" -->\n'
                "We are production-ready today.\n",
                encoding="utf-8",
            )
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import lint_claims  # type: ignore[import-not-found]

                hits = lint_claims(
                    matrix_path=_REPO / "docs" / "capability-claim-matrix-2026.md",
                    roots=[path],
                )
            finally:
                if sys.path and sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertTrue(hits)
            self.assertTrue(any("forbidden_production_ready" in h for h in hits))

    def test_allow_file_registry_still_covers_readme(self) -> None:
        """Registered honesty docs keep allow-file amnesty (README.md)."""
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_claims import lint_claims  # type: ignore[import-not-found]

            hits = lint_claims(
                matrix_path=_REPO / "docs" / "capability-claim-matrix-2026.md",
                roots=[_REPO / "README.md"],
            )
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        self.assertEqual(hits, [])

    def test_fabricated_doi_outside_audit_trail_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "live.md"
            path.write_text("See doi:10.1016/j.aei.2026.103676 for the method.\n", encoding="utf-8")
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import lint_citation_twins  # type: ignore[import-not-found]

                hits = lint_citation_twins(roots=[path])
            finally:
                if sys.path and sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertTrue(any("fabricated_doi" in h for h in hits))

    def test_elsevier_year_twin_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "twins.md"
            path.write_text(
                "10.1016/j.aei.2025.103676 and 10.1016/j.aei.2026.103676\n",
                encoding="utf-8",
            )
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import lint_citation_twins  # type: ignore[import-not-found]

                hits = lint_citation_twins(roots=[path])
            finally:
                if sys.path and sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertTrue(any("elsevier_year_twin" in h or "fabricated_doi" in h for h in hits))

    def test_partners_speech_docs_are_not_directory_blind(self) -> None:
        """HDX-LINT-01: docs/partners/ is a scan root and must actually be linted."""
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_claims import (  # type: ignore[import-not-found]
                _should_scan,
                lint_claims,
            )
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        ask = _REPO / "docs" / "partners" / "_08_15.md"
        competitive = _REPO / "docs" / "partners" / "COMPETITIVE_MATRIX_2026_08.md"
        self.assertTrue(ask.is_file())
        self.assertTrue(_should_scan(ask))
        self.assertFalse(_should_scan(competitive))
        hits = lint_claims(
            matrix_path=_REPO / "docs" / "capability-claim-matrix-2026.md",
            roots=[ask],
        )
        self.assertEqual(hits, [])

    def test_jury_trees_are_not_directory_blind(self) -> None:
        """HDX-LINT-01: architecture/quality/gtm scan; RED_TEAM stays fragment-excluded."""
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_claims import (  # type: ignore[import-not-found]
                _EXCLUDE_PATH_FRAGMENTS,
                _should_scan,
            )
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        self.assertNotIn("docs/architecture/", _EXCLUDE_PATH_FRAGMENTS)
        self.assertNotIn("docs/quality/", _EXCLUDE_PATH_FRAGMENTS)
        self.assertNotIn("docs/gtm/", _EXCLUDE_PATH_FRAGMENTS)
        self.assertTrue(
            _should_scan(_REPO / "docs" / "architecture" / "ADR-001-verdict-ownership-2026.md")
        )
        self.assertTrue(
            _should_scan(_REPO / "docs" / "quality" / "INTERPRETATION_USE_LEDGER_2026_08.md")
        )
        self.assertTrue(
            _should_scan(_REPO / "docs" / "gtm" / "SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md")
        )
        self.assertFalse(
            _should_scan(_REPO / "docs" / "quality" / "RED_TEAM_ACADEMIC_KT2_2026_08_15.md")
        )

    def test_exclusion_stats_count_fragment_blind_zone(self) -> None:
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_claims import (  # type: ignore[import-not-found]
                _SCAN_ROOTS,
                exclusion_stats,
            )
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        stats = exclusion_stats(roots=list(_SCAN_ROOTS))
        self.assertGreater(stats["excluded_by_fragment"], 0)
        self.assertGreaterEqual(stats["scanned"], 1)
        self.assertIn("excluded_untracked", stats)

    def test_builtin_patterns_include_russian_forbidden_markers(self) -> None:
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_claims import _BUILTIN_PATTERNS  # type: ignore[import-not-found]
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        by_id = dict(_BUILTIN_PATTERNS)
        self.assertIsNotNone(by_id["forbidden_accuracy_gt_90"].search("точность более 90%"))
        self.assertIsNotNone(by_id["forbidden_native_dwg"].search("нативный DWG"))
        self.assertIsNotNone(by_id["forbidden_cde_ready"].search("готово к CDE"))

    def test_scan_roots_include_submission_pack(self) -> None:
        """HDS-SUB-01: jury-facing submission/ stays in default scan roots."""
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_claims import _SCAN_ROOTS  # type: ignore[import-not-found]
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        self.assertIn(_REPO / "submission", _SCAN_ROOTS)

    def test_heading_negation_covers_following_list_items(self) -> None:
        """HDS-SUB-02: list items inherit a heading/list negation marker."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.md"
            path.write_text(
                "## Запрещено\n\n- production-ready\n- native DWG\n- CDE-ready\n",
                encoding="utf-8",
            )
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import lint_claims  # type: ignore[import-not-found]

                hits = lint_claims(
                    matrix_path=_REPO / "docs" / "capability-claim-matrix-2026.md",
                    roots=[path],
                )
            finally:
                if sys.path and sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertEqual(hits, [])

    def test_new_heading_resets_inherited_negation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.md"
            path.write_text(
                "## Запрещено\n\n- production-ready\n\n## Status\n\nWe are production-ready.\n",
                encoding="utf-8",
            )
            sys.path.insert(0, str(_REPO / "scripts"))
            try:
                from lint_claims import lint_claims  # type: ignore[import-not-found]

                hits = lint_claims(
                    matrix_path=_REPO / "docs" / "capability-claim-matrix-2026.md",
                    roots=[path],
                )
            finally:
                if sys.path and sys.path[0] == str(_REPO / "scripts"):
                    sys.path.pop(0)
            self.assertTrue(any("forbidden_production_ready" in hit for hit in hits))
            self.assertTrue(any("We are production-ready" in hit for hit in hits))

    def test_presentation_readme_is_scanned_without_allow_file(self) -> None:
        """Jury presentation pack is content-scanned; heading negation must hold."""
        path = _REPO / "submission" / "03-presentation" / "README.md"
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("claims-lint: allow-file", text[:400])
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from lint_claims import lint_claims  # type: ignore[import-not-found]

            hits = lint_claims(
                matrix_path=_REPO / "docs" / "capability-claim-matrix-2026.md",
                roots=[path],
            )
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
