"""Finding gates are a report grouping, not a 90% accuracy claim."""

from __future__ import annotations

import unittest

from aerobim.domain.finding_gate import classify_finding_gate, stamp_finding_gate
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue


def _issue(**overrides: object) -> ValidationIssue:
    payload = dict(
        rule_id="R-1",
        severity=Severity.ERROR,
        message="x",
        category=FindingCategory.IFC_VALIDATION,
        origin="deterministic",
    )
    payload.update(overrides)
    return ValidationIssue(**payload)  # type: ignore[arg-type]


class FindingGateTests(unittest.TestCase):
    def test_schema_rule_is_schema_gate_deterministic(self) -> None:
        gate, nature = classify_finding_gate(_issue(rule_id="SCHEMA-IFC-HEADER"))
        self.assertEqual(gate, "schema")
        self.assertEqual(nature, "deterministic")

    def test_ids_is_quality(self) -> None:
        gate, nature = classify_finding_gate(
            _issue(category=FindingCategory.IDS_VALIDATION, rule_id="IDS-WALL-001")
        )
        self.assertEqual(gate, "quality")
        self.assertEqual(nature, "deterministic")

    def test_clash_is_regulatory(self) -> None:
        gate, nature = classify_finding_gate(
            _issue(category=FindingCategory.SPATIAL, rule_id="SPATIAL-HARD-CLASH")
        )
        self.assertEqual(gate, "regulatory")
        self.assertEqual(nature, "deterministic")

    def test_advisory_origin_is_probabilistic(self) -> None:
        gate, nature = classify_finding_gate(
            _issue(category=FindingCategory.SPATIAL, origin="advisory")
        )
        self.assertEqual(gate, "regulatory")
        self.assertEqual(nature, "probabilistic")

    def test_stamp_writes_fields_without_touching_severity(self) -> None:
        stamped = stamp_finding_gate(_issue(rule_id="bsi-schema-1"))
        self.assertEqual(stamped.gate_class, "schema")
        self.assertEqual(stamped.answer_nature, "deterministic")
        self.assertEqual(stamped.severity, Severity.ERROR)


if __name__ == "__main__":
    unittest.main()
