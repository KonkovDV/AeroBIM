"""Trust Policy / route-decision engine for the Hybrid AI contour (domain-pure).

Implements the class × target matrix (see HYBRID_AI_FINAL_REPORT_2026_07_28.md)
**fail-closed**: any unresolved or forbidden combination returns ``BLOCKED`` with no
external call. The engine decides eligibility ONLY; it never performs I/O, never
touches ``summary.passed`` (ADR-001), and takes ``classification``/``tenant_id``/
``target`` from the TRUSTED caller — never from a model response or raw user input
(a model may not set tenant, downgrade class, or pick a route).

Masking itself (Privacy Guard) is P1: a ``PUBLIC_MASKED`` decision means "external
egress is policy-eligible but requires the Privacy Guard before any bytes leave" —
it is not a claim that data is anonymous.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from aerobim.domain.hybrid.data_classification import DataClassification


class RouteTarget(Enum):
    """Requested processing tier (trusted caller intent)."""

    LOCAL = "local"
    PRIVATE = "private"
    PUBLIC = "public"


class RouteStatus(Enum):
    """Resolved routing decision."""

    LOCAL = "local"
    PRIVATE = "private"
    PUBLIC_MASKED = "public_masked"
    BLOCKED = "blocked"
    HUMAN_REVIEW = "human_review"


@dataclass(frozen=True)
class RouteDecision:
    """Deterministic, auditable routing decision (no I/O, no verdict impact)."""

    status: RouteStatus
    classification: DataClassification
    target: RouteTarget
    reason: str
    required_permission: str | None = None

    @property
    def allowed(self) -> bool:
        """A model call may proceed only for LOCAL/PRIVATE/PUBLIC_MASKED."""
        return self.status in (RouteStatus.LOCAL, RouteStatus.PRIVATE, RouteStatus.PUBLIC_MASKED)

    @property
    def external_call(self) -> bool:
        """True only when bytes leave the local trusted box (private or public)."""
        return self.status in (RouteStatus.PRIVATE, RouteStatus.PUBLIC_MASKED)


def _blocked(
    classification: DataClassification,
    target: RouteTarget,
    reason: str,
    *,
    required_permission: str | None = None,
) -> RouteDecision:
    return RouteDecision(
        status=RouteStatus.BLOCKED,
        classification=classification,
        target=target,
        reason=reason,
        required_permission=required_permission,
    )


def decide_route(
    *,
    classification: DataClassification,
    target: RouteTarget,
    tenant_id: str,
    project_id: str | None = None,
    owner_consent: bool = False,
    private_mode_confirmed: bool = False,
) -> RouteDecision:
    """Return a fail-closed routing decision for one (class, target, tenant).

    ``classification`` and ``tenant_id`` MUST come from the trusted local contour
    (authenticated identity + object classifier), never from a model or raw input.
    Unknown tenant, or any combination not explicitly allowed below, is ``BLOCKED``.
    """

    if not tenant_id or not tenant_id.strip():
        # Cannot scope isolation without a verified tenant → fail closed.
        return _blocked(classification, target, "unknown tenant: routing blocked")

    # SECRET never reaches any model route (local special-module handling is out of
    # scope for the model router and must be explicitly built, not defaulted).
    if classification is DataClassification.SECRET:
        return _blocked(classification, target, "SECRET data must not reach any model route")

    if target is RouteTarget.LOCAL:
        # Local processing is allowed for every non-SECRET class.
        return RouteDecision(RouteStatus.LOCAL, classification, target, "local processing allowed")

    if target is RouteTarget.PRIVATE:
        if classification in (DataClassification.PUBLIC, DataClassification.INTERNAL):
            return RouteDecision(
                RouteStatus.PRIVATE, classification, target, "private contour allowed"
            )
        # CONFIDENTIAL / RESTRICTED require an explicitly confirmed closed contour.
        if private_mode_confirmed:
            return RouteDecision(
                RouteStatus.PRIVATE, classification, target, "private contour (confirmed mode)"
            )
        return _blocked(
            classification,
            target,
            f"{classification.value} needs a confirmed private contour",
            required_permission="private_mode_confirmed",
        )

    if target is RouteTarget.PUBLIC:
        if classification is DataClassification.PUBLIC:
            return RouteDecision(
                RouteStatus.PUBLIC_MASKED,
                classification,
                target,
                "public egress allowed (mask required)",
            )
        if classification is DataClassification.INTERNAL:
            if owner_consent:
                return RouteDecision(
                    RouteStatus.PUBLIC_MASKED,
                    classification,
                    target,
                    "internal public egress with owner consent (mask required)",
                )
            # Needs a data-owner decision — route to a human, do not auto-block or send.
            return RouteDecision(
                RouteStatus.HUMAN_REVIEW,
                classification,
                target,
                "internal public egress requires data-owner consent",
                required_permission="owner_consent",
            )
        # CONFIDENTIAL / RESTRICTED must never take the public route.
        return _blocked(
            classification, target, f"public route forbidden for {classification.value}"
        )

    # Unreachable given the enum, but stay fail-closed for any future target.
    return _blocked(classification, target, "unresolved route: fail-closed")


__all__ = [
    "RouteDecision",
    "RouteStatus",
    "RouteTarget",
    "decide_route",
]
