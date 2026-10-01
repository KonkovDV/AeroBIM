"""Unified honesty capability contract for four gap directions (API surface)."""

from __future__ import annotations

from typing import Any, Literal

EvidenceLevel = Literal["unit", "fixture", "integration", "customer"]
ContractStatus = Literal[
    "available",
    "partial",
    "experimental",
    "missing",
    "not_implemented",
    "fixture_only",
    "blocked_customer_data",
    "not_verified",
    "failed",
    "skipped",
]


def capability_contract(
    *,
    capability: str,
    status: ContractStatus,
    evidence_level: EvidenceLevel,
    affects_pass: bool,
    reason: str,
    claim_boundary: str,
    dependencies: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Build one honesty capability entry (never invent customer evidence)."""

    return {
        "capability": capability,
        "status": status,
        "evidence_level": evidence_level,
        "affects_pass": affects_pass,
        "reason": reason,
        "dependencies": list(dependencies or []),
        "claim_boundary": claim_boundary,
        "evidence_refs": list(evidence_refs or []),
    }


__all__ = ["ContractStatus", "EvidenceLevel", "capability_contract"]
