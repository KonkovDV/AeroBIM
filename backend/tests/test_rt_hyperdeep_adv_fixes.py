"""Hyperdeep adversarial fixes: RT-ADV-01..05, RT-ADV-09."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.application.use_cases.analyze_project_package_jobs import (
    GetAnalyzeProjectPackageJobStatusUseCase,
    SubmitAnalyzeProjectPackageJobUseCase,
)
from aerobim.core.config.settings import Settings
from aerobim.core.security.path_jail import (
    PathJailError,
    assert_path_under_tenant_prefix,
    resolve_storage_path,
    tenant_storage_prefix,
)
from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    CapabilityState,
    CapabilityStatus,
    JobStatus,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.basic_ifc_schema_validator import BasicIfcSchemaValidator
from aerobim.infrastructure.adapters.bcf_consumers import verify_bcf_zip_structure
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app

_MINIMAL_SPF = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('m.ifc','2026-07-19T00:00:00',(''),(''),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('0123456789ABCDEFGHIJ01',$,'P',$,$,$,$,(),$);
ENDSEC;
END-ISO-10303-21;
"""


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


class Adv01BsiSubmitAckNotOkTests(unittest.TestCase):
    def test_require_bsi_with_submit_ack_is_not_verified(self) -> None:
        class _FakeBsi:
            def submit(self, ifc_path: Path) -> str:
                return "submit-ack-only"

        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text(_MINIMAL_SPF, encoding="utf-8")
            uc = _minimal_uc(
                require_bsi_schema=True,
                ifc_schema_validator=BasicIfcSchemaValidator(),
                bsi_validation_service=_FakeBsi(),
                require_mep_system_clash=False,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="adv01",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n",
                        source_kind=SourceKind.STRUCTURED_TEXT,
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.ifc_schema.status, CapabilityState.NOT_VERIFIED)
        self.assertEqual(report.schema_validation_request_id, "submit-ack-only")
        self.assertFalse(report.summary.passed)


class Adv05PilotFailClosedTests(unittest.TestCase):
    def test_pilot_env_cannot_weaken_require_gates(self) -> None:
        previous = {
            key: os.environ.get(key)
            for key in (
                "AEROBIM_ENV",
                "AEROBIM_SIGNOFF_PROFILE",
                "AEROBIM_REQUIRE_CLASH",
                "AEROBIM_CLASH_AFFECTS_PASS",
                "AEROBIM_REQUIRE_BSI_SCHEMA",
                "AEROBIM_REQUIRE_MEP_SYSTEM_CLASH",
                "AEROBIM_ENFORCE_OBJECT_ACL",
                "AEROBIM_AUDIT_FAIL_CLOSED",
                "AEROBIM_BSI_LOCAL_CERT",
                "AEROBIM_API_BEARER_TOKEN",
            )
        }
        try:
            os.environ["AEROBIM_ENV"] = "production"
            os.environ["AEROBIM_SIGNOFF_PROFILE"] = "samolet_pilot"
            os.environ["AEROBIM_REQUIRE_CLASH"] = "false"
            os.environ["AEROBIM_CLASH_AFFECTS_PASS"] = "false"
            os.environ["AEROBIM_REQUIRE_BSI_SCHEMA"] = "false"
            os.environ["AEROBIM_REQUIRE_MEP_SYSTEM_CLASH"] = "false"
            os.environ["AEROBIM_ENFORCE_OBJECT_ACL"] = "false"
            os.environ["AEROBIM_AUDIT_FAIL_CLOSED"] = "false"
            os.environ["AEROBIM_BSI_LOCAL_CERT"] = "true"
            os.environ["AEROBIM_API_BEARER_TOKEN"] = "test-token"
            settings = Settings.from_env()
            self.assertTrue(settings.require_clash)
            self.assertTrue(settings.clash_affects_pass)
            self.assertTrue(settings.require_bsi_schema)
            self.assertTrue(settings.require_mep_system_clash)
            self.assertTrue(settings.enforce_object_acl)
            self.assertTrue(settings.audit_fail_closed)
            self.assertFalse(settings.bsi_local_cert)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


class Adv02TenantUploadPrefixTests(unittest.TestCase):
    def test_upload_uses_tenant_prefix(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                api_tenant_id="tenant-a",
                allow_anonymous_dev=True,
            )
            client = TestClient(create_http_app(bootstrap_container(settings)))
            response = client.post(
                "/v1/uploads",
                files={"file": ("pilot.ifc", b"ISO-10303-21;", "application/octet-stream")},
            )
            self.assertEqual(response.status_code, 200, response.text)
            path = response.json()["path"]
            self.assertTrue(path.startswith("tenants/tenant-a/uploads/"), path)

    def test_acl_denies_foreign_tenant_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            foreign = base / "tenants" / "tenant-b" / "uploads" / "x.ifc"
            foreign.parent.mkdir(parents=True)
            foreign.write_text("ISO-10303-21;", encoding="utf-8")
            resolved = resolve_storage_path(
                "tenants/tenant-b/uploads/x.ifc",
                base=base,
            )
            with self.assertRaises(PathJailError):
                assert_path_under_tenant_prefix(
                    resolved,
                    base=base,
                    tenant_id="tenant-a",
                )
            self.assertEqual(tenant_storage_prefix("tenant-a"), "tenants/tenant-a/")


class Adv03RedisIdempotencyRaceTests(unittest.TestCase):
    def test_set_nx_false_returns_existing_job(self) -> None:
        redis = MagicMock()
        store = object.__new__(
            __import__(
                "aerobim.infrastructure.adapters.redis_analyze_project_package_job_store",
                fromlist=["RedisAnalyzeProjectPackageJobStore"],
            ).RedisAnalyzeProjectPackageJobStore
        )
        store._redis = redis
        store._prefix = "aerobim:jobs:"

        existing = AnalyzeProjectPackageJob(
            job_id="a" * 32,
            request_id="r1",
            status=JobStatus.QUEUED,
            created_at="2026-07-19T00:00:00+00:00",
            idempotency_key="k1",
            tenant_id="t1",
        )

        # First get_by_idempotency miss, SET nx fails, second get hits winner.
        redis.get.side_effect = [
            None,  # first index lookup
            existing.job_id,  # after race
            store._serialize(existing),  # load winner job
        ]
        redis.set.side_effect = [False]  # nx claim lost

        raced = AnalyzeProjectPackageJob(
            job_id="b" * 32,
            request_id="r2",
            status=JobStatus.QUEUED,
            created_at="2026-07-19T00:00:00+00:00",
            idempotency_key="k1",
            tenant_id="t1",
        )
        job_id = store.create(raced)
        self.assertEqual(job_id, existing.job_id)


class Adv04NoReclaimOnGetTests(unittest.TestCase):
    def test_job_status_get_does_not_reclaim(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        store.reclaim_stale_running = MagicMock(return_value=[])  # type: ignore[method-assign]
        get_uc = GetAnalyzeProjectPackageJobStatusUseCase(store)
        store.create(
            AnalyzeProjectPackageJob(
                job_id="f" * 32,
                request_id="r",
                status=JobStatus.QUEUED,
                created_at="2026-07-19T00:00:00+00:00",
            )
        )
        job = get_uc.execute("f" * 32)
        assert job is not None
        store.reclaim_stale_running.assert_not_called()

    def test_submit_still_reclaims(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        store.reclaim_stale_running = MagicMock(return_value=[])  # type: ignore[method-assign]
        submit = SubmitAnalyzeProjectPackageJobUseCase(job_store=store)
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            request = ValidationRequest(
                request_id="adv04",
                ifc_path=ifc,
                requirement_source=RequirementSource(
                    text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n",
                    source_kind=SourceKind.STRUCTURED_TEXT,
                ),
                tenant_id="t1",
            )
            submit.execute(request)
        store.reclaim_stale_running.assert_called()


class AdvHitlTrailBeforeSaveTests(unittest.TestCase):
    def _host(self) -> MagicMock:
        host = MagicMock()
        host._priority_profile = "default"
        host._attach_remarks.side_effect = lambda issues: list(issues)
        host._build_capabilities.return_value = __import__(
            "aerobim.domain.models", fromlist=["ReportCapabilities"]
        ).ReportCapabilities()
        host._signoff_profile = "development"
        host._require_clash = False
        host._clash_affects_pass = False
        host._require_bsi_schema = False
        host._require_mep_system_clash = False
        host._review_event_store = MagicMock()
        host._audit_report_store = MagicMock()
        host._audit_report_store.get.return_value = None
        return host

    def _bundles(self, request: ValidationRequest):
        from aerobim.application.services.analyze_orchestrators import (
            AdvisoryBundle,
            DeterministicBundle,
            IngestionBundle,
        )
        from aerobim.domain.models import DrawingRegionRef

        region = DrawingRegionRef(
            sheet_id="AR-01",
            bbox_xyxy=(0.0, 0.0, 1.0, 0.5),
            confidence=0.2,
            modality="detector",
            hitl_required=True,
            hitl_reason="low_confidence",
        )
        skipped = CapabilityStatus(CapabilityState.SKIPPED, "n/a")
        ingested = IngestionBundle(
            request=request,
            requirements=(),
            drawing_annotations=(),
            drawing_regions=(region,),
            drawing_assets=(),
            raster_annotation_count=0,
            cad_capability=skipped,
            cad_issues=(),
            region_hitl_issues=(),
            norm_pack_capability=skipped,
            norm_pack_issues=(),
        )
        deterministic = DeterministicBundle(
            schema_issues=(),
            schema_request_id=None,
            ids_audit_issues=(),
            ids_issues=(),
            ifc_issues=(),
            drawing_issues=(),
            cross_document_issues=(),
            revision_merge_issues=(),
            section_pairing_issues=(),
            section_pairing_capability=skipped,
            reinforcement_provenance_issues=(),
            clash_results=(),
            clash_capability=skipped,
            clash_issues=(),
            mep_capability=CapabilityStatus(CapabilityState.NOT_VERIFIED, "n/a"),
            quantity_issues=(),
            quantity_capability=None,
            load_issues=(),
            calculation_match=skipped,
            logic_issues=(),
            engine_issues=(),
        )
        advisory = AdvisoryBundle(
            advisory_issues=(),
            advisory_ids_draft=None,
            reconciled_issues=(),
            divergences=(),
        )
        return ingested, deterministic, advisory

    def test_append_failure_prevents_report_save(self) -> None:
        from aerobim.application.services.analyze_orchestrators import EvidenceAssembler

        host = self._host()
        host._review_event_store.append.side_effect = RuntimeError("hitl disk full")
        request = ValidationRequest(
            request_id="hitl-tx",
            ifc_path=Path("model.ifc"),
            requirement_source=RequirementSource(
                text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n",
                source_kind=SourceKind.STRUCTURED_TEXT,
            ),
        )
        ingested, deterministic, advisory = self._bundles(request)
        with self.assertRaises(RuntimeError):
            EvidenceAssembler(host).assemble(request, ingested, deterministic, advisory)
        host._audit_report_store.save.assert_not_called()

    def test_save_failure_discards_hitl_trail(self) -> None:
        from aerobim.application.services.analyze_orchestrators import EvidenceAssembler

        host = self._host()
        host._audit_report_store.save.side_effect = OSError("report disk full")
        request = ValidationRequest(
            request_id="hitl-tx2",
            ifc_path=Path("model.ifc"),
            requirement_source=RequirementSource(
                text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n",
                source_kind=SourceKind.STRUCTURED_TEXT,
            ),
        )
        ingested, deterministic, advisory = self._bundles(request)
        with self.assertRaises(OSError):
            EvidenceAssembler(host).assemble(request, ingested, deterministic, advisory)
        host._review_event_store.append.assert_called()
        host._review_event_store.discard_report.assert_called_once()


class Adv09BcfXsdStatusTests(unittest.TestCase):
    def test_structural_errors_with_xsd_present_stay_not_run(self) -> None:
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("bcf.version", '<?xml version="1.0"?><Version VersionId="3.0"/>')
        with tempfile.TemporaryDirectory() as temporary_directory:
            xsd_dir = Path(temporary_directory) / "xsd"
            xsd_dir.mkdir()
            (xsd_dir / "markup.xsd").write_text("<xs:schema/>", encoding="utf-8")
            result = verify_bcf_zip_structure(buf.getvalue(), xsd_dir=xsd_dir)
        self.assertFalse(result.ok)
        self.assertEqual(result.xsd_status, "not_run")


if __name__ == "__main__":
    unittest.main()
