"""Grounding for VLM drawing reads (Kimi K3 / small Kimi-VL) — domain-pure.

Turns a raw VLM JSON response into **candidate** ``DrawingRegionRef`` overlays.
Never produces a verdict (ADR-001 / TR-2/27/31): the deterministic engine and the
expert own ``summary.passed``.

Academic posture (Jul 2026):
- Structured output must be a strict JSON schema with a tolerant parser and a
  fail-closed path on schema deviation (constrained-decoding consensus,
  arXiv:2606.09395). A non-conforming response yields **zero** grounded regions
  plus an explicit reason — never a silent best-effort guess.
- Black-box VLM verbalized confidence is **not** trustworthy as calibrated
  (Khan et al. CVPR 2024; VL-Calibration, Xiao et al. ACL 2026). We clamp it to
  [0, 1] and treat below-threshold reads as **abstention → HITL** (calibrated
  action abstention), never as accepted fact.
- Neuro-symbolic guardrail: the VLM candidate is verified/decided downstream by
  deterministic rules (Castagnone 2026, MDPI Buildings 16(3):534).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aerobim.domain.models import DrawingRegionRef

_VLM_MODALITY = "vlm"
_DEFAULT_MIN_CONFIDENCE = 0.60
_DEFAULT_COORDINATE_SYSTEM = "page-pixel"


@dataclass(frozen=True)
class VlmReadResult:
    """Outcome of grounding one VLM drawing-read response."""

    regions: tuple[DrawingRegionRef, ...] = ()
    parse_ok: bool = False
    reason: str | None = None
    hitl_count: int = 0
    evidence_refs: tuple[str, ...] = field(default=())


def _clamp_unit(value: object) -> float:
    """Clamp any numeric-ish confidence into [0, 1]; non-numeric → 0.0 (abstain)."""
    try:
        conf = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    if conf < 0.0:
        return 0.0
    if conf > 1.0:
        return 1.0
    return conf


def _parse_bbox(raw: object) -> tuple[float, float, float, float] | None:
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        return None
    try:
        x1, y1, x2, y2 = (float(v) for v in raw)
    except (TypeError, ValueError):
        return None
    return (x1, y1, x2, y2)


def ground_vlm_drawing_response(
    raw: object,
    *,
    sheet_id: str,
    model_id: str,
    min_confidence: float = _DEFAULT_MIN_CONFIDENCE,
    page_width: float | None = None,
    page_height: float | None = None,
) -> VlmReadResult:
    """Ground a raw VLM response into candidate regions; fail-closed on deviation.

    Expected schema::

        {"coordinate_system": "page-pixel",
         "regions": [{"bbox": [x1,y1,x2,y2], "text": "...", "field": "...",
                      "confidence": 0.87}]}

    Any structural deviation (not an object, missing/!list ``regions``, a region
    without a valid 4-number bbox) yields ``parse_ok=False`` with no regions and a
    reason. Regions with confidence below ``min_confidence`` are kept but flagged
    ``hitl_required`` (abstention), never dropped silently.
    """

    if not isinstance(raw, dict):
        return VlmReadResult(parse_ok=False, reason="VLM response is not a JSON object")
    regions_raw = raw.get("regions")
    if not isinstance(regions_raw, list):
        return VlmReadResult(parse_ok=False, reason="VLM response has no 'regions' array")

    coordinate_system = str(raw.get("coordinate_system") or _DEFAULT_COORDINATE_SYSTEM)
    grounded: list[DrawingRegionRef] = []
    evidence: list[str] = [f"vlm:{model_id}", f"sheet:{sheet_id}"]
    hitl = 0
    for index, region_raw in enumerate(regions_raw):
        if not isinstance(region_raw, dict):
            return VlmReadResult(
                parse_ok=False,
                reason=f"VLM region #{index} is not an object (schema deviation)",
            )
        bbox = _parse_bbox(region_raw.get("bbox"))
        if bbox is None:
            return VlmReadResult(
                parse_ok=False,
                reason=f"VLM region #{index} has an invalid bbox (schema deviation)",
            )
        confidence = _clamp_unit(region_raw.get("confidence"))
        low = confidence < min_confidence
        if low:
            hitl += 1
        grounded.append(
            DrawingRegionRef(
                sheet_id=sheet_id,
                bbox_xyxy=bbox,
                confidence=confidence,
                modality=_VLM_MODALITY,
                hitl_required=low,
                hitl_reason=(
                    f"vlm confidence {confidence:.2f} < {min_confidence:.2f} "
                    "(uncalibrated; expert review required)"
                    if low
                    else None
                ),
                coordinate_system=coordinate_system,
                page_width=page_width,
                page_height=page_height,
            )
        )

    return VlmReadResult(
        regions=tuple(grounded),
        parse_ok=True,
        reason=None,
        hitl_count=hitl,
        evidence_refs=tuple(evidence),
    )


__all__ = [
    "VlmReadResult",
    "ground_vlm_drawing_response",
]
