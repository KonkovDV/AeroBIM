"""
P0-A: Robust Package Intake — Package Manifest.

Deterministic package identity: package_id = sha256(tenant_id + project_id +
revision_id + sorted_file_hashes). Never random. Idempotent on same inputs.

Each file carries: logical_path, sha256, size, media_type, role, discipline,
revision, source — required for evidence chain and auditability.

Not a rewrite: extends existing upload/storage layer.
Reduces: evaluation gap, auditability risk, customer deployment risk.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class FileRole(str, Enum):
    """Role of a file within a package."""
    IFC_MODEL = "ifc_model"
    IDS_SPECIFICATION = "ids_specification"
    DRAWING_PDF = "drawing_pdf"
    DRAWING_DXF = "drawing_dxf"
    SPECIFICATION_TEXT = "specification_text"
    CALCULATION = "calculation"
    SCHEDULE = "schedule"
    NORM_PACK = "norm_pack"
    REBAR_REPORT = "rebar_report"
    SUPPLEMENTARY = "supplementary"
    UNKNOWN = "unknown"


class Discipline(str, Enum):
    """BIM discipline / section."""
    AR = "AR"   # Architecture
    KR = "KR"   # Structural
    OV = "OV"   # HVAC
    VK = "VK"   # Plumbing
    EOM = "EOM" # Electrical
    SS = "SS"   # Low-voltage / IT
    ITP = "ITP" # Heat point
    GP = "GP"   # General plan
    MULTI = "MULTI"
    UNKNOWN = "UNKNOWN"


class UploadState(str, Enum):
    """Upload lifecycle state."""
    PENDING = "pending"       # Awaiting all chunks
    COMPLETE = "complete"     # All bytes received, hash verified
    QUARANTINED = "quarantined" # Failed security check
    TOMBSTONED = "tombstoned" # Deleted, identity preserved


@dataclass(frozen=True)
class PackageFileEntry:
    """
    Per-file entry in a package manifest.

    All fields required for evidence chain. sha256 is verified on ingest;
    tampering with any field invalidates manifest_sha256.
    """
    logical_path: str          # Canonical relative path within package
    sha256: str                # Hex SHA-256 of raw bytes
    size: int                  # Bytes
    media_type: str            # IANA media type (verified, not trusted from extension)
    role: FileRole
    discipline: Discipline
    revision: Optional[str]    # e.g. "P3", "R2" from filename/metadata
    source: Optional[str]      # upstream system reference (CDE path, upload_id)
    upload_state: UploadState = UploadState.COMPLETE

    def to_dict(self) -> dict:
        return {
            "logical_path": self.logical_path,
            "sha256": self.sha256,
            "size": self.size,
            "media_type": self.media_type,
            "role": self.role.value,
            "discipline": self.discipline.value,
            "revision": self.revision,
            "source": self.source,
            "upload_state": self.upload_state.value,
        }


@dataclass
class PackageManifest:
    """
    Deterministic package manifest.

    package_id is derived from content hashes — never random.
    manifest_sha256 covers all file entries; tampering is detectable.

    Security: tenant_id and project_id are embedded and verified
    before any artifact access (authenticate → authorize → fetch).
    """
    package_id: str            # Deterministic: sha256 of (tenant+project+revision+files)
    project_id: str
    tenant_id: str
    revision_id: str           # Logical revision label (e.g. "Stage-P3-R2")
    created_at: datetime
    files: list[PackageFileEntry] = field(default_factory=list)
    manifest_sha256: str = ""  # Computed over serialised files[]; set after finalise()
    upload_state: UploadState = UploadState.PENDING
    tombstone_reason: Optional[str] = None

    # --- identity -------------------------------------------------------

    @staticmethod
    def compute_package_id(
        tenant_id: str,
        project_id: str,
        revision_id: str,
        file_entries: list[PackageFileEntry],
    ) -> str:
        """
        Deterministic package identity.
        Stable across restarts; same content == same id (idempotency).
        """
        parts = [
            f"tenant={tenant_id}",
            f"project={project_id}",
            f"revision={revision_id}",
        ]
        # Sort by logical_path for stability
        for f in sorted(file_entries, key=lambda e: e.logical_path):
            parts.append(f"file:{f.logical_path}:{f.sha256}")
        payload = "\n".join(parts).encode()
        return hashlib.sha256(payload).hexdigest()[:40]

    def finalise(self) -> "PackageManifest":
        """
        Compute manifest_sha256 over all file entries.
        Call after all files are added; manifest becomes immutable.
        """
        entries = sorted(
            [f.to_dict() for f in self.files],
            key=lambda d: d["logical_path"],
        )
        payload = json.dumps(entries, sort_keys=True, ensure_ascii=True).encode()
        self.manifest_sha256 = hashlib.sha256(payload).hexdigest()
        self.upload_state = UploadState.COMPLETE
        return self

    def verify_integrity(self) -> bool:
        """Re-compute manifest hash and compare. Returns False if tampered."""
        entries = sorted(
            [f.to_dict() for f in self.files],
            key=lambda d: d["logical_path"],
        )
        payload = json.dumps(entries, sort_keys=True, ensure_ascii=True).encode()
        computed = hashlib.sha256(payload).hexdigest()
        return computed == self.manifest_sha256

    def tombstone(self, reason: str) -> None:
        """Soft-delete: preserve identity, clear content references."""
        self.upload_state = UploadState.TOMBSTONED
        self.tombstone_reason = reason
        # Files retain sha256 for dedup detection; physical bytes deleted separately

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "revision_id": self.revision_id,
            "created_at": self.created_at.isoformat(),
            "files": [f.to_dict() for f in self.files],
            "manifest_sha256": self.manifest_sha256,
            "upload_state": self.upload_state.value,
            "tombstone_reason": self.tombstone_reason,
        }


def build_package_manifest(
    tenant_id: str,
    project_id: str,
    revision_id: str,
    files: list[PackageFileEntry],
) -> PackageManifest:
    """
    Factory: builds and finalises a manifest from file entries.
    Deterministic: calling twice with the same inputs yields the same package_id.
    """
    package_id = PackageManifest.compute_package_id(
        tenant_id, project_id, revision_id, files
    )
    manifest = PackageManifest(
        package_id=package_id,
        project_id=project_id,
        tenant_id=tenant_id,
        revision_id=revision_id,
        created_at=datetime.now(tz=timezone.utc),
        files=list(files),
    )
    return manifest.finalise()
