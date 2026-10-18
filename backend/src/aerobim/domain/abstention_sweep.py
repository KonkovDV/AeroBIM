"""Threshold sweep of drawing-advisory HITL. Not a calibration study.

The committed synthetic cases already carry verbalized confidences.
Raising the floor can only add ``hitl_required`` flags. ECE and Brier stay
absent: those cases have no outcome labels, so a score would be invented.
``publishable`` stays false.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Final

from aerobim.domain.vlm_grounding import ground_vlm_region_observations

SWEEP_TAUS: Final[tuple[float, ...]] = (0.35, 0.45, 0.60, 0.75)


def sweep_region_cases(
    cases: Sequence[Mapping[str, object]],
    taus: Sequence[float] = SWEEP_TAUS,
    *,
    calibrated_counterfactual: bool = False,
) -> dict[str, object]:
    """Ground each case at every floor and record the HITL share.

    ``calibrated_counterfactual=True`` pretends every case declared a
    calibrated confidence. That is a sensitivity curve, not a measured
    calibration.
    """

    if not cases:
        raise ValueError("abstention sweep requires at least one case")
    ordered = tuple(float(tau) for tau in taus)
    pairs = zip(ordered, ordered[1:], strict=False)
    if not ordered or any(previous > current for previous, current in pairs):
        raise ValueError("thresholds must be non-empty and non-decreasing")
    points: list[dict[str, object]] = []
    for tau in ordered:
        hitl = 0
        grounded = 0
        for case in cases:
            result = _ground_case(case, tau, calibrated_counterfactual=calibrated_counterfactual)
            hitl += result[0]
            grounded += result[1]
        rate = None if grounded == 0 else hitl / grounded
        points.append(
            {
                "tau": tau,
                "n_grounded": grounded,
                "hitl_count": hitl,
                "hitl_rate": rate,
            }
        )
    return {
        "artifact_type": "drawing_advisory_abstention_sweep",
        "claim_level": "fixture_only",
        "corpus_kind": "fixture",
        "publishable": False,
        "calibrated_counterfactual": calibrated_counterfactual,
        "ece": None,
        "brier": None,
        "calibration_note": (
            "ECE and Brier are omitted: the fixture has no outcome labels. "
            "Verbalized confidence is an abstention floor, not a probability."
        ),
        "points": points,
        "hitl_rate_nondecreasing": _nondecreasing(points),
    }


def _ground_case(
    case: Mapping[str, object],
    tau: float,
    *,
    calibrated_counterfactual: bool,
) -> tuple[int, int]:
    raw = case.get("vlm_response")
    if not isinstance(raw, dict):
        return (0, 0)
    calibrated = calibrated_counterfactual or case.get("confidence_calibrated") is True
    result = ground_vlm_region_observations(
        raw,
        sheet_id=str(case.get("sheet_id") or "sheet"),
        region_id=str(case.get("region_id") or case.get("case_id") or "region"),
        min_confidence=tau,
        confidence_calibrated=calibrated,
    )
    return (result.hitl_count, len(result.observations))


def _nondecreasing(points: Sequence[Mapping[str, object]]) -> bool:
    previous: float | None = None
    for point in points:
        rate = point.get("hitl_rate")
        if not isinstance(rate, float):
            continue
        if previous is not None and rate + 1e-12 < previous:
            return False
        previous = rate
    return True
