"""Demo-pack TZ clauses bind onto fixture IDS specs without inventing SP items."""

from __future__ import annotations

import unittest

from aerobim.domain.fixture_norm_bind import (
    load_fixture_norm_binds,
    stamp_issues_with_fixture_norm,
)
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue


class FixtureNormBindTests(unittest.TestCase):
    def test_committed_sidecar_binds_wall_fire_ids(self) -> None:
        binds = load_fixture_norm_binds()
        self.assertIn("Wall Fire Rating Multi", binds)
        self.assertEqual(binds["Wall Fire Rating Multi"]["norm_clause"], "п. 4.4")
        self.assertEqual(binds["Wall Fire Rating Multi"]["norm_source"], "ТЗ (демо-пакет)")

    def test_stamp_fills_empty_clause_only(self) -> None:
        issue = ValidationIssue(
            rule_id="IDS-Wall Fire Rating Multi",
            severity=Severity.ERROR,
            message="[IDS] Wall Fire Rating Multi: fail",
            category=FindingCategory.IDS_VALIDATION,
            element_guid="1XYVUKGoDDbREfVxRKsHkl",
        )
        stamped = stamp_issues_with_fixture_norm((issue,))
        self.assertEqual(stamped[0].norm_clause, "п. 4.4")
        kept = stamp_issues_with_fixture_norm(
            (
                ValidationIssue(
                    rule_id="IDS-Wall Fire Rating Multi",
                    severity=Severity.ERROR,
                    message="x",
                    category=FindingCategory.IDS_VALIDATION,
                    norm_source="already",
                    norm_clause="п. 99",
                ),
            )
        )
        self.assertEqual(kept[0].norm_clause, "п. 99")
