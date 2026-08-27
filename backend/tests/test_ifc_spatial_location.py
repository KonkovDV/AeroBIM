"""Storey/axis from IFC spatial index — never invented from OCR."""

from __future__ import annotations

import unittest

from aerobim.domain.finding_provenance import compute_stable_finding_id
from aerobim.domain.ifc_spatial_index import (
    IfcSpatialElement,
    IfcSpatialIndex,
    stamp_issues_with_spatial_location,
)
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


class _Entity:
    def __init__(self, ifc_type: str, **fields: object) -> None:
        self._ifc_type = ifc_type
        for key, value in fields.items():
            setattr(self, key, value)

    def is_a(self) -> str:
        return self._ifc_type


class _Model:
    def __init__(self, by_type: dict[str, list[_Entity]]) -> None:
        self._by_type = by_type

    def by_type(self, name: str) -> list[_Entity]:
        return list(self._by_type.get(name, []))


def _issue(
    *, guid: str | None, storey: str | None = None, axis: str | None = None
) -> ValidationIssue:
    return ValidationIssue(
        rule_id="IDS-Wall Fire Rating Multi",
        severity=Severity.ERROR,
        message="FireRating mismatch",
        ifc_entity="IFCWALL",
        category=FindingCategory.IFC_VALIDATION,
        element_guid=guid,
        storey_name=storey,
        grid_axis=axis,
        finding_id="fid-spatial-1",
        origin="deterministic",
    )


class SpatialIndexLocationTests(unittest.TestCase):
    def test_from_model_reads_storey_and_axis_tag(self) -> None:
        storey = _Entity("IfcBuildingStorey", GlobalId="st-1", Name="3 этаж")
        contain = _Entity("IfcRelContainedInSpatialStructure", RelatingStructure=storey)
        axis = _Entity("IfcGridAxis", GlobalId="ax-1", AxisTag="А", Name=None)
        referenced = _Entity("IfcRelReferencedInSpatialStructure", RelatingStructure=axis)
        wall = _Entity(
            "IfcWall",
            GlobalId="wall-1",
            Name="Wall PQ",
            ContainedInStructure=[contain],
            ReferencedInStructures=[referenced],
            Decomposes=[],
            IsGroupedBy=[],
        )
        grid_only = _Entity("IfcGrid", GlobalId="grid-1", Name="Grid A")
        fake_axis_rel = _Entity("IfcRelReferencedInSpatialStructure", RelatingStructure=grid_only)
        column = _Entity(
            "IfcColumn",
            GlobalId="col-1",
            Name="C1",
            ContainedInStructure=[],
            ReferencedInStructures=[fake_axis_rel],
            Decomposes=[],
        )
        model = _Model({"IfcSystem": [], "IfcRoot": [wall, column, storey, axis, grid_only]})
        index = IfcSpatialIndex.from_model(model)
        hit = index.lookup("wall-1")
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.storey_name, "3 этаж")
        self.assertEqual(hit.grid_axis, "А")
        miss_axis = index.lookup("col-1")
        self.assertIsNotNone(miss_axis)
        assert miss_axis is not None
        self.assertIsNone(miss_axis.grid_axis)
        self.assertIsNone(miss_axis.storey_name)

    def test_stamp_copies_index_and_keeps_finding_id_stable(self) -> None:
        index = IfcSpatialIndex(
            elements={
                "wall-1": IfcSpatialElement(
                    "wall-1",
                    "IfcWall",
                    "Wall PQ",
                    (),
                    storey_name="3 этаж",
                    grid_axis="А",
                )
            },
            systems={},
        )
        issue = _issue(guid="wall-1")
        before = compute_stable_finding_id(issue)
        stamped = stamp_issues_with_spatial_location((issue,), index)
        self.assertEqual(len(stamped), 1)
        self.assertEqual(stamped[0].storey_name, "3 этаж")
        self.assertEqual(stamped[0].grid_axis, "А")
        self.assertEqual(compute_stable_finding_id(stamped[0]), before)

    def test_remark_states_missing_when_guid_has_no_index_hit(self) -> None:
        remark = TemplateRemarkGenerator(locale="ru").generate(_issue(guid="ghost"))
        self.assertIn("этаж: нет в пространственном индексе", remark.body)
        self.assertIn("ось: нет в пространственном индексе", remark.body)
        self.assertNotIn("этаж ghost", remark.body)
        bound = TemplateRemarkGenerator(locale="ru").generate(
            _issue(guid="wall-1", storey="3 этаж", axis="А")
        )
        self.assertIn("этаж 3 этаж", bound.body)
        self.assertIn("ось А", bound.body)
        self.assertNotIn("нет в пространственном индексе", bound.body)

    def test_remark_without_guid_does_not_claim_missing_storey(self) -> None:
        remark = TemplateRemarkGenerator(locale="en").generate(_issue(guid=None))
        self.assertNotIn("storey: not in spatial index", remark.body)
        self.assertNotIn("axis: not in spatial index", remark.body)


if __name__ == "__main__":
    unittest.main()
