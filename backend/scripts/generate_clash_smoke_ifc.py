#!/usr/bin/env python3
"""Create a minimal IFC with two overlapping walls for clash-path smoke (fixture only)."""

from __future__ import annotations

from pathlib import Path

import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.geometry
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    out = repo / "samples" / "ifc" / "clash-two-overlapping-boxes.ifc"
    out.parent.mkdir(parents=True, exist_ok=True)

    f = ifcopenshell.api.project.create_file(version="IFC4")
    project = ifcopenshell.api.root.create_entity(f, ifc_class="IfcProject", name="ClashSmoke")
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

    # Overlapping extents along X — hard intersection smoke only.
    box_at("Wall-A", 0.0, 0.0, 5.0, 0.3, 3.0)
    box_at("Wall-B", 2.0, 0.0, 5.0, 0.3, 3.0)

    f.write(str(out))
    print(f"wrote {out} bytes={out.stat().st_size}")


if __name__ == "__main__":
    main()
