"""Extract IfcSpace inventory rows for advisory space-efficiency candidates."""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.space_efficiency_advisory import SpaceInventoryRow


def extract_space_inventory(ifc_path: Path | str | None) -> tuple[SpaceInventoryRow, ...]:
    """Best-effort IfcSpace inventory. Empty on missing path / missing ifcopenshell."""

    if ifc_path is None:
        return ()
    path = Path(ifc_path)
    if not path.is_file():
        return ()
    try:
        import ifcopenshell  # type: ignore[import-untyped]
        import ifcopenshell.util.element as element_util  # type: ignore[import-untyped]
    except ImportError:
        return ()

    try:
        model = ifcopenshell.open(str(path))
    except Exception:
        return ()

    rows: list[SpaceInventoryRow] = []
    for space in model.by_type("IfcSpace"):
        guid = getattr(space, "GlobalId", None) or ""
        if not guid:
            continue
        name = getattr(space, "Name", None)
        long_name = getattr(space, "LongName", None)
        predefined = getattr(space, "PredefinedType", None)
        predefined_s = str(predefined) if predefined is not None else None
        area: float | None = None
        try:
            qto = element_util.get_psets(space, qtos_only=True) or {}
            for _pset_name, props in qto.items():
                if not isinstance(props, dict):
                    continue
                raw = props.get("NetFloorArea")
                if raw is None:
                    continue
                area = float(raw)
                break
        except Exception:
            area = None
        rows.append(
            SpaceInventoryRow(
                guid=str(guid),
                name=str(name) if name else None,
                long_name=str(long_name) if long_name else None,
                net_floor_area=area,
                predefined_type=predefined_s,
            )
        )
    return tuple(rows)


__all__ = ["extract_space_inventory"]
