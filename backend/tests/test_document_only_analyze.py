"""Task 2 — document/partial package analyze without IFC (honest SKIPPED)."""

from __future__ import annotations

import unittest

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    CapabilityState,
    DrawingSource,
    GeneratedRemark,
    ParsedRequirement,
    RequirementSource,
    SourceKind,
    ValidationReport,
    ValidationRequest,
)


class _Empty:
    def extract(self, _source):
        return []

    def synthesize(self, _source):
        return []

    def analyze(self, _source):
        return []

    def validate(self, *_args, **_kwargs):
        return []


class _Remark:
    def generate(self, issue):
        return GeneratedRemark(title=issue.rule_id, body=issue.message)


class _Store:
    def __init__(self) -> None:
        self.report = None

    def save(self, report):
        self.report = report
        return report.report_id

    def get(self, report_id):
        if self.report is not None and self.report.report_id == report_id:
            return self.report
        return None


class _Extractor:
    def extract(self, _source):
        return [
            ParsedRequirement(
                rule_id="REQ-DOC-001",
                ifc_entity="IFCWALL",
                property_name="Height",
                expected_value="3.0",
                unit="m",
            )
        ]


class DocumentOnlyAnalyzeTests(unittest.TestCase):
    def test_analyze_without_ifc_skips_model_engines(self) -> None:
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=_Extractor(),
            narrative_rule_synthesizer=_Empty(),
            drawing_analyzer=_Empty(),
            ifc_validator=_Empty(),
            remark_generator=_Remark(),
            audit_report_store=_Store(),
            signoff_profile="fixture",
        )
        request = ValidationRequest(
            request_id="doc-only-1",
            ifc_path=None,
            requirement_source=RequirementSource(
                text="Wall height shall be 3.0 m",
                source_kind=SourceKind.STRUCTURED_TEXT,
            ),
            drawing_sources=(
                DrawingSource(
                    text="Sheet AR-01 wall height 2.8 m",
                    sheet_id="AR-01",
                    format="txt",
                ),
            ),
        )
        report = use_case.execute(request)
        self.assertIsInstance(report, ValidationReport)
        self.assertIsNone(report.ifc_path)
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.clash.status, CapabilityState.SKIPPED)
        self.assertIn("ifc_path omitted", report.capabilities.clash.reason or "")
        self.assertEqual(report.capabilities.quantity.status, CapabilityState.SKIPPED)


if __name__ == "__main__":
    unittest.main()
