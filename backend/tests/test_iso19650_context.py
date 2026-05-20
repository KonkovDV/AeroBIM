from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import RequirementSource, ValidationRequest
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore


class Iso19650ContextTests(unittest.TestCase):
    def test_validation_request_carries_optional_iso_fields(self) -> None:
        request = ValidationRequest(
            request_id="iso-req-001",
            ifc_path=Path("sample.ifc"),
            requirement_source=RequirementSource(text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"),
            stage="S2",
            information_container_id="cde-container-001",
            revision="P-01",
            doc_status="Shared",
        )
        self.assertEqual(request.stage, "S2")
        self.assertEqual(request.information_container_id, "cde-container-001")
        self.assertEqual(request.revision, "P-01")
        self.assertEqual(request.doc_status, "Shared")

    def test_audit_store_roundtrips_iso_fields(self) -> None:
        from aerobim.domain.models import ValidationReport, ValidationSummary
        from uuid import uuid4

        with tempfile.TemporaryDirectory() as tmp:
            storage_dir = Path(tmp)
            store = FilesystemAuditStore(
                storage_dir=storage_dir,
                object_store=LocalObjectStore(storage_dir / "objects"),
            )
            report = ValidationReport(
                report_id=uuid4().hex,
                request_id="iso-req-002",
                ifc_path=Path("missing.ifc"),
                created_at="2026-05-20T12:00:00+00:00",
                requirements=(),
                issues=(),
                summary=ValidationSummary(
                    requirement_count=0,
                    issue_count=0,
                    error_count=0,
                    warning_count=0,
                    passed=True,
                ),
                stage="S1",
                information_container_id="cde-002",
                revision="R2",
                doc_status="WIP",
            )
            store.save(report)
            loaded = store.get(report.report_id)
            assert loaded is not None
            self.assertEqual(loaded.stage, "S1")
            self.assertEqual(loaded.information_container_id, "cde-002")
            self.assertEqual(loaded.revision, "R2")
            self.assertEqual(loaded.doc_status, "WIP")


if __name__ == "__main__":
    unittest.main()
