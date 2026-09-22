"""collect_file_entries: only sources with known sha256 produce entries.

Fixture/dev runs omit sha256 → empty tuple → package_id falls back to
sha256(request_id) in build_evidence_records. This is correct behaviour;
the test suite must not require file bytes to be present.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from aerobim.application.services.package_file_entries import collect_file_entries
from aerobim.domain.models import DrawingSource, RequirementSource, ValidationRequest
from aerobim.domain.package_manifest import Discipline, FileRole, UploadState


_SHA = "ab" * 32  # 64 hex chars — a plausible sha256


def _base_request(**kwargs) -> ValidationRequest:
    defaults = dict(
        request_id="req-manifest-001",
        ifc_path=None,
        requirement_source=RequirementSource(text="REQ"),
        tenant_id="tenant-x",
        project_id="proj-y",
        revision="P1",
    )
    defaults.update(kwargs)
    return ValidationRequest(**defaults)


class TestCollectFileEntries:
    def test_empty_when_no_sha256_provided(self) -> None:
        """Fixture/dev runs → empty tuple; no error."""
        request = _base_request(drawing_sources=[])
        entries = collect_file_entries(request)
        assert entries == ()

    def test_drawing_with_sha256_produces_entry(self) -> None:
        source = DrawingSource(
            path=Path("drawings/sheet-01.pdf"),
            sha256=_SHA,
        )
        request = _base_request(drawing_sources=[source])
        entries = collect_file_entries(request)
        assert len(entries) == 1
        entry = entries[0]
        assert entry.sha256 == _SHA
        assert entry.role == FileRole.DRAWING_PDF
        assert entry.logical_path == "sheet-01.pdf"
        assert entry.upload_state == UploadState.COMPLETE
        assert entry.discipline == Discipline.UNKNOWN

    def test_drawing_without_sha256_is_skipped(self) -> None:
        source = DrawingSource(
            path=Path("drawings/sheet-02.pdf"),
            sha256=None,
        )
        request = _base_request(drawing_sources=[source])
        entries = collect_file_entries(request)
        assert entries == ()

    def test_drawing_without_path_is_skipped(self) -> None:
        source = DrawingSource(
            text="some inline text",
            sha256=_SHA,
        )
        request = _base_request(drawing_sources=[source])
        entries = collect_file_entries(request)
        assert entries == ()

    def test_ifc_sha256_attribute_produces_ifc_model_entry(self) -> None:
        request = _base_request(
            ifc_path=Path("models/building.ifc"),
            drawing_sources=[],
        )
        # Simulate upload layer attaching sha256 via object attribute.
        object.__setattr__(request, "ifc_sha256", _SHA)  # type: ignore[call-arg]
        entries = collect_file_entries(request)
        assert any(e.role == FileRole.IFC_MODEL for e in entries)
        ifc_entry = next(e for e in entries if e.role == FileRole.IFC_MODEL)
        assert ifc_entry.sha256 == _SHA
        assert ifc_entry.logical_path == "building.ifc"
        assert ifc_entry.media_type == "application/x-step"

    def test_dxf_extension_produces_drawing_dxf_role(self) -> None:
        source = DrawingSource(
            path=Path("cad/floor-plan.dxf"),
            sha256=_SHA,
        )
        request = _base_request(drawing_sources=[source])
        entries = collect_file_entries(request)
        assert len(entries) == 1
        assert entries[0].role == FileRole.DRAWING_DXF
        assert entries[0].media_type == "image/vnd.dxf"

    def test_pdf_extension_produces_drawing_pdf_role(self) -> None:
        source = DrawingSource(
            path=Path("drawings/plan.pdf"),
            sha256=_SHA,
        )
        request = _base_request(drawing_sources=[source])
        entries = collect_file_entries(request)
        assert len(entries) == 1
        assert entries[0].role == FileRole.DRAWING_PDF
        assert entries[0].media_type == "application/pdf"

    def test_only_drawings_with_sha256_included(self) -> None:
        with_hash = DrawingSource(path=Path("a.pdf"), sha256=_SHA)
        without_hash = DrawingSource(path=Path("b.pdf"), sha256=None)
        with_hash2 = DrawingSource(path=Path("c.dxf"), sha256=_SHA[:64])
        request = _base_request(drawing_sources=[with_hash, without_hash, with_hash2])
        entries = collect_file_entries(request)
        assert len(entries) == 2
        paths = {e.logical_path for e in entries}
        assert "a.pdf" in paths
        assert "c.dxf" in paths
        assert "b.pdf" not in paths

    def test_entry_revision_taken_from_drawing_source_first(self) -> None:
        source = DrawingSource(
            path=Path("drawings/sheet.pdf"),
            sha256=_SHA,
            revision="R3",
        )
        request = _base_request(drawing_sources=[source], revision="P1")
        entries = collect_file_entries(request)
        assert len(entries) == 1
        assert entries[0].revision == "R3"

    def test_entry_revision_falls_back_to_request_revision(self) -> None:
        source = DrawingSource(
            path=Path("drawings/sheet.pdf"),
            sha256=_SHA,
            revision=None,
        )
        request = _base_request(drawing_sources=[source], revision="P2")
        entries = collect_file_entries(request)
        assert len(entries) == 1
        assert entries[0].revision == "P2"
