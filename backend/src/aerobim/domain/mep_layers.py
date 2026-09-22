"""
P1-N: MEP Layer Architecture.

Geometric clash detection ≠ MEP system-aware verification.
Five formal layers; each has its own CapabilityStatus.

Do not claim higher layers are validated without corpus evidence.

Layer 1: Geometric clash             → PARTIAL (live engine is elsewhere; MEP-CLASH-001 open)
Layer 2: Clearance                   → PARTIAL (rule-driven, fixture only)
Layer 3: System semantics            → NOT_VERIFIED (needs real federated IFC)
Layer 4: Connectivity / topology     → NOT_VERIFIED
Layer 5: Rule-based system compliance → NOT_VERIFIED

Reduces: auditability risk, false claim risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CapabilityStatus(StrEnum):
    """
    Engineering vs Customer validation status.
    NOT_VERIFIED ≠ failing. It means: insufficient evidence to claim.
    unknown != pass.
    """

    ENGINEERING_DONE = "ENGINEERING_DONE"  # Implemented, tested on fixtures
    PARTIAL = "PARTIAL"  # Partially implemented
    NOT_VERIFIED = "NOT_VERIFIED"  # No validated evidence yet
    CUSTOMER_VERIFIED = "CUSTOMER_VERIFIED"  # External customer sign-off
    DEPRECATED = "DEPRECATED"  # Removed or superseded


@dataclass
class MEPLayer:
    """
    Single MEP verification layer with explicit capability status.
    Customer status is ALWAYS separate from engineering status.
    """

    layer_number: int  # 1-5
    name: str
    description: str
    engineering_status: CapabilityStatus
    customer_status: CapabilityStatus
    required_inputs: list[str]  # What IFC entities / data are needed
    known_limitations: list[str]  # Explicit limitations (not hidden)
    evidence_artifacts: list[str] = field(default_factory=list)  # Test reports etc.
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_number": self.layer_number,
            "name": self.name,
            "description": self.description,
            "engineering_status": self.engineering_status.value,
            "customer_status": self.customer_status.value,
            "required_inputs": self.required_inputs,
            "known_limitations": self.known_limitations,
            "evidence_artifacts": self.evidence_artifacts,
            "notes": self.notes,
        }


# --- Canonical MEP layer definitions for AeroBIM ---
# Update customer_status only when real customer evidence exists.

MEP_LAYERS: list[MEPLayer] = [
    MEPLayer(
        layer_number=1,
        name="Geometric Clash",
        description=(
            "Hard clash between physical elements, without system semantics. "
            "This row does not run the clash engine."
        ),
        engineering_status=CapabilityStatus.PARTIAL,
        customer_status=CapabilityStatus.NOT_VERIFIED,
        required_inputs=[
            "IFC models (IfcElement subclasses with geometry)",
            "Federated model or single-discipline IFC",
        ],
        known_limitations=[
            "The live clash path is a separate engine; Analyze does not read this table",
            "Fixture clash is partial; MEP-CLASH-001 stays open",
            "Customer environment not validated",
        ],
    ),
    MEPLayer(
        layer_number=2,
        name="Clearance Zones",
        description=(
            "Rule-driven minimum clearance checks around MEP elements "
            "(maintenance access, fire protection, thermal). "
            "Parameterised per discipline and rule set."
        ),
        engineering_status=CapabilityStatus.PARTIAL,
        customer_status=CapabilityStatus.NOT_VERIFIED,
        required_inputs=[
            "IFC with IfcDistributionElement subclasses",
            "Norm pack with clearance rules",
        ],
        known_limitations=[
            "Only SP/MGSN rules implemented; not all discipline combinations",
            "Validation only on synthetic fixtures; no customer corpus",
        ],
    ),
    MEPLayer(
        layer_number=3,
        name="System Semantics",
        description=(
            "System-aware checks: verifying elements belong to the correct "
            "named MEP system (IfcSystem), using system IDs, semantic "
            "classification (bSDD or IfcClassification), and system properties."
        ),
        engineering_status=CapabilityStatus.NOT_VERIFIED,
        customer_status=CapabilityStatus.NOT_VERIFIED,
        required_inputs=[
            "IFC with populated IfcSystem assignments",
            "IfcRelAssignsToGroup relationships",
            "Consistent system naming convention",
            "bSDD or IfcClassification references (optional but needed for semantics)",
        ],
        known_limitations=[
            "Real Russian project IFC models rarely have consistent IfcSystem assignments",
            "No validation corpus with real system semantics",
            "bSDD RU-domain coverage is limited",
        ],
        notes="NOT_VERIFIED is the honest status. Do not claim system-aware MEP until "
        "validated on real federated IFC with real system assignments.",
    ),
    MEPLayer(
        layer_number=4,
        name="Connectivity / Topology",
        description=(
            "Network topology checks: continuity of piping/duct/cable networks, "
            "correct port connections (IfcDistributionPort), open ends, "
            "missing segments, wrong flow direction."
        ),
        engineering_status=CapabilityStatus.NOT_VERIFIED,
        customer_status=CapabilityStatus.NOT_VERIFIED,
        required_inputs=[
            "IFC with IfcRelConnectsPorts",
            "IfcDistributionPort on all connected elements",
            "Flow direction properties",
        ],
        known_limitations=[
            "Russian BIM practice: ports are rarely modelled; topology not verifiable",
            "No implementation; scaffolding only",
        ],
    ),
    MEPLayer(
        layer_number=5,
        name="Rule-based System Compliance",
        description=(
            "Full system-level compliance: capacity calculations cross-check, "
            "pressure drop verification, heat loss/gain balance, "
            "load matching against calculations, regulatory norm compliance "
            "for specific system types (e.g. SP 60, SP 30)."
        ),
        engineering_status=CapabilityStatus.NOT_VERIFIED,
        customer_status=CapabilityStatus.NOT_VERIFIED,
        required_inputs=[
            "Layer 3 + Layer 4 fully verified",
            "Calculation documents (XML or PDF with extracted values)",
            "Cross-document pairing (IFC ↔ calculations)",
            "Validated norm pack for system rules",
        ],
        known_limitations=[
            "Blocked by Layers 3 and 4 not being verified",
            "Cross-document extraction accuracy not validated",
            "No customer corpus for system compliance",
        ],
        notes="This is the most complex layer. It requires all lower layers plus "
        "reliable calculation extraction. Honest status: NOT_VERIFIED.",
    ),
]


def get_layer(layer_number: int) -> MEPLayer | None:
    return next(
        (layer for layer in MEP_LAYERS if layer.layer_number == layer_number),
        None,
    )


def mep_capability_matrix() -> list[dict[str, Any]]:
    """Export current MEP capability status as structured dict."""
    return [layer.to_dict() for layer in MEP_LAYERS]


def max_verified_layer() -> int:
    """Return the highest layer number with ENGINEERING_DONE or PARTIAL status."""
    for layer in reversed(MEP_LAYERS):
        if layer.engineering_status in (
            CapabilityStatus.ENGINEERING_DONE,
            CapabilityStatus.PARTIAL,
        ):
            return layer.layer_number
    return 0
