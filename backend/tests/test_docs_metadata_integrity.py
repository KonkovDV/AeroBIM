"""WP-A3 docs-metadata-integrity gate tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts" / "check_docs_metadata_integrity.py"


class DocsMetadataIntegrityTests(unittest.TestCase):
    def _import_check(self):  # noqa: ANN202
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from check_docs_metadata_integrity import (  # type: ignore[import-not-found]
                _check_frontmatter_version_parity,
                _check_numbered_list_continuity,
                check_docs_metadata_integrity,
            )

            return (
                _check_frontmatter_version_parity,
                _check_numbered_list_continuity,
                check_docs_metadata_integrity,
            )
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)

    def test_version_mismatch_detected(self) -> None:
        parity, _, _ = self._import_check()
        text = (
            '---\nversion: "1.0.0"\nlast_updated: "2026-08-09"\n---\n'
            "# Title\n\n**v1.0.1** — body newer than frontmatter\n"
        )
        hits = parity(Path("docs/x.md"), text, {"version": "1.0.0"})
        self.assertEqual(len(hits), 1)

    def test_non_claims_numbering_gap_detected(self) -> None:
        _, continuity, _ = self._import_check()
        text = (
            "## Non-claims (explicit boundaries)\n\n"
            "1. first\n2. second\n9. skipped eight\n10. tenth\n"
        )
        hits = continuity(
            Path("docs/pilot-claim-boundary-2026.md"), text, "Non-claims (explicit boundaries)"
        )
        self.assertEqual(len(hits), 1)

    def test_engineering_status_missing_tests_collected_is_error(self) -> None:
        """N-27: dead `pass` removed — stale test counts must fail."""
        sys.path.insert(0, str(_REPO / "scripts"))
        try:
            from check_docs_metadata_integrity import (  # type: ignore[import-not-found]
                _check_engineering_status_baseline_numbers,
            )
        finally:
            if sys.path and sys.path[0] == str(_REPO / "scripts"):
                sys.path.pop(0)
        text = (
            "# Engineering Status\n\n"
            "architecture_inventory Schema 1.4.0\n"
            "We ran 1990 tests yesterday.\n"
        )
        baseline = {"backend": {"tests_collected": 2006}, "schema_version": "1.4.0"}
        hits = _check_engineering_status_baseline_numbers(
            Path("docs/ENGINEERING_STATUS_2026_08.md"), text, baseline
        )
        self.assertTrue(hits)

    def test_live_repo_passes_after_wp_a3_fixes(self) -> None:
        _, _, check = self._import_check()
        hits = check()
        self.assertEqual(hits, [], msg="\n".join(hits))


if __name__ == "__main__":
    unittest.main()
