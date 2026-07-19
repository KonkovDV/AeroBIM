"""Post-Phase-10 residuals: norm-pack tenant ACL + report-save exclusive lock."""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.application.use_cases.apply_norm_rule_hitl_event import ApplyNormRuleHitlEventUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ValidationReport, ValidationSummary
from aerobim.domain.object_acl import AuthPrincipal, principal_may_access_norm_pack
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.filesystem_review_event_store import FilesystemReviewEventStore
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore
from aerobim.infrastructure.adapters.object_store_norm_pack_version_store import (
    ObjectStoreNormRulePackVersionStore,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PACK = REPO_ROOT / "samples" / "rule-packs" / "residential-ar-reference-template.json"


class NormPackTenantIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.store = ObjectStoreNormRulePackVersionStore(
            LocalObjectStore(root / "objects"),
            index_dir=root / "index",
        )
        self.use_case = ApplyNormRuleHitlEventUseCase(
            version_store=self.store,
            review_event_store=FilesystemReviewEventStore(root / "events"),
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_versions_are_tenant_namespaced(self) -> None:
        pack_id = "SAMOLET-RESIDENTIAL-AR-REFERENCE"
        a, _ = self.use_case.execute(
            pack_id=pack_id,
            base_pack_path=REFERENCE_PACK,
            event_type="norm_rule_proposed",
            rule_diff={"rule_id": "SAM-AR-001", "evidence_text": "a"},
            proposed_by="eng-a",
            target_approval_status="draft",
            tenant_id="tenant-a",
        )
        b, _ = self.use_case.execute(
            pack_id=pack_id,
            base_pack_path=REFERENCE_PACK,
            event_type="norm_rule_proposed",
            rule_diff={"rule_id": "SAM-AR-001", "evidence_text": "b"},
            proposed_by="eng-b",
            target_approval_status="draft",
            tenant_id="tenant-b",
        )
        self.assertNotEqual(a.object_key, b.object_key)
        self.assertTrue(a.object_key.startswith("tenants/tenant-a/"))
        self.assertTrue(b.object_key.startswith("tenants/tenant-b/"))
        self.assertEqual(len(self.store.list_versions(pack_id, tenant_id="tenant-a")), 1)
        self.assertEqual(len(self.store.list_versions(pack_id, tenant_id="tenant-b")), 1)
        self.assertEqual(len(self.store.list_versions(pack_id, tenant_id="tenant-c")), 0)

    def test_principal_may_access_norm_pack(self) -> None:
        self.assertTrue(
            principal_may_access_norm_pack(
                enforce_object_acl=True,
                principal=AuthPrincipal(tenant_id="t1"),
                tenant_id="t1",
            )
        )
        self.assertFalse(
            principal_may_access_norm_pack(
                enforce_object_acl=True,
                principal=AuthPrincipal(tenant_id="t1"),
                tenant_id="t2",
            )
        )


class NormPackAclApiTests(unittest.TestCase):
    def _client(self, *, storage: Path, tenant: str):
        from fastapi.testclient import TestClient

        settings = Settings(
            application_name="aerobim-np-acl",
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

    def test_list_versions_is_tenant_scoped(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        pack_id = "SAMOLET-RESIDENTIAL-AR-REFERENCE"
        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp)
            # Seed foreign tenant versions via store directly.
            container_seed_settings = Settings(
                application_name="seed",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=storage,
                debug=True,
                api_bearer_token="secret-token",
                api_tenant_id="tenant-b",
                enforce_object_acl=True,
                allow_anonymous_dev=False,
            )
            seed = bootstrap_container(container_seed_settings)
            versions = seed.resolve(Tokens.NORM_RULE_PACK_VERSION_STORE)
            versions.save_version(
                pack_id=pack_id,
                version="0.1.0",
                payload=REFERENCE_PACK.read_bytes(),
                created_by="seed",
                parent_version=None,
                approval_status="synthetic",
                approval_ref=None,
                tenant_id="tenant-b",
            )

            client_a, _ = self._client(storage=storage, tenant="tenant-a")
            response = client_a.get(
                f"/v1/norm-packs/{pack_id}/versions",
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["versions"], [])


class ReportSaveLockTests(unittest.TestCase):
    def test_save_acquires_and_releases_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = FilesystemAuditStore(root)
            report_id = uuid4().hex
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;\n", encoding="utf-8")
            report = ValidationReport(
                report_id=report_id,
                request_id="r1",
                ifc_path=ifc,
                created_at=datetime.now(tz=UTC).isoformat(),
                requirements=(),
                issues=(),
                summary=ValidationSummary(0, 0, 0, 0, True),
                tenant_id="t1",
            )
            store.save(report)
            lock = root / "reports" / f"{report_id}.save.lock"
            self.assertFalse(lock.exists())
            self.assertTrue((root / "reports" / f"{report_id}.json").exists())


if __name__ == "__main__":
    unittest.main()
