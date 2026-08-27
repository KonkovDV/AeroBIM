"""Signed out-of-scope records — fail-closed speech licenses, not RT CLOSED.

Plan stages 1 and 2: QTO / federated MEP / Solihin class-4 rebar may be
measured only after the carrier exists, or after the appointing party signs
an OOS. An unsigned template does not license skip. A signed OOS does not
close RT-001/002/003 and never writes summary.passed.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final, Literal

OosKind = Literal["qto_space_area", "mep_federated", "rebar_class4"]

SCHEMA: Final = "aerobim_signed_oos_v1"
CHECKPOINT: Final = "NO_GO"
CLAIM_LEVEL: Final = "oos_template_only"
CLAIM_BOUNDARY: Final = (
    "Signed OOS is a speech license that a channel is unmeasured. "
    "Not product accuracy. Not customer SLA. Not MEP delivered. "
    "Not class-4 rebar delivered. Checkpoint NO_GO. "
    "closes_rt001/002/003=false."
)

OOS_KINDS: Final[tuple[OosKind, ...]] = (
    "qto_space_area",
    "mep_federated",
    "rebar_class4",
)

ALLOWED_STATEMENTS: Final[dict[OosKind, str]] = {
    "qto_space_area": (
        "Area checks are out of measurement until QTO NetFloorArea is "
        "exported. Missing QTO is not a TEP Does-not."
    ),
    "mep_federated": (
        "Federated MEP system-clash is out of measurement. "
        "mep_system_clash stays NOT_VERIFIED. Does not close RT-003."
    ),
    "rebar_class4": (
        "Reinforcement vs calculation maps (Solihin class 4) are out of "
        "measurement. Pitch pset is not bar entities. Does not parse LIRA."
    ),
}

_REQUIRED_KEYS: Final[tuple[str, ...]] = (
    "schema",
    "kind",
    "signer",
    "signed_at",
    "scope_memo",
    "statement",
)


@dataclass(frozen=True)
class OosDecision:
    """Fail-closed evaluation of one OOS payload."""

    kind: str
    status: str
    """unsigned | rejected | accepted_unmeasured"""
    accepted: bool
    licenses_unmeasured_speech: bool
    reason: str
    closes_rt001: bool = False
    closes_rt002: bool = False
    closes_rt003: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "status": self.status,
            "accepted": self.accepted,
            "licenses_unmeasured_speech": self.licenses_unmeasured_speech,
            "reason": self.reason,
            "closes_rt001": False,
            "closes_rt002": False,
            "closes_rt003": False,
            "checkpoint": CHECKPOINT,
            "claim_level": CLAIM_LEVEL,
            "claim_boundary": CLAIM_BOUNDARY,
        }


def unsigned_template(kind: OosKind) -> dict[str, Any]:
    """Appointing-party template. Empty signer keeps the record unsigned."""

    if kind not in ALLOWED_STATEMENTS:
        raise ValueError(f"unknown OOS kind: {kind}")
    return {
        "schema": SCHEMA,
        "kind": kind,
        "signer": "",
        "signed_at": "",
        "scope_memo": "",
        "statement": ALLOWED_STATEMENTS[kind],
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def evaluate_oos(payload: Mapping[str, Any] | None) -> OosDecision:
    """Accept only a fully signed payload with the locked statement."""

    if not payload:
        return OosDecision(
            kind="unknown",
            status="unsigned",
            accepted=False,
            licenses_unmeasured_speech=False,
            reason="missing OOS payload",
        )
    kind_raw = str(payload.get("kind") or "").strip()
    if kind_raw not in ALLOWED_STATEMENTS:
        return OosDecision(
            kind=kind_raw or "unknown",
            status="rejected",
            accepted=False,
            licenses_unmeasured_speech=False,
            reason="unknown or empty OOS kind",
        )
    if str(payload.get("schema") or "").strip() != SCHEMA:
        return OosDecision(
            kind=kind_raw,
            status="rejected",
            accepted=False,
            licenses_unmeasured_speech=False,
            reason=f"schema must be {SCHEMA}",
        )
    missing = [key for key in _REQUIRED_KEYS if key not in payload]
    if missing:
        return OosDecision(
            kind=kind_raw,
            status="rejected",
            accepted=False,
            licenses_unmeasured_speech=False,
            reason=f"missing keys: {', '.join(missing)}",
        )
    signer = str(payload.get("signer") or "").strip()
    signed_at = str(payload.get("signed_at") or "").strip()
    scope_memo = str(payload.get("scope_memo") or "").strip()
    statement = str(payload.get("statement") or "").strip()
    allowed_statement = ALLOWED_STATEMENTS[kind_raw]
    if statement != allowed_statement:
        return OosDecision(
            kind=kind_raw,
            status="rejected",
            accepted=False,
            licenses_unmeasured_speech=False,
            reason="statement must match the locked OOS text for this kind",
        )
    if any(
        bool(payload.get(flag))
        for flag in ("closes_rt001", "closes_rt002", "closes_rt003")
    ):
        return OosDecision(
            kind=kind_raw,
            status="rejected",
            accepted=False,
            licenses_unmeasured_speech=False,
            reason="OOS must not claim RT-001/002/003 closed",
        )
    if not signer or not signed_at or not scope_memo:
        return OosDecision(
            kind=kind_raw,
            status="unsigned",
            accepted=False,
            licenses_unmeasured_speech=False,
            reason="signer, signed_at, and scope_memo are required",
        )
    return OosDecision(
        kind=kind_raw,
        status="accepted_unmeasured",
        accepted=True,
        licenses_unmeasured_speech=True,
        reason="signed OOS licenses unmeasured speech only",
    )


def oos_snapshot() -> dict[str, Any]:
    """Coverage pin: templates exist; none are accepted in git."""

    templates = {kind: unsigned_template(kind) for kind in OOS_KINDS}
    decisions = {kind: evaluate_oos(templates[kind]).as_dict() for kind in OOS_KINDS}
    return {
        "artifact_type": "signed_oos_templates",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "kinds": list(OOS_KINDS),
        "any_accepted": False,
        "templates_unsigned": True,
        "decisions": decisions,
    }


__all__ = [
    "ALLOWED_STATEMENTS",
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "OOS_KINDS",
    "OosDecision",
    "SCHEMA",
    "evaluate_oos",
    "oos_snapshot",
    "unsigned_template",
]
