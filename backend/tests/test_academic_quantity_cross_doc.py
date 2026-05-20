from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import ConflictKind
from aerobim.domain.quantity import QuantityValue, parse_quantity, si_compare


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

        unit_mismatch = use_case._classify_conflict_kind("3.0", "m", "5.0", "m2")
        self.assertEqual(unit_mismatch, ConflictKind.UNIT_MISMATCH)

        hard_conflict = use_case._classify_conflict_kind("3.0", "m", "4.0", "m")
        self.assertEqual(hard_conflict, ConflictKind.HARD_CONFLICT)

    def test_values_conflict_string_only_would_differ_without_si(self) -> None:
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=object(),  # type: ignore[arg-type]
            narrative_rule_synthesizer=object(),  # type: ignore[arg-type]
            drawing_analyzer=object(),  # type: ignore[arg-type]
            ifc_validator=object(),  # type: ignore[arg-type]
            remark_generator=object(),  # type: ignore[arg-type]
            audit_report_store=object(),  # type: ignore[arg-type]
        )
        self.assertFalse(use_case._values_conflict("3000", "mm", "3", "m"))

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
            use_case._values_conflict(
                "3000",
                "mm",
                "3.0",
                "m",
                quantity_a=q_mm,
                quantity_b=q_m,
            )
        )
        self.assertTrue(
            use_case._values_conflict(
                "3000",
                "mm",
                "4.0",
                "m",
                quantity_a=q_mm,
                quantity_b=QuantityValue(value=4.0, unit="m", ucum_code="m", dimension="length", si_value=4.0),
            )
        )


if __name__ == "__main__":
    unittest.main()
