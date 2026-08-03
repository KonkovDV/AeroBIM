"""File-backed LLM token budget ledger — stale lock and degradation signals."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.infrastructure.adapters import file_llm_token_budget as ledger_mod
from aerobim.infrastructure.adapters.file_llm_token_budget import FileBackedLlmTokenBudget


class FileLlmTokenBudgetLedgerTests(unittest.TestCase):
    def test_stale_lock_is_cleared_and_shared_scope_restored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            budget = FileBackedLlmTokenBudget(path, max_tokens_per_day=100_000)
            lock_path = path.with_suffix(path.suffix + ".lock")
            lock_path.write_text("dead-pid\n", encoding="utf-8")
            stale_mtime = time.time() - (ledger_mod._STALE_LOCK_SECONDS + 5)
            os.utime(lock_path, (stale_mtime, stale_mtime))

            blocked = budget.check_before(estimated_tokens=100)
            self.assertIsNone(blocked)
            self.assertFalse(budget.lock_degraded)
            self.assertEqual(budget.budget_scope, "file_shared")
            snap = budget.snapshot()
            self.assertFalse(snap["lock_degraded"])

    def test_live_lock_timeout_sets_lock_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            budget = FileBackedLlmTokenBudget(path, max_tokens_per_day=100_000)
            lock_path = path.with_suffix(path.suffix + ".lock")
            lock_path.write_text("live-holder\n", encoding="utf-8")
            # Fresh mtime — not stale.
            os.utime(lock_path, None)

            with patch.object(ledger_mod, "_LOCK_TIMEOUT_SECONDS", 0.15):
                with patch.object(ledger_mod, "_LOCK_POLL_SECONDS", 0.05):
                    budget.check_before(estimated_tokens=10)

            self.assertTrue(budget.lock_degraded)
            snap = budget.snapshot()
            self.assertTrue(snap["lock_degraded"])
            self.assertEqual(snap["budget_scope"], "file_shared_lock_degraded")
            self.assertIn("lock_degraded_reason", snap)

    def test_snapshot_includes_lock_degraded_false_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            budget = FileBackedLlmTokenBudget(path)
            snap = budget.snapshot()
            self.assertIn("lock_degraded", snap)
            self.assertFalse(snap["lock_degraded"])


if __name__ == "__main__":
    unittest.main()
