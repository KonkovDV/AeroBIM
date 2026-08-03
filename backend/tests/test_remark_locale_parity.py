"""RU/EN remark parity — TZ rows 20/21 fixture evidence (structure + BCF body)."""

from __future__ import annotations

import io
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import (
    ComparisonOperator,
    FindingCategory,
    GeneratedRemark,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


def _issue(
    *,
    category: FindingCategory,
    operator: ComparisonOperator = ComparisonOperator.GREATER_OR_EQUAL,
    observed: str | None = "20",
) -> ValidationIssue:
    return ValidationIssue(
        rule_id="QTO-PARITY-001",
        severity=Severity.ERROR,
        message="Area mismatch",
        ifc_entity="IFCSPACE",
        category=category,
        property_set="Qto_SpaceBaseQuantities",
        property_name="NetFloorArea",
        operator=operator,
        expected_value="25",
        observed_value=observed,
        unit="m2",
        target_ref="Space:A101",
    )


class RemarkLocaleParityTests(unittest.TestCase):
    """Prove EN templates cover the same categories as RU and stay language-pure."""

    _CASES: tuple[tuple[FindingCategory, str, str], ...] = (
        (FindingCategory.IFC_VALIDATION, "Замечание по модели", "Model remark"),
        (FindingCategory.DRAWING_VALIDATION, "Замечание по чертежу", "Drawing remark"),
        (FindingCategory.CROSS_DOCUMENT, "Междокументное расхождение", "Cross-document conflict"),
        (FindingCategory.SPATIAL, "Пространственное замечание", "Spatial remark"),
    )

    def test_ru_en_title_parity_by_category(self) -> None:
        ru_gen = TemplateRemarkGenerator(locale="ru")
        en_gen = TemplateRemarkGenerator(locale="en")
        for category, ru_marker, en_marker in self._CASES:
            with self.subTest(category=category.value):
                issue = _issue(category=category)
                ru = ru_gen.generate(issue)
                en = en_gen.generate(issue)
                self.assertIn(ru_marker, ru.title)
                self.assertIn(en_marker, en.title)
                self.assertNotIn("Замечание", en.title)
                self.assertNotIn("Model remark", ru.title)
                # Structure parity: both have non-empty title/body; EN has no Cyrillic operators.
                self.assertTrue(ru.body.strip())
                self.assertTrue(en.body.strip())
                self.assertNotIn("не менее", en.body)
                self.assertNotIn("at least", ru.body)

    def test_en_exists_and_missing_observed(self) -> None:
        en_gen = TemplateRemarkGenerator(locale="en")
        exists = _issue(
            category=FindingCategory.IFC_VALIDATION,
            operator=ComparisonOperator.EXISTS,
            observed=None,
        )
        remark = en_gen.generate(exists)
        self.assertIn("must be present", remark.body)
        self.assertIn("not found", remark.body)
        self.assertNotIn("должно присутствовать", remark.body)

    def test_bcf_description_carries_en_remark_body(self) -> None:
        issue = _issue(category=FindingCategory.IFC_VALIDATION)
        remark = TemplateRemarkGenerator(locale="en").generate(issue)
        marked = ValidationIssue(
            rule_id=issue.rule_id,
            severity=issue.severity,
            message=issue.message,
            category=issue.category,
            element_guid="guid-en-1",
            finding_id="fid-en-1",
            origin="deterministic",
            remark=GeneratedRemark(
                title=remark.title,
                body=remark.body,
                ai_generated=False,
            ),
        )
        report = ValidationReport(
            report_id="r-en",
            request_id="req-en",
            ifc_path=None,
            created_at="2026-08-04T00:00:00+00:00",
            requirements=(),
            issues=(marked,),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=1,
                error_count=1,
                warning_count=0,
                passed=False,
            ),
        )
        bcf_bytes = export_bcf(report)
        with zipfile.ZipFile(io.BytesIO(bcf_bytes), "r") as zf:
            markup = next(n for n in zf.namelist() if n.endswith("/markup.bcf"))
            xml = zf.read(markup).decode("utf-8")
        self.assertIn("at least", xml)
        self.assertIn("value must be at least 25", xml)
        self.assertNotIn("не менее", xml)
        # BCF Title is rule_id (language-neutral); EN lives in Description body.
        self.assertIn("QTO-PARITY-001", xml)


if __name__ == "__main__":
    unittest.main()
