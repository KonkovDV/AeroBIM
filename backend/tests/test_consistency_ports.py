from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.consistency import PackageManifest, claims_from_area_requirements
from aerobim.domain.models import (
    DrawingSource,
    ParsedRequirement,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.ifc_quantity_consistency_adapter import (
    IfcQuantityConsistencyAdapter,
)
from aerobim.infrastructure.adapters.manifest_logic_consistency_adapter import (
    ManifestLogicConsistencyAdapter,
)
from aerobim.infrastructure.adapters.ocr_fallback_multimodal_drawing_pipeline import (
    OcrFallbackMultimodalDrawingPipeline,
)
from aerobim.infrastructure.adapters.spreadsheet_load_evidence_adapter import (
    SpreadsheetLoadEvidenceAdapter,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container


class ConsistencyPortsTests(unittest.TestCase):
    def test_claims_from_area_requirements(self) -> None:
        reqs = [
            ParsedRequirement(
                rule_id="A1",
                ifc_entity="IFCSPACE",
                property_name="GrossFloorArea",
                expected_value="120.5",
                unit="m2",
            ),
            ParsedRequirement(
                rule_id="T1",
                ifc_entity="IFCWALL",
                property_name="Thickness",
                expected_value="200",
                unit="mm",
            ),
        ]
        claims = claims_from_area_requirements(reqs)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].quantity_name, "GrossFloorArea")

    def test_load_match_and_mismatch(self) -> None:
        adapter = SpreadsheetLoadEvidenceAdapter()
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            ok = ValidationRequest(
                request_id="r1",
                ifc_path=ifc,
                requirement_source=RequirementSource(text="R|IFCWALL|P|T|1"),
                calculation_source=RequirementSource(
                    text="LOAD|L1|snow|10|kN|10\n",
                    source_kind=SourceKind.CALCULATION,
                ),
            )
            issues_ok = adapter.verify(ok)
            self.assertFalse(any(i.rule_id == "AEROBIM-LOAD-MISMATCH" for i in issues_ok))
            self.assertTrue(any(i.rule_id == "AEROBIM-LOAD-OK" for i in issues_ok))

            bad = ValidationRequest(
                request_id="r2",
                ifc_path=ifc,
                requirement_source=RequirementSource(text="R|IFCWALL|P|T|1"),
                calculation_source=RequirementSource(
                    text='{"loads":[{"id":"L1","expected":10,"observed":12,"unit":"kN"}]}',
                    source_kind=SourceKind.CALCULATION,
                ),
            )
            issues_bad = adapter.verify(bad)
            self.assertTrue(any(i.rule_id == "AEROBIM-LOAD-MISMATCH" for i in issues_bad))

            empty = ValidationRequest(
                request_id="r3",
                ifc_path=ifc,
                requirement_source=RequirementSource(text="R|IFCWALL|P|T|1"),
                calculation_source=RequirementSource(
                    text="   ",
                    source_kind=SourceKind.CALCULATION,
                ),
            )
            issues_empty = adapter.verify(empty)
            self.assertTrue(any(i.rule_id == "AEROBIM-LOAD-FORMAT" for i in issues_empty))

            schema = ValidationRequest(
                request_id="r4",
                ifc_path=ifc,
                requirement_source=RequirementSource(text="R|IFCWALL|P|T|1"),
                calculation_source=RequirementSource(
                    text='{"loads":[]}',
                    source_kind=SourceKind.CALCULATION,
                ),
            )
            issues_schema = adapter.verify(schema)
            self.assertTrue(any(i.rule_id == "AEROBIM-LOAD-FORMAT" for i in issues_schema))

            # RT-CALC-004: non-dict JSON rows must not greenwash LOAD-OK.
            mixed = ValidationRequest(
                request_id="r5",
                ifc_path=ifc,
                requirement_source=RequirementSource(text="R|IFCWALL|P|T|1"),
                calculation_source=RequirementSource(
                    text=(
                        '{"loads":[{"id":"L1","expected":10,"observed":10,"unit":"kN"},'
                        '"bad",{"id":"L2","expected":5,"observed":5,"unit":"kN"}]}'
                    ),
                    source_kind=SourceKind.CALCULATION,
                ),
            )
            issues_mixed = adapter.verify(mixed)
            self.assertTrue(any(i.rule_id == "AEROBIM-LOAD-ROW" for i in issues_mixed))
            self.assertFalse(any(i.rule_id == "AEROBIM-LOAD-OK" for i in issues_mixed))

            # RT-CALC-005: tabular text must not shadow disagreeing .json path.
            json_path = Path(temporary_directory) / "loads.json"
            json_path.write_text(
                '{"loads":[{"id":"L1","expected":10,"observed":99,"unit":"kN"}]}',
                encoding="utf-8",
            )
            dual = ValidationRequest(
                request_id="r6",
                ifc_path=ifc,
                requirement_source=RequirementSource(text="R|IFCWALL|P|T|1"),
                calculation_source=RequirementSource(
                    text="LOAD|L1|snow|10|kN|10\n",
                    path=json_path,
                    source_kind=SourceKind.CALCULATION,
                ),
            )
            issues_dual = adapter.verify(dual)
            self.assertTrue(any(i.rule_id == "AEROBIM-LOAD-FORMAT" for i in issues_dual))
            self.assertTrue(any(i.rule_id == "AEROBIM-LOAD-MISMATCH" for i in issues_dual))
            self.assertFalse(any(i.rule_id == "AEROBIM-LOAD-OK" for i in issues_dual))

    def test_logic_pd_without_rd(self) -> None:
        adapter = ManifestLogicConsistencyAdapter()
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            issues = adapter.analyze(
                PackageManifest(
                    request_id="r",
                    ifc_path=base / "a.ifc",
                    has_requirement_source=True,
                    has_technical_spec=False,
                    has_calculation_source=False,
                    has_ids=False,
                    drawing_count=1,
                    drawing_sheet_ids=("",),
                    pd_section_path=base / "pd.json",
                    rd_section_path=None,
                    revision=None,
                    stage=None,
                )
            )
        rules = {i.rule_id for i in issues}
        self.assertIn("AEROBIM-LOGIC-PD-WITHOUT-RD", rules)
        self.assertIn("AEROBIM-LOGIC-ORPHAN-SHEET", rules)

    def test_multimodal_degrades_without_raster(self) -> None:
        pipeline = OcrFallbackMultimodalDrawingPipeline(raster_analyzer=None)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "sheet.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            result = pipeline.analyze(DrawingSource(path=path), mode="detector_vlm")
        self.assertTrue(result.degraded)
        self.assertEqual(result.pipeline_mode_used, "unavailable")
        self.assertIn("VLM", result.reason or "")

    def test_i8a_heuristic_detector_regions_without_raster(self) -> None:
        from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (
            HeuristicLayoutRegionDetector,
        )

        pipeline = OcrFallbackMultimodalDrawingPipeline(
            raster_analyzer=None,
            region_detector=HeuristicLayoutRegionDetector(),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "sheet.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            result = pipeline.analyze(
                DrawingSource(path=path, sheet_id="AR-01"),
                mode="auto",
            )
        self.assertTrue(result.degraded)
        self.assertEqual(result.pipeline_mode_used, "detector_only")
        self.assertGreaterEqual(len(result.regions), 3)
        self.assertTrue(all(r.modality == "detector" for r in result.regions))
        self.assertIn("MISSING", result.reason or "")

    def test_quantity_empty_claims_noop(self) -> None:
        adapter = IfcQuantityConsistencyAdapter()
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            self.assertEqual(adapter.check(ifc, []), [])

    def test_bootstrap_registers_i2b_i3_tokens(self) -> None:
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
        for token in (
            Tokens.QUANTITY_CONSISTENCY_CHECKER,
            Tokens.LOAD_EVIDENCE_VERIFIER,
            Tokens.LOGIC_CONSISTENCY_ANALYZER,
            Tokens.MULTIMODAL_DRAWING_PIPELINE,
            Tokens.DRAWING_REGION_DETECTOR,
        ):
            self.assertTrue(container.is_registered(token), token)
        detector = container.resolve(Tokens.DRAWING_REGION_DETECTOR)
        self.assertEqual(type(detector).__name__, "HeuristicLayoutRegionDetector")


if __name__ == "__main__":
    unittest.main()
