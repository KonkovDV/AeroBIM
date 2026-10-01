#!/usr/bin/env python3
"""Build an IFC fixture with controlled overlapping / separated walls (extent clash).

Fixture-only: geometric AABB extents for measurement slice — not customer corpus,
not IfcClash mesh product claim, not TZ >90%.
"""

from __future__ import annotations

from pathlib import Path

import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.geometry
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit


def write_extent_clash_fixture(out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    f = ifcopenshell.api.project.create_file(version="IFC4")
    project = ifcopenshell.api.root.create_entity(f, ifc_class="IfcProject", name="ExtentClashFixture")
    ifcopenshell.api.unit.assign_unit(f)
    context = ifcopenshell.api.context.add_context(f, context_type="Model")
    body = ifcopenshell.api.context.add_context(
        f,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=context,
    )
    site = ifcopenshell.api.root.create_entity(f, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuilding", name="Building")
    storey = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuildingStorey", name="L0")
    ifcopenshell.api.aggregate.assign_object(f, products=[site], relating_object=project)
    ifcopenshell.api.aggregate.assign_object(f, products=[building], relating_object=site)
    ifcopenshell.api.aggregate.assign_object(f, products=[storey], relating_object=building)

    def box_at(name: str, x: float, y: float, dx: float, dy: float, dz: float) -> None:
        wall = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWall", name=name)
        representation = ifcopenshell.api.geometry.add_wall_representation(
            f,
            context=body,
            length=dx,
            height=dz,
            thickness=dy,
        )
        ifcopenshell.api.geometry.assign_representation(
            f, product=wall, representation=representation
        )
        ifcopenshell.api.geometry.edit_object_placement(
            f,
            product=wall,
            matrix=((1, 0, 0, x), (0, 1, 0, y), (0, 0, 1, 0), (0, 0, 0, 1)),
            is_si=True,
        )
        ifcopenshell.api.spatial.assign_container(f, products=[wall], relating_structure=storey)

    # Five intended extent overlaps (TP when labeled + detected).
    box_at("Wall-A1", 0.0, 0.0, 5.0, 0.3, 3.0)
    box_at("Wall-B1", 2.0, 0.0, 5.0, 0.3, 3.0)
    box_at("Wall-A2", 0.0, 5.0, 4.0, 0.3, 3.0)
    box_at("Wall-B2", 1.5, 5.0, 4.0, 0.3, 3.0)
    box_at("Wall-A3", 10.0, 0.0, 3.0, 0.4, 2.5)
    box_at("Wall-B3", 11.0, 0.0, 3.0, 0.4, 2.5)
    box_at("Wall-A4", 20.0, 0.0, 6.0, 0.25, 3.0)
    box_at("Wall-B4", 22.0, -0.1, 6.0, 0.25, 3.0)
    box_at("Wall-A5", 30.0, 0.0, 2.0, 0.5, 3.0)
    box_at("Wall-B5", 30.5, 0.0, 2.0, 0.5, 3.0)
    # Sixth intended overlap (KT#2 densify 2026-08-12).
    box_at("Wall-A6", 60.0, 0.0, 4.0, 0.3, 3.0)
    box_at("Wall-B6", 61.5, 0.05, 4.0, 0.3, 3.0)
    # Separated pair — must not be reported as clash.
    box_at("Wall-Sep-L", 40.0, 0.0, 2.0, 0.3, 3.0)
    box_at("Wall-Sep-R", 50.0, 0.0, 2.0, 0.3, 3.0)
    # Near-miss gap (~0.5 m) — must not be reported as AABB overlap.
    box_at("Wall-Near-L", 70.0, 0.0, 2.0, 0.3, 3.0)
    box_at("Wall-Near-R", 72.5, 0.0, 2.0, 0.3, 3.0)

    f.write(str(out))
    return out


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    out = repo / "samples" / "ifc" / "clash-extent-overlap-fixture.ifc"
    path = write_extent_clash_fixture(out)
    print(f"wrote {path} bytes={path.stat().st_size}")


if __name__ == "__main__":
    main()
