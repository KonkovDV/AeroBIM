"""Native RVT/NWD fail-closed ingest — honesty, never Autodesk-ready."""

from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.security.upload_content import (
    UploadContentError,
    reject_autodesk_zip_bytes,
    validate_upload_content,
)
from aerobim.domain.cad_ingest import NATIVE_AUTODESK_CLOSED_REASON, zip_names_indicate_autodesk
from aerobim.domain.models import (
    CapabilityState,
    DrawingSource,
    RequirementSource,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.ezdxf_cad_model_ingestor import EzdxfCadModelIngestor
from aerobim.tools.validate_native_autodesk_toolchain import probe_native_autodesk_toolchain


def _zip_bytes(*members: tuple[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in members:
            archive.writestr(name, data)
    return buffer.getvalue()


class NativeAutodeskIngestTests(unittest.TestCase):
    def test_rvt_fail_closed(self) -> None:
        ingestor = EzdxfCadModelIngestor()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "model.rvt"
            path.write_bytes(b"PK\x03\x04fake-rvt")
            result = ingestor.ingest(path)
        self.assertFalse(result.supported)
        self.assertEqual(result.format_resolved, "rvt")
        self.assertEqual(result.reason, NATIVE_AUTODESK_CLOSED_REASON)

    def test_nwd_fail_closed(self) -> None:
        ingestor = EzdxfCadModelIngestor()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "coord.nwd"
            path.write_bytes(b"\x00navisworks")
            result = ingestor.ingest(path)
        self.assertFalse(result.supported)
        self.assertEqual(result.format_resolved, "nwd")
        self.assertEqual(result.reason, NATIVE_AUTODESK_CLOSED_REASON)

    def test_package_with_rvt_forces_failed_capability(self) -> None:
        from aerobim.infrastructure.adapters.docling_requirement_extractor import (
            StructuredRequirementExtractor,
        )
        from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
        from aerobim.infrastructure.adapters.narrative_rule_synthesizer import (
            NarrativeRuleSynthesizer,
        )
        from aerobim.infrastructure.adapters.structured_drawing_analyzer import (
            StructuredDrawingAnalyzer,
        )
        from aerobim.infrastructure.adapters.template_remark_generator import (
            TemplateRemarkGenerator,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            rvt = root / "model.rvt"
            rvt.write_bytes(b"PK\x03\x04fake")
            report = AnalyzeProjectPackageUseCase(
                requirement_extractor=StructuredRequirementExtractor(),
                narrative_rule_synthesizer=NarrativeRuleSynthesizer(),
                drawing_analyzer=StructuredDrawingAnalyzer(),
                ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=InMemoryAuditStore(),
                cad_model_ingestor=EzdxfCadModelIngestor(),
            ).execute(
                ValidationRequest(
                    request_id="rvt-stakeholder-gate",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    drawing_sources=(DrawingSource(path=rvt, sheet_id="RVT1", format="rvt"),),
                )
            )

        assert report.capabilities is not None
        self.assertEqual(report.capabilities.dwg_dxf.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)
        self.assertIn("RVT/NWD", report.capabilities.dwg_dxf.reason or "")

    def test_zip_names_indicate_autodesk_members_and_revit_container(self) -> None:
        self.assertTrue(zip_names_indicate_autodesk(["nested/model.rvt"]))
        self.assertTrue(zip_names_indicate_autodesk(["BasicFileInfo"]))
        self.assertFalse(zip_names_indicate_autodesk(["markup.bcf", "viewpoint.bcfv"]))

    def test_package_with_rvt_inside_zip_without_format_forces_failed(self) -> None:
        from aerobim.infrastructure.adapters.docling_requirement_extractor import (
            StructuredRequirementExtractor,
        )
        from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
        from aerobim.infrastructure.adapters.narrative_rule_synthesizer import (
            NarrativeRuleSynthesizer,
        )
        from aerobim.infrastructure.adapters.structured_drawing_analyzer import (
            StructuredDrawingAnalyzer,
        )
        from aerobim.infrastructure.adapters.template_remark_generator import (
            TemplateRemarkGenerator,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            zipped = root / "model.zip"
            zipped.write_bytes(_zip_bytes(("nested/model.rvt", b"PK\x03\x04fake")))
            report = AnalyzeProjectPackageUseCase(
                requirement_extractor=StructuredRequirementExtractor(),
                narrative_rule_synthesizer=NarrativeRuleSynthesizer(),
                drawing_analyzer=StructuredDrawingAnalyzer(),
                ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=InMemoryAuditStore(),
                cad_model_ingestor=EzdxfCadModelIngestor(),
            ).execute(
                ValidationRequest(
                    request_id="rvt-zip-smuggle",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    drawing_sources=(DrawingSource(path=zipped, sheet_id="ZIP1"),),
                )
            )

        assert report.capabilities is not None
        self.assertEqual(report.capabilities.dwg_dxf.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)
        self.assertIn("RVT/NWD", report.capabilities.dwg_dxf.reason or "")

    def test_http_upload_explains_not_implemented(self) -> None:
        with self.assertRaises(UploadContentError) as ctx:
            validate_upload_content(filename="tower.rvt", payload=b"PK\x03\x04")
        self.assertEqual(str(ctx.exception), NATIVE_AUTODESK_CLOSED_REASON)

    def test_http_upload_rejects_zip_with_rvt_member(self) -> None:
        with self.assertRaises(UploadContentError) as ctx:
            reject_autodesk_zip_bytes(_zip_bytes(("tower.rvt", b"not-a-parser")))
        self.assertEqual(str(ctx.exception), NATIVE_AUTODESK_CLOSED_REASON)

    def test_http_upload_rejects_revit_container_renamed_zip(self) -> None:
        with self.assertRaises(UploadContentError) as ctx:
            reject_autodesk_zip_bytes(_zip_bytes(("BasicFileInfo", b"revit-container")))
        self.assertEqual(str(ctx.exception), NATIVE_AUTODESK_CLOSED_REASON)

    def test_http_upload_allows_zip_without_autodesk_members(self) -> None:
        sniffed = validate_upload_content(
            filename="pack.zip",
            payload=_zip_bytes(("markup.bcf", b"<Markup/>")),
        )
        self.assertEqual(sniffed.kind, "zip")
        reject_autodesk_zip_bytes(_zip_bytes(("markup.bcf", b"<Markup/>")))
        with self.assertRaises(UploadContentError) as ctx:
            validate_upload_content(filename="tower.rvt", payload=b"PK\x03\x04")
        self.assertEqual(str(ctx.exception), NATIVE_AUTODESK_CLOSED_REASON)

    def test_probe_never_claims_native_autodesk(self) -> None:
        payload = probe_native_autodesk_toolchain()
        self.assertEqual(payload["native_rvt_nwd"], "missing")
        self.assertEqual(payload["rvt_native"], "NOT_IMPLEMENTED")
        self.assertEqual(payload["nwd_native"], "NOT_IMPLEMENTED")
        self.assertFalse(payload["claim_allowed"])
        self.assertFalse(payload["any_ingest_supported"])
        self.assertEqual(payload["reason"], NATIVE_AUTODESK_CLOSED_REASON)


if __name__ == "__main__":
    unittest.main()
