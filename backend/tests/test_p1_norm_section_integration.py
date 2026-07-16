from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    CapabilityState,
    GeneratedRemark,
    RequirementSource,
    Severity,
    ValidationReport,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader
from aerobim.infrastructure.adapters.json_section_diff_analyzer import JsonSectionDiffAnalyzer

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PACK = REPO_ROOT / "samples" / "rule-packs" / "residential-ar-reference-template.json"
PD_SECTION = REPO_ROOT / "samples" / "sections" / "ar-pd-synthetic.json"
RD_SECTION = REPO_ROOT / "samples" / "sections" / "ar-rd-synthetic.json"


class _EmptyExtractor:
    def extract(self, _source):
        return []


class _EmptySynthesizer:
    def synthesize(self, _source):
        return []


class _EmptyDrawingAnalyzer:
    def analyze(self, _source):
        return []


class _CapturingIfcValidator:
    def __init__(self) -> None:
        self.requirements = ()

    def validate(self, _ifc_path, requirements):
        self.requirements = tuple(requirements)
        return []


class _RemarkGenerator:
    def generate(self, issue):
        return GeneratedRemark(title=issue.rule_id, body=issue.message)


class _Store:
    def __init__(self) -> None:
        self.report: ValidationReport | None = None

    def save(self, report: ValidationReport) -> str:
        self.report = report
        return report.report_id

    def get(self, report_id: str) -> ValidationReport | None:
        if self.report is not None and self.report.report_id == report_id:
            return self.report
        return None


class P1NormSectionIntegrationTests(unittest.TestCase):
    def test_norm_pack_and_section_pair_run_in_single_analysis(self) -> None:
        validator = _CapturingIfcValidator()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=_EmptyExtractor(),
            narrative_rule_synthesizer=_EmptySynthesizer(),
            drawing_analyzer=_EmptyDrawingAnalyzer(),
            ifc_validator=validator,
            remark_generator=_RemarkGenerator(),
            audit_report_store=_Store(),
            norm_rule_pack_loader=JsonNormRulePackLoader(),
            section_diff_analyzer=JsonSectionDiffAnalyzer(severity=Severity.WARNING),
        )
        report = use_case.execute(
            ValidationRequest(
                request_id="p1-integration",
                ifc_path=Path("synthetic.ifc"),
                requirement_source=RequirementSource(),
                norm_rule_pack_paths=(REFERENCE_PACK,),
                pd_section_path=PD_SECTION,
                rd_section_path=RD_SECTION,
            )
        )

        self.assertEqual(report.summary.requirement_count, 20)
        self.assertEqual(len(validator.requirements), 20)
        self.assertEqual(report.summary.issue_count, 3)
        self.assertTrue(report.summary.passed)
        self.assertEqual(report.capabilities.norm_rule_packs.status, CapabilityState.OK)
        self.assertEqual(report.capabilities.section_pairing.status, CapabilityState.OK)
        self.assertIn("synthetic-template", report.capabilities.norm_rule_packs.reason or "")
        # Enriched section-pairing capability: canonical discipline + key coverage.
        section_reason = report.capabilities.section_pairing.reason or ""
        self.assertIn("canonical-key coverage", section_reason)
        self.assertIn("AR", section_reason)

    def test_incomplete_section_pair_request_fails_closed(self) -> None:
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=_EmptyExtractor(),
            narrative_rule_synthesizer=_EmptySynthesizer(),
            drawing_analyzer=_EmptyDrawingAnalyzer(),
            ifc_validator=_CapturingIfcValidator(),
            remark_generator=_RemarkGenerator(),
            audit_report_store=_Store(),
            norm_rule_pack_loader=JsonNormRulePackLoader(),
            section_diff_analyzer=JsonSectionDiffAnalyzer(),
        )
        request = ValidationRequest(
            request_id="incomplete-pair",
            ifc_path=Path("synthetic.ifc"),
            requirement_source=RequirementSource(),
            norm_rule_pack_paths=(REFERENCE_PACK,),
            pd_section_path=PD_SECTION,
        )

        with self.assertRaisesRegex(ValueError, "requires both"):
            use_case.execute(request)


if __name__ == "__main__":
    unittest.main()
