from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.cad_ingest import CadIngestResult
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ReportCapabilities,
    RequirementSource,
    SourceKind,
)
from aerobim.domain.system_capabilities import assert_honesty_capabilities_not_silently_ok
from aerobim.infrastructure.adapters.docling_office_document_ingestor import (
    DoclingOfficeDocumentIngestor,
)
from aerobim.infrastructure.adapters.ezdxf_cad_model_ingestor import EzdxfCadModelIngestor
from aerobim.infrastructure.di.bootstrap import bootstrap_container


class CadOfficeIngestTests(unittest.TestCase):
    def test_dwg_fail_closed_without_oda(self) -> None:
        ingestor = EzdxfCadModelIngestor()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "model.dwg"
            path.write_bytes(b"AC1015fake")
            result = ingestor.ingest(path)
        self.assertIsInstance(result, CadIngestResult)
        self.assertFalse(result.supported)
        self.assertEqual(result.format_resolved, "dwg")
        self.assertIn("ODA", result.reason or "")

    def test_dxf_without_ezdxf_reports_degraded(self) -> None:
        ingestor = EzdxfCadModelIngestor()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "sheet.dxf"
            path.write_text("0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF\n", encoding="utf-8")
            result = ingestor.ingest(path)
        # Either ezdxf missing (degraded) or installed (may parse empty).
        self.assertEqual(result.format_resolved, "dxf")
        if not result.supported:
            self.assertTrue(result.degraded)
            self.assertTrue(result.reason)

    def test_dxf_with_ezdxf_extracts_text_when_installed(self) -> None:
        try:
            import ezdxf
        except ModuleNotFoundError:
            self.skipTest("ezdxf optional extra not installed")

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "annotated.dxf"
            doc = ezdxf.new()
            msp = doc.modelspace()
            msp.add_text("WALL-THK 200", dxfattribs={"insert": (10.0, 20.0)})
            doc.saveas(path)
            result = EzdxfCadModelIngestor().ingest(path, sheet_id="A-101")

        self.assertTrue(result.supported)
        self.assertGreaterEqual(len(result.annotations), 1)
        self.assertEqual(result.annotations[0].sheet_id, "A-101")
        self.assertIn("200", result.annotations[0].observed_value)

    def test_office_text_ingest(self) -> None:
        ingestor = DoclingOfficeDocumentIngestor()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "spec.txt"
            path.write_text("R1|IFCWALL|Pset|Thickness|200\n", encoding="utf-8")
            source = ingestor.ingest(path)
        self.assertIsInstance(source, RequirementSource)
        self.assertIn("R1|", source.text)
        self.assertEqual(source.source_kind, SourceKind.STRUCTURED_TEXT)

    def test_office_docx_requires_docling(self) -> None:
        ingestor = DoclingOfficeDocumentIngestor()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "brief.docx"
            path.write_bytes(b"PK\x03\x04fake")
            try:
                import docling  # noqa: F401
            except ModuleNotFoundError:
                with self.assertRaisesRegex(RuntimeError, "Docling"):
                    ingestor.ingest(path)
            else:
                # Docling installed: may succeed or fail on corrupt zip — either is fine.
                try:
                    ingestor.ingest(path)
                except Exception:  # noqa: BLE001
                    pass

    def test_dwg_dxf_honesty_allows_not_verified_forbids_ok(self) -> None:
        assert_honesty_capabilities_not_silently_ok(
            ReportCapabilities(
                dwg_dxf=CapabilityStatus(CapabilityState.NOT_VERIFIED, "DXF via ezdxf; DWG missing")
            )
        )
        with self.assertRaises(AssertionError):
            assert_honesty_capabilities_not_silently_ok(
                ReportCapabilities(dwg_dxf=CapabilityStatus(CapabilityState.OK, "fake"))
            )

    def test_bootstrap_registers_new_tokens(self) -> None:
        tmp = tempfile.mkdtemp()
        settings = Settings(
            application_name="test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(tmp) / "var",
            debug=True,
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        container = bootstrap_container(settings)
        self.assertTrue(container.is_registered(Tokens.MEP_SYSTEM_GRAPH_PROVIDER))
        self.assertTrue(container.is_registered(Tokens.CAD_MODEL_INGESTOR))
        self.assertTrue(container.is_registered(Tokens.OFFICE_DOCUMENT_INGESTOR))
        self.assertTrue(container.is_registered(Tokens.DETERMINISM_GATE))
        provider = container.resolve(Tokens.MEP_SYSTEM_GRAPH_PROVIDER)
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake = Path(temporary_directory) / "mep.ifc"
            fake.write_text("ISO-10303-21;", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "MEP-CLASH-001"):
                provider.build(fake)


if __name__ == "__main__":
    unittest.main()
