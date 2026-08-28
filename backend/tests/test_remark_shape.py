"""Remark shape is a checkable payload (п. 2.1.5), not title+body prose."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.models import (
    ComparisonOperator,
    FindingCategory,
    GeneratedRemark,
    Severity,
    ValidationIssue,
)
from aerobim.domain.remark_shape import (
    UNBOUND_CLAUSE_EN,
    UNBOUND_CLAUSE_RU,
    merge_advisory_onto_template,
    shape_from_remark,
    validate_remark_shape,
)
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator

_REPO = Path(__file__).resolve().parents[2]
_SCHEMA = _REPO / "samples" / "schemas" / "remark-shape.schema.json"


def _issue(**overrides: object) -> ValidationIssue:
    payload = dict(
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
        element_guid="guid-1",
        target_ref="Space:A101",
    )
    payload.update(overrides)
    return ValidationIssue(**payload)  # type: ignore[arg-type]


class RemarkShapeSchemaTests(unittest.TestCase):
    def test_empty_essence_fails(self) -> None:
        payload = {
            "essence": "",
            "clause_cite": UNBOUND_CLAUSE_RU,
            "clause_bound": False,
            "location": {"line": "без точной привязки"},
            "detail": "развёрнуто",
        }
        self.assertIn("essence missing", validate_remark_shape(payload))

    def test_unbound_marker_is_valid(self) -> None:
        payload = {
            "essence": "Площадь меньше ожидаемой",
            "clause_cite": UNBOUND_CLAUSE_RU,
            "clause_bound": False,
            "location": {"line": "этаж: нет в пространственном индексе"},
            "detail": "ожидание 25",
        }
        self.assertEqual(validate_remark_shape(payload), [])

    def test_bound_plus_unbound_marker_invalid(self) -> None:
        payload = {
            "essence": "Площадь меньше ожидаемой",
            "clause_cite": UNBOUND_CLAUSE_RU,
            "clause_bound": True,
            "location": {"line": "GUID guid-1"},
            "detail": "ожидание 25",
        }
        errors = validate_remark_shape(payload)
        self.assertTrue(any("unbound marker" in item for item in errors))

    def test_unbound_flag_with_real_cite_invalid(self) -> None:
        payload = {
            "essence": "Cover too thin",
            "clause_cite": "СП 63 п. 8.1",
            "clause_bound": False,
            "location": {"line": UNBOUND_CLAUSE_EN},
            "detail": "detail",
        }
        errors = validate_remark_shape(payload)
        self.assertTrue(any("not the unbound marker" in item for item in errors))

    def test_generator_output_validates(self) -> None:
        remark = TemplateRemarkGenerator(locale="ru").generate(_issue())
        violations = validate_remark_shape(shape_from_remark(remark).as_payload())
        self.assertEqual(violations, [])
        self.assertEqual(remark.clause_cite, UNBOUND_CLAUSE_RU)
        self.assertFalse(remark.clause_bound)
        bound = TemplateRemarkGenerator(locale="ru").generate(
            _issue(norm_source="СП 63", norm_clause="п. 8.1")
        )
        self.assertTrue(bound.clause_bound)
        self.assertEqual(bound.clause_cite, "СП 63 п. 8.1")
        self.assertEqual(validate_remark_shape(shape_from_remark(bound).as_payload()), [])

    def test_json_schema_file_accepts_generator_payload(self) -> None:
        import jsonschema

        schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
        remark = TemplateRemarkGenerator(locale="en").generate(
            _issue(storey_name="L3", grid_axis="A")
        )
        jsonschema.validate(shape_from_remark(remark).as_payload(), schema)

    def test_overlay_keeps_template_clause_and_location(self) -> None:
        template = TemplateRemarkGenerator(locale="ru").generate(
            _issue(norm_source="СТО-1", norm_clause="п. 2", storey_name="3 этаж")
        )
        draft = GeneratedRemark(
            title="Черновик AI",
            body="Сформировано по детерминированной находке.",
            ai_generated=True,
            expert_confirmation_required=True,
        )
        merged = merge_advisory_onto_template(template, draft)
        self.assertEqual(merged.clause_cite, "СТО-1 п. 2")
        self.assertTrue(merged.clause_bound)
        self.assertEqual(merged.storey_name, "3 этаж")
        self.assertTrue(merged.ai_generated)
        self.assertEqual(merged.detail, draft.body)
        self.assertEqual(validate_remark_shape(shape_from_remark(merged).as_payload()), [])


if __name__ == "__main__":
    unittest.main()
