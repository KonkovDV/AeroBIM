#!/usr/bin/env python3
"""Two-file crossing-wall IFC pair plus IfcPipeSegment vs wall for federated
IfcClash smoke (not customer evidence, not MEP system-aware)."""

from __future__ import annotations

from pathlib import Path

import ifcopenshell.api


def _new_model(name: str):
    model = ifcopenshell.api.run("project.create_file")
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name=name)
    length = ifcopenshell.api.run("unit.add_si_unit", model, unit_type="LENGTHUNIT", prefix="MILLI")
    area = ifcopenshell.api.run("unit.add_si_unit", model, unit_type="AREAUNIT")
    ifcopenshell.api.run("unit.assign_unit", model, units=[length, area])
    model3d = ifcopenshell.api.run("context.add_context", model, context_type="Model")
    body = ifcopenshell.api.run(
        "context.add_context",
        model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=model3d,
    )
    site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuilding", name="Building"
    )
    storey = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuildingStorey", name="L0"
    )
    ifcopenshell.api.run("aggregate.assign_object", model, products=[site], relating_object=project)
    ifcopenshell.api.run(
        "aggregate.assign_object", model, products=[building], relating_object=site
    )
    ifcopenshell.api.run(
        "aggregate.assign_object", model, products=[storey], relating_object=building
    )
    return model, body, storey


def _element_2pt(
    model,
    *,
    body,
    storey,
    ifc_class: str,
    name: str,
    p1: tuple[float, float],
    p2: tuple[float, float],
) -> None:
    element = ifcopenshell.api.run("root.create_entity", model, ifc_class=ifc_class, name=name)
    ifcopenshell.api.run(
        "spatial.assign_container", model, products=[element], relating_structure=storey
    )
    rep = ifcopenshell.api.run(
        "geometry.create_2pt_wall",
        model,
        element=element,
        context=body,
        p1=p1,
        p2=p2,
        elevation=0.0,
        height=3.0,
        thickness=0.2,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model, product=element, representation=rep
    )


def _wall_2pt(
    model, *, body, storey, name: str, p1: tuple[float, float], p2: tuple[float, float]
) -> None:
    _element_2pt(
        model, body=body, storey=storey, ifc_class="IfcWall", name=name, p1=p1, p2=p2
    )


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    out_dir = repo / "samples" / "ifc"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Planted pair is hash-pinned in docs/evidence/federated-clash-*. Do not
    # rewrite existing files when regenerating the clearance-gap pair.
    path_a = out_dir / "clash-federated-box-a.ifc"
    if path_a.is_file():
        print(f"keep {path_a} bytes={path_a.stat().st_size}")
    else:
        file_a, body_a, storey_a = _new_model("ClashFederatedA")
        _wall_2pt(file_a, body=body_a, storey=storey_a, name="Wall-A", p1=(0.0, 0.0), p2=(4.0, 0.0))
        file_a.write(str(path_a))
        print(f"wrote {path_a} bytes={path_a.stat().st_size}")

    path_b = out_dir / "clash-federated-box-b.ifc"
    if path_b.is_file():
        print(f"keep {path_b} bytes={path_b.stat().st_size}")
    else:
        file_b, body_b, storey_b = _new_model("ClashFederatedB")
        _wall_2pt(
            file_b,
            body=body_b,
            storey=storey_b,
            name="Wall-B",
            p1=(2.0, -1.0),
            p2=(2.0, 1.0),
        )
        file_b.write(str(path_b))
        print(f"wrote {path_b} bytes={path_b.stat().st_size}")

    path_p = out_dir / "clash-federated-pipe-b.ifc"
    if path_p.is_file():
        print(f"keep {path_p} bytes={path_p.stat().st_size}")
    else:
        file_p, body_p, storey_p = _new_model("ClashFederatedPipe")
        _element_2pt(
            file_p,
            body=body_p,
            storey=storey_p,
            ifc_class="IfcPipeSegment",
            name="Pipe-B",
            p1=(2.0, -1.0),
            p2=(2.0, 1.0),
        )
        file_p.write(str(path_p))
        print(f"wrote {path_p} bytes={path_p.stat().st_size}")

    # Parallel walls, 0.2 m thick, centerlines 0.23 m apart → ~30 mm gap.
    # Intersection should miss; 50 mm clearance should hit.
    # HVAC sprinkler fixture has no tessellated geometry — do not use it here.
    file_g1, body_g1, storey_g1 = _new_model("ClashClearanceGapA")
    _wall_2pt(
        file_g1,
        body=body_g1,
        storey=storey_g1,
        name="Wall-Gap-A",
        p1=(0.0, 0.0),
        p2=(4.0, 0.0),
    )
    path_g1 = out_dir / "clash-clearance-gap-a.ifc"
    file_g1.write(str(path_g1))

    file_g2, body_g2, storey_g2 = _new_model("ClashClearanceGapB")
    _wall_2pt(
        file_g2,
        body=body_g2,
        storey=storey_g2,
        name="Wall-Gap-B",
        p1=(0.0, 0.23),
        p2=(4.0, 0.23),
    )
    path_g2 = out_dir / "clash-clearance-gap-b.ifc"
    file_g2.write(str(path_g2))

    print(f"wrote {path_g1} bytes={path_g1.stat().st_size}")
    print(f"wrote {path_g2} bytes={path_g2.stat().st_size}")


if __name__ == "__main__":
    main()
