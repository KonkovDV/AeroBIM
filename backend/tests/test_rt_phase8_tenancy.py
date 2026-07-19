"""Phase 8 tenancy: job ACL, scoped idempotency, concurrency, advisory isolation."""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.application.use_cases.analyze_project_package_jobs import (
    JobConcurrencyLimitError,
    SubmitAnalyzeProjectPackageJobUseCase,
)
from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    FindingCategory,
    JobStatus,
    RequirementSource,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
)
from aerobim.domain.object_acl import AuthPrincipal, principal_may_access_job
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


def _request(*, tenant_id: str | None, request_id: str = "req") -> ValidationRequest:
    return ValidationRequest(
        request_id=request_id,
        ifc_path=Path("sample.ifc"),
        requirement_source=RequirementSource(
            text="height = 3 m",
            source_kind=SourceKind.STRUCTURED_TEXT,
        ),
        tenant_id=tenant_id,
    )


class Phase8JobTenancyUnitTests(unittest.TestCase):
    def test_idempotency_is_tenant_scoped(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        submit = SubmitAnalyzeProjectPackageJobUseCase(store)
        a = submit.execute(_request(tenant_id="tenant-a"), idempotency_key="same-key")
        b = submit.execute(_request(tenant_id="tenant-b"), idempotency_key="same-key")
        self.assertNotEqual(a.job_id, b.job_id)
        self.assertEqual(a.tenant_id, "tenant-a")
        self.assertEqual(b.tenant_id, "tenant-b")
        again = submit.execute(_request(tenant_id="tenant-a"), idempotency_key="same-key")
        self.assertEqual(again.job_id, a.job_id)

    def test_concurrency_limit_per_tenant(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        submit = SubmitAnalyzeProjectPackageJobUseCase(store)
        submit.execute(_request(tenant_id="t1", request_id="1"), max_concurrent_per_tenant=1)
        with self.assertRaises(JobConcurrencyLimitError):
            submit.execute(_request(tenant_id="t1", request_id="2"), max_concurrent_per_tenant=1)
        # Other tenant unaffected.
        other = submit.execute(
            _request(tenant_id="t2", request_id="3"),
            max_concurrent_per_tenant=1,
        )
        self.assertEqual(other.tenant_id, "t2")

    def test_principal_may_access_job(self) -> None:
        job = AnalyzeProjectPackageJob(
            job_id="a" * 32,
            request_id="r",
            status=JobStatus.QUEUED,
            created_at=datetime.now(tz=UTC).isoformat(),
            tenant_id="tenant-a",
        )
        self.assertTrue(
            principal_may_access_job(
                enforce_object_acl=True,
                principal=AuthPrincipal(tenant_id="tenant-a"),
                job=job,
            )
        )
        self.assertFalse(
            principal_may_access_job(
                enforce_object_acl=True,
                principal=AuthPrincipal(tenant_id="tenant-b"),
                job=job,
            )
        )


class Phase8JobAclApiTests(unittest.TestCase):
    def _client(self, *, storage: Path, tenant: str):
        from fastapi.testclient import TestClient

        settings = Settings(
            application_name="aerobim-p8",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=storage,
            debug=True,
            api_bearer_token="secret-token",
            api_tenant_id=tenant,
            enforce_object_acl=True,
            allow_anonymous_dev=False,
        )
        container = bootstrap_container(settings)
        return TestClient(create_http_app(container)), container

    def test_cross_tenant_job_get_and_cancel_denied(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client_a, container = self._client(storage=Path(tmp), tenant="tenant-a")
            store = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
            job_id = uuid4().hex
            store.create(
                AnalyzeProjectPackageJob(
                    job_id=job_id,
                    request_id="foreign",
                    status=JobStatus.QUEUED,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    tenant_id="tenant-b",
                )
            )
            headers = {"Authorization": "Bearer secret-token"}
            get_resp = client_a.get(
                f"/v1/analyze/project-package/jobs/{job_id}",
                headers=headers,
            )
            self.assertEqual(get_resp.status_code, 403, get_resp.text)
            cancel_resp = client_a.post(
                f"/v1/analyze/project-package/jobs/{job_id}/cancel",
                headers=headers,
            )
            self.assertEqual(cancel_resp.status_code, 403, cancel_resp.text)


class Phase8AdvisoryIsolationTests(unittest.TestCase):
    def test_advisory_error_cannot_raise_engine_error_count(self) -> None:
        gate = DeterminismGate()
        engine = (
            ValidationIssue(
                rule_id="DET-1",
                severity=Severity.WARNING,
                message="deterministic warning",
                category=FindingCategory.IFC_VALIDATION,
                origin="deterministic",
            ),
        )
        advisory = (
            ValidationIssue(
                rule_id="ADV-1",
                severity=Severity.ERROR,
                message="advisory hallucination",
                category=FindingCategory.IFC_VALIDATION,
                origin="advisory",
            ),
        )
        reconciled, divergences = gate.reconcile(engine_issues=engine, advisory_issues=advisory)
        self.assertEqual(sum(1 for i in reconciled if i.severity is Severity.ERROR), 0)
        advisory_info = [
            i for i in reconciled if i.rule_id == "ADV-1" and i.severity is Severity.INFO
        ]
        self.assertTrue(advisory_info)
        self.assertTrue(divergences)


class Phase8ValidateIfcTenantStampTests(unittest.TestCase):
    def test_validate_ifc_stamps_principal_tenant(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        samples = Path(__file__).resolve().parents[2] / "samples" / "ifc"
        ifc_files = list(samples.glob("*.ifc")) if samples.exists() else []
        if not ifc_files:
            raise unittest.SkipTest("no IFC fixtures")

        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp)
            target = storage / "model.ifc"
            target.write_bytes(ifc_files[0].read_bytes())
            client, container = Phase8JobAclApiTests()._client(
                storage=storage,
                tenant="tenant-stamp",
            )
            response = client.post(
                "/v1/validate/ifc",
                headers={"Authorization": "Bearer secret-token"},
                json={
                    "ifc_path": "model.ifc",
                    "requirement_text": "R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n",
                },
            )
            self.assertEqual(response.status_code, 200, response.text)
            report_id = response.json()["report_id"]
            store = container.resolve(Tokens.AUDIT_REPORT_STORE)
            report = store.get(report_id)
            assert isinstance(report, ValidationReport)
            self.assertEqual(report.tenant_id, "tenant-stamp")


if __name__ == "__main__":
    unittest.main()
