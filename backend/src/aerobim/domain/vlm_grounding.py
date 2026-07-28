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

import math
from dataclasses import dataclass, field

from aerobim.domain.models import DrawingRegionRef
from aerobim.domain.vlm_normalize import is_allowed_kind, normalize_observation_value

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
    """Clamp confidence into [0, 1]; non-numeric / non-finite → 0.0 (abstain).

    NaN must not leak: ``nan < 0`` and ``nan > 1`` are both False, so an unclamped
    NaN would also slip past the ``< min_confidence`` abstention gate and read as
    high confidence. ``json.loads`` accepts the ``NaN`` literal, so this path is
    reachable from a hostile/buggy VLM response — fail closed to 0.0.
    """
    try:
        conf = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(conf):
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
        coords = tuple(float(v) for v in raw)
    except (TypeError, ValueError):
        return None
    # Reject NaN/Inf coordinates: not JSON-serializable and invalid as overlays.
    if not all(math.isfinite(coord) for coord in coords):
        return None
    return (coords[0], coords[1], coords[2], coords[3])


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


def _parse_bbox_rel(raw: object) -> tuple[float, float, float, float] | None:
    """Normalized [0,1] bbox; reject out-of-range / non-finite / degenerate (§4)."""
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        return None
    try:
        coords = tuple(float(v) for v in raw)
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(c) for c in coords):
        return None
    x1, y1, x2, y2 = coords
    if not (0.0 <= x1 < x2 <= 1.0 and 0.0 <= y1 < y2 <= 1.0):
        return None
    return (x1, y1, x2, y2)


@dataclass(frozen=True)
class VlmObservation:
    """One candidate observation from a region read (§4 schema)."""

    kind: str
    raw_value: str
    normalized_value: str | None
    bbox_rel: tuple[float, float, float, float]
    confidence: float
    hitl_required: bool
    confidence_calibrated: bool = False
    evidence_note: str = ""
    evidence_note_truncated: bool = False


@dataclass(frozen=True)
class VlmRegionReadResult:
    """Grounded outcome of one region read (§4)."""

    sheet_id: str
    region_id: str
    readable: bool
    observations: tuple[VlmObservation, ...] = ()
    parse_ok: bool = False
    reason: str | None = None
    hitl_count: int = 0
    dropped_count: int = 0


# Image-based prompt-injection hardening (arXiv 2603.03637; MDPI Electronics
# 14(10):1907, 2025; OWASP LLM Top-10 2025). A hostile image can steer the model
# to flood the advisory surface or emit a huge payload. The verdict is already
# out of reach (advisory-only, our normalizer ignores the model's value), so
# these are resource/noise bounds — fail-closed, drop-not-whole.
_MAX_OBSERVATIONS_PER_REGION = 128
_MAX_RAW_VALUE_CHARS = 512
_MAX_EVIDENCE_NOTE_CHARS = 512


def ground_vlm_region_observations(
    raw: object,
    *,
    sheet_id: str,
    region_id: str,
    min_confidence: float = _DEFAULT_MIN_CONFIDENCE,
    confidence_calibrated: bool = False,
) -> VlmRegionReadResult:
    """Ground the §4 observations schema; fail-closed only on structural deviation.

    Per §4: an observation with an invalid kind or out-of-range/degenerate
    ``bbox_rel`` is **dropped** (not the whole answer); the ``normalized_value`` is
    recomputed by OUR deterministic normalizer — the model's own value is ignored
    (paraphrase-divergence defense). Top-level structural problems fail closed.

    Abstention: a VLM's **verbalized** ``confidence`` is uncalibrated (EMNLP 2025
    main.74 "Seeing is Believing"; arXiv 2504.14848; LLM confidence surveys — high
    self-reported confidence is a poor guide to correctness). So unless a
    ``confidence_calibrated`` source is explicitly configured, EVERY candidate is
    flagged ``hitl_required`` and the numeric confidence is display/ranking only;
    high self-reported confidence must never silently clear expert review.
    """

    if not isinstance(raw, dict):
        return VlmRegionReadResult(
            sheet_id=sheet_id,
            region_id=region_id,
            readable=False,
            parse_ok=False,
            reason="VLM region response is not a JSON object",
        )
    observations_raw = raw.get("observations")
    if not isinstance(observations_raw, list):
        return VlmRegionReadResult(
            sheet_id=sheet_id,
            region_id=region_id,
            readable=False,
            parse_ok=False,
            reason="VLM region response has no 'observations' array",
        )

    readable = bool(raw.get("readable", True))
    grounded: list[VlmObservation] = []
    hitl = 0
    dropped = 0
    for observation_raw in observations_raw:
        if len(grounded) >= _MAX_OBSERVATIONS_PER_REGION:
            dropped += 1  # over per-region budget — injected flood guard
            continue
        if not isinstance(observation_raw, dict):
            dropped += 1
            continue
        kind = str(observation_raw.get("kind", "")).strip().lower()
        bbox = _parse_bbox_rel(observation_raw.get("bbox_rel"))
        if not is_allowed_kind(kind) or bbox is None:
            dropped += 1
            continue
        raw_value = str(observation_raw.get("raw_value", "") or "")
        if len(raw_value) > _MAX_RAW_VALUE_CHARS:
            dropped += 1  # oversized payload — injection/garbage guard
            continue
        confidence = _clamp_unit(observation_raw.get("confidence"))
        # Uncalibrated verbalized confidence must not clear expert review: HITL
        # every candidate unless a calibrated confidence source is configured.
        needs_hitl = confidence < min_confidence or not confidence_calibrated
        if needs_hitl:
            hitl += 1
        # §17.5: truncating evidence_note must not silently hide an attack/corruption
        # payload — keep a bounded note but flag that truncation happened.
        note_raw = str(observation_raw.get("evidence_note", "") or "")
        grounded.append(
            VlmObservation(
                kind=kind,
                raw_value=raw_value,
                normalized_value=normalize_observation_value(kind, raw_value),
                bbox_rel=bbox,
                confidence=confidence,
                hitl_required=needs_hitl,
                confidence_calibrated=confidence_calibrated,
                evidence_note=note_raw[:_MAX_EVIDENCE_NOTE_CHARS],
                evidence_note_truncated=len(note_raw) > _MAX_EVIDENCE_NOTE_CHARS,
            )
        )

    reason: str | None = None
    if not readable and not grounded:
        reason = str(raw.get("unreadable_reason") or "region marked unreadable")
    elif dropped:
        reason = f"{dropped} observation(s) dropped (invalid/oversized/over-budget)"
    return VlmRegionReadResult(
        sheet_id=sheet_id,
        region_id=region_id,
        readable=readable,
        observations=tuple(grounded),
        parse_ok=True,
        reason=reason,
        hitl_count=hitl,
        dropped_count=dropped,
    )


__all__ = [
    "VlmObservation",
    "VlmReadResult",
    "VlmRegionReadResult",
    "ground_vlm_drawing_response",
    "ground_vlm_region_observations",
]
