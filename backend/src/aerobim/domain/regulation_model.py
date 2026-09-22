"""
P1-A: Regulatory Information Model.

Full traceability: norm_pack → norm_document → clause → interpretation
  → requirement → rule → execution → evidence → result.

Each rule:
  - Has stable_version (immutable after publish)
  - Has provenance: norm_ref + clause + jurisdiction
  - Has review statuses: interpretation / legal / technical / approval
  - Has explicit evidence_requirements
  - Production-only when all reviews APPROVED

BRISE-Vienna 2026 Regulation Information Matrix parallel:
  legal interpretation → implementation → testing → validation → acceptance.

Reduces: auditability risk, evaluation gap, interoperability risk.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class RuleSeverity(str, Enum):
    ERROR = "error"      # Blocking — any ERROR → summary.passed=false
    WARNING = "warning"  # Non-blocking
    INFO = "info"        # Advisory only


class ExecutionMode(str, Enum):
    DETERMINISTIC = "deterministic"  # Must pass DeterminismGate
    ADVISORY = "advisory"            # AI contribution; human must confirm
    SKIPPED = "skipped"             # Not applicable for this scope


class EvidenceRequirementType(str, Enum):
    IFC_PROPERTY = "ifc_property"
    IFC_GUID = "ifc_guid"
    DOCUMENT_VALUE = "document_value"
    CROSS_DOC_MATCH = "cross_doc_match"
    CALCULATION_MATCH = "calc_match"
    GEOMETRIC = "geometric"


@dataclass(frozen=True)
class NormRef:
    """Traceable reference to a normative document."""
    document_id: str    # e.g. "SP-70.13330.2022", "MOEXP-IDS-2025"
    clause: str         # e.g. "п.8.3.1", "Table 3"
    jurisdiction: str   # e.g. "RU", "RU-MOW"
    effective_from: str  # ISO date
    publisher: str
    url: Optional[str] = None


@dataclass
class EvidenceRequirement:
    """
    Specifies what evidence must be collected to evaluate a rule.
    Missing required evidence → NOT_VERIFIED, never silent PASS.
    """
    req_type: EvidenceRequirementType
    description: str
    required: bool = True
    ifc_entity: Optional[str] = None
    ifc_property_set: Optional[str] = None
    ifc_property_name: Optional[str] = None
    document_field: Optional[str] = None


@dataclass
class RuleInterpretation:
    """
    Human-authored interpretation of a clause for automated checking.
    Unapproved interpretation → rule cannot be in production.
    """
    interpretation_id: str
    clause_text: str           # Verbatim quoted clause
    interpretation_text: str   # How the clause maps to automated checks
    ambiguity_notes: Optional[str] = None
    interpretation_status: ReviewStatus = ReviewStatus.PENDING
    legal_review_status: ReviewStatus = ReviewStatus.PENDING
    technical_review_status: ReviewStatus = ReviewStatus.PENDING
    approval_status: ReviewStatus = ReviewStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    @property
    def is_production_ready(self) -> bool:
        return all(
            s == ReviewStatus.APPROVED
            for s in (
                self.interpretation_status,
                self.legal_review_status,
                self.technical_review_status,
                self.approval_status,
            )
        )


@dataclass
class ComplianceRule:
    """
    Single compliance rule with full provenance.

    rule_id + stable_version uniquely identifies a rule across time.
    Content immutable after approval_status=APPROVED.
    Any change → new version.

    AI cannot generate a production rule without:
      - approved norm_ref
      - approved interpretation
      - stated evidence_requirements
      - explicit severity
    """
    rule_id: str            # Stable, e.g. "AR-COVER-001"
    stable_version: str     # Semver, immutable after publish
    name: str
    description: str
    norm_ref: NormRef
    interpretation: RuleInterpretation
    scope: str              # e.g. "residential", "all"
    discipline: str         # e.g. "AR", "KR"
    severity: RuleSeverity
    execution_mode: ExecutionMode
    inputs: list[str]
    preconditions: list[str]
    logic_description: str  # Human-readable; not code
    parameters: dict[str, Any] = field(default_factory=dict)
    exceptions: list[str] = field(default_factory=list)
    evidence_requirements: list[EvidenceRequirement] = field(default_factory=list)
    applicability_filter: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    approval_status: ReviewStatus = ReviewStatus.PENDING

    @property
    def rule_hash(self) -> str:
        """Stable content hash. Changes on any field change."""
        payload = json.dumps(
            {
                "rule_id": self.rule_id,
                "stable_version": self.stable_version,
                "norm_ref_document": self.norm_ref.document_id,
                "norm_ref_clause": self.norm_ref.clause,
                "logic_description": self.logic_description,
                "parameters": self.parameters,
                "severity": self.severity.value,
                "execution_mode": self.execution_mode.value,
            },
            sort_keys=True,
        ).encode()
        return hashlib.sha256(payload).hexdigest()[:16]

    def is_production_ready(self) -> bool:
        return (
            self.approval_status == ReviewStatus.APPROVED
            and self.interpretation.is_production_ready
        )


@dataclass
class NormPack:
    """
    Versioned, immutable norm pack.

    pack_hash is sealed on finalise().
    Each execution stores pack_hash + rule_hash + input_hash + engine_version
    + configuration_hash + result_hash.
    Old results NEVER adopt new norm versions.
    """
    pack_id: str
    version: str
    name: str
    publisher: str
    jurisdiction: str
    scope: str
    source_ref: str
    effective_from: str
    effective_to: Optional[str] = None
    rules: list[ComplianceRule] = field(default_factory=list)
    pack_hash: str = ""

    def finalise(self) -> "NormPack":
        rule_hashes = sorted(r.rule_hash for r in self.rules)
        payload = json.dumps(
            {"pack_id": self.pack_id, "version": self.version,
             "jurisdiction": self.jurisdiction, "rule_hashes": rule_hashes},
            sort_keys=True,
        ).encode()
        self.pack_hash = hashlib.sha256(payload).hexdigest()
        return self

    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        return next((r for r in self.rules if r.rule_id == rule_id), None)

    def production_rules(self) -> list[ComplianceRule]:
        """Only rules that passed all review gates."""
        return [r for r in self.rules if r.is_production_ready()]


@dataclass
class ExecutionProvenance:
    """
    Execution-time provenance record.
    Stored alongside every report/evidence artifact.
    Enables full reproduction: same hashes → same result.
    """
    pack_hash: str
    rule_hash: str
    input_hash: str          # sha256 of IFC + supplementary inputs
    engine_version: str      # AeroBIM semver
    configuration_hash: str  # sha256 of active settings
    result_hash: str         # sha256 of findings JSON
    timestamp: str           # ISO datetime
    tenant_id: str
    project_id: str
    package_id: str

    def to_dict(self) -> dict:
        return {
            "pack_hash": self.pack_hash,
            "rule_hash": self.rule_hash,
            "input_hash": self.input_hash,
            "engine_version": self.engine_version,
            "configuration_hash": self.configuration_hash,
            "result_hash": self.result_hash,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "package_id": self.package_id,
        }
