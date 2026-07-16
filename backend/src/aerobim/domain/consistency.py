"""Domain types for quantity / load сверка and package logic checks."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aerobim.domain.models import DrawingAnnotation, DrawingRegionRef
from aerobim.domain.quantity import QuantityValue, parse_quantity

_AREA_NAME_HINTS = (
    "grossfloorarea",
    "netfloorarea",
    "grossarea",
    "netarea",
    "area",
    "площад",
)
_VOLUME_NAME_HINTS = ("grossvolume", "netvolume", "volume", "объём", "объем")


@dataclass(frozen=True)
class QuantityClaim:
    """Declared area/space quantity to match against IFC Qto values (сверка)."""

    claim_id: str
    target_ref: str | None
    ifc_entity: str | None
    quantity_name: str
    declared: QuantityValue
    source_id: str | None = None


@dataclass(frozen=True)
class PackageManifest:
    """Lightweight package topology for logical consistency checks."""

    request_id: str
    ifc_path: Path
    has_requirement_source: bool
    has_technical_spec: bool
    has_calculation_source: bool
    has_ids: bool
    drawing_count: int
    drawing_sheet_ids: tuple[str, ...]
    pd_section_path: Path | None
    rd_section_path: Path | None
    revision: str | None
    stage: str | None


@dataclass(frozen=True)
class MultimodalDrawingResult:
    annotations: tuple[DrawingAnnotation, ...]
    regions: tuple[DrawingRegionRef, ...] = ()
    pipeline_mode_used: str = "ocr_only"
    degraded: bool = True
    reason: str | None = None


def claims_from_area_requirements(requirements: Sequence[Any]) -> list[QuantityClaim]:
    """Build QuantityClaim list from ParsedRequirement-like objects with area/volume units."""

    claims: list[QuantityClaim] = []
    for req in requirements:
        unit = (getattr(req, "unit", None) or "").strip()
        name = (getattr(req, "property_name", None) or "").strip()
        name_cf = name.casefold()
        unit_cf = unit.casefold()
        is_area = any(h in name_cf for h in _AREA_NAME_HINTS) or unit_cf in {
            "m2",
            "м2",
            "m²",
            "м²",
            "sqm",
        }
        is_volume = any(h in name_cf for h in _VOLUME_NAME_HINTS) or unit_cf in {
            "m3",
            "м3",
            "m³",
            "м³",
        }
        if not (is_area or is_volume):
            continue
        expected = getattr(req, "expected_value", None)
        if expected is None:
            continue
        try:
            numeric = float(str(expected).replace(",", ".").split()[0])
        except ValueError:
            continue
        default_unit = unit or ("m2" if is_area else "m3")
        declared = parse_quantity(numeric, default_unit)
        claims.append(
            QuantityClaim(
                claim_id=str(getattr(req, "rule_id", "qty")),
                target_ref=getattr(req, "target_ref", None),
                ifc_entity=getattr(req, "ifc_entity", None),
                quantity_name=name or ("GrossFloorArea" if is_area else "GrossVolume"),
                declared=declared,
                source_id=getattr(req, "source", None),
            )
        )
    return claims
