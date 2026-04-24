from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.use_cases.analyze_project_package import (
    AnalyzeProjectPackageUseCase,
    build_openrebar_provenance_digest,
)
from aerobim.domain.models import (
    ComparisonOperator,
    DrawingAnnotation,
    DrawingSource,
    FindingCategory,
    ParsedRequirement,
    ProblemZone,
    RequirementSource,
    RuleScope,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


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


class FakeSynthesizer:
    def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
        return [
            ParsedRequirement(
                rule_id="REQ-DRW-001",
                ifc_entity="IFCWALL",
                rule_scope=RuleScope.DRAWING_ANNOTATION,
                target_ref="WALL-01",
                property_name="thickness",
                operator=ComparisonOperator.GREATER_OR_EQUAL,
                expected_value="200",
                unit="mm",
                source_kind=SourceKind.TECHNICAL_SPECIFICATION,
            )
        ]


class FakeDrawingAnalyzer:
    def analyze(self, _source: DrawingSource) -> list[DrawingAnnotation]:
        return [
            DrawingAnnotation(
                annotation_id="ANN-001",
                sheet_id="A-101",
                target_ref="WALL-01",
                measure_name="thickness",
                observed_value="150",
                unit="mm",
                problem_zone=ProblemZone(
                    sheet_id="A-101", page_number=1, x=10, y=20, width=100, height=50
                ),
            )
        ]


class FakeValidator:
    def validate(
        self, _ifc_path: Path, _requirements: list[ParsedRequirement]
    ) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                rule_id="REQ-001",
                severity=Severity.ERROR,
                message="Property value mismatch",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
                observed_value="REI30",
                element_guid="3s2Yw0ExampleGuid",
            )
        ]


class FakeIdsValidator:
    def validate(self, _ids_path: Path, _ifc_path: Path) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                rule_id="IDS-001",
                severity=Severity.WARNING,
                message="IDS mismatch",
                category=FindingCategory.IDS_VALIDATION,
                element_guid="ids-element-guid",
            )
        ]


class NoOpIdsValidator:
    def validate(self, _ids_path: Path, _ifc_path: Path) -> list[ValidationIssue]:
        return []


class FakeVisionDrawingAnalyzer:
    def analyze_image(
        self,
        _image_path: Path,
        sheet_id: str | None = None,
    ) -> list[DrawingAnnotation]:
        return [
            DrawingAnnotation(
                annotation_id="VLM-ANN-001",
                sheet_id=sheet_id or "IMG-001",
                target_ref="WALL-IMG-01",
                measure_name="thickness",
                observed_value="220",
                unit="mm",
                problem_zone=ProblemZone(
                    sheet_id=sheet_id or "IMG-001",
                    page_number=1,
                    x=5,
                    y=10,
                    width=50,
                    height=20,
                ),
                source="vision-analyzer",
            )
        ]


class FakeStore:
    def __init__(self) -> None:
        self.saved_report_id: str | None = None
        self.report: ValidationReport | None = None

    def save(self, report: ValidationReport) -> str:
        self.saved_report_id = report.report_id
        self.report = report
        return report.report_id

    def get(self, report_id: str) -> ValidationReport | None:
        if self.report is None or self.report.report_id != report_id:
            return None
        return self.report


def _build_openrebar_report_payload(
    *,
    fallback_used: bool,
    master_problem_strategy: str = "restricted-master-lp-highs",
    total_waste_percent: float = 0.0,
) -> dict[str, object]:
    return {
        "contractId": "OpenRebar.reinforcement.report.v1",
        "schemaVersion": "1.0.0",
        "generatedAtUtc": "2026-04-16T00:00:00Z",
        "metadata": {
            "projectCode": "Residential Tower Alpha",
            "slabId": "SLAB-03",
            "sourceSystem": "OpenRebar",
            "targetSystem": "AeroBIM",
            "countryCode": "RU",
            "designCode": "SP63",
            "normativeProfileId": "ru.sp63.2018",
            "normativeTablesVersion": "v1",
        },
        "normativeProfile": {
            "profileId": "ru.sp63.2018",
            "jurisdiction": "RU",
            "designCode": "SP63",
            "tablesVersion": "v1",
        },
        "analysisProvenance": {
            "geometry": {
                "decompositionAlgorithm": "grid-scan",
                "rectangularShortcutFillRatio": 0.9,
                "minRectangleAreaMm2": 1000.0,
                "samplingResolutionPerAxis": 64,
                "cellCoverageInclusionThreshold": 0.5,
            },
            "optimization": {
                "optimizerId": "column-generation",
                "masterProblemStrategy": master_problem_strategy,
                "pricingStrategy": "bounded-knapsack-dp",
                "integerizationStrategy": "repair-ffd",
                "demandAggregationPrecisionMm": 0.1,
                "qualityFloor": "production",
                "anyFallbackMasterSolverUsed": fallback_used,
            },
        },
        "isolineFileName": "floor-03.dxf",
        "isolineFileFormat": "dxf",
        "slab": {
            "concreteClass": "B25",
            "thicknessMm": 200,
            "coverMm": 25,
            "effectiveDepthMm": 175,
            "areaMm2": 1_000_000,
            "openingCount": 0,
            "boundingBox": {
                "minX": 0,
                "minY": 0,
                "maxX": 1000,
                "maxY": 1000,
                "width": 1000,
                "height": 1000,
            },
        },
        "zones": [],
        "optimizationByDiameter": [],
        "placement": {
            "requested": False,
            "executed": False,
            "success": True,
            "totalRebarsPlaced": 0,
            "totalTagsCreated": 0,
            "totalBendingDetails": 0,
            "warnings": [],
            "errors": [],
        },
        "summary": {
            "parsedZoneCount": 0,
            "classifiedZoneCount": 0,
            "totalRebarSegments": 0,
            "totalWastePercent": total_waste_percent,
            "totalWasteMm": 0.0,
            "totalMassKg": 0.0,
        },
    }


class AnalyzeProjectPackageUseCaseTests(unittest.TestCase):
    def test_execute_builds_multimodal_report_with_generated_remarks(self) -> None:
        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=FakeExtractor(),
            narrative_rule_synthesizer=FakeSynthesizer(),
            drawing_analyzer=FakeDrawingAnalyzer(),
            ifc_validator=FakeValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-001",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(
                    text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                ),
                technical_spec_source=RequirementSource(
                    text="Лист A-101: толщина WALL-01 не менее 200 мм",
                    source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                ),
                drawing_sources=(
                    DrawingSource(text="ANN-001|A-101|WALL-01|thickness|150|mm|1|10|20|100|50"),
                ),
            )
        )

        self.assertEqual(report.summary.requirement_count, 2)
        self.assertEqual(report.summary.issue_count, 2)
        self.assertEqual(report.summary.error_count, 2)
        self.assertEqual(report.summary.drawing_annotation_count, 1)
        self.assertEqual(report.summary.generated_remark_count, 2)
        self.assertEqual(len(report.drawing_annotations), 1)
        self.assertTrue(all(issue.remark is not None for issue in report.issues))
        self.assertEqual(store.saved_report_id, report.report_id)

    def test_execute_copies_project_metadata_into_report(self) -> None:
        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=FakeExtractor(),
            narrative_rule_synthesizer=FakeSynthesizer(),
            drawing_analyzer=FakeDrawingAnalyzer(),
            ifc_validator=FakeValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-metadata",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(
                    text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                ),
                technical_spec_source=RequirementSource(
                    text="Лист A-101: толщина WALL-01 не менее 200 мм",
                    source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                ),
                project_name="Residential Tower Alpha",
                discipline="structure",
            )
        )

        self.assertEqual(report.project_name, "Residential Tower Alpha")
        self.assertEqual(report.discipline, "structure")
        assert store.report is not None
        self.assertEqual(store.report.project_name, "Residential Tower Alpha")
        self.assertEqual(store.report.discipline, "structure")

    def test_execute_merges_ids_issues_into_multimodal_report(self) -> None:
        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=FakeExtractor(),
            narrative_rule_synthesizer=FakeSynthesizer(),
            drawing_analyzer=FakeDrawingAnalyzer(),
            ifc_validator=FakeValidator(),
            ids_validator=FakeIdsValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-ids-multimodal",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(
                    text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                ),
                technical_spec_source=RequirementSource(
                    text="Лист A-101: толщина WALL-01 не менее 200 мм",
                    source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                ),
                drawing_sources=(
                    DrawingSource(text="ANN-001|A-101|WALL-01|thickness|150|mm|1|10|20|100|50"),
                ),
                ids_path=Path("rules.ids"),
            )
        )

        ids_issues = [
            issue for issue in report.issues if issue.category == FindingCategory.IDS_VALIDATION
        ]
        self.assertEqual(len(ids_issues), 1)
        self.assertEqual(report.summary.issue_count, 3)
        self.assertEqual(report.summary.warning_count, 1)
        self.assertEqual(report.summary.generated_remark_count, 3)

    def test_execute_accepts_ids_only_validation_path(self) -> None:
        class EmptyExtractor:
            def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class EmptySynthesizer:
            def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpDrawingAnalyzer:
            def analyze(self, _source: DrawingSource) -> list[DrawingAnnotation]:
                return []

        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=EmptyExtractor(),
            narrative_rule_synthesizer=EmptySynthesizer(),
            drawing_analyzer=NoOpDrawingAnalyzer(),
            ifc_validator=FakeValidator(),
            ids_validator=FakeIdsValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-ids-only",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(text=""),
                ids_path=Path("rules.ids"),
            )
        )

        self.assertEqual(report.summary.requirement_count, 0)
        self.assertEqual(report.summary.issue_count, 1)
        self.assertEqual(report.summary.warning_count, 1)
        self.assertEqual(report.issues[0].category, FindingCategory.IDS_VALIDATION)

    def test_execute_routes_pdf_drawings_to_vision_analyzer(self) -> None:
        class ExplodingStructuredAnalyzer:
            def analyze(self, _source: DrawingSource) -> list[DrawingAnnotation]:
                raise AssertionError(
                    "Structured analyzer should not be used for pure PDF/image input"
                )

        class NoOpExtractor:
            def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpSynthesizer:
            def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpValidator:
            def validate(
                self,
                _ifc_path: Path,
                _requirements: list[ParsedRequirement],
            ) -> list[ValidationIssue]:
                return []

        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=NoOpExtractor(),
            narrative_rule_synthesizer=NoOpSynthesizer(),
            drawing_analyzer=ExplodingStructuredAnalyzer(),
            ifc_validator=NoOpValidator(),
            ids_validator=FakeIdsValidator(),
            vision_drawing_analyzer=FakeVisionDrawingAnalyzer(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-vision-pdf",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(text=""),
                ids_path=Path("rules.ids"),
                drawing_sources=(
                    DrawingSource(
                        text="",
                        path=Path("sheet-openrebar.pdf"),
                        sheet_id="A-101",
                        format="pdf",
                    ),
                ),
            )
        )

        self.assertEqual(report.summary.drawing_annotation_count, 1)
        self.assertEqual(report.drawing_annotations[0].source, "vision-analyzer")
        self.assertEqual(report.drawing_annotations[0].sheet_id, "A-101")
        self.assertEqual(len(report.drawing_assets), 1)
        self.assertEqual(report.drawing_assets[0].sheet_id, "A-101")
        self.assertEqual(report.drawing_assets[0].source_path, Path("sheet-openrebar.pdf"))

    def test_execute_merges_structured_and_vision_annotations(self) -> None:
        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=FakeExtractor(),
            narrative_rule_synthesizer=FakeSynthesizer(),
            drawing_analyzer=FakeDrawingAnalyzer(),
            ifc_validator=FakeValidator(),
            ids_validator=FakeIdsValidator(),
            vision_drawing_analyzer=FakeVisionDrawingAnalyzer(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-vision-merge",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(
                    text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                ),
                technical_spec_source=RequirementSource(
                    text="Лист A-101: толщина WALL-01 не менее 200 мм",
                    source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                ),
                ids_path=Path("rules.ids"),
                drawing_sources=(
                    DrawingSource(
                        text="ANN-001|A-101|WALL-01|thickness|150|mm|1|10|20|100|50",
                        path=Path("sheet-openrebar.pdf"),
                        sheet_id="A-101",
                        format="pdf",
                    ),
                ),
            )
        )

        self.assertEqual(report.summary.drawing_annotation_count, 2)
        sources = {annotation.source for annotation in report.drawing_annotations}
        self.assertIn("vision-analyzer", sources)
        self.assertIn("drawing-text", sources)
        target_refs = {annotation.target_ref for annotation in report.drawing_annotations}
        self.assertIn("WALL-01", target_refs)
        self.assertIn("WALL-IMG-01", target_refs)

    def test_execute_materializes_raster_drawing_asset_candidates(self) -> None:
        class NoOpExtractor:
            def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpSynthesizer:
            def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpStructuredAnalyzer:
            def analyze(self, _source: DrawingSource) -> list[DrawingAnnotation]:
                return []

        class NoOpValidator:
            def validate(
                self,
                _ifc_path: Path,
                _requirements: list[ParsedRequirement],
            ) -> list[ValidationIssue]:
                return []

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image_path = Path(tmp.name)

        try:
            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=NoOpExtractor(),
                narrative_rule_synthesizer=NoOpSynthesizer(),
                drawing_analyzer=NoOpStructuredAnalyzer(),
                ifc_validator=NoOpValidator(),
                ids_validator=FakeIdsValidator(),
                vision_drawing_analyzer=FakeVisionDrawingAnalyzer(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-raster-asset",
                    ifc_path=Path("sample.ifc"),
                    requirement_source=RequirementSource(text=""),
                    ids_path=Path("rules.ids"),
                    drawing_sources=(
                        DrawingSource(
                            text="",
                            path=image_path,
                            sheet_id="A-201",
                            format="png",
                        ),
                    ),
                )
            )

            self.assertEqual(len(report.drawing_assets), 1)
            self.assertEqual(report.drawing_assets[0].sheet_id, "A-201")
            self.assertEqual(report.drawing_assets[0].page_number, 1)
            self.assertEqual(report.drawing_assets[0].source_path, image_path)
        finally:
            image_path.unlink(missing_ok=True)

    def test_execute_warns_when_openrebar_fallback_solver_was_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text(
                json.dumps(_build_openrebar_report_payload(fallback_used=True)),
                encoding="utf-8",
            )

            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=FakeExtractor(),
                narrative_rule_synthesizer=FakeSynthesizer(),
                drawing_analyzer=FakeDrawingAnalyzer(),
                ifc_validator=FakeValidator(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-openrebar-fallback",
                    ifc_path=Path("sample.ifc"),
                    requirement_source=RequirementSource(
                        text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                    ),
                    reinforcement_report_path=report_path,
                    project_name="Residential Tower Alpha",
                )
            )

            fallback_warnings = [
                issue for issue in report.issues if issue.rule_id == "OPENREBAR-OPT-FALLBACK"
            ]
            self.assertEqual(len(fallback_warnings), 1)
            self.assertEqual(fallback_warnings[0].severity, Severity.WARNING)
            self.assertEqual(
                fallback_warnings[0].category,
                FindingCategory.CROSS_DOCUMENT,
            )

    def test_execute_warns_when_openrebar_master_strategy_is_not_highs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text(
                json.dumps(
                    _build_openrebar_report_payload(
                        fallback_used=False,
                        master_problem_strategy="restricted-master-lp-coordinate-descent",
                    )
                ),
                encoding="utf-8",
            )

            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=FakeExtractor(),
                narrative_rule_synthesizer=FakeSynthesizer(),
                drawing_analyzer=FakeDrawingAnalyzer(),
                ifc_validator=FakeValidator(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-openrebar-strategy",
                    ifc_path=Path("sample.ifc"),
                    requirement_source=RequirementSource(
                        text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                    ),
                    reinforcement_report_path=report_path,
                    project_name="Residential Tower Alpha",
                )
            )

            strategy_warnings = [
                issue for issue in report.issues if issue.rule_id == "OPENREBAR-OPT-STRATEGY"
            ]
            self.assertEqual(len(strategy_warnings), 1)
            self.assertEqual(strategy_warnings[0].severity, Severity.WARNING)
            self.assertIn(
                "coordinate-descent",
                strategy_warnings[0].observed_value or "",
            )

    def test_execute_warns_when_openrebar_digest_mismatch_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text(
                json.dumps(_build_openrebar_report_payload(fallback_used=False)),
                encoding="utf-8",
            )

            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=FakeExtractor(),
                narrative_rule_synthesizer=FakeSynthesizer(),
                drawing_analyzer=FakeDrawingAnalyzer(),
                ifc_validator=FakeValidator(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-openrebar-digest",
                    ifc_path=Path("sample.ifc"),
                    requirement_source=RequirementSource(
                        text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                    ),
                    reinforcement_report_path=report_path,
                    reinforcement_source_digest="0" * 64,
                    project_name="Residential Tower Alpha",
                )
            )

            digest_warnings = [
                issue for issue in report.issues if issue.rule_id == "OPENREBAR-PROVENANCE-DIGEST"
            ]
            self.assertEqual(len(digest_warnings), 1)
            self.assertEqual(digest_warnings[0].severity, Severity.WARNING)
            self.assertEqual(digest_warnings[0].expected_value, "0" * 64)
            self.assertIsNotNone(digest_warnings[0].observed_value)
            self.assertEqual(len(digest_warnings[0].observed_value or ""), 64)

    def test_execute_warns_when_openrebar_total_waste_exceeds_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text(
                json.dumps(
                    _build_openrebar_report_payload(
                        fallback_used=False,
                        total_waste_percent=12.7,
                    )
                ),
                encoding="utf-8",
            )

            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=FakeExtractor(),
                narrative_rule_synthesizer=FakeSynthesizer(),
                drawing_analyzer=FakeDrawingAnalyzer(),
                ifc_validator=FakeValidator(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-openrebar-waste-threshold",
                    ifc_path=Path("sample.ifc"),
                    requirement_source=RequirementSource(
                        text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                    ),
                    reinforcement_report_path=report_path,
                    reinforcement_waste_warning_threshold_percent=10.0,
                    project_name="Residential Tower Alpha",
                )
            )

            threshold_warnings = [
                issue for issue in report.issues if issue.rule_id == "OPENREBAR-WASTE-THRESHOLD"
            ]
            self.assertEqual(len(threshold_warnings), 1)
            self.assertEqual(threshold_warnings[0].severity, Severity.WARNING)
            self.assertEqual(threshold_warnings[0].expected_value, "<= 10")
            self.assertEqual(threshold_warnings[0].observed_value, "12.7")

    def test_execute_escalates_openrebar_warnings_when_mode_enforced(self) -> None:
        class NoOpExtractor:
            def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpSynthesizer:
            def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpDrawingAnalyzer:
            def analyze(self, _source: DrawingSource) -> list[DrawingAnnotation]:
                return []

        class NoOpValidator:
            def validate(
                self,
                _ifc_path: Path,
                _requirements: list[ParsedRequirement],
            ) -> list[ValidationIssue]:
                return []

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text(
                json.dumps(_build_openrebar_report_payload(fallback_used=True)),
                encoding="utf-8",
            )

            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=NoOpExtractor(),
                narrative_rule_synthesizer=NoOpSynthesizer(),
                drawing_analyzer=NoOpDrawingAnalyzer(),
                ifc_validator=NoOpValidator(),
                ids_validator=NoOpIdsValidator(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-openrebar-enforced",
                    ifc_path=Path("sample.ifc"),
                    requirement_source=RequirementSource(text=""),
                    ids_path=Path("rules.ids"),
                    reinforcement_report_path=report_path,
                    reinforcement_provenance_mode="enforced",
                    project_name="Residential Tower Alpha",
                )
            )

            fallback_issues = [
                issue for issue in report.issues if issue.rule_id == "OPENREBAR-OPT-FALLBACK"
            ]
            self.assertEqual(len(fallback_issues), 1)
            self.assertEqual(fallback_issues[0].severity, Severity.ERROR)
            self.assertFalse(report.summary.passed)

    def test_execute_keeps_minor_openrebar_warning_as_warning_when_mode_enforced(self) -> None:
        class NoOpExtractor:
            def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpSynthesizer:
            def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpDrawingAnalyzer:
            def analyze(self, _source: DrawingSource) -> list[DrawingAnnotation]:
                return []

        class NoOpValidator:
            def validate(
                self,
                _ifc_path: Path,
                _requirements: list[ParsedRequirement],
            ) -> list[ValidationIssue]:
                return []

        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = _build_openrebar_report_payload(fallback_used=False)
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=NoOpExtractor(),
                narrative_rule_synthesizer=NoOpSynthesizer(),
                drawing_analyzer=NoOpDrawingAnalyzer(),
                ifc_validator=NoOpValidator(),
                ids_validator=NoOpIdsValidator(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-openrebar-enforced-minor",
                    ifc_path=Path("sample.ifc"),
                    requirement_source=RequirementSource(text=""),
                    ids_path=Path("rules.ids"),
                    reinforcement_report_path=report_path,
                    reinforcement_source_digest=build_openrebar_provenance_digest(payload),
                    reinforcement_provenance_mode="enforced",
                    project_name="Residential Tower Beta",
                )
            )

            project_code_issues = [
                issue for issue in report.issues if issue.rule_id == "OPENREBAR-PROJECT-CODE"
            ]
            self.assertEqual(len(project_code_issues), 1)
            self.assertEqual(project_code_issues[0].severity, Severity.WARNING)
            self.assertTrue(report.summary.passed)

    def test_execute_escalates_critical_openrebar_warning_when_mode_enforced(self) -> None:
        class NoOpExtractor:
            def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpSynthesizer:
            def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return []

        class NoOpDrawingAnalyzer:
            def analyze(self, _source: DrawingSource) -> list[DrawingAnnotation]:
                return []

        class NoOpValidator:
            def validate(
                self,
                _ifc_path: Path,
                _requirements: list[ParsedRequirement],
            ) -> list[ValidationIssue]:
                return []

        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = _build_openrebar_report_payload(fallback_used=False)
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=NoOpExtractor(),
                narrative_rule_synthesizer=NoOpSynthesizer(),
                drawing_analyzer=NoOpDrawingAnalyzer(),
                ifc_validator=NoOpValidator(),
                ids_validator=NoOpIdsValidator(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-openrebar-enforced-critical",
                    ifc_path=Path("sample.ifc"),
                    requirement_source=RequirementSource(text=""),
                    ids_path=Path("rules.ids"),
                    reinforcement_report_path=report_path,
                    reinforcement_source_digest="0" * 64,
                    reinforcement_provenance_mode="enforced",
                    project_name="Residential Tower Alpha",
                )
            )

            digest_issues = [
                issue for issue in report.issues if issue.rule_id == "OPENREBAR-PROVENANCE-DIGEST"
            ]
            self.assertEqual(len(digest_issues), 1)
            self.assertEqual(digest_issues[0].severity, Severity.ERROR)
            self.assertFalse(report.summary.passed)

    def test_execute_warns_when_openrebar_report_provided_without_reference_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text(
                json.dumps(_build_openrebar_report_payload(fallback_used=False)),
                encoding="utf-8",
            )

            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=FakeExtractor(),
                narrative_rule_synthesizer=FakeSynthesizer(),
                drawing_analyzer=FakeDrawingAnalyzer(),
                ifc_validator=FakeValidator(),
                ids_validator=NoOpIdsValidator(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-openrebar-no-digest",
                    ifc_path=Path("sample.ifc"),
                    requirement_source=RequirementSource(
                        text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                    ),
                    reinforcement_report_path=report_path,
                    reinforcement_source_digest=None,
                    project_name="Residential Tower Alpha",
                )
            )

            missing_digest_issues = [
                issue
                for issue in report.issues
                if issue.rule_id == "OPENREBAR-PROVENANCE-REFERENCE-MISSING"
            ]
            self.assertEqual(len(missing_digest_issues), 1)
            self.assertEqual(missing_digest_issues[0].severity, Severity.WARNING)
            self.assertEqual(missing_digest_issues[0].expected_value, "provided")

    def test_execute_raises_for_invalid_openrebar_report_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "openrebar.result.json"
            report_path.write_text("{invalid-json", encoding="utf-8")

            store = FakeStore()
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=FakeExtractor(),
                narrative_rule_synthesizer=FakeSynthesizer(),
                drawing_analyzer=FakeDrawingAnalyzer(),
                ifc_validator=FakeValidator(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=store,
            )

            with self.assertRaises(ValueError):
                use_case.execute(
                    ValidationRequest(
                        request_id="req-openrebar-invalid-json",
                        ifc_path=Path("sample.ifc"),
                        requirement_source=RequirementSource(
                            text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                        ),
                        reinforcement_report_path=report_path,
                    )
                )


class CalculationSourceTests(unittest.TestCase):
    """Tests that calculation_source feeds into synthesized requirements."""

    CALC_FIXTURE = (
        Path(__file__).resolve().parents[2] / "samples" / "calculations" / "area-requirement.txt"
    )

    def test_calculation_text_produces_synthesized_requirements(self) -> None:
        from aerobim.infrastructure.adapters.narrative_rule_synthesizer import (
            NarrativeRuleSynthesizer as RealSynthesizer,
        )

        synthesizer = RealSynthesizer()
        source = RequirementSource(
            text=(
                "Помещение ГОС-001: площадь не менее 25 м2\n"
                "Wall ГОС-002 fire rating должна быть REI90"
            ),
            source_kind=SourceKind.CALCULATION,
        )
        rules = synthesizer.synthesize(source)
        self.assertEqual(len(rules), 2)
        rule_ids_lower = " ".join(r.rule_id for r in rules).lower()
        self.assertIn("area", rule_ids_lower)
        self.assertIn("fire-rating", rule_ids_lower)

    def test_calculation_fixture_file_produces_area_requirement(self) -> None:
        from aerobim.infrastructure.adapters.narrative_rule_synthesizer import (
            NarrativeRuleSynthesizer as RealSynthesizer,
        )

        if not self.CALC_FIXTURE.exists():
            self.skipTest("Calculation fixture not found")

        synthesizer = RealSynthesizer()
        source = RequirementSource(
            text="",
            path=self.CALC_FIXTURE,
            source_kind=SourceKind.CALCULATION,
        )
        rules = synthesizer.synthesize(source)
        self.assertGreaterEqual(len(rules), 1, "Fixture should produce at least 1 requirement")
        area_rules = [r for r in rules if "area" in r.rule_id.lower()]
        self.assertEqual(len(area_rules), 1)
        self.assertEqual(area_rules[0].expected_value, "25")

    def test_calculation_source_in_multimodal_use_case(self) -> None:
        """calculation_source is processed end-to-end by AnalyzeProjectPackageUseCase."""
        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=FakeExtractor(),
            narrative_rule_synthesizer=FakeSynthesizer(),
            drawing_analyzer=FakeDrawingAnalyzer(),
            ifc_validator=FakeValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-calc",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(
                    text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                ),
                calculation_source=RequirementSource(
                    text="Помещение ГОС-001: площадь не менее 25 м2",
                    source_kind=SourceKind.CALCULATION,
                ),
            )
        )

        self.assertGreater(
            report.summary.requirement_count,
            1,
            "Should include synthesized requirement from calculation",
        )
        self.assertEqual(store.saved_report_id, report.report_id)


if __name__ == "__main__":
    unittest.main()
