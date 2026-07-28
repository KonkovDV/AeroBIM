"""Hybrid AI routing contour (domain-pure).

Data classification + fail-closed trust-policy engine. No I/O, no verdict impact
(ADR-001). See audit/reports/HYBRID_AI_ARCHITECTURE_2026_07_28.md.
"""

from aerobim.domain.hybrid.audit_event import (
    AuditSecretLeakError,
    HybridAuditEvent,
    build_route_audit_event,
    redact_audit_fields,
)
from aerobim.domain.hybrid.data_classification import (
    DataClassification,
    classify_object,
    most_restrictive,
    rank,
)
from aerobim.domain.hybrid.privacy_guard import (
    MaskResult,
    PrivacyGuard,
    PrivacyLeakError,
    TokenVault,
    truncate_flagged,
)
from aerobim.domain.hybrid.trust_policy import (
    RouteDecision,
    RouteStatus,
    RouteTarget,
    decide_route,
)

__all__ = [
    "AuditSecretLeakError",
    "DataClassification",
    "HybridAuditEvent",
    "MaskResult",
    "PrivacyGuard",
    "PrivacyLeakError",
    "RouteDecision",
    "RouteStatus",
    "RouteTarget",
    "TokenVault",
    "build_route_audit_event",
    "classify_object",
    "decide_route",
    "most_restrictive",
    "rank",
    "redact_audit_fields",
    "truncate_flagged",
]
