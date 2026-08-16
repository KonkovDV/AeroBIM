"""Advisory-origin decoder — one function for hash + Acceptance Gate."""

from __future__ import annotations

import unittest

from aerobim.domain.advisory_origin import is_advisory_issue
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue


class AdvisoryOriginTests(unittest.TestCase):
    def test_origin_advisory_without_agent_prefix(self) -> None:
        issue = ValidationIssue(
            rule_id="IDS-001",
            severity=Severity.INFO,
            category=FindingCategory.IFC_VALIDATION,
            message="llm",
            origin="advisory",
        )
        self.assertTrue(is_advisory_issue(issue))
        self.assertTrue(is_advisory_issue({"rule_id": "IDS-001", "origin": "advisory"}))

    def test_compliance_agent_source_and_prefixes(self) -> None:
        self.assertTrue(
            is_advisory_issue(
                ValidationIssue(
                    rule_id="HINT",
                    severity=Severity.INFO,
                    category=FindingCategory.DRAWING_VALIDATION,
                    message="hint",
                    source_id="compliance-agent",
                )
            )
        )
        self.assertTrue(is_advisory_issue({"rule_id": "AGENT-1"}))
        self.assertTrue(is_advisory_issue({"rule_id": "AEROBIM-AGENT-9"}))
        self.assertFalse(
            is_advisory_issue(
                ValidationIssue(
                    rule_id="IDS-WALL-001",
                    severity=Severity.ERROR,
                    category=FindingCategory.IDS_VALIDATION,
                    message="missing",
                    origin="deterministic",
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
