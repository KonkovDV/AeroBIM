"""§3 layers 0-1: deterministic decision of whether/where a VLM runs (domain-pure).

Layer 0 — if a machine-readable text layer exists, the VLM is not invoked at all
(cheapest, fully reproducible). Layer 1 — otherwise each detected layout region
becomes ONE narrow read task (one region = one call); the whole sheet is never
sent to the VLM. This module is pure: no I/O, no image handling.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from aerobim.domain.models import DrawingRegionRef


@dataclass(frozen=True)
class RegionReadTask:
    region_id: str
    bbox_xyxy: tuple[float, float, float, float]


@dataclass(frozen=True)
class RegionReadPlan:
    skip_vlm: bool
    reason: str
    tasks: tuple[RegionReadTask, ...] = ()


def plan_region_reads(
    *,
    text_layer_present: bool,
    regions: Sequence[DrawingRegionRef],
) -> RegionReadPlan:
    """Return the region-restricted read plan for one sheet (layers 0-1)."""
    if text_layer_present:
        return RegionReadPlan(
            skip_vlm=True,
            reason="Layer 0: machine-readable text layer present; VLM not invoked",
        )
    tasks = tuple(
        RegionReadTask(
            region_id=f"r{index:02d}-{region.modality or 'region'}",
            bbox_xyxy=region.bbox_xyxy,
        )
        for index, region in enumerate(regions)
    )
    if not tasks:
        return RegionReadPlan(
            skip_vlm=True,
            reason="Layer 1: no layout regions detected; VLM not invoked",
        )
    return RegionReadPlan(
        skip_vlm=False,
        reason=f"Layer 1: {len(tasks)} region(s) queued for region-restricted VLM",
        tasks=tasks,
    )


__all__ = ["RegionReadPlan", "RegionReadTask", "plan_region_reads"]
