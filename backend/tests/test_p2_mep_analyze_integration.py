"""P2-02 integration: federated MEP ENG_FIXTURE scope on full analyze path."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import CapabilityState, RequirementSource, Severity, ValidationRequest
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.scoped_mep_system_graph_provider import (
    ScopedMepSystemGraphProvider,
)
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator

REPO = Path(__file__).resolve().parents[2]
MEP_IFC = REPO / "samples" / "mep" / "hvac-sprinkler-systems.ifc"
VERIFIED_SCOPE = REPO / "samples" / "mep" / "federated-scope-verified-fixture.json"
REQ = REPO / "samples" / "requirements" / "techlab-demo-rules.txt"


def _minimal_uc(**kwargs: object) -> AnalyzeProjectPackageUseCase:
    base = {
        "requirement_extractor": StructuredRequirementExtractor(),
        "narrative_rule_synthesizer": NarrativeRuleSynthesizer(),
        "drawing_analyzer": StructuredDrawingAnalyzer(),
        "ifc_validator": MagicMock(validate=MagicMock(return_value=[])),
        "remark_generator": TemplateRemarkGenerator(),
        "audit_report_store": InMemoryAuditStore(),
    }
    base.update(kwargs)
    return AnalyzeProjectPackageUseCase(**base)  # type: ignore[arg-type]


class MepAnalyzeIntegrationTests(unittest.TestCase):
    def test_eng_fixture_scope_matrix_honesty_on_analyze_path(self) -> None:
        if not MEP_IFC.exists() or not VERIFIED_SCOPE.exists():
            self.skipTest("MEP fixture missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")
        if not REQ.exists():
            self.skipTest("requirement fixture missing")

        scoped = ScopedMepSystemGraphProvider(scope_path=VERIFIED_SCOPE, repo_root=REPO)
        uc = _minimal_uc(
            mep_system_graph_provider=scoped,
            mep_federated_scope_path=VERIFIED_SCOPE,
            require_mep_system_clash=True,
        )
        report = uc.execute(
            ValidationRequest(
                request_id="p2-mep-analyze-eng-fixture",
                ifc_path=MEP_IFC,
                requirement_source=RequirementSource(
                    text=REQ.read_text(encoding="utf-8"),
                    path=REQ,
                ),
            )
        )

        assert report.capabilities is not None
        mep_cap = report.capabilities.mep_system_clash
        self.assertEqual(mep_cap.status, CapabilityState.NOT_VERIFIED)
        reason = (mep_cap.reason or "").lower()
        self.assertTrue(
            "eng_fixture" in reason or "synthetic" in reason,
            msg=mep_cap.reason,
        )
        self.assertNotEqual(mep_cap.status, CapabilityState.OK)
        self.assertFalse(report.summary.passed)

        template_issues = [
            issue for issue in report.issues if issue.rule_id == "AEROBIM-MEP-TEMPLATE"
        ]
        self.assertTrue(template_issues)
        self.assertTrue(all(issue.severity == Severity.WARNING for issue in template_issues))
        forbidden_errors = [
            issue
            for issue in report.issues
            if issue.rule_id == "AEROBIM-MEP-FORBIDDEN" and issue.severity == Severity.ERROR
        ]
        self.assertEqual(forbidden_errors, [])


if __name__ == "__main__":
    unittest.main()
