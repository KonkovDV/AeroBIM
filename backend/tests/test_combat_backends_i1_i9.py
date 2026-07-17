"""Combat-backend tests: CAD EntityGraph, Hybrid CV, relational I9, MEP opt-in."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.ezdxf_cad_entity_loader import EzdxfCadEntityLoader
from aerobim.infrastructure.adapters.hybrid_drawing_analyzer import HybridDrawingAnalyzer
from aerobim.infrastructure.adapters.ifc_system_aware_clash import IfcSystemAwareClash
from aerobim.infrastructure.adapters.oda_cad_model_ingestor import OdaCadModelIngestor
from aerobim.infrastructure.adapters.relational_ifc_knowledge_graph import (
    RelationalIfcKnowledgeGraph,
)
from aerobim.infrastructure.adapters.unconfigured_system_clash import UnconfiguredSystemClash
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.evaluate_detection_precision import evaluate_detection_precision
from aerobim.tools.evaluate_ifc_qa import evaluate_ifc_qa

_REPO = Path(__file__).resolve().parents[2]
_SAMPLES = _REPO / "samples"


class CombatBackendTests(unittest.TestCase):
    def test_cad_entity_loader_dxf_fixture(self) -> None:
        path = _SAMPLES / "cad" / "minimal-entities.dxf"
        self.assertTrue(path.is_file())
        graph = EzdxfCadEntityLoader().load(path)
        self.assertEqual(graph.format, "dxf")
        assert graph.capability is not None
        # Without ezdxf → SKIPPED; with ezdxf → NOT_VERIFIED (never OK).
        self.assertIn(graph.capability.status.value, {"skipped", "not_verified", "failed"})
        self.assertNotEqual(graph.capability.status.value, "ok")

    def test_oda_stub_disabled_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "a.dwg"
            path.write_bytes(b"AC1015")
            result = OdaCadModelIngestor(enabled=False).ingest(path)
        self.assertFalse(result.supported)
        self.assertIn("ODA", result.reason or "")

    def test_hybrid_degrades_outside_allowlist(self) -> None:
        analyzer = HybridDrawingAnalyzer()
        result = analyzer.analyze(
            DrawingSource(sheet_id="S1", path=None),
            sheet_type="unknown",
        )
        self.assertTrue(result.degraded)
        self.assertIn("allowlist", (result.reason or "").lower())

    def test_hybrid_allowlisted_still_degraded_no_yolo_claim(self) -> None:
        analyzer = HybridDrawingAnalyzer()
        result = analyzer.analyze(
            DrawingSource(sheet_id="AR-01", path=None),
            sheet_type="plan_ar",
        )
        self.assertTrue(result.degraded)
        self.assertNotIn("YOLO weights loaded", result.reason or "")

    def test_relational_ifc_kg_query_walls(self) -> None:
        ifc = _SAMPLES / "ifc" / "wall-pset-qto-pass.ifc"
        result = RelationalIfcKnowledgeGraph().query_nl("Найди стены", ifc_path=ifc)
        self.assertEqual(result.backend, "relational")
        self.assertGreaterEqual(len(result.element_guids), 1)
        self.assertNotIn("93", result.reason or "")

    def test_ifc_qa_fixture_harness(self) -> None:
        report = evaluate_ifc_qa(
            _SAMPLES / "benchmarks" / "ifc-qa-ru" / "questions-fixture.json",
            _SAMPLES / "ifc" / "wall-pset-qto-pass.ifc",
        )
        self.assertEqual(report["artifact_type"], "aerobim_ifc_qa_fixture_evaluation")
        self.assertIn("Fixture", str(report["warning"]))
        self.assertGreaterEqual(float(report["accuracy"]), 0.5)

    def test_precision_per_discipline_and_clash_split(self) -> None:
        report = evaluate_detection_precision(
            _SAMPLES / "benchmarks" / "detection-precision" / "labels-synthetic.json",
            _SAMPLES / "benchmarks" / "detection-precision" / "detections-synthetic.json",
        )
        self.assertIn("per_discipline", report)
        self.assertIn("clash_vs_nonclash", report)
        self.assertIn("clash", report["clash_vs_nonclash"])
        self.assertIn("non_clash", report["clash_vs_nonclash"])

    def test_system_clash_default_unconfigured(self) -> None:
        with self.assertRaises(RuntimeError):
            UnconfiguredSystemClash().detect(Path("x.ifc"))

    def test_system_clash_opt_in_requires_memo(self) -> None:
        adapter = IfcSystemAwareClash(enabled=True, scope_memo_ref=None)
        with self.assertRaises(RuntimeError) as ctx:
            adapter.detect(Path("x.ifc"))
        self.assertIn("SCOPE_MEMO", str(ctx.exception))

    def test_di_wires_relational_kg_and_hybrid(self) -> None:
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
        self.assertIsInstance(
            container.resolve(Tokens.IFC_KNOWLEDGE_GRAPH),
            RelationalIfcKnowledgeGraph,
        )
        self.assertIsInstance(
            container.resolve(Tokens.DRAWING_ANALYZER_PORT),
            HybridDrawingAnalyzer,
        )
        self.assertIsInstance(container.resolve(Tokens.SYSTEM_CLASH), UnconfiguredSystemClash)
        self.assertIsInstance(
            container.resolve(Tokens.ODA_CAD_MODEL_INGESTOR),
            OdaCadModelIngestor,
        )


if __name__ == "__main__":
    unittest.main()
