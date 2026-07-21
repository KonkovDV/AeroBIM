"""MEP federated scope wiring in analyze use case."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.mep import UnconfiguredMepSystemGraphProvider
from aerobim.domain.models import CapabilityState
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


def _minimal_uc(**kwargs: object) -> AnalyzeProjectPackageUseCase:
    base = {
        "requirement_extractor": StructuredRequirementExtractor(),
        "narrative_rule_synthesizer": NarrativeRuleSynthesizer(),
        "drawing_analyzer": StructuredDrawingAnalyzer(),
        "ifc_validator": MagicMock(validate=MagicMock(return_value=[])),
        "remark_generator": TemplateRemarkGenerator(),
        "audit_report_store": InMemoryAuditStore(),
        "mep_system_graph_provider": UnconfiguredMepSystemGraphProvider(),
    }
    base.update(kwargs)
    return AnalyzeProjectPackageUseCase(**base)  # type: ignore[arg-type]


class MepFederatedScopeWiringTests(unittest.TestCase):
    def test_verified_scope_with_missing_paths_fails_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scope_path = Path(tmpdir) / "scope.json"
            scope_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "status": "VERIFIED",
                        "federated_ifc_paths": ["missing-hvac.ifc"],
                    }
                ),
                encoding="utf-8",
            )
            ifc = Path(tmpdir) / "model.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(mep_federated_scope_path=scope_path)
            status = uc._probe_mep_system_graph(ifc)
        self.assertEqual(status.status, CapabilityState.FAILED)
        self.assertIn("missing IFC paths", status.reason or "")

    def test_not_verified_template_keeps_not_verified(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        template = repo / "samples" / "mep" / "federated-scope-template.json"
        if not template.exists():
            self.skipTest("template missing")
        with tempfile.TemporaryDirectory() as tmpdir:
            ifc = Path(tmpdir) / "model.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(mep_federated_scope_path=template)
            status = uc._probe_mep_system_graph(ifc)
        self.assertEqual(status.status, CapabilityState.NOT_VERIFIED)
        self.assertIn("scope_status=NOT_VERIFIED", status.reason or "")


if __name__ == "__main__":
    unittest.main()
