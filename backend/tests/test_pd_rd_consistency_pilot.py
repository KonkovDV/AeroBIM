"""PD/RD wall-width source-contradiction pilot (synthetic)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.drawing_ifc_consistency import (
    RULE_AMBIGUOUS,
    RULE_ID,
    RULE_INCOMPLETE,
    RULE_REVISION_MIXED,
    RULE_VERSION,
    IfcQuantityObservation,
    compare_drawing_length_to_ifc,
    parse_annotation_length,
)
from aerobim.domain.models import (
    CapabilityState,
    ConflictKind,
    DrawingAnnotation,
    DrawingSource,
    ProblemZone,
    RequirementSource,
    Severity,
    SourceKind,
    ValidationRequest,
)
from aerobim.domain.quantity import parse_quantity
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.benchmark_project_package import load_benchmark_pack
from aerobim.tools.ensure_pd_rd_pilot_drawings import ensure_pilot_drawings
from aerobim.tools.run_pd_rd_consistency_pilot import VARIANTS, run_pd_rd_consistency_pilot

_REPO = Path(__file__).resolve().parents[2]
_PACK = _REPO / "samples" / "demo" / "pd-rd-consistency-pilot-2026-09"


def _ann(
    *,
    value: str,
    unit: str | None = "mm",
    target: str = "WALL-01",
    measure: str = "thickness",
) -> DrawingAnnotation:
    return DrawingAnnotation(
        annotation_id="a1",
        sheet_id="A-101",
        target_ref=target,
        measure_name=measure,
        observed_value=value,
        unit=unit,
        problem_zone=ProblemZone(sheet_id="A-101", page_number=1, x=10, y=10, width=40, height=12),
        source="raster-drawing-analyzer",
    )


def _obs(*, guid: str = "2nJrDaLQfJ1QPhdJR0o97J", mm: float = 200.0) -> IfcQuantityObservation:
    return IfcQuantityObservation(
        global_id=guid,
        name="WALL-01",
        quantity_name="Width",
        value=parse_quantity(mm / 1000.0, "m"),
        ifc_sha256="abc",
        ifc_revision="R1",
    )


class DrawingIfcConsistencyDomainTests(unittest.TestCase):
    def test_missing_value_is_not_zero(self) -> None:
        self.assertIsNone(parse_annotation_length(_ann(value="", unit="mm")))
        self.assertIsNone(parse_annotation_length(_ann(value="n/a", unit="mm")))
        parsed = parse_annotation_length(_ann(value="0", unit="mm"))
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.si_value, 0.0)

    def test_units_normalize_and_match(self) -> None:
        result = compare_drawing_length_to_ifc(
            annotations=(_ann(value="0.20", unit="m"),),
            observations=(_obs(mm=200.0),),
            drawing_sources=(DrawingSource(sheet_id="A-101", revision="R1"),),
            ifc_revision="R1",
        )
        self.assertTrue(result.ran)
        self.assertFalse(any(issue.rule_id == RULE_ID for issue in result.issues))
        self.assertEqual(result.capability.status, CapabilityState.OK)

    def test_controlled_mismatch_is_hard_conflict_with_evidence(self) -> None:
        drawing = DrawingSource(
            path=Path("a-101.pdf"),
            sheet_id="A-101",
            revision="R1",
            sha256="drawsha",
        )
        result = compare_drawing_length_to_ifc(
            annotations=(_ann(value="150", unit="mm"),),
            observations=(_obs(mm=200.0),),
            drawing_sources=(drawing,),
            ifc_revision="R1",
            ifc_sha256="ifcsha",
        )
        hits = [issue for issue in result.issues if issue.rule_id == RULE_ID]
        self.assertEqual(len(hits), 1)
        issue = hits[0]
        self.assertEqual(issue.severity, Severity.ERROR)
        self.assertEqual(issue.conflict_kind, ConflictKind.HARD_CONFLICT)
        self.assertEqual(issue.element_guid, "2nJrDaLQfJ1QPhdJR0o97J")
        self.assertEqual(issue.problem_zone.page_number, 1)
        self.assertIn(f"rule:{RULE_ID}@{RULE_VERSION}", issue.evidence_refs)
        self.assertTrue(any("ifc:" in ref and "guid:" in ref for ref in issue.evidence_refs))
        self.assertTrue(any(ref.startswith("drawing:") for ref in issue.evidence_refs))
        self.assertIn("150", issue.observed_value or "")
        self.assertIn("200", issue.expected_value or "")
        self.assertNotIn("СП ", issue.message)

    def test_ambiguous_match_is_not_hard_conflict(self) -> None:
        result = compare_drawing_length_to_ifc(
            annotations=(_ann(value="150", unit="mm"),),
            observations=(
                _obs(guid="2nJrDaLQfJ1QPhdJR0o97J", mm=200.0),
                _obs(guid="3rH_tKFeT2wQPlyfwCmALO", mm=150.0),
            ),
            drawing_sources=(DrawingSource(sheet_id="A-101", revision="R1"),),
            ifc_revision="R1",
        )
        self.assertTrue(any(issue.rule_id == RULE_AMBIGUOUS for issue in result.issues))
        self.assertFalse(any(issue.rule_id == RULE_ID for issue in result.issues))
        self.assertEqual(result.capability.status, CapabilityState.NOT_VERIFIED)

    def test_mixed_revision_skips_value_compare(self) -> None:
        result = compare_drawing_length_to_ifc(
            annotations=(_ann(value="150", unit="mm"),),
            observations=(_obs(mm=200.0),),
            drawing_sources=(DrawingSource(sheet_id="A-101", revision="R2"),),
            ifc_revision="R1",
        )
        self.assertTrue(any(issue.rule_id == RULE_REVISION_MIXED for issue in result.issues))
        self.assertFalse(any(issue.rule_id == RULE_ID for issue in result.issues))

    def test_unparsed_field_is_incomplete_not_success(self) -> None:
        result = compare_drawing_length_to_ifc(
            annotations=(_ann(value="", unit="mm"),),
            observations=(_obs(mm=200.0),),
            drawing_sources=(DrawingSource(sheet_id="A-101", revision="R1"),),
            ifc_revision="R1",
        )
        self.assertTrue(any(issue.rule_id == RULE_INCOMPLETE for issue in result.issues))
        self.assertFalse(any(issue.rule_id == RULE_ID for issue in result.issues))
        self.assertEqual(result.capability.status, CapabilityState.NOT_VERIFIED)


class PdRdPilotAnalyzeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_pilot_drawings(_PACK)

    def _analyze(self, variant: str):
        pack = load_benchmark_pack(_PACK / VARIANTS[variant])
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="pd-rd-pilot-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                api_bearer_token="secret-token",
                allow_anonymous_dev=False,
            )
            container = bootstrap_container(settings)
            use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
            return use_case.execute(pack.request)

    def test_clean_and_unit_have_no_hard_conflict(self) -> None:
        for variant in ("clean", "unit"):
            with self.subTest(variant=variant):
                report = self._analyze(variant)
                self.assertTrue(
                    any(
                        ann.target_ref == "WALL-01" and ann.measure_name == "thickness"
                        for ann in report.drawing_annotations
                    ),
                    msg=variant,
                )
                self.assertFalse(
                    any(issue.rule_id == RULE_ID for issue in report.issues),
                    msg=variant,
                )

    def test_defect_traces_to_both_sources(self) -> None:
        report = self._analyze("defect")
        hits = [issue for issue in report.issues if issue.rule_id == RULE_ID]
        self.assertEqual(len(hits), 1)
        issue = hits[0]
        self.assertFalse(report.summary.passed)
        self.assertEqual(issue.element_guid, "2nJrDaLQfJ1QPhdJR0o97J")
        self.assertEqual(issue.problem_zone.page_number, 1)
        self.assertIn("150", issue.observed_value or "")
        self.assertTrue(issue.evidence_refs)
        self.assertGreaterEqual(len(issue.evidence_refs), 3)

    def test_missing_and_parser_do_not_pass_or_invent_violation(self) -> None:
        for variant in ("missing", "parser-error", "unsupported", "ifc-missing-width", "ambiguous"):
            with self.subTest(variant=variant):
                report = self._analyze(variant)
                self.assertFalse(report.summary.passed, msg=variant)
                self.assertFalse(
                    any(issue.rule_id == RULE_ID for issue in report.issues),
                    msg=variant,
                )
                outcome = getattr(report.summary.outcome, "value", report.summary.outcome)
                self.assertNotEqual(outcome, "pass", msg=variant)

    def test_mixed_revision_detected(self) -> None:
        report = self._analyze("mixed-rev")
        self.assertTrue(any(issue.rule_id == RULE_REVISION_MIXED for issue in report.issues))
        self.assertFalse(any(issue.rule_id == RULE_ID for issue in report.issues))

    def test_cli_writes_bcf_and_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_pd_rd_consistency_pilot(
                variant="defect",
                output_dir=Path(tmp),
                expert_verdict="accepted",
                expert_subject="lab-expert",
            )
            self.assertTrue(summary["hard_conflict"])
            self.assertTrue(summary["bcf"]["structural_ok"])
            self.assertGreaterEqual(summary["bcf"]["consumed_topics"], 1)
            self.assertEqual(summary["bcf"]["cde_import"], "NOT_VERIFIED")
            self.assertIsNotNone(summary["expert_event"])
            self.assertEqual(summary["expert_event"]["actor"], "lab-expert")
            self.assertTrue((Path(tmp) / "report.json").is_file())
            self.assertTrue((Path(tmp) / "findings.bcfzip").is_file())


class PdRdPilotHitlApiTests(unittest.TestCase):
    def _client(
        self,
        *,
        storage: Path,
        token: str | None = "secret-token",
        allow_anonymous_dev: bool = False,
    ):
        from fastapi.testclient import TestClient

        from aerobim.presentation.http.api import create_http_app

        settings = Settings(
            application_name="pd-rd-hitl",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=storage,
            debug=True,
            api_bearer_token=token,
            api_tenant_id="tenant-a",
            enforce_object_acl=True,
            allow_anonymous_dev=allow_anonymous_dev,
        )
        container = bootstrap_container(settings)
        return TestClient(create_http_app(container)), container

    def _seed(self, container) -> str:
        from datetime import UTC, datetime
        from uuid import uuid4

        from aerobim.domain.models import ValidationReport, ValidationSummary

        settings = container.resolve(Tokens.SETTINGS)
        store = container.resolve(Tokens.AUDIT_REPORT_STORE)
        ifc_path = settings.storage_dir / "models" / "model.ifc"
        ifc_path.parent.mkdir(parents=True, exist_ok=True)
        ifc_path.write_text("ISO-10303-21;\n", encoding="utf-8")
        report_id = uuid4().hex
        store.save(
            ValidationReport(
                report_id=report_id,
                request_id="pd-rd-hitl",
                ifc_path=ifc_path,
                created_at=datetime.now(tz=UTC).isoformat(),
                requirements=(),
                issues=(),
                summary=ValidationSummary(0, 0, 0, 0, True),
                tenant_id="tenant-a",
            )
        )
        return report_id

    def test_unauthenticated_cannot_assign_expert_status(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(storage=Path(tmp))
            report_id = self._seed(container)
            response = client.post(
                f"/v1/reports/{report_id}/review-events",
                json={"event_type": "accepted", "note": "no auth"},
            )
            self.assertEqual(response.status_code, 401, response.text)

    def test_service_bearer_and_role_spoof_cannot_accept(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(storage=Path(tmp))
            report_id = self._seed(container)
            response = client.post(
                f"/v1/reports/{report_id}/review-events",
                headers={"Authorization": "Bearer secret-token"},
                json={
                    "event_type": "accepted",
                    "actor": "expert",
                    "roles": ["reviewer", "admin"],
                    "note": "spoof",
                },
            )
            self.assertEqual(response.status_code, 403, response.text)

    def test_anonymous_dev_cannot_accept(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(
                storage=Path(tmp),
                token=None,
                allow_anonymous_dev=True,
            )
            report_id = self._seed(container)
            response = client.post(
                f"/v1/reports/{report_id}/review-events",
                json={"event_type": "accepted", "actor": "expert"},
            )
            self.assertEqual(response.status_code, 403, response.text)
            opened = client.post(
                f"/v1/reports/{report_id}/review-events",
                json={"event_type": "opened"},
            )
            self.assertEqual(opened.status_code, 200, opened.text)


class PdRdRequestShapeTests(unittest.TestCase):
    def test_validation_request_carries_ifc_and_drawing(self) -> None:
        request = ValidationRequest(
            request_id="shape",
            ifc_path=_PACK / "wall-01-width-200mm.ifc",
            requirement_source=RequirementSource(text="", source_kind=SourceKind.STRUCTURED_TEXT),
            drawing_sources=(
                DrawingSource(
                    path=_PACK / "a-101-thickness-150mm.pdf",
                    sheet_id="A-101",
                    format="pdf",
                    revision="R1",
                ),
            ),
            revision="R1",
        )
        self.assertTrue(request.ifc_path.is_file())
        self.assertEqual(request.drawing_sources[0].revision, "R1")


if __name__ == "__main__":
    unittest.main()
