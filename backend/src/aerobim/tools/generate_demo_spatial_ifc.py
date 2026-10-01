"""Author the demo IFC with storey + one grid (jury spatial location).

Reads ``samples/ifc/walls-multi-entity.ifc``, writes
``samples/ifc/walls-multi-entity-spatial.ifc`` keeping wall GUIDs and psets.
Not a customer model. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

from pathlib import Path

import ifcopenshell
import ifcopenshell.guid

_REPO = Path(__file__).resolve().parents[4]
_SRC = _REPO / "samples" / "ifc" / "walls-multi-entity.ifc"
_DST = _REPO / "samples" / "ifc" / "walls-multi-entity-spatial.ifc"


def write_spatial_demo_ifc(*, src: Path = _SRC, dst: Path = _DST) -> Path:
    model = ifcopenshell.open(str(src))
    project = model.by_type("IfcProject")[0]
    walls = list(model.by_type("IfcWall"))
    if not walls:
        raise RuntimeError("source IFC has no IfcWall")

    site = model.create_entity(
        "IfcSite",
        GlobalId=ifcopenshell.guid.new(),
        Name="Demo site",
    )
    building = model.create_entity(
        "IfcBuilding",
        GlobalId=ifcopenshell.guid.new(),
        Name="Demo building",
    )
    storey = model.create_entity(
        "IfcBuildingStorey",
        GlobalId=ifcopenshell.guid.new(),
        Name="1 этаж",
    )
    model.create_entity(
        "IfcRelAggregates",
        GlobalId=ifcopenshell.guid.new(),
        RelatingObject=project,
        RelatedObjects=[site],
    )
    model.create_entity(
        "IfcRelAggregates",
        GlobalId=ifcopenshell.guid.new(),
        RelatingObject=site,
        RelatedObjects=[building],
    )
    model.create_entity(
        "IfcRelAggregates",
        GlobalId=ifcopenshell.guid.new(),
        RelatingObject=building,
        RelatedObjects=[storey],
    )

    origin = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    z_dir = model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    x_dir = model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0))
    axis2 = model.create_entity(
        "IfcAxis2Placement3D",
        Location=origin,
        Axis=z_dir,
        RefDirection=x_dir,
    )
    placement = model.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=axis2,
    )
    context = model.create_entity(
        "IfcGeometricRepresentationContext",
        ContextIdentifier="Model",
        ContextType="Model",
        CoordinateSpaceDimension=3,
        Precision=1.0e-5,
        WorldCoordinateSystem=axis2,
    )
    p_u0 = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    p_u1 = model.create_entity("IfcCartesianPoint", Coordinates=(10000.0, 0.0, 0.0))
    p_v0 = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    p_v1 = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 10000.0, 0.0))
    line_u = model.create_entity("IfcPolyline", Points=[p_u0, p_u1])
    line_v = model.create_entity("IfcPolyline", Points=[p_v0, p_v1])
    axis_u = model.create_entity(
        "IfcGridAxis",
        AxisTag="А",
        AxisCurve=line_u,
        SameSense=True,
    )
    axis_v = model.create_entity(
        "IfcGridAxis",
        AxisTag="1",
        AxisCurve=line_v,
        SameSense=True,
    )
    geom = model.create_entity("IfcGeometricCurveSet", Elements=[line_u, line_v])
    shape = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="FootPrint",
        RepresentationType="GeometricCurveSet",
        Items=[geom],
    )
    prod = model.create_entity("IfcProductDefinitionShape", Representations=[shape])
    grid = model.create_entity(
        "IfcGrid",
        GlobalId=ifcopenshell.guid.new(),
        Name="Demo grid",
        ObjectPlacement=placement,
        Representation=prod,
        UAxes=[axis_u],
        VAxes=[axis_v],
    )
    model.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        RelatingStructure=storey,
        RelatedElements=[*walls, grid],
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    model.write(str(dst))
    return dst


def main() -> int:
    path = write_spatial_demo_ifc()
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
