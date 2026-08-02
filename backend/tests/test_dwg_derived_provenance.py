"""DWG conversion MVP — hash-verified derived-provenance wave.

Contract (FOUR_DIRECTION_GAP_ANALYSIS §1.3 steps 3/5/6):
- a declared ``*.derived-provenance.json`` sidecar is evidence only when both
  SHA-256 values recompute (in-toto/SLSA posture, mirrors BCF T2 binding);
- verified pair → ``dwg_dxf=NOT_VERIFIED`` (derived route, never OK);
- tampered/foreign sidecar → FAILED, strictly worse than no sidecar at all;
- no sidecar → legacy RT-D behavior (unsupported DWG fails the package).
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.cad_conversion_qa import (
    ConversionQaPolicy,
    conversion_qa_section_payload,
    evaluate_conversion_loss,
)
from aerobim.domain.derived_cad_provenance import (
    build_derived_cad_provenance,
    find_derived_provenance_sidecar,
    verify_derived_cad_provenance,
    verify_derived_provenance_sidecar,
    write_derived_provenance_sidecar,
)
from aerobim.domain.models import (
    CapabilityState,
    DrawingSource,
    RequirementSource,
    Severity,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.ezdxf_cad_model_ingestor import EzdxfCadModelIngestor
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.tools.register_dwg_conversion import main as register_main


def _minimal_uc(**kwargs: object) -> AnalyzeProjectPackageUseCase:
    base: dict[str, object] = {
        "requirement_extractor": StructuredRequirementExtractor(),
        "narrative_rule_synthesizer": NarrativeRuleSynthesizer(),
        "drawing_analyzer": StructuredDrawingAnalyzer(),
        "ifc_validator": MagicMock(validate=MagicMock(return_value=[])),
        "remark_generator": TemplateRemarkGenerator(),
        "audit_report_store": InMemoryAuditStore(),
    }
    base.update(kwargs)
    return AnalyzeProjectPackageUseCase(**base)  # type: ignore[arg-type]


def _write_pair(root: Path) -> tuple[Path, Path]:
    source = root / "plan.dwg"
    derived = root / "plan.pdf"
    source.write_bytes(b"AC1032 fake dwg bytes")
    derived.write_bytes(b"%PDF-1.4 fake derived sheet")
    return source, derived


def _register_verified_sidecar(
    source: Path, derived: Path, *, qa_section: dict[str, object] | None = None
) -> Path:
    provenance = build_derived_cad_provenance(
        source_dwg=source,
        derived=derived,
        derived_format="pdf",
        conversion_tool="external-converter",
        conversion_tool_version="1.0.0",
    )
    sidecar = write_derived_provenance_sidecar(provenance, source)
    if qa_section is not None:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        payload["conversion_qa"] = qa_section
        sidecar.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return sidecar


class DerivedProvenanceVerificationTests(unittest.TestCase):
    def test_valid_pair_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, derived = _write_pair(Path(tmp))
            sidecar = _register_verified_sidecar(source, derived)
            result = verify_derived_provenance_sidecar(sidecar)
        self.assertTrue(result.verified)
        self.assertEqual(result.mismatches, ())
        assert result.provenance is not None
        self.assertEqual(result.provenance.derived_format, "pdf")

    def test_tampered_derived_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, derived = _write_pair(Path(tmp))
            sidecar = _register_verified_sidecar(source, derived)
            derived.write_bytes(b"%PDF-1.4 TAMPERED after registration")
            result = verify_derived_provenance_sidecar(sidecar)
        self.assertFalse(result.verified)
        self.assertTrue(any("derived artifact" in mismatch for mismatch in result.mismatches))

    def test_missing_hash_fields_are_mandatory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, derived = _write_pair(Path(tmp))
            # source_dwg=None → source hash absent → never verified.
            provenance = build_derived_cad_provenance(
                source_dwg=None,
                derived=derived,
                derived_format="pdf",
            )
            result = verify_derived_cad_provenance(provenance, base_dir=Path(tmp))
        self.assertFalse(result.verified)
        self.assertTrue(any("mandatory" in mismatch for mismatch in result.mismatches))

    def test_path_jail_blocks_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            outside = root / "outside.pdf"
            outside.write_bytes(b"%PDF-1.4 outside jail")
            source = package_dir / "plan.dwg"
            source.write_bytes(b"AC1032")
            provenance = build_derived_cad_provenance(
                source_dwg=source,
                derived=outside,
                derived_format="pdf",
            )
            result = verify_derived_cad_provenance(provenance, base_dir=package_dir)
        self.assertFalse(result.verified)
        self.assertTrue(any("path jail" in mismatch for mismatch in result.mismatches))

    def test_unreadable_sidecar_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = Path(tmp) / "plan.dwg.derived-provenance.json"
            sidecar.write_text("{not json", encoding="utf-8")
            result = verify_derived_provenance_sidecar(sidecar)
        self.assertFalse(result.verified)
        self.assertTrue(any("unreadable" in mismatch for mismatch in result.mismatches))

    def test_find_sidecar_naming_convention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, derived = _write_pair(Path(tmp))
            self.assertIsNone(find_derived_provenance_sidecar(source))
            sidecar = _register_verified_sidecar(source, derived)
            self.assertEqual(find_derived_provenance_sidecar(source), sidecar)
            self.assertEqual(sidecar.name, "plan.dwg.derived-provenance.json")


class ConversionQaTests(unittest.TestCase):
    def test_no_loss_is_ok(self) -> None:
        report = evaluate_conversion_loss(
            expected_sheets=("AR-01",),
            expected_layers=("WALLS", "DIMS"),
            observed_sheets=("ar-01",),
            observed_layers=("walls", "DIMS"),
        )
        self.assertEqual(report.status, "ok")
        self.assertEqual(report.layer_loss_ratio, 0.0)

    def test_missing_sheet_fails_by_default(self) -> None:
        report = evaluate_conversion_loss(
            expected_sheets=("AR-01", "AR-02"),
            expected_layers=(),
            observed_sheets=("AR-01",),
            observed_layers=(),
        )
        self.assertEqual(report.status, "failed")
        self.assertEqual(report.missing_sheets, ("AR-02",))

    def test_layer_loss_within_policy_warns(self) -> None:
        report = evaluate_conversion_loss(
            expected_sheets=(),
            expected_layers=("A", "B", "C", "D"),
            observed_sheets=(),
            observed_layers=("A", "B", "C"),
        )
        self.assertEqual(report.status, "failed")  # strict default: any loss fails
        tolerant = evaluate_conversion_loss(
            expected_sheets=(),
            expected_layers=("A", "B", "C", "D"),
            observed_sheets=(),
            observed_layers=("A", "B", "C"),
            policy=ConversionQaPolicy(max_layer_loss_ratio=0.5),
        )
        self.assertEqual(tolerant.status, "warning")
        self.assertAlmostEqual(tolerant.layer_loss_ratio, 0.25)

    def test_sidecar_qa_failed_rejects_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, derived = _write_pair(Path(tmp))
            qa = conversion_qa_section_payload(
                expected_sheets=("AR-01", "AR-02"),
                expected_layers=(),
                observed_sheets=("AR-01",),
                observed_layers=(),
                policy=ConversionQaPolicy(),
            )
            sidecar = _register_verified_sidecar(source, derived, qa_section=qa)
            result = verify_derived_provenance_sidecar(sidecar)
        self.assertFalse(result.verified)
        self.assertTrue(any("conversion QA failed" in m for m in result.mismatches))

    def test_sidecar_qa_status_field_cannot_whitewash(self) -> None:
        # A hand-written "status": "ok" inside conversion_qa must be ignored:
        # the verdict is recomputed from inventories.
        with tempfile.TemporaryDirectory() as tmp:
            source, derived = _write_pair(Path(tmp))
            qa = conversion_qa_section_payload(
                expected_sheets=("AR-01", "AR-02"),
                expected_layers=(),
                observed_sheets=("AR-01",),
                observed_layers=(),
                policy=ConversionQaPolicy(),
            )
            qa["status"] = "ok"
            sidecar = _register_verified_sidecar(source, derived, qa_section=qa)
            result = verify_derived_provenance_sidecar(sidecar)
        self.assertFalse(result.verified)

    def test_malformed_qa_section_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, derived = _write_pair(Path(tmp))
            sidecar = _register_verified_sidecar(
                source, derived, qa_section={"expected_sheets": "not-a-list"}
            )
            result = verify_derived_provenance_sidecar(sidecar)
        self.assertFalse(result.verified)
        self.assertTrue(any("malformed" in m for m in result.mismatches))


class AnalyzeDerivedRouteTests(unittest.TestCase):
    def _run_package(self, root: Path) -> object:
        ifc = root / "m.ifc"
        ifc.write_text("ISO-10303-21;", encoding="utf-8")
        uc = _minimal_uc(cad_model_ingestor=EzdxfCadModelIngestor())
        return uc.execute(
            ValidationRequest(
                request_id="dwg-derived-route",
                ifc_path=ifc,
                requirement_source=RequirementSource(
                    text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                ),
                drawing_sources=(DrawingSource(path=root / "plan.dwg", sheet_id="DWG1"),),
            )
        )

    def test_impossible_supported_dwg_fails_closed(self) -> None:
        """Misconfigured ingestor returning supported+dwg must never look OK."""

        class _BrokenDwgIngestor:
            def ingest(self, path, *, sheet_id=None):
                from aerobim.domain.cad_ingest import CadIngestResult

                return CadIngestResult(
                    annotations=(),
                    format_resolved="dwg",
                    entity_count=0,
                    degraded=False,
                    supported=True,
                    reason=None,
                )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "plan.dwg"
            source.write_bytes(b"AC1032")
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            report = _minimal_uc(cad_model_ingestor=_BrokenDwgIngestor()).execute(
                ValidationRequest(
                    request_id="dwg-impossible-supported",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    drawing_sources=(DrawingSource(path=source, sheet_id="DWG1"),),
                )
            )
        capability = report.capabilities.dwg_dxf  # type: ignore[attr-defined]
        self.assertEqual(capability.status, CapabilityState.FAILED)
        self.assertNotEqual(capability.status, CapabilityState.OK)
        impossible = [
            issue
            for issue in report.issues  # type: ignore[attr-defined]
            if issue.rule_id == "AEROBIM-CAD-DWG-IMPOSSIBLE-SUPPORTED"
        ]
        self.assertEqual(len(impossible), 1)

    def test_verified_sidecar_registers_derived_route_never_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, derived = _write_pair(root)
            _register_verified_sidecar(source, derived)
            report = self._run_package(root)
        assert report.capabilities is not None  # type: ignore[attr-defined]
        capability = report.capabilities.dwg_dxf  # type: ignore[attr-defined]
        self.assertEqual(capability.status, CapabilityState.NOT_VERIFIED)
        self.assertNotEqual(capability.status, CapabilityState.OK)
        self.assertIn("hash-verified derived substitute", capability.reason or "")
        registration = [
            issue
            for issue in report.issues  # type: ignore[attr-defined]
            if issue.rule_id == "AEROBIM-CAD-DWG-DERIVED"
        ]
        self.assertEqual(len(registration), 1)
        self.assertIs(registration[0].severity, Severity.INFO)
        self.assertIn("native DWG is not parsed", registration[0].message)
        self.assertTrue(
            any(ref.startswith("source_dwg_sha256:") for ref in registration[0].evidence_refs)
        )

    def test_tampered_sidecar_fails_package_dwg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, derived = _write_pair(root)
            _register_verified_sidecar(source, derived)
            derived.write_bytes(b"TAMPERED")
            report = self._run_package(root)
        capability = report.capabilities.dwg_dxf  # type: ignore[attr-defined]
        self.assertEqual(capability.status, CapabilityState.FAILED)
        self.assertIn("hash verification", capability.reason or "")
        warnings = [
            issue
            for issue in report.issues  # type: ignore[attr-defined]
            if issue.rule_id == "AEROBIM-CAD-DWG-DERIVED"
        ]
        self.assertEqual(len(warnings), 1)
        self.assertIs(warnings[0].severity, Severity.WARNING)

    def test_no_sidecar_keeps_legacy_rt_d_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "plan.dwg"
            source.write_bytes(b"AC1032")
            report = self._run_package(root)
        capability = report.capabilities.dwg_dxf  # type: ignore[attr-defined]
        self.assertEqual(capability.status, CapabilityState.FAILED)

    def test_qa_warning_keeps_route_and_surfaces_loss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, derived = _write_pair(root)
            qa = conversion_qa_section_payload(
                expected_sheets=(),
                expected_layers=("A", "B", "C", "D"),
                observed_sheets=(),
                observed_layers=("A", "B", "C"),
                policy=ConversionQaPolicy(max_layer_loss_ratio=0.5),
            )
            _register_verified_sidecar(source, derived, qa_section=qa)
            report = self._run_package(root)
        capability = report.capabilities.dwg_dxf  # type: ignore[attr-defined]
        self.assertEqual(capability.status, CapabilityState.NOT_VERIFIED)
        qa_issues = [
            issue
            for issue in report.issues  # type: ignore[attr-defined]
            if issue.rule_id == "AEROBIM-CAD-DWG-QA"
        ]
        self.assertEqual(len(qa_issues), 1)
        self.assertIs(qa_issues[0].severity, Severity.WARNING)
        self.assertIn("layer loss", qa_issues[0].message)

    def test_qa_failed_rejects_derived_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, derived = _write_pair(root)
            qa = conversion_qa_section_payload(
                expected_sheets=("AR-01", "AR-02"),
                expected_layers=(),
                observed_sheets=("AR-01",),
                observed_layers=(),
                policy=ConversionQaPolicy(),
            )
            _register_verified_sidecar(source, derived, qa_section=qa)
            report = self._run_package(root)
        capability = report.capabilities.dwg_dxf  # type: ignore[attr-defined]
        self.assertEqual(capability.status, CapabilityState.FAILED)
        self.assertIn("conversion QA failed", capability.reason or "")


class RegisterDwgConversionCliTests(unittest.TestCase):
    def test_cli_roundtrip_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, derived = _write_pair(Path(tmp))
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = register_main(
                    [
                        "--source-dwg",
                        str(source),
                        "--derived",
                        str(derived),
                        "--derived-format",
                        "pdf",
                        "--tool",
                        "oda-file-converter",
                        "--tool-version",
                        "26.4",
                    ]
                )
            payload = json.loads(buffer.getvalue())
            sidecar = Path(payload["sidecar_path"])
            self.assertTrue(sidecar.is_file())
            self.assertTrue(verify_derived_provenance_sidecar(sidecar).verified)
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["verified"])
        self.assertIn("dwg_dxf never OK", payload["claim_boundary"])

    def test_cli_missing_source_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            derived = Path(tmp) / "plan.pdf"
            derived.write_bytes(b"%PDF-1.4")
            exit_code = register_main(
                [
                    "--source-dwg",
                    str(Path(tmp) / "absent.dwg"),
                    "--derived",
                    str(derived),
                    "--derived-format",
                    "pdf",
                ]
            )
        self.assertEqual(exit_code, 1)

    def test_cli_qa_loss_fails_registration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, derived = _write_pair(Path(tmp))
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = register_main(
                    [
                        "--source-dwg",
                        str(source),
                        "--derived",
                        str(derived),
                        "--derived-format",
                        "pdf",
                        "--expected-sheet",
                        "AR-01",
                        "--expected-sheet",
                        "AR-02",
                        "--observed-sheet",
                        "AR-01",
                    ]
                )
            payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["verified"])
        self.assertEqual(payload["conversion_qa_status"], "failed")


if __name__ == "__main__":
    unittest.main()
