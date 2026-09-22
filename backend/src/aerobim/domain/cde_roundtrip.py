"""
P1-L: Local CDE Reference Simulator + BCF 3.0 Roundtrip.

Local reference CDE for engineering validation of the handoff contract.
Workflow:
  AeroBIM → create issue → push BCF → CDE (simulator)
  → retrieve issue → match finding → update status → re-import

Verifies roundtrip identity: push + pull = same finding.

Capability status (MUST remain honest):
  ENGINEERING: DONE (after tests pass)
  CUSTOMER: NOT_VERIFIED (until real customer CDE environment)

BCF 3.0 target per buildingSMART standard.
openCDE Foundation/Documents APIs as interoperability target.
Do not invent proprietary replacement for BCF 3.0.

Reduces: interoperability risk, auditability risk.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class BCFTopicStatus(StrEnum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REOPENED = "ReOpened"


class BCFTopicType(StrEnum):
    ISSUE = "Issue"
    REQUEST = "Request"
    FAULT = "Fault"
    REMARK = "Remark"
    UNKNOWN = "Unknown"


class BCFPriority(StrEnum):
    CRITICAL = "Critical"
    MAJOR = "Major"
    NORMAL = "Normal"
    MINOR = "Minor"


@dataclass
class BCFComponent:
    """IFC element reference in BCF viewpoint."""

    ifc_guid: str
    originating_system: str = "AeroBIM"
    authoring_tool_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ifc_guid": self.ifc_guid,
            "originating_system": self.originating_system,
            "authoring_tool_id": self.authoring_tool_id,
        }


@dataclass
class BCFViewpoint:
    """BCF 3.0 viewpoint with components."""

    viewpoint_id: str
    snapshot: str | None = None  # base64 PNG or None
    components: list[BCFComponent] = field(default_factory=list)
    camera_x: float | None = None
    camera_y: float | None = None
    camera_z: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "viewpoint_id": self.viewpoint_id,
            "components": [c.to_dict() for c in self.components],
            "camera": {"x": self.camera_x, "y": self.camera_y, "z": self.camera_z}
            if self.camera_x is not None
            else None,
        }


@dataclass
class BCFTopic:
    """
    BCF 3.0 topic — issue handoff contract between AeroBIM and CDE.

    Stably linked to: finding_id + ifc_guid + revision + evidence.
    topic_id is stable and used for roundtrip identity verification.
    """

    topic_id: str  # UUID; stable across roundtrip
    title: str
    description: str
    status: BCFTopicStatus
    topic_type: BCFTopicType
    priority: BCFPriority
    author: str
    creation_date: str  # ISO datetime
    modified_date: str
    assigned_to: str | None = None
    labels: list[str] = field(default_factory=list)
    components: list[BCFComponent] = field(default_factory=list)
    viewpoints: list[BCFViewpoint] = field(default_factory=list)
    # AeroBIM-specific linkage (in BCF extended attributes / links)
    aerobim_finding_id: str | None = None
    aerobim_evidence_ref: str | None = None
    aerobim_revision_id: str | None = None
    aerobim_rule_id: str | None = None
    aerobim_norm_pack_hash: str | None = None

    @property
    def content_hash(self) -> str:
        """Stable hash for roundtrip identity verification."""
        payload = json.dumps(
            {
                "topic_id": self.topic_id,
                "title": self.title,
                "description": self.description,
                "aerobim_finding_id": self.aerobim_finding_id,
                "aerobim_revision_id": self.aerobim_revision_id,
                "aerobim_rule_id": self.aerobim_rule_id,
                "components": sorted(c.ifc_guid for c in self.components),
            },
            sort_keys=True,
        ).encode()
        return hashlib.sha256(payload).hexdigest()[:24]

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "topic_type": self.topic_type.value,
            "priority": self.priority.value,
            "author": self.author,
            "creation_date": self.creation_date,
            "modified_date": self.modified_date,
            "assigned_to": self.assigned_to,
            "labels": self.labels,
            "components": [c.to_dict() for c in self.components],
            "viewpoints": [v.to_dict() for v in self.viewpoints],
            "aerobim_finding_id": self.aerobim_finding_id,
            "aerobim_evidence_ref": self.aerobim_evidence_ref,
            "aerobim_revision_id": self.aerobim_revision_id,
            "aerobim_rule_id": self.aerobim_rule_id,
            "aerobim_norm_pack_hash": self.aerobim_norm_pack_hash,
            "content_hash": self.content_hash,
        }


class RoundtripResult(StrEnum):
    OK = "OK"  # Push + pull = identical
    HASH_MISMATCH = "HASH_MISMATCH"  # Content changed in transit
    TOPIC_MISSING = "TOPIC_MISSING"  # Pull returned nothing
    FINDING_UNMATCHED = "FINDING_UNMATCHED"  # finding_id not matched
    ERROR = "ERROR"


@dataclass
class RoundtripRecord:
    """
    Verification record for a single BCF roundtrip.
    Engineering status is determined by this record passing.
    Customer status remains NOT_VERIFIED until real CDE environment.
    """

    record_id: str
    topic_id: str
    finding_id: str
    push_content_hash: str
    pull_content_hash: str | None
    result: RoundtripResult
    tested_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    cde_endpoint: str = "local_simulator"  # Never fake as real CDE
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "topic_id": self.topic_id,
            "finding_id": self.finding_id,
            "push_content_hash": self.push_content_hash,
            "pull_content_hash": self.pull_content_hash,
            "result": self.result.value,
            "tested_at": self.tested_at.isoformat(),
            "cde_endpoint": self.cde_endpoint,
            "notes": self.notes,
        }


class LocalCDESimulator:
    """
    Local reference CDE simulator for engineering validation.

    IMPORTANT: This is NOT a customer CDE. It is a local roundtrip
    test harness. Capability claims:
      ENGINEERING_STATUS: DONE (when roundtrip tests pass)
      CUSTOMER_STATUS: NOT_VERIFIED (until real customer environment)

    openCDE Foundation/Documents APIs are the interoperability target.
    """

    def __init__(self) -> None:
        self._topics: dict[str, BCFTopic] = {}
        self._status_updates: dict[str, list[dict[str, Any]]] = {}

    def push_topic(self, topic: BCFTopic) -> str:
        """Simulate CDE receiving a BCF topic. Returns topic_id."""
        self._topics[topic.topic_id] = topic
        return topic.topic_id

    def get_topic(self, topic_id: str) -> BCFTopic | None:
        """Simulate CDE returning a topic."""
        return self._topics.get(topic_id)

    def update_status(self, topic_id: str, new_status: BCFTopicStatus, actor: str) -> bool:
        """Simulate CDE updating topic status."""
        topic = self._topics.get(topic_id)
        if topic is None:
            return False
        topic.status = new_status
        topic.modified_date = datetime.now(tz=UTC).isoformat()
        self._status_updates.setdefault(topic_id, []).append(
            {"status": new_status.value, "actor": actor, "timestamp": topic.modified_date}
        )
        return True

    def verify_roundtrip(self, topic: BCFTopic) -> RoundtripRecord:
        """
        Push + pull + compare content_hash.
        PASS only when push_hash == pull_hash.
        """
        push_hash = topic.content_hash
        topic_id = self.push_topic(topic)
        pulled = self.get_topic(topic_id)

        if pulled is None:
            return RoundtripRecord(
                record_id=str(uuid.uuid4()),
                topic_id=topic_id,
                finding_id=topic.aerobim_finding_id or "",
                push_content_hash=push_hash,
                pull_content_hash=None,
                result=RoundtripResult.TOPIC_MISSING,
                notes="CDE simulator returned nothing for pushed topic_id",
            )

        pull_hash = pulled.content_hash
        if push_hash != pull_hash:
            result = RoundtripResult.HASH_MISMATCH
            notes = f"Hash mismatch: push={push_hash[:8]}... pull={pull_hash[:8]}..."
        elif pulled.aerobim_finding_id != topic.aerobim_finding_id:
            result = RoundtripResult.FINDING_UNMATCHED
            notes = (
                f"finding_id mismatch: "
                f"pushed={topic.aerobim_finding_id} pulled={pulled.aerobim_finding_id}"
            )
        else:
            result = RoundtripResult.OK
            notes = "Roundtrip OK: push_hash == pull_hash, finding_id matched"

        return RoundtripRecord(
            record_id=str(uuid.uuid4()),
            topic_id=topic_id,
            finding_id=topic.aerobim_finding_id or "",
            push_content_hash=push_hash,
            pull_content_hash=pull_hash,
            result=result,
            notes=notes,
        )

    def all_topics(self) -> list[BCFTopic]:
        return list(self._topics.values())


def make_bcf_topic_from_finding(
    finding_id: str,
    rule_id: str,
    norm_pack_hash: str,
    revision_id: str,
    title: str,
    description: str,
    ifc_guids: list[str],
    author: str,
    evidence_ref: str | None = None,
    priority: BCFPriority = BCFPriority.MAJOR,
) -> BCFTopic:
    """Factory: create BCF 3.0 topic from AeroBIM finding."""
    now = datetime.now(tz=UTC).isoformat()
    return BCFTopic(
        topic_id=str(uuid.uuid4()),
        title=title,
        description=description,
        status=BCFTopicStatus.OPEN,
        topic_type=BCFTopicType.ISSUE,
        priority=priority,
        author=author,
        creation_date=now,
        modified_date=now,
        components=[BCFComponent(ifc_guid=g) for g in ifc_guids],
        aerobim_finding_id=finding_id,
        aerobim_evidence_ref=evidence_ref,
        aerobim_revision_id=revision_id,
        aerobim_rule_id=rule_id,
        aerobim_norm_pack_hash=norm_pack_hash,
    )
