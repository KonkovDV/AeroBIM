"""RT-C3PO-010: OCR coincidence must not clear DRAWING_ANNOTATION engine ERROR."""

from __future__ import annotations

import unittest

from aerobim.application.services.drawing_annotation_validation import (
    DrawingAnnotationValidator,
    annotation_is_ocr,
)
from aerobim.domain.models import (
    ComparisonOperator,
    DrawingAnnotation,
    ParsedRequirement,
    RuleScope,
    Severity,
    SourceKind,
    ToleranceConfig,
)


def _thickness_rule() -> ParsedRequirement:
    return ParsedRequirement(
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


def _ann(*, source: str, value: str = "220") -> DrawingAnnotation:
    return DrawingAnnotation(
        annotation_id="ANN-001",
        sheet_id="A-101",
        target_ref="WALL-01",
        measure_name="thickness",
        observed_value=value,
        unit="mm",
        source=source,
    )


class OcrDoesNotClearDrawingErrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = DrawingAnnotationValidator(ToleranceConfig())

    def test_ocr_only_match_keeps_engine_error(self) -> None:
        issues = self.validator.validate((_thickness_rule(),), (_ann(source="ocr", value="220"),))
        self.assertEqual(len(issues), 1)
        self.assertIs(issues[0].severity, Severity.ERROR)
        self.assertIn("OCR coincidence", issues[0].message)

    def test_analyzer_ocr_source_stamp_keeps_error(self) -> None:
        issues = self.validator.validate(
            (_thickness_rule(),),
            (_ann(source="raster-drawing-analyzer-ocr", value="220"),),
        )
        self.assertEqual(len(issues), 1)
        self.assertIs(issues[0].severity, Severity.ERROR)

    def test_text_layer_match_still_clears_when_values_ok(self) -> None:
        issues = self.validator.validate(
            (_thickness_rule(),),
            (_ann(source="raster-drawing-analyzer", value="220"),),
        )
        self.assertEqual(issues, [])

    def test_ocr_cannot_override_text_layer_mismatch(self) -> None:
        issues = self.validator.validate(
            (_thickness_rule(),),
            (
                _ann(source="raster-drawing-analyzer", value="50"),
                _ann(source="ocr", value="220"),
            ),
        )
        self.assertTrue(any(issue.severity is Severity.ERROR for issue in issues))
        self.assertTrue(
            any("does not match the normalized rule" in issue.message for issue in issues)
        )

    def test_annotation_is_ocr_helper(self) -> None:
        self.assertTrue(annotation_is_ocr(_ann(source="raster-drawing-analyzer-ocr")))
        self.assertFalse(annotation_is_ocr(_ann(source="raster-drawing-analyzer")))
        self.assertFalse(annotation_is_ocr(_ann(source="drawing-text")))


if __name__ == "__main__":
    unittest.main()
