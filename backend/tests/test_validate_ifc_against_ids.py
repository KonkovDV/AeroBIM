# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
from aerobim.domain.models import (
    ParsedRequirement,
    RequirementSource,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
)


class FakeExtractor:
    def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
        return [
            ParsedRequirement(
                rule_id="REQ-001",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
            )
        ]


class FakeValidator:
    def validate(
        self, _ifc_path: Path, requirements: list[ParsedRequirement]
    ) -> list[ValidationIssue]:
        requirement = requirements[0]
        return [
            ValidationIssue(
                rule_id=requirement.rule_id,
                severity=Severity.ERROR,
                message="Property value mismatch",
                ifc_entity=requirement.ifc_entity,
                property_set=requirement.property_set,
                property_name=requirement.property_name,
                expected_value=requirement.expected_value,
                observed_value="REI30",
                element_guid="3s2Yw0ExampleGuid",
            )
        ]


class FakeStore:
    def __init__(self) -> None:
        self.saved_report_id: str | None = None

    def save(self, report: ValidationReport) -> str:
        self.saved_report_id = report.report_id
        return report.report_id


class ValidateIfcAgainstIdsUseCaseTests(unittest.TestCase):
    def test_execute_builds_report_and_persists_it(self) -> None:
        store = FakeStore()
        use_case = ValidateIfcAgainstIdsUseCase(FakeExtractor(), FakeValidator(), store)

        report = use_case.execute(
            ValidationRequest(
                request_id="req-001",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(
                    text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                ),
            )
        )

        self.assertEqual(report.summary.requirement_count, 1)
        self.assertEqual(report.summary.issue_count, 1)
        self.assertEqual(report.summary.error_count, 1)
        self.assertFalse(report.summary.passed)
        self.assertEqual(store.saved_report_id, report.report_id)


if __name__ == "__main__":
    unittest.main()
