from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.di.tokens import Tokens
from aerobim.domain.architecture import CONTOUR_PORTS, Contour
from aerobim.domain.mep import (
    MepClashMatrix,
    MepClearanceClass,
    MepClearanceRule,
    MepSystem,
    MepSystemGraph,
    MepSystemNode,
    SyntheticMepSystemGraphProvider,
    UnconfiguredMepSystemGraphProvider,
    evaluate_matrix_against_graph,
    evaluate_system_pair,
)
from aerobim.domain.models import (
    CapabilityState,
    RequirementSource,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


def _minimal_uc(**kwargs):
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


def _sample_matrix() -> MepClashMatrix:
    return MepClashMatrix(
        scope_memo_ref="SYNTHETIC-SCOPE",
        synthetic=True,
        claim_boundary="unit-test only",
        rules=(
            MepClearanceRule(
                system_a="HVAC-SUPPLY",
                system_b="SPRINKLER",
                allowed_intersection=False,
                clearance_class=MepClearanceClass.HARD,
                min_clearance_m=0.05,
                priority=10,
                exception_kinds=("sleeve",),
                discipline_a="OV",
                discipline_b="PT",
            ),
            MepClearanceRule(
                system_a="HVAC-SUPPLY",
                system_b="CABLE-TRAY",
                allowed_intersection=True,
                clearance_class=MepClearanceClass.SOFT,
                exception_kinds=("intentional_containment",),
            ),
        ),
    )


class MepSystemGraphContractTests(unittest.TestCase):
    def test_unconfigured_provider_fails_closed(self) -> None:
        provider = UnconfiguredMepSystemGraphProvider()
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake = Path(temporary_directory) / "mep.ifc"
            fake.write_text("ISO-10303-21;", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "MEP-CLASH-001"):
                provider.build(fake)

    def test_mep_port_in_deterministic_contour_and_token_exists(self) -> None:
        self.assertIn("MepSystemGraphProvider", CONTOUR_PORTS[Contour.DETERMINISTIC_VALIDATION])
        self.assertEqual(Tokens.MEP_SYSTEM_GRAPH_PROVIDER, "mep_system_graph_provider")

    def test_synthetic_provider_builds_multi_system_graph(self) -> None:
        provider = SyntheticMepSystemGraphProvider()
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake = Path(temporary_directory) / "synthetic.ifc"
            fake.write_text("ISO-10303-21;", encoding="utf-8")
            graph = provider.build(fake)
        self.assertTrue(graph.synthetic)
        self.assertGreaterEqual(len(graph.nodes), 3)
        self.assertGreaterEqual(len(graph.edges), 2)
        ids = {node.system_id for node in graph.nodes}
        self.assertIn("HVAC-SUPPLY", ids)
        self.assertIn("SPRINKLER", ids)

    def test_allowed_intersection_does_not_create_finding(self) -> None:
        hvac = MepSystem(
            system_id="HVAC-SUPPLY",
            system_type="HVAC",
            discipline="OV",
            element_guids=("a",),
        )
        tray = MepSystem(
            system_id="CABLE-TRAY",
            system_type="EL",
            discipline="EL",
            element_guids=("b",),
        )
        finding = evaluate_system_pair(
            system_a=hvac,
            system_b=tray,
            matrix=_sample_matrix(),
            intersecting=True,
        )
        self.assertIsNone(finding)

    def test_forbidden_intersection_creates_finding_with_provenance(self) -> None:
        hvac = MepSystemNode(
            system_id="HVAC-SUPPLY",
            system_type="HVAC",
            discipline="OV",
            element_guids=("guid-hvac",),
            source_ifc="unit.ifc",
        )
        spk = MepSystemNode(
            system_id="SPRINKLER",
            system_type="FIRE",
            discipline="PT",
            element_guids=("guid-spk",),
        )
        finding = evaluate_system_pair(
            system_a=hvac,
            system_b=spk,
            matrix=_sample_matrix(),
            source_ifc="unit.ifc",
            intersecting=True,
        )
        assert finding is not None
        self.assertEqual(finding.verdict, "forbidden")
        self.assertEqual(finding.capability_hint, "error")
        self.assertEqual(finding.clearance_class, MepClearanceClass.HARD)
        self.assertEqual(finding.element_guid_a, "guid-hvac")
        self.assertEqual(finding.element_guid_b, "guid-spk")
        self.assertEqual(finding.exception_kinds, ("sleeve",))
        self.assertEqual(finding.priority, 10)
        self.assertEqual(finding.source_ifc, "unit.ifc")

    def test_unclassified_pair_is_not_verified_not_confident_error(self) -> None:
        a = MepSystem(system_id="DRAIN", system_type="PL", discipline="VK")
        b = MepSystem(system_id="GAS", system_type="GAS", discipline="GSV")
        finding = evaluate_system_pair(
            system_a=a,
            system_b=b,
            matrix=_sample_matrix(),
            intersecting=True,
        )
        assert finding is not None
        self.assertEqual(finding.verdict, "unclassified")
        self.assertEqual(finding.capability_hint, "not_verified")
        self.assertIn("NOT_VERIFIED", finding.message)

    def test_matrix_eval_integration_multi_systems(self) -> None:
        provider = SyntheticMepSystemGraphProvider()
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake = Path(temporary_directory) / "multi.ifc"
            fake.write_text("ISO-10303-21;", encoding="utf-8")
            graph = provider.build(fake)
        findings = evaluate_matrix_against_graph(graph, _sample_matrix())
        verdicts = {f.verdict for f in findings}
        # HVAC↔SPRINKLER forbidden; HVAC↔CABLE-TRAY allowed (no finding);
        # SPRINKLER↔CABLE-TRAY unclassified.
        self.assertIn("forbidden", verdicts)
        self.assertIn("unclassified", verdicts)
        self.assertTrue(all(f.verdict != "allowed" for f in findings))
        forbidden = next(f for f in findings if f.verdict == "forbidden")
        self.assertEqual(forbidden.clearance_class, MepClearanceClass.HARD)

    def test_missing_provider_with_require_mep_blocks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(
                mep_system_graph_provider=None,
                require_mep_system_clash=True,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="mep-missing",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.mep_system_clash.status, CapabilityState.NOT_VERIFIED)
        self.assertFalse(report.summary.passed)

    def test_unconfigured_provider_with_require_mep_not_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(
                mep_system_graph_provider=UnconfiguredMepSystemGraphProvider(),
                require_mep_system_clash=True,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="mep-unconfigured",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.mep_system_clash.status, CapabilityState.NOT_VERIFIED)
        self.assertIn("MEP-CLASH-001", report.capabilities.mep_system_clash.reason or "")
        self.assertFalse(report.summary.passed)

    def test_synthetic_provider_never_grants_ok_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(
                mep_system_graph_provider=SyntheticMepSystemGraphProvider(),
                require_mep_system_clash=True,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="mep-synthetic",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.mep_system_clash.status, CapabilityState.NOT_VERIFIED)
        self.assertIn("synthetic", (report.capabilities.mep_system_clash.reason or "").lower())
        self.assertNotEqual(report.capabilities.mep_system_clash.status, CapabilityState.OK)
        self.assertFalse(report.summary.passed)

    def test_empty_graph_from_custom_provider_stays_not_verified(self) -> None:
        class _EmptyGraph:
            def build(self, ifc_path):  # noqa: ANN001
                return MepSystemGraph(nodes=(), edges=(), source_ifc=str(ifc_path))

        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(
                mep_system_graph_provider=_EmptyGraph(),
                require_mep_system_clash=True,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="mep-empty",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.mep_system_clash.status, CapabilityState.NOT_VERIFIED)


if __name__ == "__main__":
    unittest.main()
