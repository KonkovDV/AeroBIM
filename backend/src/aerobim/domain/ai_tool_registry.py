"""Typed advisory tool registry — AI cannot change verdict (ADR-001)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

AdvisoryToolName = Literal[
    "ids_assist_draft",
    "norm_corpus_retrieve",
    "requirement_interpret",
    "ifc_kg_query",
    "compliance_agent_review",
]


@dataclass(frozen=True)
class AdvisoryToolContract:
    """Registry row for AI advisory tools — never on deterministic sign-off path."""

    name: AdvisoryToolName
    allowlist: frozenset[str]
    json_schema_id: str
    timeout_seconds: float
    max_steps: int
    evidence_required: bool
    can_change_verdict: bool = False
    contour: str = "ai_advisory"

    def validate_invocation(self, *, tool_name: str, tenant_id: str | None) -> None:
        if tool_name != self.name:
            raise ValueError(f"tool {tool_name!r} does not match contract {self.name!r}")
        if self.can_change_verdict:
            raise ValueError("advisory tools must not change verdict")
        if tenant_id is not None and tenant_id not in self.allowlist and self.allowlist:
            raise ValueError(f"tenant {tenant_id!r} not in advisory tool allowlist")


DEFAULT_ADVISORY_TOOL_REGISTRY: tuple[AdvisoryToolContract, ...] = (
    AdvisoryToolContract(
        name="ids_assist_draft",
        allowlist=frozenset(),
        json_schema_id="aerobim.ids_assist_draft.v1",
        timeout_seconds=30.0,
        max_steps=1,
        evidence_required=True,
    ),
    AdvisoryToolContract(
        name="norm_corpus_retrieve",
        allowlist=frozenset(),
        json_schema_id="aerobim.norm_corpus_retrieve.v1",
        timeout_seconds=15.0,
        max_steps=3,
        evidence_required=True,
    ),
    AdvisoryToolContract(
        name="requirement_interpret",
        allowlist=frozenset(),
        json_schema_id="aerobim.requirement_interpret.v1",
        timeout_seconds=20.0,
        max_steps=2,
        evidence_required=True,
    ),
    AdvisoryToolContract(
        name="ifc_kg_query",
        allowlist=frozenset(),
        json_schema_id="aerobim.ifc_kg_query.v1",
        timeout_seconds=10.0,
        max_steps=5,
        evidence_required=True,
    ),
    AdvisoryToolContract(
        name="compliance_agent_review",
        allowlist=frozenset(),
        json_schema_id="aerobim.compliance_agent_review.v1",
        timeout_seconds=60.0,
        max_steps=8,
        evidence_required=True,
    ),
)


def lookup_advisory_tool(name: str) -> AdvisoryToolContract | None:
    for contract in DEFAULT_ADVISORY_TOOL_REGISTRY:
        if contract.name == name:
            return contract
    return None


def advisory_trace_record(
    *,
    tool_name: str,
    request_id: str,
    steps: int,
    evidence_refs: tuple[str, ...],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Serializable trace row for replay — does not mutate report verdict."""

    contract = lookup_advisory_tool(tool_name)
    if contract is None:
        raise ValueError(f"unknown advisory tool: {tool_name}")
    if steps > contract.max_steps:
        raise ValueError(f"{tool_name} exceeded max_steps={contract.max_steps}")
    if contract.evidence_required and not evidence_refs:
        raise ValueError(f"{tool_name} requires evidence_refs")
    return {
        "tool_name": tool_name,
        "request_id": request_id,
        "steps": steps,
        "evidence_refs": list(evidence_refs),
        "can_change_verdict": False,
        "payload": payload,
    }


__all__ = [
    "AdvisoryToolContract",
    "AdvisoryToolName",
    "DEFAULT_ADVISORY_TOOL_REGISTRY",
    "advisory_trace_record",
    "lookup_advisory_tool",
]
