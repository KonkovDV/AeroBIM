"""Per-contour package analyze timing (profiling input — no optimization claims)."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from aerobim.domain.architecture import DEFAULT_PACKAGE_STAGE_BUDGET, Contour, StageBudget


@dataclass
class PackageTraceCollector:
    """Records wall-time per contour during one analyze execute()."""

    stage_budget: StageBudget = field(default_factory=lambda: DEFAULT_PACKAGE_STAGE_BUDGET)
    _elapsed_seconds: dict[str, float] = field(default_factory=dict, init=False)
    _active: dict[str, float] = field(default_factory=dict, init=False)

    def span(self, contour: Contour):
        return _ContourSpan(self, contour)

    def record(self, contour: Contour, elapsed_seconds: float) -> None:
        key = contour.value
        self._elapsed_seconds[key] = self._elapsed_seconds.get(key, 0.0) + elapsed_seconds

    def elapsed(self, contour: Contour) -> float:
        return self._elapsed_seconds.get(contour.value, 0.0)

    def total_elapsed_seconds(self) -> float:
        return sum(self._elapsed_seconds.values())

    def bottleneck_contour(self) -> str | None:
        if not self._elapsed_seconds:
            return None
        return max(self._elapsed_seconds.items(), key=lambda item: item[1])[0]

    def budget_utilization(self) -> dict[str, float]:
        minutes = {
            Contour.INGESTION.value: self.stage_budget.ingestion_minutes,
            Contour.DETERMINISTIC_VALIDATION.value: (
                self.stage_budget.deterministic_validation_minutes
            ),
            Contour.AI_ADVISORY.value: self.stage_budget.ai_advisory_minutes,
            Contour.EVIDENCE_REPORTING.value: self.stage_budget.evidence_reporting_minutes,
        }
        util: dict[str, float] = {}
        for key, elapsed in self._elapsed_seconds.items():
            budget_seconds = minutes.get(key, 0.0) * 60.0
            if budget_seconds <= 0:
                util[key] = 0.0
            else:
                util[key] = round(elapsed / budget_seconds, 4)
        return util

    def recommendations(self) -> tuple[str, ...]:
        """Heuristic next-step hints — evidence for profiling wave only."""

        hints: list[str] = []
        util = self.budget_utilization()
        bottleneck = self.bottleneck_contour()
        if bottleneck:
            hints.append(f"bottleneck_contour={bottleneck}")
        for contour, ratio in sorted(util.items(), key=lambda item: item[1], reverse=True):
            if ratio >= 0.75:
                if contour == Contour.INGESTION.value:
                    hints.append("consider OCR cache or drawing fan-out review")
                elif contour == Contour.DETERMINISTIC_VALIDATION.value:
                    hints.append("consider IFC parse cache or spatial index before fan-out")
                elif contour == Contour.AI_ADVISORY.value:
                    hints.append("advisory contour hot — verify max_steps and tool timeouts")
                elif contour == Contour.EVIDENCE_REPORTING.value:
                    hints.append("consider streaming report assembly for large issue sets")
        if not hints:
            hints.append("no contour exceeded 75% of stage budget on this run")
        return tuple(hints)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "elapsed_seconds": dict(sorted(self._elapsed_seconds.items())),
            "total_elapsed_seconds": round(self.total_elapsed_seconds(), 6),
            "stage_budget_minutes": self.stage_budget.as_dict(),
            "budget_utilization": self.budget_utilization(),
            "bottleneck_contour": self.bottleneck_contour(),
            "recommendations": list(self.recommendations()),
            "claim_boundary": "fixture profiling only; not customer SLA proof",
        }


class _ContourSpan:
    def __init__(self, collector: PackageTraceCollector, contour: Contour) -> None:
        self._collector = collector
        self._contour = contour
        self._started_at: float | None = None

    def __enter__(self) -> _ContourSpan:
        self._started_at = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        if self._started_at is None:
            return
        self._collector.record(self._contour, perf_counter() - self._started_at)


__all__ = ["PackageTraceCollector"]
