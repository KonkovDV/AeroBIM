from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import (
    ConflictKind,
    DrawingAsset,
    FindingCategory,
    ParsedRequirement,
    ProblemZone,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
    compute_issue_priority,
)

_TEST_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
)


class _NullLogger:
    """Silent logger for tests — satisfies StructuredLogger protocol."""

    def info(self, message: str, **context: object) -> None:
        pass

    def warning(self, message: str, **context: object) -> None:
        pass

    def error(self, message: str, **context: object) -> None:
        pass

    def debug(self, message: str, **context: object) -> None:
        pass


def _make_test_container(
    api_bearer_token: str | None = None,
    *,
    environment: str = "test",
    allow_anonymous_dev: bool = True,
):
    """Build a container backed by InMemoryAuditStore for fast HTTP tests."""
    import tempfile

    from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
    from aerobim.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
    from aerobim.core.config.settings import Settings
    from aerobim.core.di.container import Container, Lifecycle
    from aerobim.core.di.tokens import Tokens
    from aerobim.infrastructure.adapters.docling_requirement_extractor import (
        StructuredRequirementExtractor,
    )
    from aerobim.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator
    from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
    from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
    from aerobim.infrastructure.adapters.openrebar_evidence_verifier import (
        OpenRebarEvidenceVerifier,
    )
    from aerobim.infrastructure.adapters.structured_drawing_analyzer import (
        StructuredDrawingAnalyzer,
    )
    from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator

    tmp = tempfile.mkdtemp()
    settings = Settings(
        application_name="test",
        environment=environment,
        host="127.0.0.1",
        port=8080,
        storage_dir=Path(tmp),
        debug=True,
        cors_origins=_TEST_CORS_ORIGINS,
        api_bearer_token=api_bearer_token,
        allow_anonymous_dev=allow_anonymous_dev,
    )
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    store = InMemoryAuditStore()
    container = Container()
    container.register(Tokens.SETTINGS, lambda _: settings)
    container.register(Tokens.LOGGER, lambda _: _NullLogger(), lifecycle=Lifecycle.SINGLETON)
    container.register(
        Tokens.REQUIREMENT_EXTRACTOR,
        lambda _: StructuredRequirementExtractor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.NARRATIVE_RULE_SYNTHESIZER,
        lambda _: NarrativeRuleSynthesizer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DRAWING_ANALYZER,
        lambda _: StructuredDrawingAnalyzer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.IFC_VALIDATOR, lambda _: IfcOpenShellValidator(), lifecycle=Lifecycle.SINGLETON
    )
    container.register(Tokens.IDS_VALIDATOR, lambda _: None, lifecycle=Lifecycle.SINGLETON)
    container.register(
        Tokens.REMARK_GENERATOR, lambda _: TemplateRemarkGenerator(), lifecycle=Lifecycle.SINGLETON
    )
    container.register(Tokens.AUDIT_REPORT_STORE, lambda _: store, lifecycle=Lifecycle.SINGLETON)
    container.register(
        Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE,
        lambda c: ValidateIfcAgainstIdsUseCase(
            requirement_extractor=c.resolve(Tokens.REQUIREMENT_EXTRACTOR),
            ifc_validator=c.resolve(Tokens.IFC_VALIDATOR),
            audit_report_store=c.resolve(Tokens.AUDIT_REPORT_STORE),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE,
        lambda c: AnalyzeProjectPackageUseCase(
            requirement_extractor=c.resolve(Tokens.REQUIREMENT_EXTRACTOR),
            narrative_rule_synthesizer=c.resolve(Tokens.NARRATIVE_RULE_SYNTHESIZER),
            drawing_analyzer=c.resolve(Tokens.DRAWING_ANALYZER),
            ifc_validator=c.resolve(Tokens.IFC_VALIDATOR),
            remark_generator=c.resolve(Tokens.REMARK_GENERATOR),
            audit_report_store=c.resolve(Tokens.AUDIT_REPORT_STORE),
            external_evidence_verifier=OpenRebarEvidenceVerifier(),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    return container


def _make_seed_report() -> ValidationReport:
    return ValidationReport(
        report_id=uuid4().hex,
        request_id="req-http-test",
        ifc_path=Path("seed.ifc"),
        created_at=datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=(
            ValidationIssue(
                rule_id="RULE-HTML-001",
                severity=Severity.ERROR,
                message='User-controlled <tag> & "quote" content',
                element_guid="seed-guid",
            ),
        ),
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=1,
            error_count=1,
            warning_count=0,
            passed=False,
        ),
    )


class ApiSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_path_traversal_ifc_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            json={
                "ifc_path": "../../etc/passwd",
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
            },
        )
        self.assertGreaterEqual(response.status_code, 400)
        self.assertLess(response.status_code, 500)

    def test_path_traversal_unix_style_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            json={
                "ifc_path": "../../../secret/model.ifc",
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
            },
        )
        self.assertGreaterEqual(response.status_code, 400)
        self.assertLess(response.status_code, 500)

    def test_path_traversal_reinforcement_report_rejected(self) -> None:
        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": "model.ifc",
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "reinforcement_report_path": "../../outside/openrebar.result.json",
            },
        )
        self.assertGreaterEqual(response.status_code, 400)
        self.assertLess(response.status_code, 500)

    def test_health_returns_ok(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("service", data)
        self.assertNotIn("environment", data)

    def test_health_response_shape_locked(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"service", "status"})

    def test_requirement_path_traversal_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            json={
                "ifc_path": "fixtures/model.ifc",
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "requirement_path": "../../outside/requirements.txt",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_api_token_is_enforced_when_configured(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.presentation.http.api import create_http_app

        secured_container = _make_test_container(api_bearer_token="test-token")
        secured_client = TestClient(create_http_app(secured_container))

        no_auth_response = secured_client.get("/v1/reports")
        self.assertEqual(no_auth_response.status_code, 401)

        wrong_auth_response = secured_client.get(
            "/v1/reports",
            headers={"Authorization": "Bearer wrong-token"},
        )
        self.assertEqual(wrong_auth_response.status_code, 401)

        ok_response = secured_client.get(
            "/v1/reports",
            headers={"Authorization": "Bearer test-token"},
        )
        self.assertEqual(ok_response.status_code, 200)


class ApiReportEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.core.di.tokens import Tokens
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)
        cls.store = container.resolve(Tokens.AUDIT_REPORT_STORE)

    def _seed_report_summary(
        self,
        report_id: str,
        *,
        passed: bool,
        project_name: str | None,
        discipline: str | None,
    ) -> None:
        report = ValidationReport(
            report_id=report_id,
            request_id=f"req-{report_id}",
            ifc_path=Path("seed.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            project_name=project_name,
            discipline=discipline,
            requirements=(),
            issues=(),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=0 if passed else 2,
                error_count=0 if passed else 2,
                warning_count=0,
                passed=passed,
            ),
        )
        self.store.save(report)

    def test_list_reports_empty(self) -> None:
        response = self.client.get("/v1/reports")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("reports", data)
        self.assertIn("count", data)

    def test_list_reports_response_shape_locked(self) -> None:
        response = self.client.get("/v1/reports")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload.keys()), {"reports", "count"})
        self.assertIsInstance(payload["reports"], list)
        self.assertIsInstance(payload["count"], int)

    def test_list_reports_filters_by_project_discipline_and_passed(self) -> None:
        self._seed_report_summary(
            "a" * 32,
            passed=True,
            project_name="Residential Tower Alpha",
            discipline="architecture",
        )
        self._seed_report_summary(
            "b" * 32,
            passed=False,
            project_name="Residential Tower Alpha",
            discipline="structure",
        )
        self._seed_report_summary(
            "c" * 32,
            passed=False,
            project_name="Hospital Beta",
            discipline="mechanical",
        )

        response = self.client.get("/v1/reports?project=tower&discipline=arch&passed=true")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["reports"][0]["report_id"], "a" * 32)
        self.assertEqual(data["reports"][0]["project_name"], "Residential Tower Alpha")
        self.assertEqual(data["reports"][0]["discipline"], "architecture")

    def test_get_report_invalid_id_format_returns_400(self) -> None:
        response = self.client.get("/v1/reports/not-a-uuid-format")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid report ID format", response.json()["detail"])

    def test_get_nonexistent_report_returns_404(self) -> None:
        response = self.client.get("/v1/reports/00000000000000000000000000000000")
        self.assertEqual(response.status_code, 404)

    def test_get_report_hides_internal_storage_fields(self) -> None:
        report_id = "d" * 32
        report = ValidationReport(
            report_id=report_id,
            request_id=f"req-{report_id}",
            ifc_path=Path("internal/model.ifc"),
            ifc_object_key="aerobim/ifc-sources/report-1/model.ifc",
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=0,
                error_count=0,
                warning_count=0,
                passed=True,
            ),
            drawing_assets=(
                DrawingAsset(
                    asset_id="asset-1",
                    sheet_id="A-101",
                    page_number=1,
                    stored_filename="asset-1.png",
                    object_key="aerobim/drawing-assets/report-1/asset-1.png",
                    source_path=Path("internal/asset-1.png"),
                ),
            ),
        )
        self.store.save(report)

        response = self.client.get(f"/v1/reports/{report_id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn("ifc_path", payload)
        self.assertNotIn("ifc_object_key", payload)
        self.assertNotIn("object_key", payload["drawing_assets"][0])
        self.assertNotIn("source_path", payload["drawing_assets"][0])

    def test_export_nonexistent_report_returns_404(self) -> None:
        response = self.client.get("/v1/reports/00000000000000000000000000000000/export/json")
        self.assertEqual(response.status_code, 404)

    def test_export_html_nonexistent_report_returns_404(self) -> None:
        response = self.client.get("/v1/reports/00000000000000000000000000000000/export/html")
        self.assertEqual(response.status_code, 404)


class ApiAnalyzeProjectPackageEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.core.di.tokens import Tokens
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)
        cls.settings = container.resolve(Tokens.SETTINGS)

    def _write_openrebar_report_fixture(
        self,
        *,
        fallback_used: bool,
        master_problem_strategy: str = "restricted-master-lp-highs",
        total_waste_percent: float = 0.0,
    ) -> str:
        fixture_dir = self.settings.storage_dir / "fixtures"
        fixture_dir.mkdir(parents=True, exist_ok=True)
        report_path = fixture_dir / "openrebar.result.json"
        report_path.write_text(
            json.dumps(
                {
                    "contractId": "OpenRebar.reinforcement.report.v1",
                    "schemaVersion": "1.0.0",
                    "generatedAtUtc": "2026-04-16T00:00:00Z",
                    "metadata": {
                        "projectCode": "Residential Tower Alpha",
                        "slabId": "SLAB-03",
                        "sourceSystem": "OpenRebar",
                        "targetSystem": "AeroBIM",
                        "countryCode": "RU",
                        "designCode": "SP63",
                        "normativeProfileId": "ru.sp63.2018",
                        "normativeTablesVersion": "v1",
                    },
                    "normativeProfile": {
                        "profileId": "ru.sp63.2018",
                        "jurisdiction": "RU",
                        "designCode": "SP63",
                        "tablesVersion": "v1",
                    },
                    "analysisProvenance": {
                        "geometry": {
                            "decompositionAlgorithm": "grid-scan",
                            "rectangularShortcutFillRatio": 0.9,
                            "minRectangleAreaMm2": 1000.0,
                            "samplingResolutionPerAxis": 64,
                            "cellCoverageInclusionThreshold": 0.5,
                        },
                        "optimization": {
                            "optimizerId": "column-generation",
                            "masterProblemStrategy": master_problem_strategy,
                            "pricingStrategy": "bounded-knapsack-dp",
                            "integerizationStrategy": "repair-ffd",
                            "demandAggregationPrecisionMm": 0.1,
                            "qualityFloor": "production",
                            "anyFallbackMasterSolverUsed": fallback_used,
                        },
                    },
                    "isolineFileName": "floor-03.dxf",
                    "isolineFileFormat": "dxf",
                    "slab": {
                        "concreteClass": "B25",
                        "thicknessMm": 200,
                        "coverMm": 25,
                        "effectiveDepthMm": 175,
                        "areaMm2": 1_000_000,
                        "openingCount": 0,
                        "boundingBox": {
                            "minX": 0,
                            "minY": 0,
                            "maxX": 1000,
                            "maxY": 1000,
                            "width": 1000,
                            "height": 1000,
                        },
                    },
                    "zones": [],
                    "optimizationByDiameter": [],
                    "placement": {
                        "requested": False,
                        "executed": False,
                        "success": True,
                        "totalRebarsPlaced": 0,
                        "totalTagsCreated": 0,
                        "totalBendingDetails": 0,
                        "warnings": [],
                        "errors": [],
                    },
                    "summary": {
                        "parsedZoneCount": 0,
                        "classifiedZoneCount": 0,
                        "totalRebarSegments": 0,
                        "totalWastePercent": total_waste_percent,
                        "totalWasteMm": 0.0,
                        "totalMassKg": 0.0,
                    },
                }
            ),
            encoding="utf-8",
        )
        return str(Path("fixtures") / "openrebar.result.json")

    def _write_openrebar_handoff_fixture(
        self,
        *,
        reinforcement_report_path: str,
        report_sha256: str | None = None,
    ) -> str:
        fixture_dir = self.settings.storage_dir / "fixtures"
        fixture_dir.mkdir(parents=True, exist_ok=True)
        report_abs_path = self.settings.storage_dir / reinforcement_report_path
        expected_sha = report_sha256 or hashlib.sha256(report_abs_path.read_bytes()).hexdigest()
        handoff_path = fixture_dir / "openrebar.handoff.json"
        handoff_path.write_text(
            json.dumps(
                {
                    "handoff_type": "openrebar-aerobim-report-handoff.v1",
                    "schema_version": "1.0.0",
                    "generated_at_utc": "2026-04-22T00:00:00Z",
                    "reinforcement_report_path": reinforcement_report_path,
                    "report_sha256": expected_sha,
                    "contract_id": "OpenRebar.reinforcement.report.v1",
                    "report_schema_version": "1.0.0",
                    "project_code": "Residential Tower Alpha",
                    "slab_id": "SLAB-03",
                }
            ),
            encoding="utf-8",
        )
        return str(Path("fixtures") / "openrebar.handoff.json")

    def _write_ifc_fixture(self) -> str:
        # Use a known-valid IFC sample from repository fixtures while keeping
        # API path resolution inside storage boundary.
        source_fixture = (
            Path(__file__).resolve().parents[2] / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
        )
        fixture_dir = self.settings.storage_dir / "fixtures"
        fixture_dir.mkdir(parents=True, exist_ok=True)
        target_fixture = fixture_dir / "wall-fire-rating-rei60.ifc"
        target_fixture.write_bytes(source_fixture.read_bytes())
        return str(Path("fixtures") / "wall-fire-rating-rei60.ifc")

    def test_analyze_project_package_persists_iso19650_context_fields(self) -> None:
        ifc_path = self._write_ifc_fixture()

        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": ifc_path,
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Pilot Moscow",
                "stage": "S2",
                "information_container_id": "cde-pilot-moscow-001",
                "revision": "P-01",
                "doc_status": "Shared",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get("stage"), "S2")
        self.assertEqual(payload.get("information_container_id"), "cde-pilot-moscow-001")
        self.assertEqual(payload.get("revision"), "P-01")
        self.assertEqual(payload.get("doc_status"), "Shared")

    def test_analyze_project_package_includes_openrebar_fallback_warning(self) -> None:
        ifc_path = self._write_ifc_fixture()
        reinforcement_report_path = self._write_openrebar_report_fixture(fallback_used=True)

        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": ifc_path,
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Residential Tower Alpha",
                "reinforcement_report_path": reinforcement_report_path,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        issue_ids = {issue["rule_id"] for issue in payload.get("issues", [])}
        self.assertIn("OPENREBAR-OPT-FALLBACK", issue_ids)

    def test_analyze_project_package_includes_openrebar_digest_warning(self) -> None:
        ifc_path = self._write_ifc_fixture()
        reinforcement_report_path = self._write_openrebar_report_fixture(fallback_used=False)

        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": ifc_path,
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Residential Tower Alpha",
                "reinforcement_report_path": reinforcement_report_path,
                "reinforcement_source_digest": "0" * 64,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        issue_ids = {issue["rule_id"] for issue in payload.get("issues", [])}
        self.assertIn("OPENREBAR-PROVENANCE-DIGEST", issue_ids)

    def test_analyze_project_package_accepts_openrebar_handoff_manifest(self) -> None:
        ifc_path = self._write_ifc_fixture()
        reinforcement_report_path = self._write_openrebar_report_fixture(fallback_used=False)
        reinforcement_handoff_path = self._write_openrebar_handoff_fixture(
            reinforcement_report_path=reinforcement_report_path
        )

        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": ifc_path,
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Residential Tower Alpha",
                "reinforcement_handoff_path": reinforcement_handoff_path,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        openrebar_issue_ids = {
            issue["rule_id"]
            for issue in payload.get("issues", [])
            if issue.get("rule_id", "").startswith("OPENREBAR-")
        }
        self.assertEqual(openrebar_issue_ids, set())

    def test_analyze_project_package_rejects_openrebar_handoff_sha_mismatch(self) -> None:
        ifc_path = self._write_ifc_fixture()
        reinforcement_report_path = self._write_openrebar_report_fixture(fallback_used=False)
        reinforcement_handoff_path = self._write_openrebar_handoff_fixture(
            reinforcement_report_path=reinforcement_report_path,
            report_sha256="0" * 64,
        )

        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": ifc_path,
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Residential Tower Alpha",
                "reinforcement_handoff_path": reinforcement_handoff_path,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("report_sha256 mismatch", response.json().get("detail", ""))

    def test_analyze_project_package_rejects_conflicting_openrebar_inputs(self) -> None:
        ifc_path = self._write_ifc_fixture()
        reinforcement_report_path = self._write_openrebar_report_fixture(fallback_used=False)
        reinforcement_handoff_path = self._write_openrebar_handoff_fixture(
            reinforcement_report_path=reinforcement_report_path
        )

        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": ifc_path,
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Residential Tower Alpha",
                "reinforcement_report_path": reinforcement_report_path,
                "reinforcement_handoff_path": reinforcement_handoff_path,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot be combined", response.json().get("detail", ""))

    def test_analyze_project_package_includes_openrebar_strategy_warning(self) -> None:
        ifc_path = self._write_ifc_fixture()
        reinforcement_report_path = self._write_openrebar_report_fixture(
            fallback_used=False,
            master_problem_strategy="restricted-master-lp-coordinate-descent",
        )

        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": ifc_path,
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Residential Tower Alpha",
                "reinforcement_report_path": reinforcement_report_path,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        issue_ids = {issue["rule_id"] for issue in payload.get("issues", [])}
        self.assertIn("OPENREBAR-OPT-STRATEGY", issue_ids)

    def test_analyze_project_package_includes_openrebar_waste_threshold_warning(self) -> None:
        ifc_path = self._write_ifc_fixture()
        reinforcement_report_path = self._write_openrebar_report_fixture(
            fallback_used=False,
            total_waste_percent=12.7,
        )

        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": ifc_path,
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Residential Tower Alpha",
                "reinforcement_report_path": reinforcement_report_path,
                "reinforcement_waste_warning_threshold_percent": 10.0,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        issue_ids = {issue["rule_id"] for issue in payload.get("issues", [])}
        self.assertIn("OPENREBAR-WASTE-THRESHOLD", issue_ids)

    def test_analyze_project_package_enforced_mode_escalates_openrebar_warning(self) -> None:
        ifc_path = self._write_ifc_fixture()
        reinforcement_report_path = self._write_openrebar_report_fixture(fallback_used=True)

        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": ifc_path,
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Residential Tower Alpha",
                "reinforcement_report_path": reinforcement_report_path,
                "reinforcement_provenance_mode": "enforced",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        fallback_issues = [
            issue
            for issue in payload.get("issues", [])
            if issue.get("rule_id") == "OPENREBAR-OPT-FALLBACK"
        ]
        self.assertEqual(len(fallback_issues), 1)
        self.assertEqual(fallback_issues[0].get("severity"), "error")

    def test_reinforcement_digest_endpoint_returns_expected_digest(self) -> None:
        from aerobim.infrastructure.adapters.openrebar_evidence_verifier import (
            build_openrebar_provenance_digest,
        )

        reinforcement_report_path = self._write_openrebar_report_fixture(fallback_used=False)
        report_abs_path = self.settings.storage_dir / reinforcement_report_path
        payload = json.loads(report_abs_path.read_text(encoding="utf-8"))
        expected_digest = build_openrebar_provenance_digest(payload)

        response = self.client.post(
            "/v1/analyze/project-package/reinforcement-digest",
            json={"reinforcement_report_path": reinforcement_report_path},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body.get("provenance_digest"), expected_digest)
        self.assertEqual(body.get("contract_id"), "OpenRebar.reinforcement.report.v1")
        self.assertEqual(body.get("project_code"), "Residential Tower Alpha")
        self.assertEqual(body.get("slab_id"), "SLAB-03")

    def test_reinforcement_digest_response_shape_locked(self) -> None:
        reinforcement_report_path = self._write_openrebar_report_fixture(fallback_used=False)
        response = self.client.post(
            "/v1/analyze/project-package/reinforcement-digest",
            json={"reinforcement_report_path": reinforcement_report_path},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            set(body.keys()),
            {
                "reinforcement_report_path",
                "provenance_digest",
                "contract_id",
                "schema_version",
                "project_code",
                "slab_id",
                "claim_labels",
            },
        )
        self.assertIn("calculation_match", body["claim_labels"])
        self.assertIn("calculation_correctness", body["claim_labels"])

    def test_system_capabilities_honesty_surface(self) -> None:
        response = self.client.get("/v1/system/capabilities")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["artifact_type"], "system_capabilities")
        self.assertEqual(body["schema_version"], "1.1.0")
        honesty = body["honesty"]
        self.assertEqual(honesty["dwg_dxf"]["status"], "missing")
        self.assertEqual(honesty["cv_human_level"]["status"], "missing")
        self.assertEqual(honesty["mep_system_clash"]["status"], "not_verified")
        self.assertEqual(honesty["calculation_correctness"]["status"], "not_implemented")
        self.assertIn("calculation_match", body["claim_boundary"])
        self.assertIn("calculation_correctness", body["claim_boundary"])
        self.assertIn("precision_claim", body["claim_boundary"])
        intake = body["customer_intake_gate"]
        self.assertEqual(intake["checkpoint"], "NO_GO")
        self.assertEqual(intake.get("true_gates"), [])

    def test_reinforcement_digest_endpoint_rejects_path_traversal(self) -> None:
        response = self.client.post(
            "/v1/analyze/project-package/reinforcement-digest",
            json={"reinforcement_report_path": "../../outside/openrebar.result.json"},
        )

        self.assertEqual(response.status_code, 400)


class ApiIfcSourceEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.core.di.tokens import Tokens
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)
        cls.store = container.resolve(Tokens.AUDIT_REPORT_STORE)
        cls.settings = container.resolve(Tokens.SETTINGS)

    def _seed_report_with_ifc_source(
        self, relative_path: str = "models/seed.ifc"
    ) -> tuple[str, Path]:
        source_path = self.settings.storage_dir / relative_path
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")

        report = ValidationReport(
            report_id=uuid4().hex,
            request_id="req-ifc-source",
            ifc_path=source_path,
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=0,
                error_count=0,
                warning_count=0,
                passed=True,
            ),
        )
        self.store.save(report)
        return report.report_id, source_path

    def test_report_ifc_source_returns_file_bytes(self) -> None:
        report_id, source_path = self._seed_report_with_ifc_source()

        response = self.client.get(f"/v1/reports/{report_id}/source/ifc")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, source_path.read_bytes())
        self.assertIn("attachment; filename=", response.headers.get("content-disposition", ""))

    def test_report_ifc_source_returns_404_when_file_missing(self) -> None:
        report_id, source_path = self._seed_report_with_ifc_source("models/missing.ifc")
        source_path.unlink()

        response = self.client.get(f"/v1/reports/{report_id}/source/ifc")

        self.assertEqual(response.status_code, 404)
        self.assertIn("IFC source", response.json()["detail"])

    def test_report_ifc_source_rejects_paths_outside_storage_boundary(self) -> None:
        outside_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: outside_dir.exists() and outside_dir.rmdir())
        outside_file = outside_dir / "outside.ifc"
        outside_file.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
        self.addCleanup(lambda: outside_file.exists() and outside_file.unlink())

        report = ValidationReport(
            report_id=uuid4().hex,
            request_id="req-ifc-outside",
            ifc_path=outside_file,
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=0,
                error_count=0,
                warning_count=0,
                passed=True,
            ),
        )
        self.store.save(report)

        response = self.client.get(f"/v1/reports/{report.report_id}/source/ifc")

        self.assertEqual(response.status_code, 409)
        self.assertIn("escapes storage boundary", response.json()["detail"])

    def test_report_ifc_source_rejects_invalid_report_id_format(self) -> None:
        response = self.client.get("/v1/reports/not-valid-id/source/ifc")
        self.assertEqual(response.status_code, 400)


class ApiDrawingAssetPreviewEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.core.di.tokens import Tokens
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)
        cls.store = container.resolve(Tokens.AUDIT_REPORT_STORE)
        cls.settings = container.resolve(Tokens.SETTINGS)

    def _seed_report_with_drawing_asset(self) -> tuple[str, str, Path]:
        report_id = uuid4().hex
        asset_id = "drawing-001-page-001"
        asset_dir = self.settings.storage_dir / "drawing-assets" / report_id
        asset_dir.mkdir(parents=True, exist_ok=True)
        preview_path = asset_dir / f"{asset_id}.png"
        preview_path.write_bytes(b"\x89PNG\r\n\x1a\npreview")

        report = ValidationReport(
            report_id=report_id,
            request_id="req-drawing-preview",
            ifc_path=self.settings.storage_dir / "model.ifc",
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=0,
                error_count=0,
                warning_count=0,
                passed=True,
            ),
            drawing_assets=(
                DrawingAsset(
                    asset_id=asset_id,
                    sheet_id="A-101",
                    page_number=1,
                    media_type="image/png",
                    coordinate_width=320,
                    coordinate_height=200,
                    stored_filename=preview_path.name,
                ),
            ),
        )
        self.store.save(report)
        return report_id, asset_id, preview_path

    def test_report_drawing_asset_preview_returns_bytes(self) -> None:
        report_id, asset_id, preview_path = self._seed_report_with_drawing_asset()

        response = self.client.get(f"/v1/reports/{report_id}/drawing-assets/{asset_id}/preview")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, preview_path.read_bytes())
        self.assertIn("image/png", response.headers.get("content-type", ""))

    def test_report_drawing_asset_preview_returns_404_when_file_missing(self) -> None:
        report_id, asset_id, preview_path = self._seed_report_with_drawing_asset()
        preview_path.unlink()

        response = self.client.get(f"/v1/reports/{report_id}/drawing-assets/{asset_id}/preview")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Drawing asset preview", response.json()["detail"])

    def test_report_drawing_asset_preview_returns_404_when_asset_missing(self) -> None:
        report_id, _asset_id, _preview_path = self._seed_report_with_drawing_asset()

        response = self.client.get(f"/v1/reports/{report_id}/drawing-assets/missing-asset/preview")

        self.assertEqual(response.status_code, 404)

    def test_report_drawing_asset_preview_rejects_invalid_asset_id_format(self) -> None:
        report_id, _asset_id, _preview_path = self._seed_report_with_drawing_asset()
        response = self.client.get(f"/v1/reports/{report_id}/drawing-assets/invalid!asset/preview")
        self.assertEqual(response.status_code, 400)


class ApiJobEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_get_job_rejects_invalid_job_id_format(self) -> None:
        response = self.client.get("/v1/analyze/project-package/jobs/not-a-valid-id")
        self.assertEqual(response.status_code, 400)


class ApiHtmlExportTests(unittest.TestCase):
    """Tests for the HTML report export endpoint."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.core.di.tokens import Tokens
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)
        cls.store = container.resolve(Tokens.AUDIT_REPORT_STORE)

    def _seed_report(self) -> str:
        report = _make_seed_report()
        self.store.save(report)
        return report.report_id

    def test_html_export_returns_html_content_type(self) -> None:
        report_id = self._seed_report()
        html_resp = self.client.get(f"/v1/reports/{report_id}/export/html")
        self.assertEqual(html_resp.status_code, 200)
        self.assertIn("text/html", html_resp.headers.get("content-type", ""))
        self.assertIn("<!DOCTYPE html>", html_resp.text)
        self.assertIn("Validation Report", html_resp.text)
        self.assertIn("seed-guid", html_resp.text)

    def test_html_export_escapes_special_characters(self) -> None:
        """Ensure XSS-safe rendering of user-controlled data."""
        from aerobim.presentation.http.api import _esc

        self.assertEqual(
            _esc('<script>alert("xss")</script>'),
            "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;",
        )
        self.assertEqual(_esc("A & B"), "A &amp; B")

    def test_html_export_shows_priority_column_and_category_sections(self) -> None:
        """Verify priority score and category grouping are present."""
        report = ValidationReport(
            report_id=uuid4().hex,
            request_id="req-html-rich",
            ifc_path=Path("rich.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(
                ValidationIssue(
                    rule_id="RULE-HIGH-001",
                    severity=Severity.ERROR,
                    message="High priority issue",
                    category=FindingCategory.CROSS_DOCUMENT,
                    element_guid="guid-high",
                    expected_value="REI60",
                    observed_value="REI30",
                    unit="",
                    conflict_kind=ConflictKind.HARD_CONFLICT,
                    priority=55,
                    finding_id="fid-html-high",
                    source_id="pkg-main",
                    evidence_refs=("pkg-main@r1#ifc:guid-high",),
                ),
                ValidationIssue(
                    rule_id="RULE-LOW-001",
                    severity=Severity.INFO,
                    message="Low priority issue",
                    category=FindingCategory.IFC_VALIDATION,
                    element_guid="guid-low",
                    priority=10,
                    finding_id="fid-html-low",
                    source_id="pkg-main",
                    evidence_refs=("pkg-main@r1#ifc:guid-low",),
                ),
            ),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=2,
                error_count=1,
                warning_count=0,
                passed=False,
            ),
        )
        self.store.save(report)
        html_resp = self.client.get(f"/v1/reports/{report.report_id}/export/html")
        self.assertEqual(html_resp.status_code, 200)
        text = html_resp.text
        self.assertIn("Priority", text)
        self.assertIn("55", text)
        self.assertIn("Cross-Document Contradictions", text)
        self.assertIn("IFC Model Validation", text)
        self.assertIn("REI60", text)
        self.assertIn("REI30", text)
        self.assertIn("finding_id=fid-html-high", text)
        self.assertIn("evidence_refs=pkg-main@r1#ifc:guid-high", text)

    def test_html_export_escapes_problem_zone_content(self) -> None:
        """Verify problem zone coordinates and sheet are escaped."""
        report = ValidationReport(
            report_id=uuid4().hex,
            request_id="req-html-pz",
            ifc_path=Path("pz.ifc"),
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(
                ValidationIssue(
                    rule_id="RULE-PZ-001",
                    severity=Severity.WARNING,
                    message="Zone issue",
                    element_guid="guid-pz",
                    problem_zone=ProblemZone(
                        sheet_id="A-101 <script>",
                        x=120.5,
                        y=80.0,
                    ),
                    priority=25,
                ),
            ),
            summary=ValidationSummary(
                requirement_count=0,
                issue_count=1,
                error_count=0,
                warning_count=1,
                passed=False,
            ),
        )
        self.store.save(report)
        html_resp = self.client.get(f"/v1/reports/{report.report_id}/export/html")
        self.assertEqual(html_resp.status_code, 200)
        text = html_resp.text
        self.assertIn("A-101 &lt;script&gt;", text)
        self.assertNotIn("<script>", text)


class IssuePriorityScoringTests(unittest.TestCase):
    """Tests for compute_issue_priority scoring matrix."""

    def test_error_cross_document_hard_conflict_is_highest(self) -> None:
        issue = ValidationIssue(
            rule_id="R1",
            severity=Severity.ERROR,
            message="msg",
            category=FindingCategory.CROSS_DOCUMENT,
            conflict_kind=ConflictKind.HARD_CONFLICT,
        )
        self.assertEqual(compute_issue_priority(issue), 55)

    def test_warning_ids_validation_no_conflict_is_mid(self) -> None:
        issue = ValidationIssue(
            rule_id="R2",
            severity=Severity.WARNING,
            message="msg",
            category=FindingCategory.IDS_VALIDATION,
        )
        self.assertEqual(compute_issue_priority(issue), 30)

    def test_info_ifc_validation_is_lowest(self) -> None:
        issue = ValidationIssue(
            rule_id="R3",
            severity=Severity.INFO,
            message="msg",
            category=FindingCategory.IFC_VALIDATION,
        )
        self.assertEqual(compute_issue_priority(issue), 10)

    def test_default_issue_is_zero(self) -> None:
        issue = ValidationIssue(rule_id="R4", severity=Severity.INFO, message="msg")
        self.assertEqual(compute_issue_priority(issue), 10)


class ConfidenceScoringTests(unittest.TestCase):
    """Tests for deterministic confidence scoring."""

    def test_structured_text_full_columns_is_highest(self) -> None:
        req = ParsedRequirement(
            rule_id="R1",
            ifc_entity="IfcWall",
            property_set="Pset_WallCommon",
            property_name="LoadBearing",
            expected_value="true",
            unit="m",
            source_kind=SourceKind.STRUCTURED_TEXT,
        )
        from aerobim.application.services.confidence_scorer import score_confidence

        self.assertAlmostEqual(score_confidence(req), 1.0, places=2)

    def test_technical_specification_is_lower(self) -> None:
        req = ParsedRequirement(
            rule_id="R2",
            expected_value="REI60",
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
        )
        from aerobim.application.services.confidence_scorer import score_confidence

        score = score_confidence(req)
        self.assertLess(score, 0.85)
        self.assertGreaterEqual(score, 0.5)

    def test_drawing_annotation_without_value_is_lowest(self) -> None:
        req = ParsedRequirement(
            rule_id="R3",
            source_kind=SourceKind.DRAWING,
        )
        from aerobim.application.services.confidence_scorer import score_confidence

        score = score_confidence(req)
        self.assertLess(score, 0.7)

    def test_missing_expected_value_penalty_applies(self) -> None:
        req = ParsedRequirement(
            rule_id="R4",
            ifc_entity="IfcWall",
            property_set="Pset_WallCommon",
            property_name="LoadBearing",
            source_kind=SourceKind.STRUCTURED_TEXT,
        )
        from aerobim.application.services.confidence_scorer import score_confidence

        score = score_confidence(req)
        self.assertLess(score, 1.0)
        self.assertGreaterEqual(score, 0.8)


class MetadataPropagationTests(unittest.TestCase):
    """Tests for source_id, evidence_modality, confidence roundtrip."""

    def test_source_id_evidence_modality_confidence_roundtrip_through_store(self) -> None:
        import tempfile

        from aerobim.domain.models import (
            ConflictKind,
            FindingCategory,
            Severity,
            ValidationIssue,
            ValidationReport,
        )
        from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore

        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemAuditStore(Path(tmp))
            report = ValidationReport(
                report_id="rpt-meta",
                request_id="req-meta",
                ifc_path=Path("sample.ifc"),
                created_at="2026-04-09T12:00:00Z",
                requirements=(),
                issues=(
                    ValidationIssue(
                        rule_id="META-001",
                        severity=Severity.WARNING,
                        message="Meta test",
                        category=FindingCategory.CROSS_DOCUMENT,
                        conflict_kind=ConflictKind.UNIT_MISMATCH,
                        source_id="tz-v1",
                        evidence_modality="technical-specification",
                        confidence=0.85,
                    ),
                ),
                summary=ValidationSummary(
                    requirement_count=0,
                    issue_count=0,
                    error_count=0,
                    warning_count=0,
                    passed=True,
                ),
            )

            store.save(report)
            loaded = store.get("rpt-meta")

            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(len(loaded.issues), 1)
            issue = loaded.issues[0]
            self.assertEqual(issue.source_id, "tz-v1")
            self.assertEqual(issue.evidence_modality, "technical-specification")
            self.assertEqual(issue.confidence, 0.85)


class ApiMalformedInputTests(unittest.TestCase):
    """Tests for malformed/edge-case API inputs."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_missing_ifc_path_rejected(self) -> None:
        response = self.client.post("/v1/validate/ifc", json={})
        self.assertEqual(response.status_code, 422)

    def test_empty_body_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            content=b"",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 422)

    def test_non_json_body_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            content=b"not json",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 422)

    def test_oversized_requirement_text_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            json={"ifc_path": "model.ifc", "requirement_text": "x" * 60_000},
        )
        self.assertEqual(response.status_code, 422)

    def test_analyze_missing_ifc_path_rejected(self) -> None:
        response = self.client.post("/v1/analyze/project-package", json={})
        self.assertEqual(response.status_code, 422)

    def test_analyze_too_many_drawings_rejected(self) -> None:
        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": "model.ifc",
                "drawings": [{"text": ""} for _ in range(65)],
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_report_id_not_found_returns_404(self) -> None:
        import uuid

        valid_but_missing_id = uuid.uuid4().hex
        response = self.client.get(f"/v1/reports/{valid_but_missing_id}")
        self.assertEqual(response.status_code, 404)

    def test_invalid_report_id_returns_400(self) -> None:
        response = self.client.get("/v1/reports/invalid-id-xyz")
        self.assertEqual(response.status_code, 400)


class ApiAnalyzeProjectPackageIdsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        import tempfile

        from aerobim.core.config.settings import Settings
        from aerobim.core.di.container import Container, Lifecycle
        from aerobim.core.di.tokens import Tokens
        from aerobim.domain.models import (
            FindingCategory,
            Severity,
            ValidationIssue,
            ValidationReport,
            ValidationSummary,
        )
        from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
        from aerobim.presentation.http.api import create_http_app

        class _NoOpValidateUseCase:
            def execute(self, _request):
                return ValidationReport(
                    report_id="0" * 32,
                    request_id="noop",
                    ifc_path=Path("noop.ifc"),
                    created_at="2026-04-11T00:00:00+00:00",
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(
                        requirement_count=0,
                        issue_count=0,
                        error_count=0,
                        warning_count=0,
                        passed=True,
                    ),
                )

        class _RecordingAnalyzeUseCase:
            def __init__(self) -> None:
                self.last_request = None

            def execute(self, request):
                self.last_request = request
                return ValidationReport(
                    report_id="1" * 32,
                    request_id=request.request_id,
                    ifc_path=request.ifc_path,
                    created_at="2026-04-11T00:00:00+00:00",
                    requirements=(),
                    issues=(
                        ValidationIssue(
                            rule_id="IDS-API-001",
                            severity=Severity.WARNING,
                            message="IDS propagated through API",
                            category=FindingCategory.IDS_VALIDATION,
                        ),
                    ),
                    summary=ValidationSummary(
                        requirement_count=0,
                        issue_count=1,
                        error_count=0,
                        warning_count=1,
                        passed=True,
                    ),
                )

        temp_dir = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temp_dir.cleanup)
        settings = Settings(
            application_name="test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(temp_dir.name),
            debug=True,
            cors_origins=_TEST_CORS_ORIGINS,
            allow_anonymous_dev=True,
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)

        store = InMemoryAuditStore()
        container = Container()
        cls.analyze_use_case = _RecordingAnalyzeUseCase()
        container.register(Tokens.SETTINGS, lambda _: settings)
        container.register(Tokens.LOGGER, lambda _: _NullLogger(), lifecycle=Lifecycle.SINGLETON)
        container.register(
            Tokens.AUDIT_REPORT_STORE,
            lambda _: store,
            lifecycle=Lifecycle.SINGLETON,
        )
        container.register(
            Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE,
            lambda _: _NoOpValidateUseCase(),
            lifecycle=Lifecycle.SINGLETON,
        )
        container.register(
            Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE,
            lambda _: cls.analyze_use_case,
            lifecycle=Lifecycle.SINGLETON,
        )

        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_analyze_project_package_accepts_ids_path(self) -> None:
        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": "models/model.ifc",
                "ids_path": "rules/project.ids",
                "requirement_text": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["warning_count"], 1)
        assert self.analyze_use_case.last_request is not None
        self.assertEqual(self.analyze_use_case.last_request.ids_path.name, "project.ids")
        self.assertEqual(self.analyze_use_case.last_request.ifc_path.name, "model.ifc")


def _make_async_job_test_client(analyze_use_case):
    import tempfile

    from fastapi.testclient import TestClient

    from aerobim.application.use_cases.analyze_project_package_jobs import (
        AnalyzeProjectPackageJobRunner,
        GetAnalyzeProjectPackageJobStatusUseCase,
        SubmitAnalyzeProjectPackageJobUseCase,
    )
    from aerobim.core.config.settings import Settings
    from aerobim.core.di.container import Container, Lifecycle
    from aerobim.core.di.tokens import Tokens
    from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
        InMemoryAnalyzeProjectPackageJobStore,
    )
    from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
    from aerobim.presentation.http.api import create_http_app

    class _NoOpValidateUseCase:
        def execute(self, _request):
            return ValidationReport(
                report_id="0" * 32,
                request_id="noop",
                ifc_path=Path("noop.ifc"),
                created_at="2026-04-11T00:00:00+00:00",
                requirements=(),
                issues=(),
                summary=ValidationSummary(
                    requirement_count=0,
                    issue_count=0,
                    error_count=0,
                    warning_count=0,
                    passed=True,
                ),
            )

    temp_dir = tempfile.TemporaryDirectory()
    settings = Settings(
        application_name="test",
        environment="test",
        host="127.0.0.1",
        port=8080,
        storage_dir=Path(temp_dir.name),
        debug=True,
        cors_origins=_TEST_CORS_ORIGINS,
        allow_anonymous_dev=True,
    )
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    audit_store = InMemoryAuditStore()
    job_store = InMemoryAnalyzeProjectPackageJobStore()
    container = Container()
    container.register(Tokens.SETTINGS, lambda _: settings)
    container.register(Tokens.LOGGER, lambda _: _NullLogger(), lifecycle=Lifecycle.SINGLETON)
    container.register(
        Tokens.AUDIT_REPORT_STORE, lambda _: audit_store, lifecycle=Lifecycle.SINGLETON
    )
    container.register(
        Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE,
        lambda _: _NoOpValidateUseCase(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE,
        lambda _: analyze_use_case,
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE,
        lambda _: job_store,
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.SUBMIT_ANALYZE_PROJECT_PACKAGE_JOB_USE_CASE,
        lambda current: SubmitAnalyzeProjectPackageJobUseCase(
            current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.GET_ANALYZE_PROJECT_PACKAGE_JOB_STATUS_USE_CASE,
        lambda current: GetAnalyzeProjectPackageJobStatusUseCase(
            current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_JOB_RUNNER,
        lambda current: AnalyzeProjectPackageJobRunner(
            analyze_use_case=current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE),
            job_store=current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE),
            logger=current.resolve(Tokens.LOGGER),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )

    app = create_http_app(container)
    client = TestClient(app)
    return client, temp_dir


class ApiAnalyzeProjectPackageJobTests(unittest.TestCase):
    def test_submit_job_returns_202_and_status_endpoint_reports_success(self) -> None:
        class _SucceedingAnalyzeUseCase:
            def __init__(self) -> None:
                self.last_request = None

            def execute(self, request):
                self.last_request = request
                return ValidationReport(
                    report_id="2" * 32,
                    request_id=request.request_id,
                    ifc_path=request.ifc_path,
                    created_at="2026-04-14T12:00:00+00:00",
                    project_name=request.project_name,
                    discipline=request.discipline,
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(
                        requirement_count=0,
                        issue_count=0,
                        error_count=0,
                        warning_count=0,
                        passed=True,
                    ),
                )

        analyze_use_case = _SucceedingAnalyzeUseCase()
        client, temp_dir = _make_async_job_test_client(analyze_use_case)
        self.addCleanup(temp_dir.cleanup)

        response = client.post(
            "/v1/analyze/project-package/submit",
            json={
                "ifc_path": "models/model.ifc",
                "requirement_text": "REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                "project_name": "Residential Tower Alpha",
                "discipline": "architecture",
            },
        )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertEqual(payload["request_id"], payload["request_id"])
        self.assertIn("job_id", payload)
        self.assertEqual(
            payload["status_url"], f"/v1/analyze/project-package/jobs/{payload['job_id']}"
        )

        status_response = client.get(payload["status_url"])
        self.assertEqual(status_response.status_code, 200)
        status_payload = status_response.json()
        self.assertEqual(status_payload["status"], "succeeded")
        self.assertEqual(status_payload["report_id"], "2" * 32)
        self.assertEqual(status_payload["report_url"], f"/v1/reports/{'2' * 32}")
        self.assertEqual(analyze_use_case.last_request.project_name, "Residential Tower Alpha")
        self.assertEqual(analyze_use_case.last_request.discipline, "architecture")

    def test_submit_job_surfaces_failed_status_when_background_run_raises(self) -> None:
        class _FailingAnalyzeUseCase:
            def execute(self, _request):
                raise ValueError(
                    "No requirements were extracted or synthesized from the provided sources"
                )

        client, temp_dir = _make_async_job_test_client(_FailingAnalyzeUseCase())
        self.addCleanup(temp_dir.cleanup)

        response = client.post(
            "/v1/analyze/project-package/submit",
            json={
                "ifc_path": "models/model.ifc",
                "requirement_text": "REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
            },
        )

        self.assertEqual(response.status_code, 202)
        status_response = client.get(response.json()["status_url"])
        self.assertEqual(status_response.status_code, 200)
        status_payload = status_response.json()
        self.assertEqual(status_payload["status"], "failed")
        self.assertIn("No requirements", status_payload["error_message"])
        self.assertIsNone(status_payload["report_id"])

    def test_get_unknown_async_job_returns_404(self) -> None:
        class _SucceedingAnalyzeUseCase:
            def execute(self, request):
                return ValidationReport(
                    report_id="2" * 32,
                    request_id=request.request_id,
                    ifc_path=request.ifc_path,
                    created_at="2026-04-14T12:00:00+00:00",
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(
                        requirement_count=0,
                        issue_count=0,
                        error_count=0,
                        warning_count=0,
                        passed=True,
                    ),
                )

        client, temp_dir = _make_async_job_test_client(_SucceedingAnalyzeUseCase())
        self.addCleanup(temp_dir.cleanup)

        response = client.get(f"/v1/analyze/project-package/jobs/{'f' * 32}")

        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
