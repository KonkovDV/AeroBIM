"""Persistence contracts for report commit / recovery (Red Team Phase 3).

Lifecycle (normative):
RECEIVED → ARTIFACTS_VALIDATED → ARTIFACTS_PERSISTED → REPORT_COMMITTED
→ AUDIT_COMMITTED → REVIEWABLE
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class ReportCommitState(StrEnum):
    RECEIVED = "received"
    ARTIFACTS_VALIDATED = "artifacts_validated"
    ARTIFACTS_PERSISTED = "artifacts_persisted"
    REPORT_COMMITTED = "report_committed"
    AUDIT_COMMITTED = "audit_committed"
    REVIEWABLE = "reviewable"
    ORPHAN_UNCOMMITTED = "orphan_uncommitted"
    CORRUPT = "corrupt"


class RecoveryStatus(StrEnum):
    NOT_NEEDED = "not_needed"
    PENDING = "pending"
    CLEANED = "cleaned"
    FAILED = "failed"
    RESOLVED_COMMITTED = "resolved_committed"


@dataclass(frozen=True)
class ArtifactHash:
    algorithm: Literal["sha256"] = "sha256"
    digest: str = ""
    byte_length: int = 0


@dataclass(frozen=True)
class ArtifactManifestEntry:
    object_key: str
    role: str
    """Role: ifc_source | drawing_preview | report_json | other."""
    sha256: str | None = None
    byte_length: int | None = None


@dataclass(frozen=True)
class ArtifactManifest:
    schema_version: str = "1.0.0"
    report_id: str = ""
    commit_state: ReportCommitState = ReportCommitState.RECEIVED
    artifacts: tuple[ArtifactManifestEntry, ...] = ()
    ifc_object_key: str | None = None
    committed_at: str | None = None

    def object_keys(self) -> tuple[str, ...]:
        return tuple(entry.object_key for entry in self.artifacts)


@dataclass(frozen=True)
class PersistenceResult:
    report_id: str
    commit_state: ReportCommitState
    reviewable: bool
    artifact_keys: tuple[str, ...] = ()
    error: str | None = None


def is_report_reviewable(*, committed: bool, report_json_exists: bool) -> bool:
    """A report is reviewable only when JSON and commit marker both exist."""

    return committed and report_json_exists


def build_commit_manifest_payload(
    *,
    report_id: str,
    artifact_keys: list[str] | tuple[str, ...],
    ifc_object_key: str | None,
    committed_at: str,
    commit_state: ReportCommitState = ReportCommitState.REVIEWABLE,
) -> dict[str, object]:
    artifacts = [
        ArtifactManifestEntry(
            object_key=key,
            role="ifc_source" if key.startswith("ifc-sources/") else "drawing_preview",
        )
        for key in artifact_keys
    ]
    if ifc_object_key and ifc_object_key not in artifact_keys:
        artifacts.insert(
            0,
            ArtifactManifestEntry(object_key=ifc_object_key, role="ifc_source"),
        )
    manifest = ArtifactManifest(
        report_id=report_id,
        commit_state=commit_state,
        artifacts=tuple(artifacts),
        ifc_object_key=ifc_object_key,
        committed_at=committed_at,
    )
    return {
        "schema_version": manifest.schema_version,
        "report_id": manifest.report_id,
        "committed": True,
        "commit_state": manifest.commit_state.value,
        "ifc_object_key": manifest.ifc_object_key,
        "artifact_keys": list(manifest.object_keys()),
        "artifacts": [
            {
                "object_key": entry.object_key,
                "role": entry.role,
                "sha256": entry.sha256,
                "byte_length": entry.byte_length,
            }
            for entry in manifest.artifacts
        ],
        "committed_at": manifest.committed_at,
    }


__all__ = [
    "ArtifactHash",
    "ArtifactManifest",
    "ArtifactManifestEntry",
    "PersistenceResult",
    "RecoveryStatus",
    "ReportCommitState",
    "build_commit_manifest_payload",
    "is_report_reviewable",
]
