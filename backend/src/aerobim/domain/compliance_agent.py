"""Compliance agent plan/result types (application-facing, domain-pure data)."""

from __future__ import annotations

from dataclasses import dataclass, field

from aerobim.domain.models import ValidationIssue
from aerobim.domain.norm_assist import IdsCompileDraft, NormPassage


@dataclass(frozen=True)
class AgentToolStep:
    """One planned or executed tool invocation (allowlisted name only)."""

    tool_name: str
    rationale: str
    arguments: dict[str, str] = field(default_factory=dict)
    status: str = "planned"  # planned | ok | skipped | error
    detail: str | None = None


@dataclass(frozen=True)
class AgentRunResult:
    """Advisory agent output — never authoritative for summary.passed."""

    steps: tuple[AgentToolStep, ...] = ()
    advisory_issues: tuple[ValidationIssue, ...] = ()
    norm_passages: tuple[NormPassage, ...] = ()
    ids_draft: IdsCompileDraft | None = None
    capped: bool = False
    """True when max_steps truncated the plan."""
