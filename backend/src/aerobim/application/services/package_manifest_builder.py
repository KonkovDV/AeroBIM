"""Seal a package manifest when file hashes are already known.

An empty entry list returns None. compute_package_id is not called in that
case. created_at is not part of manifest_sha256.
"""

from __future__ import annotations

from aerobim.domain.models import ValidationRequest
from aerobim.domain.package_manifest import (
    PackageFileEntry,
    PackageManifest,
    build_package_manifest,
)


def build_manifest_when_entries_present(
    request: ValidationRequest,
    file_entries: tuple[PackageFileEntry, ...],
) -> PackageManifest | None:
    """None when no file hashes are available."""
    if not file_entries:
        return None
    tenant = (request.tenant_id or "").strip() or "unknown"
    project = (request.project_id or request.project_name or "").strip() or "unknown"
    revision = (request.revision or "").strip() or "unversioned"
    return build_package_manifest(tenant, project, revision, list(file_entries))


def manifest_trace_fields(manifest: PackageManifest | None) -> dict[str, object]:
    """Fields safe to append to tool_traces. No created_at."""
    if manifest is None:
        return {"manifest_sha256": None}
    return {"manifest_sha256": manifest.manifest_sha256}


__all__ = [
    "build_manifest_when_entries_present",
    "manifest_trace_fields",
]
