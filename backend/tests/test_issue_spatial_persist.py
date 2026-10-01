"""Storey, axis, gate, and remark shape survive audit-store reload."""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.finding_gate import stamp_finding_gate
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.models import (
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


class SpatialRemarkPersistTests(unittest.TestCase):
    def test_storey_axis_gate_and_remark_shape_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemAuditStore(root)
            ifc = root / "model.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            issue = stamp_finding_gate(
                ensure_finding_provenance(
                    ValidationIssue(
                        rule_id="QTO-001",
                        severity=Severity.ERROR,
                        message="Area mismatch",
                        category=FindingCategory.IFC_VALIDATION,
                        element_guid="guid-1",
                        source_id="ids-pack",
                        evidence_refs=("ids-pack#ifc:guid-1",),
                        origin="deterministic",
                        storey_name="3 этаж",
                        grid_axis="A",
                        remark=TemplateRemarkGenerator(locale="ru").generate(
                            ValidationIssue(
                                rule_id="QTO-001",
                                severity=Severity.ERROR,
                                message="Area mismatch",
                                category=FindingCategory.IFC_VALIDATION,
                                element_guid="guid-1",
                                storey_name="3 этаж",
                                grid_axis="A",
                                norm_source="СТО-1",
                                norm_clause="п. 2",
                            )
                        ),
                    )
                )
            )
            report = ValidationReport(
                report_id="a" * 32,
                request_id="spatial-round-trip",
                ifc_path=ifc,
                created_at=datetime.now(tz=UTC).isoformat(),
                requirements=(),
                issues=(issue,),
                summary=ValidationSummary(0, 1, 1, 0, False),
            )
            store.save(report)
            loaded = store.get(report.report_id)
            assert loaded is not None
            reloaded = loaded.issues[0]
            self.assertEqual(reloaded.storey_name, "3 этаж")
            self.assertEqual(reloaded.grid_axis, "A")
            self.assertEqual(reloaded.gate_class, "regulatory")
            self.assertEqual(reloaded.answer_nature, "deterministic")
            assert reloaded.remark is not None
            self.assertEqual(reloaded.remark.essence, "Area mismatch")
            self.assertEqual(reloaded.remark.clause_cite, "СТО-1 п. 2")
            self.assertTrue(reloaded.remark.clause_bound)
            self.assertEqual(reloaded.remark.storey_name, "3 этаж")
            self.assertEqual(reloaded.remark.grid_axis, "A")


if __name__ == "__main__":
    unittest.main()
