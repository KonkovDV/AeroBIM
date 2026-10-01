"""Commit-signing policy honesty (N-35 / A-4)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class CommitSigningPolicyHonestyTests(unittest.TestCase):
    def test_policy_does_not_claim_enforcement_while_ratio_zero(self) -> None:
        policy_path = REPO_ROOT / "governance" / "commit_signing_policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertIn("enforce_ci", policy)
        # Until signed commits exist, CI must not pretend enforcement is on.
        if float(policy.get("min_signed_ratio", 0.0) or 0.0) <= 0.0:
            self.assertFalse(
                bool(policy.get("enforce_ci")),
                "enforce_ci=true with min_signed_ratio=0 is a decorative control",
            )
        notes = str(policy.get("notes") or "")
        self.assertTrue(
            "honesty" in notes.lower() or "N-45" in notes,
            "policy notes must state honesty / N-45 rationale",
        )


if __name__ == "__main__":
    unittest.main()
