"""Hybrid AI routing contour (domain-pure).

Data classification + fail-closed trust-policy engine. No I/O, no verdict impact
(ADR-001). See audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md.
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
from aerobim.domain.hybrid.model_router import (
    ModelProfile,
    ModelRouter,
    ModelSelection,
    ModelTier,
    ProviderRegistry,
)
from aerobim.domain.hybrid.privacy_guard import (
    MaskResult,
    PrivacyGuard,
    PrivacyLeakError,
    TokenVault,
    truncate_flagged,
)
from aerobim.domain.hybrid.sensitive_entities import (
    DetectedEntity,
    EntityKind,
    detect_entities,
    scan_payload,
    suggest_mask_rules,
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
    "DetectedEntity",
    "EntityKind",
    "HybridAuditEvent",
    "MaskResult",
    "ModelProfile",
    "ModelRouter",
    "ModelSelection",
    "ModelTier",
    "PrivacyGuard",
    "PrivacyLeakError",
    "ProviderRegistry",
    "RouteDecision",
    "RouteStatus",
    "RouteTarget",
    "TokenVault",
    "build_route_audit_event",
    "classify_object",
    "decide_route",
    "detect_entities",
    "most_restrictive",
    "rank",
    "redact_audit_fields",
    "scan_payload",
    "suggest_mask_rules",
    "truncate_flagged",
]
