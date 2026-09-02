"""Storey/axis from IFC spatial index — never invented from OCR."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.finding_provenance import compute_stable_finding_id
from aerobim.domain.ifc_spatial_index import (
    IfcSpatialElement,
    IfcSpatialIndex,
    read_spatial_index_json,
    stamp_issues_with_spatial_location,
    write_spatial_index_json,
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

    def test_two_grids_in_storey_does_not_guess_nearest_axis(self) -> None:
        """A2 HOLD: nearest IfcGrid intersection is not implemented (live_tree_triage)."""
        storey = _Entity(
            "IfcBuildingStorey",
            GlobalId="st-1",
            Name="5 этаж",
            ContainsElements=[],
        )
        axis_a = _Entity("IfcGridAxis", GlobalId="ax-a", AxisTag="А", Name=None)
        axis_1 = _Entity("IfcGridAxis", GlobalId="ax-1", AxisTag="1", Name=None)
        grid_a = _Entity("IfcGrid", GlobalId="grid-a", Name="Grid A", UAxes=[axis_a])
        grid_1 = _Entity("IfcGrid", GlobalId="grid-1", Name="Grid 1", UAxes=[axis_1])
        contain = _Entity(
            "IfcRelContainedInSpatialStructure",
            RelatingStructure=storey,
            RelatedElements=[grid_a, grid_1],
        )
        storey.ContainsElements = [contain]
        wall_rel = _Entity("IfcRelContainedInSpatialStructure", RelatingStructure=storey)
        wall = _Entity(
            "IfcWall",
            GlobalId="wall-house5",
            Name="W",
            ContainedInStructure=[wall_rel],
            ReferencedInStructures=[],
            Decomposes=[],
        )
        model = _Model({"IfcSystem": [], "IfcRoot": [wall, storey, grid_a, grid_1, axis_a, axis_1]})
        index = IfcSpatialIndex.from_model(model)
        hit = index.lookup("wall-house5")
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.storey_name, "5 этаж")
        self.assertIsNone(hit.grid_axis)

    def test_from_model_uses_unique_storey_grid_u_axis(self) -> None:
        storey = _Entity(
            "IfcBuildingStorey",
            GlobalId="st-1",
            Name="1 этаж",
            ContainsElements=[],
        )
        axis = _Entity("IfcGridAxis", GlobalId="ax-1", AxisTag="А", Name=None)
        grid = _Entity("IfcGrid", GlobalId="grid-1", Name="Demo grid", UAxes=[axis])
        contain = _Entity(
            "IfcRelContainedInSpatialStructure",
            RelatingStructure=storey,
            RelatedElements=[grid],
        )
        storey.ContainsElements = [contain]
        wall_rel = _Entity("IfcRelContainedInSpatialStructure", RelatingStructure=storey)
        wall = _Entity(
            "IfcWall",
            GlobalId="wall-1",
            Name="W",
            ContainedInStructure=[wall_rel],
            ReferencedInStructures=[],
            Decomposes=[],
        )
        model = _Model({"IfcSystem": [], "IfcRoot": [wall, storey, grid, axis]})
        index = IfcSpatialIndex.from_model(model)
        hit = index.lookup("wall-1")
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.storey_name, "1 этаж")
        self.assertEqual(hit.grid_axis, "А")

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

    def test_json_sidecar_roundtrip_is_not_a_disk_r_tree(self) -> None:
        index = IfcSpatialIndex(
            elements={
                "wall-1": IfcSpatialElement(
                    "wall-1",
                    "IfcWall",
                    "Wall PQ",
                    ("sys-1",),
                    storey_name="3 этаж",
                    grid_axis="А",
                )
            },
            systems={"sys-1": ("wall-1",)},
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.json"
            write_spatial_index_json(index, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact_type"], "ifc_spatial_index_sidecar")
            self.assertFalse(payload["disk_r_tree"])
            self.assertFalse(payload["streaming_parser"])
            self.assertFalse(payload["wired_into_analyze"])
            self.assertFalse(payload["raises_default_cap"])
            loaded = read_spatial_index_json(path)
            hit = loaded.lookup("wall-1")
            self.assertIsNotNone(hit)
            assert hit is not None
            self.assertEqual(hit.storey_name, "3 этаж")
            self.assertEqual(hit.grid_axis, "А")
            self.assertEqual(loaded.system_members("sys-1"), ("wall-1",))
            payload["disk_r_tree"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                read_spatial_index_json(path)


if __name__ == "__main__":
    unittest.main()
