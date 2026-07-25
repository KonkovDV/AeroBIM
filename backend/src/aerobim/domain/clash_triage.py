"""Deterministic clash relevance triage — advisory ordering, never a verdict.

July 2026 practice alignment: raw clash lists overload reviewers, so modern
BIM-coordination pipelines run a relevance-triage step (dedup + severity
banding + stable ranking) before HITL review (Ailem et al. 2026, Automation in
Construction, clash relevance filtering; Koo et al. 2026, ASCE JCEM, clash
analysis/resolution framework). AeroBIM implements the *deterministic* subset:

- symmetric-pair dedup (A↔B == B↔A) keeping the worst instance;
- penetration-depth / clearance-gap bands with documented thresholds;
- stable, input-order-independent ranking for review and BCF topic order;
- an atomic, self-verifiable rationale per item (each triage claim carries the
  deterministic inputs that justify it — TACO/EACL-2026-style atomic claims).

Claim boundary: no ML relevance model is claimed (customer corpus absent,
RT-001). Triage is advisory presentation metadata; it never writes
``summary.passed`` and never suppresses a clash from the report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from aerobim.domain.models import ClashResult


class ClashTriageBand(StrEnum):
    """Reviewer-facing severity band; ordering is CRITICAL > MAJOR > MINOR > NEGLIGIBLE."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    NEGLIGIBLE = "negligible"


_BAND_ORDER: dict[ClashTriageBand, int] = {
    ClashTriageBand.CRITICAL: 0,
    ClashTriageBand.MAJOR: 1,
    ClashTriageBand.MINOR: 2,
    ClashTriageBand.NEGLIGIBLE: 3,
}


@dataclass(frozen=True)
class ClashTriageConfig:
    """Documented deterministic thresholds (metres).

    Hard clashes band by penetration depth; clearance clashes band by gap
    (smaller gap = worse). Defaults follow common coordination tolerance
    practice (mm-scale noise vs cm-scale rework risk); they are presentation
    thresholds, not norm values, and are overridable per deployment.
    """

    hard_critical_depth_m: float = 0.050
    hard_major_depth_m: float = 0.010
    hard_minor_depth_m: float = 0.001
    clearance_major_gap_m: float = 0.002

    def band_for(self, clash: ClashResult) -> ClashTriageBand:
        if clash.clash_type == "clearance":
            if clash.distance <= self.clearance_major_gap_m:
                return ClashTriageBand.MAJOR
            return ClashTriageBand.MINOR
        depth = clash.distance
        if depth >= self.hard_critical_depth_m:
            return ClashTriageBand.CRITICAL
        if depth >= self.hard_major_depth_m:
            return ClashTriageBand.MAJOR
        if depth >= self.hard_minor_depth_m:
            return ClashTriageBand.MINOR
        return ClashTriageBand.NEGLIGIBLE


@dataclass(frozen=True)
class TriagedClash:
    """One deduped clash with band, rank and an atomic verifiable rationale."""

    clash: ClashResult
    band: ClashTriageBand
    rank: int
    """1-based deterministic review order (1 = review first)."""
    pair_key: tuple[str, str]
    rationale: str
    """Atomic claim with the deterministic inputs that justify the band."""
    duplicates_merged: int = 1
    """Number of raw engine rows collapsed into this item (symmetric dedup)."""


@dataclass(frozen=True)
class ClashTriageResult:
    """Advisory triage output — ordering metadata only, never a verdict."""

    items: tuple[TriagedClash, ...]
    duplicate_count: int
    band_counts: dict[ClashTriageBand, int] = field(default_factory=dict)
    config: ClashTriageConfig = field(default_factory=ClashTriageConfig)


def pair_key(clash: ClashResult) -> tuple[str, str]:
    """Undirected element pair identity (A↔B == B↔A)."""

    a = clash.element_a_guid.strip()
    b = clash.element_b_guid.strip()
    return (a, b) if a <= b else (b, a)


def _severity_metric(clash: ClashResult) -> float:
    """Higher = worse. Hard: deeper penetration; clearance: smaller gap."""

    if clash.clash_type == "clearance":
        return -clash.distance
    return clash.distance


def _rationale(clash: ClashResult, band: ClashTriageBand, config: ClashTriageConfig) -> str:
    if clash.clash_type == "clearance":
        return (
            f"clearance gap={clash.distance:.4f}m; "
            f"major_gap<={config.clearance_major_gap_m:.4f}m -> band={band.value}"
        )
    return (
        f"hard depth={clash.distance:.4f}m; thresholds "
        f"critical>={config.hard_critical_depth_m:.4f}m, "
        f"major>={config.hard_major_depth_m:.4f}m, "
        f"minor>={config.hard_minor_depth_m:.4f}m -> band={band.value}"
    )


def triage_clash_results(
    results: tuple[ClashResult, ...] | list[ClashResult],
    *,
    config: ClashTriageConfig | None = None,
) -> ClashTriageResult:
    """Dedupe, band and rank clash results deterministically.

    Output is independent of input order: grouping is by undirected pair +
    clash_type keeping the worst instance; ranking sorts by (band, severity
    metric desc, pair_key, clash_type). No clash is dropped — negligible items
    stay in the tail so reviewers still see them.
    """

    cfg = config or ClashTriageConfig()
    groups: dict[tuple[str, str, str], tuple[ClashResult, int]] = {}
    for clash in results:
        key = (*pair_key(clash), clash.clash_type)
        existing = groups.get(key)
        if existing is None:
            groups[key] = (clash, 1)
        else:
            worst, count = existing
            if _severity_metric(clash) > _severity_metric(worst):
                worst = clash
            groups[key] = (worst, count + 1)

    duplicate_count = sum(count - 1 for _, count in groups.values())

    staged: list[tuple[tuple[int, float, str, str, str], ClashResult, int]] = []
    for (a, b, clash_type), (worst, count) in groups.items():
        band = cfg.band_for(worst)
        sort_key = (_BAND_ORDER[band], -_severity_metric(worst), a, b, clash_type)
        staged.append((sort_key, worst, count))
    staged.sort(key=lambda row: row[0])

    items: list[TriagedClash] = []
    band_counts: dict[ClashTriageBand, int] = {}
    for rank, (_, worst, count) in enumerate(staged, start=1):
        band = cfg.band_for(worst)
        band_counts[band] = band_counts.get(band, 0) + 1
        items.append(
            TriagedClash(
                clash=worst,
                band=band,
                rank=rank,
                pair_key=pair_key(worst),
                rationale=_rationale(worst, band, cfg),
                duplicates_merged=count,
            )
        )

    return ClashTriageResult(
        items=tuple(items),
        duplicate_count=duplicate_count,
        band_counts=band_counts,
        config=cfg,
    )
