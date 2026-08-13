"""IfcOpenShell AABB broadphase for MEP system pairs (NOT geometry-verified).

Uses ``ifcopenshell.geom.create_shape`` world-coord vertex extents per system
member, unions per system, then keeps graph edges whose AABBs overlap.

Claim boundary: AABB overlap ≠ intersection / clearance / Solibri clash.
Always pair with ``geometry_verified=False`` on analyze.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

from aerobim.domain.mep import MepSystemGraph
from aerobim.domain.mep_aabb import (
    AabbFilterResult,
    AxisAlignedBox3d,
    applied_aabb_result,
    filter_pairs_by_aabb,
    unavailable_aabb_result,
    union_aabb,
)
from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_session

_logger = logging.getLogger("aerobim.mep_aabb")


class IfcAabbMepPairFilter:
    """Broadphase candidate filter over federated/source IFC paths on the graph."""

    def __init__(self, *, eps_m: float = 0.0) -> None:
        self._eps_m = eps_m

    def filter_pairs(self, graph: MepSystemGraph) -> AabbFilterResult:
        edge_pairs: set[tuple[str, str]] = {
            cast(tuple[str, str], tuple(sorted((a.strip(), b.strip()), key=str.casefold)))
            for a, b in graph.edges
        }
        if not edge_pairs:
            return unavailable_aabb_result(
                reason="graph has no edges for AABB filter",
                pairs_before=0,
            )

        paths = _source_paths(graph)
        if not paths:
            return unavailable_aabb_result(
                reason="no source IFC paths on graph for AABB filter",
                pairs_before=len(edge_pairs),
            )

        guid_boxes: dict[str, AxisAlignedBox3d] = {}
        for path in paths:
            try:
                session = open_ifc_session(Path(path))
            except Exception as exc:  # noqa: BLE001
                _logger.info("AABB filter: cannot open %s: %s", path, exc)
                continue
            guid_boxes.update(_element_boxes_from_model(session.model))

        if not guid_boxes:
            return unavailable_aabb_result(
                reason=(
                    "no element AABBs built (missing geometry / create_shape failed) "
                    "— falling back to co_presence/connects edges"
                ),
                pairs_before=len(edge_pairs),
            )

        system_boxes: dict[str, AxisAlignedBox3d] = {}
        for node in graph.nodes:
            member_boxes = [guid_boxes[guid] for guid in node.element_guids if guid in guid_boxes]
            merged = union_aabb(member_boxes)
            if merged is not None:
                system_boxes[node.system_id] = merged

        if len(system_boxes) < 2:
            return unavailable_aabb_result(
                reason=(
                    f"AABB built for {len(system_boxes)} system(s) only "
                    "(need ≥2) — falling back to edges"
                ),
                pairs_before=len(edge_pairs),
            )

        kept = filter_pairs_by_aabb(edge_pairs, system_boxes, eps=self._eps_m)
        return applied_aabb_result(
            kept,
            boxes_built=len(system_boxes),
            pairs_before=len(edge_pairs),
        )


def _source_paths(graph: MepSystemGraph) -> list[str]:
    raw = graph.source_ifc or ""
    if not raw.strip():
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _element_boxes_from_model(
    model: Any, *, ifc_types: tuple[str, ...] | None = None
) -> dict[str, AxisAlignedBox3d]:
    try:
        import ifcopenshell.geom
    except ModuleNotFoundError:
        return {}

    settings_factory: Any = ifcopenshell.geom.settings
    geom_settings: Any = settings_factory()
    try:
        geom_settings.set(geom_settings.USE_WORLD_COORDS, True)
    except Exception:  # noqa: BLE001 — settings enum variance across versions
        pass

    boxes: dict[str, AxisAlignedBox3d] = {}
    try:
        if ifc_types:
            products = []
            seen: set[int] = set()
            for type_name in ifc_types:
                for product in model.by_type(type_name):
                    ident = id(product)
                    if ident in seen:
                        continue
                    seen.add(ident)
                    products.append(product)
        else:
            products = list(model.by_type("IfcProduct"))
    except Exception:  # noqa: BLE001
        return {}

    for product in products:
        guid = str(getattr(product, "GlobalId", "") or "").strip()
        if not guid:
            continue
        box = _bbox_from_product(ifcopenshell.geom, geom_settings, product)
        if box is not None:
            boxes[guid] = box
    return boxes


def _bbox_from_product(geom: Any, settings: Any, product: Any) -> AxisAlignedBox3d | None:
    try:
        shape = geom.create_shape(settings, product)
    except Exception:  # noqa: BLE001 — many products lack tessellatable geometry
        return None
    geometry = getattr(shape, "geometry", None)
    verts = getattr(geometry, "verts", None) if geometry is not None else None
    if not verts:
        return None
    try:
        coords = list(verts)
    except TypeError:
        return None
    if len(coords) < 3 or len(coords) % 3 != 0:
        return None
    xs = coords[0::3]
    ys = coords[1::3]
    zs = coords[2::3]
    try:
        return AxisAlignedBox3d(
            xmin=float(min(xs)),
            ymin=float(min(ys)),
            zmin=float(min(zs)),
            xmax=float(max(xs)),
            ymax=float(max(ys)),
            zmax=float(max(zs)),
        )
    except (TypeError, ValueError):
        return None


__all__ = ["IfcAabbMepPairFilter"]
