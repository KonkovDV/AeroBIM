"""Regression: DWG / MEP / calc / BCF→СОД honesty — never false-positive claims."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.domain.cad_ingest import NATIVE_DWG_MISSING_REASON
from aerobim.domain.calculation_evidence import (
    FORBIDDEN_CALC_CLAIM_PHRASES,
    independent_solver_not_implemented_payload,
)
from aerobim.domain.derived_cad_provenance import build_derived_cad_provenance
from aerobim.domain.errors import HonestyCapabilityError
from aerobim.domain.mep import (
    FederatedMepScope,
    UnconfiguredMepSystemGraphProvider,
)
from aerobim.domain.mep_intake import assess_mep_customer_intake
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ReportCapabilities,
)
from aerobim.domain.system_capabilities import (
    assert_honesty_capabilities_not_silently_ok,
    build_four_direction_contracts,
    build_system_capabilities_payload,
    enforce_honesty_capabilities,
    load_bcf_t2_status_snapshot,
)
from aerobim.infrastructure.adapters.ezdxf_cad_model_ingestor import EzdxfCadModelIngestor
from aerobim.infrastructure.adapters.oda_cad_model_ingestor import OdaCadModelIngestor
from aerobim.tools.verify_bcf_t2_evidence import verify_bcf_t2_evidence_dir

REPO = Path(__file__).resolve().parents[2]
MATRIX_TEMPLATE = REPO / "samples" / "mep" / "clearance-matrix-template.json"
MATRIX_SCHEMA = REPO / "samples" / "mep" / "clearance-matrix.schema.json"
CDE_PROOF = REPO / "audit" / "evidence" / "cde-import-proof"


class NativeDwgHonestyTests(unittest.TestCase):
    def test_native_dwg_never_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.dwg"
            path.write_bytes(b"AC1015fake")
            result = EzdxfCadModelIngestor().ingest(path)
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, NATIVE_DWG_MISSING_REASON)
        with self.assertRaises(AssertionError):
            assert_honesty_capabilities_not_silently_ok(
                ReportCapabilities(
                    dwg_dxf=CapabilityStatus(CapabilityState.OK, "dwg_dxf=ok forbidden")
                )
            )

    def test_oda_stub_does_not_flip_positive_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.dwg"
            path.write_bytes(b"AC1015fake")
            disabled = OdaCadModelIngestor(enabled=False).ingest(path)
            enabled = OdaCadModelIngestor(enabled=True).ingest(path)
        self.assertFalse(disabled.supported)
        self.assertFalse(enabled.supported)
        self.assertEqual(disabled.reason, NATIVE_DWG_MISSING_REASON)
        self.assertEqual(enabled.reason, NATIVE_DWG_MISSING_REASON)
        caps = ReportCapabilities(dwg_dxf=CapabilityStatus(CapabilityState.FAILED, enabled.reason))
        enforce_honesty_capabilities(caps)
        policy = build_signoff_policy(profile="development")
        self.assertFalse(
            policy.summary_passed(error_count=0, capabilities=caps),
            "FAILED dwg_dxf must block summary.passed",
        )

    def test_unsupported_suffix_not_silent_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.xyz"
            path.write_text("not-cad", encoding="utf-8")
            result = EzdxfCadModelIngestor().ingest(path)
        self.assertFalse(result.supported)
        self.assertTrue(result.degraded)
        self.assertIn("Unsupported", result.reason or "")

    def test_derived_file_requires_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.dwg"
            derived = Path(tmp) / "sheet.pdf"
            source.write_bytes(b"AC1015")
            derived.write_bytes(b"%PDF-1.4 fake")
            prov = build_derived_cad_provenance(
                source_dwg=source,
                derived=derived,
                derived_format="pdf",
                conversion_tool="external-converter",
                conversion_tool_version="1.0.0",
            )
        self.assertIsNotNone(prov.source_dwg_sha256)
        self.assertIsNotNone(prov.derived_sha256)
        self.assertEqual(prov.derived_format, "pdf")
        self.assertTrue(prov.loss_notes)
        self.assertNotEqual(prov.derived_format, "dwg")

    def test_conversion_missing_blocks_required_dwg_pass(self) -> None:
        caps = ReportCapabilities(
            dwg_dxf=CapabilityStatus(
                CapabilityState.FAILED,
                "DWG conversion failed; derived PDF/IFC unavailable",
            )
        )
        policy = build_signoff_policy(profile="samolet_pilot")
        self.assertFalse(policy.summary_passed(error_count=0, capabilities=caps))


class MepHonestyTests(unittest.TestCase):
    def test_unconfigured_provider_raises_gap(self) -> None:
        provider = UnconfiguredMepSystemGraphProvider()
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "mep.ifc"
            fake.write_text("ISO-10303-21;", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "MEP-CLASH-001"):
                provider.build_graph(fake)

    def test_intake_blocked_without_customer_scope(self) -> None:
        result = assess_mep_customer_intake(None, matrix_path_exists=False, matrix_synthetic=True)
        self.assertEqual(result.status, "blocked_customer_data")
        self.assertTrue(result.affects_pass)
        self.assertIn("federated MEP", result.reason)

    def test_fixture_scope_stays_fixture_only(self) -> None:
        scope = FederatedMepScope(
            schema_version="1.0.0",
            status="ENG_FIXTURE",
            federated_ifc_paths=("samples/mep/hvac-sprinkler-systems.ifc",),
            scope_memo_ref="memo",
            clearance_matrix_ref="samples/mep/clearance-matrix-template.json",
            claim_boundary="engineering fixture",
        )
        result = assess_mep_customer_intake(scope, matrix_path_exists=True, matrix_synthetic=True)
        self.assertEqual(result.status, "fixture_only")
        self.assertFalse(result.ready)

    def test_mep_system_clash_never_ok_on_honesty(self) -> None:
        with self.assertRaises(HonestyCapabilityError):
            enforce_honesty_capabilities(
                ReportCapabilities(
                    mep_system_clash=CapabilityStatus(CapabilityState.OK, "fake full MEP")
                )
            )

    def test_require_mep_blocks_pass_when_not_verified(self) -> None:
        caps = ReportCapabilities()
        self.assertEqual(caps.mep_system_clash.status, CapabilityState.NOT_VERIFIED)
        policy = build_signoff_policy(profile="samolet_pilot", require_mep_system_clash=True)
        self.assertFalse(policy.summary_passed(error_count=0, capabilities=caps))

    def test_clearance_matrix_schema_validates_template(self) -> None:
        try:
            import jsonschema
        except ModuleNotFoundError:
            self.skipTest("jsonschema not installed")
        schema = json.loads(MATRIX_SCHEMA.read_text(encoding="utf-8"))
        template = json.loads(MATRIX_TEMPLATE.read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(template))
        self.assertEqual(errors, [], [e.message for e in errors])
        pair = template["pairs"][0]
        self.assertIn("source_discipline", pair)
        self.assertIn("expected_result", pair)
        self.assertTrue(template.get("synthetic"))


class CalculationHonestyTests(unittest.TestCase):
    def test_independent_solver_payload(self) -> None:
        payload = independent_solver_not_implemented_payload()
        self.assertEqual(payload["status"], "not_implemented")
        self.assertEqual(payload["claim"], "evidence_consistency_only")
        self.assertTrue(payload["affects_pass"])

    def test_forbidden_claim_phrases_blocked(self) -> None:
        self.assertIn("calculation_correctness_verified", FORBIDDEN_CALC_CLAIM_PHRASES)
        payload = build_system_capabilities_payload()
        for phrase in (
            "calculation_correctness_verified",
            "DWG-ready",
            "dwg_supported",
            "CDE_READY",
        ):
            self.assertIn(phrase, payload["forbidden_claim_phrases"])
        self.assertNotIn(
            "calculation_correctness_verified",
            json.dumps(payload["honesty"]),
        )

    def test_calculation_correctness_never_ok(self) -> None:
        with self.assertRaises(HonestyCapabilityError):
            enforce_honesty_capabilities(
                ReportCapabilities(
                    calculation_correctness=CapabilityStatus(
                        CapabilityState.OK, "calculation_correctness_verified"
                    )
                )
            )


class BcfT2HonestyTests(unittest.TestCase):
    def test_repo_t2_remains_not_verified(self) -> None:
        snap = load_bcf_t2_status_snapshot()
        self.assertEqual(snap["status"], "not_verified")
        self.assertFalse(snap["claim_allowed"])
        report = verify_bcf_t2_evidence_dir(CDE_PROOF)
        self.assertEqual(report["status"], "not_verified")
        self.assertFalse(report["claim_allowed"])
        self.assertEqual(report["tier"], "T2")

    def test_partial_import_without_screenshot_not_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "import-log.txt").write_text("import ok", encoding="utf-8")
            (root / "hashes.json").write_text('{"bcf":"abc"}', encoding="utf-8")
            (root / "STATUS.json").write_text(
                json.dumps({"status": "VERIFIED", "claim_allowed": True}),
                encoding="utf-8",
            )
            report = verify_bcf_t2_evidence_dir(root)
        self.assertEqual(report["status"], "not_verified")
        self.assertIn("screenshot.png", report["missing_files"])

    def test_incompatible_status_not_cde_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "import-log.txt").write_text("x", encoding="utf-8")
            (root / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (root / "hashes.json").write_text('{"a":"1"}', encoding="utf-8")
            (root / "STATUS.json").write_text(
                json.dumps({"status": "PARTIAL", "claim_allowed": True}),
                encoding="utf-8",
            )
            report = verify_bcf_t2_evidence_dir(root)
        self.assertFalse(report["claim_allowed"])
        self.assertNotEqual(report["status"], "available")


class UnifiedContractTests(unittest.TestCase):
    def test_direction_contracts_shape(self) -> None:
        rows = build_four_direction_contracts()
        required = {
            "capability",
            "status",
            "evidence_level",
            "affects_pass",
            "reason",
            "dependencies",
            "claim_boundary",
            "evidence_refs",
        }
        by_name = {row["capability"]: row for row in rows}
        self.assertEqual(by_name["native_dwg"]["status"], "missing")
        self.assertEqual(by_name["dxf_ingest"]["status"], "partial")
        self.assertEqual(
            by_name["dwg_derived_pdf_ifc_route"]["status"],
            "partial",
        )
        self.assertIn("available_as_derived_input", by_name["dwg_derived_pdf_ifc_route"]["reason"])
        self.assertIn("not dwg_supported", by_name["dwg_derived_pdf_ifc_route"]["reason"])
        self.assertNotEqual(by_name["dwg_derived_pdf_ifc_route"]["status"], "available")
        boundary = by_name["dwg_derived_pdf_ifc_route"]["claim_boundary"]
        self.assertIn("not DWG support", boundary)
        self.assertEqual(by_name["mep_system_aware_rules"]["status"], "blocked_customer_data")
        self.assertEqual(by_name["mep_system_graph"]["status"], "fixture_only")
        self.assertEqual(by_name["calculation_correctness"]["status"], "not_implemented")
        self.assertEqual(by_name["bcf_21_export"]["status"], "available")
        self.assertEqual(by_name["bcf_t1_structural"]["status"], "available")
        self.assertEqual(by_name["bcf_cde_t2_import"]["status"], "not_verified")
        for row in rows:
            self.assertEqual(required, set(row.keys()))
            self.assertNotEqual(row["status"], "ok")
            if row["evidence_level"] == "fixture":
                self.assertNotEqual(row["status"], "available")

    def test_failed_capability_blocks_summary_passed(self) -> None:
        caps = ReportCapabilities(
            clash=CapabilityStatus(CapabilityState.FAILED, "required clash missing"),
        )
        policy = build_signoff_policy(profile="samolet_pilot")
        self.assertFalse(policy.summary_passed(error_count=0, capabilities=caps))


if __name__ == "__main__":
    unittest.main()
