"""Post-Phase-10 residuals: tenant object keys, advisory ERROR isolation, zip/path fuzz."""

from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.security.path_jail import PathJailError, resolve_storage_path
from aerobim.core.security.zip_limits import ZipBombError, inspect_zip_bytes
from aerobim.domain.models import (
    FindingCategory,
    RequirementSource,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


def _minimal_uc(**kwargs: object) -> AnalyzeProjectPackageUseCase:
    base = {
        "requirement_extractor": StructuredRequirementExtractor(),
        "narrative_rule_synthesizer": NarrativeRuleSynthesizer(),
        "drawing_analyzer": StructuredDrawingAnalyzer(),
        "ifc_validator": MagicMock(validate=MagicMock(return_value=[])),
        "remark_generator": TemplateRemarkGenerator(),
        "audit_report_store": InMemoryAuditStore(),
    }
    base.update(kwargs)
    return AnalyzeProjectPackageUseCase(**base)  # type: ignore[arg-type]


class TenantObjectKeyTests(unittest.TestCase):
    def test_ifc_object_key_prefixed_by_tenant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = FilesystemAuditStore(root)
            ifc = root / "model.ifc"
            ifc.write_text("ISO-10303-21;\n", encoding="utf-8")
            report_id = uuid4().hex
            report = ValidationReport(
                report_id=report_id,
                request_id="r1",
                ifc_path=ifc,
                created_at=datetime.now(tz=UTC).isoformat(),
                requirements=(),
                issues=(),
                summary=ValidationSummary(0, 0, 0, 0, True),
                tenant_id="tenant-a",
            )
            store.save(report)
            loaded = store.get(report_id)
            assert loaded is not None
            self.assertIsNotNone(loaded.ifc_object_key)
            assert loaded.ifc_object_key is not None
            self.assertTrue(
                loaded.ifc_object_key.startswith(f"tenants/tenant-a/ifc-sources/{report_id}/")
            )


class AdvisoryErrorMatrixTests(unittest.TestCase):
    def test_advisory_error_does_not_change_passed_or_engine_errors(self) -> None:
        class _Agent:
            def run(self, _request: ValidationRequest):
                return MagicMock(
                    advisory_issues=(
                        ValidationIssue(
                            rule_id="ADV-HALLUCINATION",
                            severity=Severity.ERROR,
                            message="advisory must not block",
                            category=FindingCategory.IFC_VALIDATION,
                            origin="advisory",
                            source_id="compliance-agent",
                        ),
                    ),
                    ids_draft=None,
                )

        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;\n", encoding="utf-8")
            request = ValidationRequest(
                request_id="adv-on",
                ifc_path=ifc,
                requirement_source=RequirementSource(
                    text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n",
                    source_kind=SourceKind.STRUCTURED_TEXT,
                ),
            )
            uc_on = _minimal_uc(compliance_agent=_Agent())
            report_on = uc_on.execute(request)
            uc_off = _minimal_uc(compliance_agent=None)
            report_off = uc_off.execute(
                ValidationRequest(
                    request_id="adv-off",
                    ifc_path=ifc,
                    requirement_source=request.requirement_source,
                )
            )

        self.assertEqual(report_on.summary.passed, report_off.summary.passed)
        self.assertEqual(report_on.summary.error_count, report_off.summary.error_count)
        on_errors = [i for i in report_on.issues if i.severity is Severity.ERROR]
        self.assertTrue(all(i.origin != "advisory" for i in on_errors))

    def test_determinism_gate_demotes_advisory_error(self) -> None:
        reconciled, _ = DeterminismGate().reconcile(
            engine_issues=(),
            advisory_issues=(
                ValidationIssue(
                    rule_id="ADV-1",
                    severity=Severity.ERROR,
                    message="noise",
                    category=FindingCategory.IFC_VALIDATION,
                    origin="advisory",
                ),
            ),
        )
        self.assertEqual(sum(1 for i in reconciled if i.severity is Severity.ERROR), 0)
        self.assertTrue(any(i.severity is Severity.INFO for i in reconciled))


class ZipAndPathAdversarialTests(unittest.TestCase):
    def test_zip_too_many_members(self) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(10):
                zf.writestr(f"m{i}.txt", b"x")
        with self.assertRaises(ZipBombError):
            inspect_zip_bytes(buf.getvalue(), max_members=5)

    def test_zip_member_too_large(self) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("big.bin", b"a" * 2048)
        with self.assertRaises(ZipBombError):
            inspect_zip_bytes(buf.getvalue(), max_member_bytes=1024)

    def test_path_jail_double_dot_segments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            with self.assertRaises(PathJailError):
                resolve_storage_path("uploads/../../etc/passwd", base=base)
            with self.assertRaises(PathJailError):
                resolve_storage_path("uploads/foo/../../../escape.ifc", base=base)


if __name__ == "__main__":
    unittest.main()
