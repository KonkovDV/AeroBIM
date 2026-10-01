"""Drawing sheet coordinate systems for 2D provenance (fixture-first)."""

from __future__ import annotations

from dataclasses import dataclass

from aerobim.domain.models import DrawingAsset, DrawingRegionRef


@dataclass(frozen=True)
class SheetCoordinateSystem:
    sheet_id: str
    width: float
    height: float
    units: str = "page-pixel"
    origin: str = "bottom-left"

    def normalize_bbox(
        self,
        bbox_xyxy: tuple[float, float, float, float],
    ) -> tuple[float, float, float, float]:
        x0, y0, x1, y1 = bbox_xyxy
        if self.width <= 0 or self.height <= 0:
            raise ValueError("coordinate system requires positive width/height")
        return (
            max(0.0, min(1.0, x0 / self.width)),
            max(0.0, min(1.0, y0 / self.height)),
            max(0.0, min(1.0, x1 / self.width)),
            max(0.0, min(1.0, y1 / self.height)),
        )


def coordinate_system_from_asset(asset: DrawingAsset) -> SheetCoordinateSystem | None:
    if asset.coordinate_width is None or asset.coordinate_height is None:
        return None
    if asset.coordinate_width <= 0 or asset.coordinate_height <= 0:
        return None
    return SheetCoordinateSystem(
        sheet_id=asset.sheet_id,
        width=float(asset.coordinate_width),
        height=float(asset.coordinate_height),
    )


def coordinate_system_from_region(region: DrawingRegionRef) -> SheetCoordinateSystem | None:
    if region.page_width is None or region.page_height is None:
        return None
    if region.page_width <= 0 or region.page_height <= 0:
        return None
    units = (region.coordinate_system or "page-pixel").strip() or "page-pixel"
    return SheetCoordinateSystem(
        sheet_id=region.sheet_id,
        width=float(region.page_width),
        height=float(region.page_height),
        units=units,
    )


__all__ = [
    "SheetCoordinateSystem",
    "coordinate_system_from_asset",
    "coordinate_system_from_region",
]
