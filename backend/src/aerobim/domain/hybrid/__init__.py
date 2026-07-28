"""Hybrid AI routing contour (domain-pure).

Data classification + fail-closed trust-policy engine. No I/O, no verdict impact
(ADR-001). See audit/reports/HYBRID_AI_ARCHITECTURE_2026_07_28.md.
"""

from aerobim.domain.hybrid.data_classification import (
    DataClassification,
    classify_object,
    most_restrictive,
    rank,
)
from aerobim.domain.hybrid.trust_policy import (
    RouteDecision,
    RouteStatus,
    RouteTarget,
    decide_route,
)

__all__ = [
    "DataClassification",
    "RouteDecision",
    "RouteStatus",
    "RouteTarget",
    "classify_object",
    "decide_route",
    "most_restrictive",
    "rank",
]
