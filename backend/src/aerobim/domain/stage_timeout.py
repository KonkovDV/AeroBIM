"""Per-contour stage wall-time enforcement for package analyze."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Literal

from aerobim.domain.architecture import DEFAULT_PACKAGE_STAGE_BUDGET, Contour, StageBudget


class StageTimeoutExceeded(RuntimeError):
    """Raised when a contour exceeds its configured wall-time budget."""

    def __init__(self, *, contour: Contour, budget_seconds: float, elapsed_seconds: float) -> None:
        self.contour = contour
        self.budget_seconds = budget_seconds
        self.elapsed_seconds = elapsed_seconds
        super().__init__(
            f"Stage timeout for {contour.value}: elapsed {elapsed_seconds:.3f}s "
            f"> budget {budget_seconds:.3f}s"
        )


def contour_budget_seconds(contour: Contour, budget: StageBudget | None = None) -> float:
    active = budget or DEFAULT_PACKAGE_STAGE_BUDGET
    minutes = {
        Contour.INGESTION: active.ingestion_minutes,
        Contour.DETERMINISTIC_VALIDATION: active.deterministic_validation_minutes,
        Contour.AI_ADVISORY: active.ai_advisory_minutes,
        Contour.EVIDENCE_REPORTING: active.evidence_reporting_minutes,
    }[contour]
    return minutes * 60.0


def enforce_stage_timeout(
    *,
    contour: Contour,
    elapsed_seconds: float,
    budget: StageBudget | None = None,
) -> None:
    limit = contour_budget_seconds(contour, budget)
    if elapsed_seconds > limit:
        raise StageTimeoutExceeded(
            contour=contour,
            budget_seconds=limit,
            elapsed_seconds=elapsed_seconds,
        )


@dataclass
class StageTimeoutGuard:
    """Context manager that fails closed when a contour exceeds its budget."""

    contour: Contour
    budget: StageBudget | None = None
    _started_at: float | None = None

    def __enter__(self) -> StageTimeoutGuard:
        self._started_at = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> Literal[False]:  # noqa: ANN001
        if self._started_at is None:
            return False
        elapsed = perf_counter() - self._started_at
        enforce_stage_timeout(
            contour=self.contour,
            elapsed_seconds=elapsed,
            budget=self.budget,
        )
        return False


__all__ = [
    "StageTimeoutExceeded",
    "StageTimeoutGuard",
    "contour_budget_seconds",
    "enforce_stage_timeout",
]
