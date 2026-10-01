"""Extract IfcWall Qto_WallBaseQuantities.Width as SI length observations."""

from __future__ import annotations

import hashlib
from pathlib import Path

from aerobim.domain.drawing_ifc_consistency import QTO_WIDTH, IfcQuantityObservation
from aerobim.domain.quantity import parse_quantity
from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_session

_QTO_PSET = "Qto_WallBaseQuantities"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_float(raw: object) -> float | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int | float):
        return float(raw)
    if isinstance(raw, str):
        text = raw.strip().replace(",", ".")
        if not text:
            return None
        try:
            return float(text.split()[0])
        except ValueError:
            return None
    return None


class IfcWallWidthExtractor:
    """Read wall Width QTO; missing property stays missing (not 0)."""

    def extract(
        self,
        ifc_path: Path,
        *,
        ifc_revision: str | None = None,
    ) -> list[IfcQuantityObservation]:
        if not ifc_path.exists():
            raise FileNotFoundError(ifc_path)
        try:
            from ifcopenshell.util.element import get_psets
            from ifcopenshell.util.unit import calculate_unit_scale
        except ModuleNotFoundError as exc:
            raise RuntimeError("Install ifcopenshell for drawing↔IFC width compare") from exc

        with open_ifc_session(ifc_path) as session:
            model = session.model
            try:
                length_scale = float(calculate_unit_scale(model, "LENGTHUNIT"))
            except Exception as exc:
                raise RuntimeError("LENGTHUNIT scale NOT_VERIFIED") from exc
            if length_scale <= 0:
                raise RuntimeError("LENGTHUNIT scale NOT_VERIFIED")
            digest = _sha256_file(ifc_path)
            observations: list[IfcQuantityObservation] = []
            try:
                walls = tuple(model.by_type("IfcWall"))
            except Exception:
                walls = ()
            names: dict[str, int] = {}
            tags: dict[str, int] = {}
            for wall in walls:
                name = str(getattr(wall, "Name", "") or "").strip()
                tag = str(getattr(wall, "Tag", "") or "").strip()
                if name:
                    names[name] = names.get(name, 0) + 1
                if tag:
                    tags[tag] = tags.get(tag, 0) + 1
            for wall in walls:
                guid = str(getattr(wall, "GlobalId", "") or "").strip()
                name = str(getattr(wall, "Name", "") or "").strip()
                tag = str(getattr(wall, "Tag", "") or "").strip()
                display_name = name or tag
                if not guid or not display_name:
                    continue
                if name and names.get(name, 0) > 1:
                    continue
                if (not name) and tag and tags.get(tag, 0) > 1:
                    continue
                psets = get_psets(wall)
                props = psets.get(_QTO_PSET)
                if not isinstance(props, dict):
                    continue
                raw_width = None
                for prop_name, prop_value in props.items():
                    if prop_name.strip() != QTO_WIDTH:
                        continue
                    raw_width = _as_float(prop_value)
                    break
                if raw_width is None:
                    continue
                si_metres = raw_width * length_scale
                quantity = parse_quantity(si_metres, "m")
                observations.append(
                    IfcQuantityObservation(
                        global_id=guid,
                        name=display_name,
                        quantity_name=QTO_WIDTH,
                        value=quantity,
                        ifc_path=ifc_path,
                        ifc_sha256=digest,
                        ifc_revision=ifc_revision,
                    )
                )
            return observations
