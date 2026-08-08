"""Norm-rule check eligibility + expert-required listing (WP-04).

LLM / narrative structuring may draft rule text. A rule enters deterministic
checking only when:

1. Pack status is customer_approved/approved with a full approval object
   (loader fail-closed; ``advisory_only`` is False).
2. ``execution_mode`` is ``deterministic``.
3. An explicit expert confirmation journal entry with ``decision=confirmed``
   exists for that rule.

``execution_mode=expert_required`` rules never auto-check; list them via
``list_expert_required_rules`` / the CLI tool for human follow-up.

Schema 1.0.0 legacy packs without ``execution_mode`` keep prior behaviour
(approved pack rules remain checkable) so fixtures do not silently break.
Schema 2.0.0 packs always require journal confirmation for deterministic rules.

Does not close RT-002: fixture/draft packs remain advisory; customer-approved
packs still need a real customer signature outside engineering fixtures.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

from aerobim.domain.models import NormRulePack, ParsedRequirement

ExpertDecision = Literal["confirmed", "rejected", "deferred"]
ExecutionMode = Literal["deterministic", "expert_required"]


@dataclass(frozen=True)
class ExpertConfirmationEntry:
    confirmed_by: str
    confirmed_at: str
    decision: ExpertDecision
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at,
            "decision": self.decision,
        }
        if self.note is not None:
            payload["note"] = self.note
        return payload


@dataclass(frozen=True)
class RaseRoles:
    """RASE roles: requirement / applicability / selection / exclusion."""

    requirement: str
    applicability: str
    selection: str
    exclusion: str

    def to_dict(self) -> dict[str, str]:
        return {
            "requirement": self.requirement,
            "applicability": self.applicability,
            "selection": self.selection,
            "exclusion": self.exclusion,
        }


def has_expert_confirmation(requirement: ParsedRequirement) -> bool:
    """True when journal contains at least one confirmed decision."""

    for entry in requirement.expert_confirmation_journal:
        if entry.decision == "confirmed":
            return True
    return False


def is_rule_checkable(
    requirement: ParsedRequirement,
    *,
    pack: NormRulePack | None = None,
    schema_version: str | None = None,
) -> bool:
    """Return whether the rule may enter the deterministic checker.

    ``expert_required`` never auto-checks. Schema 2.0.0 ``deterministic`` rules
    require an expert confirmation journal entry. Schema 1.x legacy rules without
    ``execution_mode`` keep prior advisory/demo evaluation behaviour; positive
    sign-off still requires ``customer_approved`` + approval object (pack
    ``advisory_only`` / capability policy), which does not close RT-002.
    """

    if pack is not None:
        version = pack.schema_version
    else:
        version = schema_version or "1.0.0"

    mode = requirement.execution_mode
    if mode == "expert_required":
        return False

    # Schema 2.0.0: deterministic rules require explicit expert confirmation
    # before they enter checking (LLM drafts are not enough).
    if version.startswith("2."):
        if mode != "deterministic":
            return False
        return has_expert_confirmation(requirement)

    # Schema 1.x legacy: optional execution_mode; if present, honour it.
    if mode == "deterministic":
        if requirement.expert_confirmation_journal:
            return has_expert_confirmation(requirement)
        return True
    if mode is None:
        return True
    return False


def can_contribute_positive_norm_outcome(
    pack: NormRulePack,
    requirement: ParsedRequirement | None = None,
) -> bool:
    """Positive norm outcome requires customer_approved pack + approval ref.

    Fixture/engineering packs never satisfy this; RT-002 stays OPEN until a real
    customer-approved pack exists. Optional ``requirement`` must also be checkable.
    """

    from aerobim.domain.models import RulePackStatus

    if pack.advisory_only or pack.status is not RulePackStatus.APPROVED:
        return False
    if not (pack.approval_reference or pack.customer_approval_ref):
        return False
    if requirement is not None and not is_rule_checkable(requirement, pack=pack):
        return False
    return True


def list_expert_required_rules(
    pack: NormRulePack,
) -> tuple[ParsedRequirement, ...]:
    """Rules that cannot be auto-checked (execution_mode=expert_required)."""

    return tuple(rule for rule in pack.rules if rule.execution_mode == "expert_required")


def list_awaiting_expert_confirmation(
    pack: NormRulePack,
) -> tuple[ParsedRequirement, ...]:
    """Deterministic v2 rules lacking a confirmed journal entry."""

    if not pack.schema_version.startswith("2."):
        return ()
    awaiting: list[ParsedRequirement] = []
    for rule in pack.rules:
        if rule.execution_mode != "deterministic":
            continue
        if not has_expert_confirmation(rule):
            awaiting.append(rule)
    return tuple(awaiting)


def partition_checkable_rules(
    pack: NormRulePack,
) -> tuple[tuple[ParsedRequirement, ...], tuple[ParsedRequirement, ...]]:
    """Split pack rules into (checkable, non_checkable)."""

    checkable: list[ParsedRequirement] = []
    deferred: list[ParsedRequirement] = []
    for rule in pack.rules:
        if is_rule_checkable(rule, pack=pack):
            checkable.append(rule)
        else:
            deferred.append(rule)
    return tuple(checkable), tuple(deferred)


def expert_required_report(pack: NormRulePack) -> dict[str, Any]:
    """JSON-serialisable listing for report/tool surfaces."""

    expert_rules = list_expert_required_rules(pack)
    awaiting = list_awaiting_expert_confirmation(pack)
    return {
        "artifact": "expert-required-norm-rules",
        "claim_boundary": (
            "Listing only; does not grant customer_approved status or close RT-002. "
            "LLM-drafted text is not checkable without expert confirmation journal."
        ),
        "pack_id": pack.pack_id,
        "pack_version": pack.version,
        "pack_status": pack.status.value,
        "schema_version": pack.schema_version,
        "advisory_only": pack.advisory_only,
        "expert_required_count": len(expert_rules),
        "awaiting_confirmation_count": len(awaiting),
        "expert_required": [
            {
                "rule_id": rule.rule_id,
                "source": rule.norm_source,
                "clause_number": rule.norm_clause,
                "requirement_text": rule.requirement_text or rule.evidence_text,
                "discipline": rule.discipline,
                "stage": rule.stage,
                "criticality": rule.criticality,
                "evidence_required": rule.evidence_required,
                "execution_mode": rule.execution_mode,
            }
            for rule in expert_rules
        ],
        "awaiting_expert_confirmation": [
            {
                "rule_id": rule.rule_id,
                "execution_mode": rule.execution_mode,
                "journal_entries": len(rule.expert_confirmation_journal),
            }
            for rule in awaiting
        ],
    }


def parse_expert_confirmation_journal(
    raw: object,
    *,
    field: str,
) -> tuple[ExpertConfirmationEntry, ...]:
    """Parse and validate journal entries; empty tuple when absent."""

    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"{field} must be an array when provided")
    entries: list[ExpertConfirmationEntry] = []
    for index, item in enumerate(raw):
        prefix = f"{field}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{prefix} must be a JSON object")
        confirmed_by = item.get("confirmed_by")
        confirmed_at = item.get("confirmed_at")
        decision = item.get("decision")
        if not isinstance(confirmed_by, str) or not confirmed_by.strip():
            raise ValueError(f"{prefix}.confirmed_by must be a non-empty string")
        if not isinstance(confirmed_at, str) or not confirmed_at.strip():
            raise ValueError(f"{prefix}.confirmed_at must be a non-empty string")
        if decision not in {"confirmed", "rejected", "deferred"}:
            raise ValueError(f"{prefix}.decision must be one of confirmed|rejected|deferred")
        note = item.get("note")
        if note is not None and (not isinstance(note, str) or not note.strip()):
            raise ValueError(f"{prefix}.note must be a non-empty string when provided")
        entries.append(
            ExpertConfirmationEntry(
                confirmed_by=confirmed_by.strip(),
                confirmed_at=confirmed_at.strip(),
                decision=cast(ExpertDecision, decision),
                note=note.strip() if isinstance(note, str) else None,
            )
        )
    return tuple(entries)


def parse_rase_roles(raw: object, *, field: str, required: bool) -> RaseRoles | None:
    if raw is None:
        if required:
            raise ValueError(f"{field} is required")
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"{field} must be a JSON object")
    requirement = raw.get("requirement")
    applicability = raw.get("applicability")
    selection = raw.get("selection")
    exclusion = raw.get("exclusion")
    if exclusion is None:
        exclusion = raw.get("exception")  # legacy alias
    for key, value in (
        ("requirement", requirement),
        ("applicability", applicability),
        ("selection", selection),
        ("exclusion", exclusion),
    ):
        if not isinstance(value, str) or not value.strip():
            if required:
                raise ValueError(f"{field}.{key} must be a non-empty string")
            return None
    assert isinstance(requirement, str)
    assert isinstance(applicability, str)
    assert isinstance(selection, str)
    assert isinstance(exclusion, str)
    return RaseRoles(
        requirement=requirement.strip(),
        applicability=applicability.strip(),
        selection=selection.strip(),
        exclusion=exclusion.strip(),
    )


def filter_checkable_requirements(
    requirements: Sequence[ParsedRequirement],
    *,
    pack: NormRulePack,
) -> list[ParsedRequirement]:
    return [rule for rule in requirements if is_rule_checkable(rule, pack=pack)]


__all__ = [
    "ExpertConfirmationEntry",
    "ExpertDecision",
    "ExecutionMode",
    "RaseRoles",
    "can_contribute_positive_norm_outcome",
    "expert_required_report",
    "filter_checkable_requirements",
    "has_expert_confirmation",
    "is_rule_checkable",
    "list_awaiting_expert_confirmation",
    "list_expert_required_rules",
    "parse_expert_confirmation_journal",
    "parse_rase_roles",
    "partition_checkable_rules",
]
