"""Edge-case tests to harden the system against production failure modes.

Covers:
- Structured logger JSON output format
- Correlation ID middleware propagation
- Narrative synthesizer multi-pattern extraction
- Drawing analyzer malformed input rejection
- Empty / boundary input handling across adapters
"""

from __future__ import annotations

import json
import logging
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.models import (
    ComparisonOperator,
    FindingCategory,
    RequirementSource,
    RuleScope,
    Severity,
    SourceKind,
    ValidationIssue,
)

# ---------------------------------------------------------------------------
# A: Structured Logger
# ---------------------------------------------------------------------------

class StructuredLoggerTests(unittest.TestCase):
    def test_json_output_format(self) -> None:
        from aerobim.infrastructure.adapters.json_structured_logger import JsonStructuredLogger

        logger = JsonStructuredLogger(name="test-json-format", level=logging.DEBUG)
        # Capture stderr output
        import io
        handler = logger._logger.handlers[0]
        stream = io.StringIO()
        handler.stream = stream  # type: ignore[attr-defined]

        logger.info("test message", request_id="abc-123", count=42)

        output = stream.getvalue().strip()
        parsed = json.loads(output)
        self.assertEqual(parsed["message"], "test message")
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["request_id"], "abc-123")
        self.assertEqual(parsed["count"], 42)
        self.assertIn("timestamp", parsed)

    def test_error_level(self) -> None:
        from aerobim.infrastructure.adapters.json_structured_logger import JsonStructuredLogger

        logger = JsonStructuredLogger(name="test-error-level", level=logging.DEBUG)
        import io
        handler = logger._logger.handlers[0]
        stream = io.StringIO()
        handler.stream = stream  # type: ignore[attr-defined]

        logger.error("something broke", module="api")

        output = stream.getvalue().strip()
        parsed = json.loads(output)
        self.assertEqual(parsed["level"], "ERROR")
        self.assertEqual(parsed["module"], "api")


# ---------------------------------------------------------------------------
# B: Narrative Rule Synthesizer — multi-pattern and edge cases
# ---------------------------------------------------------------------------

class NarrativeSynthesizerEdgeCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        from aerobim.infrastructure.adapters.narrative_rule_synthesizer import (
            NarrativeRuleSynthesizer,
        )
        self.synthesizer = NarrativeRuleSynthesizer()

    def test_empty_source_returns_no_rules(self) -> None:
        source = RequirementSource(text="", source_kind=SourceKind.TECHNICAL_SPECIFICATION)
        result = self.synthesizer.synthesize(source)
        self.assertEqual(result, [])

    def test_area_pattern_extraction_russian(self) -> None:
        source = RequirementSource(
            text="Помещение A101 площадь не менее 25 м2",
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
        )
        result = self.synthesizer.synthesize(source)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].ifc_entity, "IFCSPACE")
        self.assertEqual(result[0].rule_scope, RuleScope.IFC_QUANTITY)
        self.assertEqual(result[0].operator, ComparisonOperator.GREATER_OR_EQUAL)
        self.assertEqual(result[0].expected_value, "25")

    def test_fire_rating_pattern_extraction(self) -> None:
        source = RequirementSource(
            text="IfcWall fire rating must be REI60",
            source_kind=SourceKind.STRUCTURED_TEXT,
        )
        result = self.synthesizer.synthesize(source)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].ifc_entity, "IFCWALL")
        self.assertEqual(result[0].property_name, "FireRating")
        self.assertEqual(result[0].expected_value, "REI60")

    def test_mixed_patterns_multi_line(self) -> None:
        source = RequirementSource(
            text=(
                "Room B202 area at least 30 sqm\n"
                "Wall fire rating must be REI120\n"
                "# This is a comment\n"
                "Random unmatched line\n"
            ),
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
        )
        result = self.synthesizer.synthesize(source)
        self.assertEqual(len(result), 2, "Should extract area + fire rating, skip comment and unmatched")

    def test_area_pattern_english(self) -> None:
        source = RequirementSource(
            text="Room X100 area at least 50.5 m2",
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
        )
        result = self.synthesizer.synthesize(source)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].expected_value, "50.5")

    def test_file_based_source(self) -> None:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
        tmp.write("Wall fire rating must be REI45\n")
        tmp.close()
        source = RequirementSource(
            text="",
            path=Path(tmp.name),
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
        )
        result = self.synthesizer.synthesize(source)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].expected_value, "REI45")
        Path(tmp.name).unlink()


# ---------------------------------------------------------------------------
# C: Drawing Analyzer — malformed input & edge cases
# ---------------------------------------------------------------------------

class DrawingAnalyzerEdgeCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        from aerobim.infrastructure.adapters.structured_drawing_analyzer import (
            StructuredDrawingAnalyzer,
        )
        self.analyzer = StructuredDrawingAnalyzer()

    def test_malformed_text_too_few_columns(self) -> None:
        from aerobim.domain.models import DrawingSource
        source = DrawingSource(text="col1|col2|col3")
        with self.assertRaises(ValueError) as ctx:
            self.analyzer.analyze(source)
        self.assertIn("Malformed drawing annotation", str(ctx.exception))

    def test_empty_text_returns_empty(self) -> None:
        from aerobim.domain.models import DrawingSource
        source = DrawingSource(text="")
        result = self.analyzer.analyze(source)
        self.assertEqual(result, [])

    def test_comment_lines_skipped(self) -> None:
        from aerobim.domain.models import DrawingSource
        source = DrawingSource(text="# This is a comment\n\n")
        result = self.analyzer.analyze(source)
        self.assertEqual(result, [])

    def test_json_non_list_raises(self) -> None:
        from aerobim.domain.models import DrawingSource
        source = DrawingSource(text='{"not": "a list"}', path=Path("test.json"))
        with self.assertRaises(ValueError) as ctx:
            self.analyzer.analyze(source)
        self.assertIn("must be a list", str(ctx.exception))


# ---------------------------------------------------------------------------
# D: Template Remark Generator — all branches
# ---------------------------------------------------------------------------

class RemarkGeneratorEdgeCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        from aerobim.infrastructure.adapters.template_remark_generator import (
            TemplateRemarkGenerator,
        )
        self.generator = TemplateRemarkGenerator()

    def test_ifc_remark_gte_operator(self) -> None:
        issue = ValidationIssue(
            rule_id="QTO-001",
            severity=Severity.ERROR,
            message="Area mismatch",
            ifc_entity="IFCSPACE",
            category=FindingCategory.IFC_VALIDATION,
            property_set="Qto_SpaceBaseQuantities",
            property_name="NetFloorArea",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value="25",
            observed_value="20",
            unit="m2",
        )
        remark = self.generator.generate(issue)
        self.assertIn("не менее", remark.body)
        self.assertIn("25", remark.body)

    def test_drawing_remark(self) -> None:
        from aerobim.domain.models import ProblemZone
        issue = ValidationIssue(
            rule_id="DWG-001",
            severity=Severity.WARNING,
            message="Thickness mismatch",
            category=FindingCategory.DRAWING_VALIDATION,
            property_name="WallThickness",
            observed_value="180",
            expected_value="200",
            unit="мм",
            problem_zone=ProblemZone(sheet_id="Sheet-A1"),
        )
        remark = self.generator.generate(issue)
        self.assertIn("чертежу", remark.title)
        self.assertIn("Sheet-A1", remark.body)

    def test_missing_observed_value(self) -> None:
        issue = ValidationIssue(
            rule_id="TEST-001",
            severity=Severity.ERROR,
            message="Property missing",
            property_name="SomeProperty",
        )
        remark = self.generator.generate(issue)
        self.assertIn("не найдено", remark.body)

    def test_exists_operator_text(self) -> None:
        issue = ValidationIssue(
            rule_id="EXISTS-001",
            severity=Severity.ERROR,
            message="Must exist",
            operator=ComparisonOperator.EXISTS,
            property_name="FireRating",
        )
        remark = self.generator.generate(issue)
        self.assertIn("должно присутствовать", remark.body)


# ---------------------------------------------------------------------------
# E: Correlation middleware
# ---------------------------------------------------------------------------

class CorrelationTests(unittest.TestCase):
    def test_get_correlation_id_default_empty(self) -> None:
        from aerobim.presentation.http.correlation import get_correlation_id
        # Outside a request context, should return empty string
        cid = get_correlation_id()
        self.assertEqual(cid, "")

    def test_middleware_sets_response_header(self) -> None:
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except ModuleNotFoundError:
            self.skipTest("FastAPI not installed")

        app = FastAPI()

        from aerobim.presentation.http.correlation import HEADER_NAME, add_correlation_middleware
        add_correlation_middleware(app)

        @app.get("/test")
        def test_endpoint() -> dict[str, str]:
            from aerobim.presentation.http.correlation import get_correlation_id
            return {"cid": get_correlation_id()}

        client = TestClient(app)

        # Auto-generated ID
        resp = client.get("/test")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(HEADER_NAME, resp.headers)
        self.assertEqual(len(resp.headers[HEADER_NAME]), 32)  # uuid4 hex

        # Provided ID
        resp = client.get("/test", headers={HEADER_NAME: "my-custom-id"})
        self.assertEqual(resp.json()["cid"], "my-custom-id")
        self.assertEqual(resp.headers[HEADER_NAME], "my-custom-id")


# ---------------------------------------------------------------------------
# F: Requirement extractor edge cases
# ---------------------------------------------------------------------------

class RequirementExtractorEdgeCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        from aerobim.infrastructure.adapters.docling_requirement_extractor import (
            StructuredRequirementExtractor,
        )
        self.extractor = StructuredRequirementExtractor()

    def test_malformed_row_raises(self) -> None:
        source = RequirementSource(text="only|three|columns", source_kind=SourceKind.STRUCTURED_TEXT)
        with self.assertRaises(ValueError) as ctx:
            self.extractor.extract(source)
        self.assertIn("Malformed requirement", str(ctx.exception))

    def test_comment_lines_skipped(self) -> None:
        source = RequirementSource(
            text="# header\n\n# another comment",
            source_kind=SourceKind.STRUCTURED_TEXT,
        )
        result = self.extractor.extract(source)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
