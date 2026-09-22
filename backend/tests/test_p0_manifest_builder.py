"""Seal a manifest only when file hashes are already present."""

from __future__ import annotations

from datetime import timedelta

from aerobim.application.services.package_manifest_builder import (
    build_manifest_when_entries_present,
    manifest_trace_fields,
)
from aerobim.domain.models import RequirementSource, ValidationRequest
from aerobim.domain.package_manifest import (
    Discipline,
    FileRole,
    PackageFileEntry,
    UploadState,
)

_SHA_A = "ab" * 32
_SHA_B = "cd" * 32


def _request() -> ValidationRequest:
    return ValidationRequest(
        request_id="req-manifest-seal",
        ifc_path=None,
        requirement_source=RequirementSource(text="REQ"),
        tenant_id="tenant-x",
        project_id="proj-y",
        revision="P1",
    )


def _entry(sha256: str, logical_path: str = "model.ifc") -> PackageFileEntry:
    return PackageFileEntry(
        logical_path=logical_path,
        sha256=sha256,
        size=0,
        media_type="application/x-step",
        role=FileRole.IFC_MODEL,
        discipline=Discipline.UNKNOWN,
        revision="P1",
        source=None,
        upload_state=UploadState.COMPLETE,
    )


class TestBuildManifestWhenEntriesPresent:
    def test_empty_entries_return_none(self) -> None:
        assert build_manifest_when_entries_present(_request(), ()) is None
        assert manifest_trace_fields(None) == {"manifest_sha256": None}

    def test_entries_seal_a_stable_hash(self) -> None:
        entries = (_entry(_SHA_A),)
        first = build_manifest_when_entries_present(_request(), entries)
        second = build_manifest_when_entries_present(_request(), entries)
        assert first is not None
        assert second is not None
        assert first.verify_integrity() is True
        assert first.package_id == second.package_id
        assert first.manifest_sha256 == second.manifest_sha256
        assert len(first.manifest_sha256) == 64
        assert manifest_trace_fields(first) == {"manifest_sha256": first.manifest_sha256}

    def test_different_file_hash_changes_the_seal(self) -> None:
        first = build_manifest_when_entries_present(_request(), (_entry(_SHA_A),))
        second = build_manifest_when_entries_present(_request(), (_entry(_SHA_B),))
        assert first is not None and second is not None
        assert first.manifest_sha256 != second.manifest_sha256
        assert first.package_id != second.package_id

    def test_replacing_a_file_hash_breaks_integrity(self) -> None:
        manifest = build_manifest_when_entries_present(_request(), (_entry(_SHA_A),))
        assert manifest is not None
        manifest.files[0] = _entry(_SHA_B)
        assert manifest.verify_integrity() is False

    def test_created_at_is_not_part_of_the_seal(self) -> None:
        manifest = build_manifest_when_entries_present(_request(), (_entry(_SHA_A),))
        assert manifest is not None
        sealed = manifest.manifest_sha256
        manifest.created_at = manifest.created_at + timedelta(days=1)
        assert manifest.verify_integrity() is True
        assert manifest.manifest_sha256 == sealed
