"""Atomic delivery tests for TZ architecture ports (I9 + SystemClash + aliases)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.application.services.agentic_review_orchestrator import AgenticReviewOrchestrator
from aerobim.application.services.compliance_agent_orchestrator import (
    ComplianceAgentOrchestrator,
)
from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.architecture import CONTOUR_PORTS, Contour
from aerobim.domain.models import DrawingSource, RequirementSource, ValidationRequest
from aerobim.domain.tz_architecture_ports import IfcKnowledgeQueryResult
from aerobim.infrastructure.adapters.deterministic_requirement_interpreter import (
    DeterministicRequirementInterpreter,
)
from aerobim.infrastructure.adapters.deterministic_requirement_to_ids_compiler import (
    DeterministicRequirementToIdsCompiler,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.ezdxf_cad_entity_loader import EzdxfCadEntityLoader
from aerobim.infrastructure.adapters.hybrid_drawing_analyzer import HybridDrawingAnalyzer
from aerobim.infrastructure.adapters.relational_ifc_knowledge_graph import (
    RelationalIfcKnowledgeGraph,
)
from aerobim.infrastructure.adapters.stub_ifc_knowledge_graph import StubIfcKnowledgeGraph
from aerobim.infrastructure.adapters.unconfigured_system_clash import UnconfiguredSystemClash
from aerobim.infrastructure.di.bootstrap import bootstrap_container


class TzArchitecturePortsTests(unittest.TestCase):
    def test_contour_ports_include_tz_aliases(self) -> None:
        self.assertIn("IfcKnowledgeGraphPort", CONTOUR_PORTS[Contour.AI_ADVISORY])
        self.assertIn("AgenticReviewOrchestrator", CONTOUR_PORTS[Contour.AI_ADVISORY])
        self.assertIn("RequirementInterpreterPort", CONTOUR_PORTS[Contour.AI_ADVISORY])
        self.assertIn("SystemClashPort", CONTOUR_PORTS[Contour.DETERMINISTIC_VALIDATION])
        self.assertIn("DrawingAnalyzerPort", CONTOUR_PORTS[Contour.INGESTION])
        self.assertIn("CadEntityLoaderPort", CONTOUR_PORTS[Contour.INGESTION])

    def test_di_resolves_new_tokens(self) -> None:
        tmp = tempfile.mkdtemp()
        settings = Settings(
            application_name="test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(tmp) / "var",
            debug=True,
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        container = bootstrap_container(settings)
        kg = container.resolve(Tokens.IFC_KNOWLEDGE_GRAPH)
        clash = container.resolve(Tokens.SYSTEM_CLASH)
        interpreter = container.resolve(Tokens.REQUIREMENT_INTERPRETER)
        loader = container.resolve(Tokens.CAD_ENTITY_LOADER)
        drawing = container.resolve(Tokens.DRAWING_ANALYZER_PORT)
        agentic = container.resolve(Tokens.AGENTIC_REVIEW_ORCHESTRATOR)
        self.assertIsInstance(kg, RelationalIfcKnowledgeGraph)
        self.assertIsInstance(clash, UnconfiguredSystemClash)
        self.assertIsInstance(interpreter, DeterministicRequirementInterpreter)
        self.assertIsInstance(loader, EzdxfCadEntityLoader)
        self.assertIsInstance(drawing, HybridDrawingAnalyzer)
        self.assertIsInstance(agentic, AgenticReviewOrchestrator)

    def test_stub_ifc_kg_is_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            result = StubIfcKnowledgeGraph().query_nl("walls?", ifc_path=ifc)
        self.assertIsInstance(result, IfcKnowledgeQueryResult)
        self.assertTrue(result.degraded)
        self.assertEqual(result.backend, "stub")
        self.assertEqual(result.element_guids, ())

    def test_system_clash_fail_closed(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            UnconfiguredSystemClash().detect(Path("missing.ifc"))
        self.assertIn("MEP-CLASH-001", str(ctx.exception))

    def test_agent_allowlists_ifc_kg_and_system_clash(self) -> None:
        agent = ComplianceAgentOrchestrator(
            ifc_knowledge_graph=StubIfcKnowledgeGraph(),
            system_clash=UnconfiguredSystemClash(),
            max_steps=4,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            request = ValidationRequest(
                request_id="tz-1",
                ifc_path=ifc,
                requirement_source=RequirementSource(text=""),
            )
            result = agent.run(request)
        names = [step.tool_name for step in result.steps]
        self.assertIn("query_ifc_kg", names)
        self.assertIn("detect_system_clash", names)
        self.assertTrue(
            any(issue.rule_id == "AEROBIM-AGENT-IFC-KG" for issue in result.advisory_issues)
        )
        self.assertTrue(
            any(issue.rule_id == "AEROBIM-AGENT-MEP-CLASH" for issue in result.advisory_issues)
        )

    def test_requirement_interpreter_advisory(self) -> None:
        interpreter = DeterministicRequirementInterpreter(
            DeterministicRequirementToIdsCompiler(StructuredRequirementExtractor())
        )
        rules = interpreter.interpret(
            "R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n",
            locale="ru",
        )
        self.assertGreaterEqual(len(rules), 1)
        self.assertTrue(rules[0].advisory_only)

    def test_cad_entity_loader_dwg_not_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "a.dwg"
            path.write_bytes(b"AC1015")
            graph = EzdxfCadEntityLoader().load(path)
        self.assertEqual(graph.format, "dwg")
        assert graph.capability is not None
        self.assertNotEqual(graph.capability.status.value, "ok")

    def test_drawing_analyzer_port_degrades_without_path(self) -> None:
        port = HybridDrawingAnalyzer()
        annotations = port.analyze(DrawingSource(sheet_id="S1", path=None))
        self.assertTrue(annotations.degraded)

    def test_stub_kg_still_available_for_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            result = StubIfcKnowledgeGraph().query_nl("walls?", ifc_path=ifc)
        self.assertTrue(result.degraded)
        self.assertEqual(result.backend, "stub")


if __name__ == "__main__":
    unittest.main()
