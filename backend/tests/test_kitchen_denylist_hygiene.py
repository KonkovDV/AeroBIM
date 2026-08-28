"""Kitchen denylist hygiene: fail-closed pin, no literals in guard files."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "scripts"))

from kitchen_denylist import (  # noqa: E402
    KitchenDenylistError,
    lint_guard_files_have_no_literals,
    lint_kitchen_tokens,
    lint_pack_quarantine,
    load_tokens,
    verify_pin,
)


class KitchenDenylistHygieneTests(unittest.TestCase):
    def test_pin_verifies_against_local_or_ci_list(self) -> None:
        tokens = load_tokens()
        verify_pin(tokens)
        self.assertGreaterEqual(len(tokens), 1)

    def test_guard_files_contain_no_denylist_literals(self) -> None:
        self.assertEqual(lint_guard_files_have_no_literals(), [])

    def test_working_tree_scan_is_clean(self) -> None:
        self.assertEqual(lint_kitchen_tokens(), [])

    def test_pack_quarantine_allows_documented_dwg_fixture_only(self) -> None:
        hits = lint_pack_quarantine()
        self.assertEqual(hits, [])

    def test_count_mismatch_reports_counts_not_tokens(self) -> None:
        previous = os.environ.get("AEROBIM_KITCHEN_DENYLIST_PATH")
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "short-denylist.txt"
            path.write_text("synthetic-count-probe-only\n", encoding="utf-8")
            os.environ["AEROBIM_KITCHEN_DENYLIST_PATH"] = str(path)
            try:
                with self.assertRaises(KitchenDenylistError) as ctx:
                    verify_pin()
                message = str(ctx.exception)
                self.assertIn("got 1", message)
                self.assertIn("pin 27", message)
                self.assertNotIn("synthetic-count-probe-only", message)
            finally:
                if previous is None:
                    os.environ.pop("AEROBIM_KITCHEN_DENYLIST_PATH", None)
                else:
                    os.environ["AEROBIM_KITCHEN_DENYLIST_PATH"] = previous

    def test_ci_passes_denylist_via_env_not_composite_input(self) -> None:
        action_path = _REPO / ".github" / "actions" / "materialize-kitchen-denylist" / "action.yml"
        workflow = (_REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        action = action_path.read_text(encoding="utf-8")
        self.assertNotIn("inputs:", action)
        self.assertIn("AEROBIM_KITCHEN_DENYLIST", action)
        self.assertNotIn("with:\n          denylist:", workflow)
        secret_line = "AEROBIM_KITCHEN_DENYLIST: ${{ secrets.AEROBIM_KITCHEN_DENYLIST }}"
        self.assertIn(secret_line, workflow)

    def test_missing_denylist_is_fail_closed(self) -> None:
        previous = os.environ.get("AEROBIM_KITCHEN_DENYLIST_PATH")
        os.environ["AEROBIM_KITCHEN_DENYLIST_PATH"] = str(
            Path(tempfile.gettempdir()) / "aerobim-missing-kitchen-denylist.txt"
        )
        try:
            hits = lint_kitchen_tokens()
            self.assertTrue(hits)
            self.assertTrue(hits[0].startswith("[kitchen_denylist] fail-closed"))
            with self.assertRaises(KitchenDenylistError):
                load_tokens()
        finally:
            if previous is None:
                os.environ.pop("AEROBIM_KITCHEN_DENYLIST_PATH", None)
            else:
                os.environ["AEROBIM_KITCHEN_DENYLIST_PATH"] = previous


if __name__ == "__main__":
    unittest.main()
