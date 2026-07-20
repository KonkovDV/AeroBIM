"""Package-level Shared-gate outcome (ADR-001 companion to ``summary.passed``)."""

from __future__ import annotations

from enum import StrEnum


class PackageOutcome(StrEnum):
    """Expert-facing package reading derived from deterministic Shared-gate inputs."""

    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"
    FAILED = "failed"


def summary_passed_from_outcome(outcome: PackageOutcome) -> bool:
    """Derive Shared-gate ``passed`` solely from ``PackageOutcome``."""

    return outcome in {PackageOutcome.PASS, PackageOutcome.PASS_WITH_WARNINGS}
