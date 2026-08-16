from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.services.cross_document_contradictions import (
    CrossDocumentContradictionDetector,
)
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    ConflictKind,
    FindingCategory,
    ParsedRequirement,
    Severity,
    SourceKind,
    ToleranceConfig,
)
from aerobim.domain.quantity import QuantityValue, normalize_unit_token, parse_quantity, si_compare


class AcademicQuantityCrossDocTests(unittest.TestCase):
    def test_si_compare_treats_mm_and_m_as_equivalent(self) -> None:
        a = parse_quantity(3000.0, "mm")
        b = parse_quantity(3.0, "m")
        self.assertTrue(si_compare(a, b, epsilon=0.001))

    def test_classify_conflict_kind_unit_mismatch_vs_hard_conflict(self) -> None:
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=object(),  # type: ignore[arg-type]
            narrative_rule_synthesizer=object(),  # type: ignore[arg-type]
            drawing_analyzer=object(),  # type: ignore[arg-type]
            ifc_validator=object(),  # type: ignore[arg-type]
            remark_generator=object(),  # type: ignore[arg-type]
            audit_report_store=object(),  # type: ignore[arg-type]
        )

        detector = use_case._cross_doc_detector()
        unit_mismatch = detector.classify_conflict_kind("3.0", "m", "5.0", "m2")
        self.assertEqual(unit_mismatch, ConflictKind.UNIT_MISMATCH)

        hard_conflict = detector.classify_conflict_kind("3.0", "m", "4.0", "m")
        self.assertEqual(hard_conflict, ConflictKind.HARD_CONFLICT)

        equal_si = detector.classify_conflict_kind("3.0", "m", "3000", "mm")
        self.assertEqual(equal_si, ConflictKind.SOFT_CONFLICT_WITHIN_TOLERANCE)

        within_eps = detector.classify_conflict_kind("3.0", "m", "3.0005", "m")
        self.assertEqual(within_eps, ConflictKind.SOFT_CONFLICT_WITHIN_TOLERANCE)

    def test_values_conflict_string_only_would_differ_without_si(self) -> None:
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=object(),  # type: ignore[arg-type]
            narrative_rule_synthesizer=object(),  # type: ignore[arg-type]
            drawing_analyzer=object(),  # type: ignore[arg-type]
            ifc_validator=object(),  # type: ignore[arg-type]
            remark_generator=object(),  # type: ignore[arg-type]
            audit_report_store=object(),  # type: ignore[arg-type]
        )
        self.assertFalse(use_case._cross_doc_detector().values_conflict("3000", "mm", "3", "m"))

    def test_values_conflict_prefers_typed_quantity_over_string_encoding(self) -> None:
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=object(),  # type: ignore[arg-type]
            narrative_rule_synthesizer=object(),  # type: ignore[arg-type]
            drawing_analyzer=object(),  # type: ignore[arg-type]
            ifc_validator=object(),  # type: ignore[arg-type]
            remark_generator=object(),  # type: ignore[arg-type]
            audit_report_store=object(),  # type: ignore[arg-type]
        )
        q_mm = parse_quantity(3000.0, "mm")
        q_m = parse_quantity(3.0, "m")
        self.assertFalse(
            use_case._cross_doc_detector().values_conflict(
                "3000",
                "mm",
                "3.0",
                "m",
                quantity_a=q_mm,
                quantity_b=q_m,
            )
        )
        self.assertTrue(
            use_case._cross_doc_detector().values_conflict(
                "3000",
                "mm",
                "4.0",
                "m",
                quantity_a=q_mm,
                quantity_b=QuantityValue(
                    value=4.0, unit="m", ucum_code="m", dimension="length", si_value=4.0
                ),
            )
        )


class CrossDocHd10SeamTests(unittest.TestCase):
    def _detector(self) -> CrossDocumentContradictionDetector:
        return CrossDocumentContradictionDetector(ToleranceConfig(), Severity.ERROR)

    def _width(
        self,
        source: SourceKind,
        value: str,
        unit: str,
    ) -> ParsedRequirement:
        return ParsedRequirement(
            rule_id="REQ-WIDTH",
            ifc_entity="IFCWALL",
            property_set="Pset_WallCommon",
            property_name="GrossSideArea",
            expected_value=value,
            unit=unit,
            source_kind=source,
        )

    def test_nfkc_folds_superscript_two_to_ascii(self) -> None:
        self.assertEqual(normalize_unit_token("м²"), "м2")
        self.assertEqual(normalize_unit_token("m\u00b2"), "m2")
        self.assertEqual(parse_quantity(12.0, "м²").ucum_code, "m2")

    def test_classify_does_not_hard_conflict_equal_si_across_unit_glyphs(self) -> None:
        detector = self._detector()
        kind = detector.classify_conflict_kind("12.0", "м²", "12.0", "м2")
        self.assertEqual(kind, ConflictKind.SOFT_CONFLICT_WITHIN_TOLERANCE)

    def test_detect_emits_soft_for_nfkc_equivalent_units_within_eps(self) -> None:
        detector = self._detector()
        issues = detector.detect(
            [
                self._width(SourceKind.STRUCTURED_TEXT, "10.00", "м²"),
                self._width(SourceKind.CALCULATION, "10.005", "м2"),
            ]
        )
        area_issues = [issue for issue in issues if issue.category == FindingCategory.CROSS_DOCUMENT]
        self.assertEqual(len(area_issues), 1)
        self.assertEqual(area_issues[0].conflict_kind, ConflictKind.SOFT_CONFLICT_WITHIN_TOLERANCE)
        self.assertEqual(area_issues[0].severity, Severity.INFO)

    def test_detect_does_not_emit_hard_for_metre_millimetre_equivalence(self) -> None:
        detector = self._detector()
        issues = detector.detect(
            [
                self._width(SourceKind.STRUCTURED_TEXT, "3.0", "m"),
                self._width(SourceKind.CALCULATION, "3000", "mm"),
            ]
        )
        self.assertEqual(
            [issue for issue in issues if issue.category == FindingCategory.CROSS_DOCUMENT],
            [],
        )


if __name__ == "__main__":
    unittest.main()
