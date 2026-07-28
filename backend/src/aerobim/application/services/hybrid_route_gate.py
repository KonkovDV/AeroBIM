"""HybridRouteGate: fail-closed pre-gate composing the Hybrid AI P0/P1 layers.

Single entry point that turns a (data object, requested tier, tenant) into an
auditable ROUTING decision — classify → policy → (mask on egress) → audit event.

Invariants (brief §16):
- **Verdict-neutral**: the gate returns a routing decision + optional masked payload
  + a ``HybridAuditEvent`` (``verdict_impact="none"``). It has no ``summary.passed``
  and cannot change the deterministic verdict (ADR-001). It is deliberately NOT wired
  into ``AnalyzeProjectPackageUseCase`` — like ``ADVISORY_VLM_PIPELINE`` it is an
  available advisory-contour component, so OFF==ON holds by construction.
- **Fail-closed egress**: external egress requires masking. If a payload must leave
  but no PrivacyGuard / mask rules are available, ``masked`` is ``None`` and
  ``may_call_external`` is ``False`` — never send unmasked bytes.
- Unknown tenant / forbidden class → the policy returns BLOCKED; the gate performs no
  masking and no external call.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aerobim.domain.hybrid.audit_event import HybridAuditEvent, build_route_audit_event
from aerobim.domain.hybrid.data_classification import classify_object
from aerobim.domain.hybrid.privacy_guard import PrivacyGuard
from aerobim.domain.hybrid.trust_policy import RouteDecision, RouteTarget, decide_route


@dataclass(frozen=True)
class HybridGateResult:
    """Outcome of one gate evaluation. Carries NO verdict (routing only)."""

    decision: RouteDecision
    audit_event: HybridAuditEvent
    masked: dict[str, Any] | None = None

    @property
    def may_call_external(self) -> bool:
        """True only when the route egresses AND a safe (masked) payload is ready."""
        return self.decision.external_call and self.masked is not None


class HybridRouteGate:
    """Compose classification + fail-closed policy + optional masking + audit."""

    def __init__(
        self,
        *,
        privacy_guard: PrivacyGuard | None = None,
        policy_version: str = "1.0.0",
    ) -> None:
        self._guard = privacy_guard
        self._policy_version = policy_version

    def evaluate(
        self,
        *,
        object_kind: str,
        target: RouteTarget,
        tenant_id: str,
        task_type: str,
        request_id: str,
        project_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
        mask_rules: Mapping[str, str] | None = None,
        owner_consent: bool = False,
        private_mode_confirmed: bool = False,
        event_id: str | None = None,
        timestamp: str | None = None,
    ) -> HybridGateResult:
        """Classify + decide route + (mask on egress) + audit; returns routing only.

        ``payload=None`` = question-only egress (no document leaves) and is allowed on
        an egress route. A non-None payload requires a PrivacyGuard + ``mask_rules`` to
        egress; otherwise (or if masking refuses/raises) ``masked`` is ``None`` and
        ``may_call_external`` is ``False`` (fail-closed), with the reason audited.
        """
        classification = classify_object(object_kind)
        decision = decide_route(
            classification=classification,
            target=target,
            tenant_id=tenant_id,
            project_id=project_id,
            owner_consent=owner_consent,
            private_mode_confirmed=private_mode_confirmed,
        )

        masked: dict[str, Any] | None = None
        fields_sent: tuple[str, ...] = ()
        fields_removed: tuple[str, ...] = ()
        mask_version: str | None = None
        egress_failure: str | None = None
        if decision.external_call:
            # External egress requires masking. Fail closed if we cannot mask, and
            # record WHY so the audit distinguishes a refusal from a real egress (§13).
            if payload is None:
                masked = {}  # question-only egress: nothing to send
            elif self._guard is None or mask_rules is None:
                egress_failure = "external egress fail-closed: no privacy guard / mask rules"
            else:
                try:
                    result = self._guard.mask_payload(
                        payload, tenant_id=tenant_id, rules=mask_rules
                    )
                except ValueError as exc:
                    # PrivacyLeakError / non-scalar keep / bad tenant -> refuse egress,
                    # keep an audit trail, do not crash the caller (fail-closed).
                    egress_failure = f"masking refused egress: {type(exc).__name__}"
                else:
                    masked = result.masked
                    fields_sent = result.fields_sent
                    fields_removed = result.fields_removed
                    mask_version = result.mask_version

        event = build_route_audit_event(
            event_id=event_id or uuid.uuid4().hex,
            timestamp=timestamp or datetime.now(tz=UTC).isoformat(),
            request_id=request_id,
            tenant_id=tenant_id,
            task_type=task_type,
            decision=decision,
            policy_version=self._policy_version,
            failure_reason=egress_failure,
            project_id=project_id,
            fields_sent=fields_sent,
            fields_removed=fields_removed,
            mask_version=mask_version,
        )
        return HybridGateResult(decision=decision, audit_event=event, masked=masked)


__all__ = [
    "HybridGateResult",
    "HybridRouteGate",
]
