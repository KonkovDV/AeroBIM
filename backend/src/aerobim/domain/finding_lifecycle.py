"""
P1-E: Finding Lifecycle — Revision Intelligence.

Formal lifecycle states for findings across revisions:
  NEW → PERSISTED (unchanged across revisions)
  NEW / PERSISTED → RESOLVED (fixed in new revision)
  RESOLVED → REGRESSED (reappears in later revision)
  RESOLVED → REOPENED (human action, same revision)
  Any → SUPERSEDED (rule version changed, re-evaluated)

Closed-loop revalidation:
  Finding → Issue → Model revision N+1 → Change detection
  → Targeted re-check → Finding status update.

Revision diff categories:
  unchanged / added / removed / modified / moved /
  metadata_changed / geometry_changed / relationship_changed /
  rule_impacting_change.

Reduces: auditability risk, evaluation gap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class FindingStatus(StrEnum):
    """Lifecycle status of a finding."""

    NEW = "NEW"  # First detected in this revision
    PERSISTED = "PERSISTED"  # Present in previous revision(s) unchanged
    RESOLVED = "RESOLVED"  # Fixed in current revision
    REGRESSED = "REGRESSED"  # Was RESOLVED, reappears
    REOPENED = "REOPENED"  # Human action: re-opened after RESOLVED
    SUPERSEDED = "SUPERSEDED"  # Rule version changed; replaced by new evaluation
    NOT_VERIFIED = "NOT_VERIFIED"  # Insufficient evidence; unknown ≠ pass


class ReviewAction(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    FALSE_POSITIVE = "false_positive"
    NEEDS_CLARIFICATION = "needs_clarification"
    ASSIGN = "assign"
    REASSIGN = "reassign"
    ADD_NOTE = "add_note"
    EDIT_REMARK = "edit_remark"
    CLOSE = "close"
    REOPEN = "reopen"
    APPROVE_REMARK = "approve_remark"


class ChangeCategory(StrEnum):
    """How an element changed between revisions."""

    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"
    METADATA_CHANGED = "metadata_changed"
    GEOMETRY_CHANGED = "geometry_changed"
    RELATIONSHIP_CHANGED = "relationship_changed"
    RULE_IMPACTING_CHANGE = "rule_impacting_change"  # Requires re-check


@dataclass
class RemarkVersion:
    """
    Immutable remark snapshot. Human-edited text is never overwritten.
    AI may generate; human approves.
    """

    remark_version_id: str
    generated_remark: str  # Template/AI-generated draft
    reviewer_edited_remark: str | None = None  # Human edit (never auto-overwritten)
    approved_remark: str | None = None  # Final, locked text
    approved_by: str | None = None
    approved_at: datetime | None = None
    language: str = "ru"  # "ru" or "en"
    generated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    @property
    def final_text(self) -> str:
        """Returns the most authoritative remark text."""
        return self.approved_remark or self.reviewer_edited_remark or self.generated_remark

    @property
    def is_approved(self) -> bool:
        return self.approved_remark is not None and self.approved_by is not None


@dataclass
class ReviewEvent:
    """Audit trail entry for reviewer actions."""

    event_id: str
    finding_id: str
    action: ReviewAction
    actor: str  # User ID
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    note: str | None = None
    assigned_to: str | None = None
    remark_version_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "finding_id": self.finding_id,
            "action": self.action.value,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "note": self.note,
            "assigned_to": self.assigned_to,
            "remark_version_id": self.remark_version_id,
        }


@dataclass
class ElementRevisionDiff:
    """Change record for one IFC element between two revisions."""

    ifc_guid: str
    change_category: ChangeCategory
    previous_revision_id: str
    current_revision_id: str
    changed_properties: list[str] = field(default_factory=list)
    is_rule_impacting: bool = False
    notes: str | None = None


@dataclass
class Finding:
    """
    A compliance finding with full lifecycle tracking.

    Traceability:
      finding_id → evidence_refs → EvidenceRecord.provenance_id
      → stable hash of (source_hash, rule_version, norm_pack_hash,
        engine_version, configuration_hash, locator, actual, expected)

    Lifecycle:
      NEW on first detection.
      PERSISTED when same fingerprint found in previous revision.
      RESOLVED when fingerprint absent in new revision.
      REGRESSED when RESOLVED finding fingerprint reappears.
      SUPERSEDED when rule version changes; a new finding replaces.
    """

    finding_id: str
    rule_id: str
    rule_version: str
    norm_pack_id: str
    norm_pack_version: str
    package_id: str
    revision_id: str
    tenant_id: str
    project_id: str
    status: FindingStatus = FindingStatus.NEW

    # Severity from rule (deterministic; AI cannot change)
    severity: str = "error"  # "error" | "warning" | "info"
    discipline: str = "UNKNOWN"

    # Evidence
    evidence_refs: list[str] = field(default_factory=list)  # evidence_id list
    is_ai_advisory: bool = False  # True if any evidence is AI_ADVISORY

    # Remark lifecycle
    remark_versions: list[RemarkVersion] = field(default_factory=list)

    # Cross-revision linkage
    previous_finding_id: str | None = None  # For PERSISTED / REGRESSED
    superseded_by: str | None = None  # For SUPERSEDED
    bcf_topic_id: str | None = None  # BCF 3.0 topic ID

    # Review
    reviewer_id: str | None = None
    assigned_to: str | None = None
    review_events: list[ReviewEvent] = field(default_factory=list)

    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    # Determinism gate: AI cannot flip this
    _deterministic_verdict: bool | None = field(default=None, repr=False)

    @property
    def fingerprint(self) -> str:
        """Stable identity for cross-revision comparison."""
        import hashlib

        payload = (
            f"{self.rule_id}:{self.rule_version}:" + "|".join(sorted(self.evidence_refs))
        ).encode()
        return hashlib.sha256(payload).hexdigest()[:16]

    def transition_to(self, new_status: FindingStatus, actor: str = "system") -> None:
        """Advance lifecycle state."""
        self.status = new_status
        self.updated_at = datetime.now(tz=UTC)

    def add_remark_version(self, remark: RemarkVersion) -> None:
        """Append remark; never overwrites human-edited text."""
        self.remark_versions.append(remark)
        self.updated_at = datetime.now(tz=UTC)

    @property
    def current_remark(self) -> RemarkVersion | None:
        return self.remark_versions[-1] if self.remark_versions else None

    def record_review(self, event: ReviewEvent) -> None:
        self.review_events.append(event)
        self.updated_at = datetime.now(tz=UTC)
        if event.assigned_to:
            self.assigned_to = event.assigned_to
        if event.action == ReviewAction.REOPEN:
            self.transition_to(FindingStatus.REOPENED, event.actor)
        elif event.action == ReviewAction.CLOSE:
            self.transition_to(FindingStatus.RESOLVED, event.actor)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "norm_pack_id": self.norm_pack_id,
            "norm_pack_version": self.norm_pack_version,
            "package_id": self.package_id,
            "revision_id": self.revision_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "status": self.status.value,
            "severity": self.severity,
            "discipline": self.discipline,
            "evidence_refs": self.evidence_refs,
            "is_ai_advisory": self.is_ai_advisory,
            "previous_finding_id": self.previous_finding_id,
            "superseded_by": self.superseded_by,
            "bcf_topic_id": self.bcf_topic_id,
            "reviewer_id": self.reviewer_id,
            "assigned_to": self.assigned_to,
            "current_remark": self.current_remark.final_text if self.current_remark else None,
            "remark_approved": self.current_remark.is_approved if self.current_remark else False,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def classify_finding_against_previous(
    current: Finding,
    previous_findings_by_fingerprint: dict[str, Finding],
) -> FindingStatus:
    """
    Determine lifecycle status by comparing fingerprints across revisions.
    Called by the re-check pipeline after loading previous revision results.
    """
    prev = previous_findings_by_fingerprint.get(current.fingerprint)
    if prev is None:
        return FindingStatus.NEW
    if prev.status == FindingStatus.RESOLVED:
        return FindingStatus.REGRESSED
    return FindingStatus.PERSISTED
