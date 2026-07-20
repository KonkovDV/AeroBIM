"""RTATOM Wave A1 (+ critical A2) remediation regressions (2026-07-20)."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.core.security.path_jail import (
    PathJailError,
    assert_path_under_tenant_prefix,
    safe_storage_token,
    tenant_storage_prefix,
)
from aerobim.core.security.upload_quota import FilesystemUploadQuotaStore
from aerobim.domain.models import (
    ClashResult,
    ReviewEvent,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.review_state_machine import latest_hitl_state
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app
from aerobim.tools.export_evidence_bundle import _render_bundle_html


class SafeStorageTokenTests(unittest.TestCase):
    def test_slash_and_underscore_do_not_collide(self) -> None:
        slash = safe_storage_token("Tenant/A")
        underscore = safe_storage_token("Tenant_A")
        self.assertNotEqual(slash, underscore)
        self.assertEqual(underscore, "Tenant_A")
        self.assertEqual(slash, "Tenant!2fA")

    def test_colon_is_hex_encoded(self) -> None:
        self.assertEqual(safe_storage_token("a:b"), "a!3ab")

    def test_empty_token_rejected(self) -> None:
        with self.assertRaises(PathJailError):
            safe_storage_token("   ")

    def test_tenant_prefix_uses_encoding(self) -> None:
        self.assertEqual(tenant_storage_prefix("Tenant/A"), "tenants/Tenant!2fA/")


class PathJailTenantPrefixTests(unittest.TestCase):
    def test_assert_path_under_tenant_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            allowed = base / "tenants" / "Tenant!2fA" / "uploads" / "x.ifc"
            allowed.parent.mkdir(parents=True)
            allowed.write_text("ok", encoding="utf-8")
            assert_path_under_tenant_prefix(
                allowed, base=base, tenant_id="Tenant/A"
            )
            outsider = base / "tenants" / "Tenant_A" / "uploads" / "x.ifc"
            outsider.parent.mkdir(parents=True)
            outsider.write_text("no", encoding="utf-8")
            with self.assertRaises(PathJailError):
                assert_path_under_tenant_prefix(
                    outsider, base=base, tenant_id="Tenant/A"
                )


class ClashPolicyFlipTests(unittest.TestCase):
    def test_production_policy_forces_clash_affects_pass(self) -> None:
        policy = build_signoff_policy(
            profile="production",
            clash_affects_pass=False,
            require_clash=False,
        )
        self.assertTrue(policy.clash_affects_pass)
        self.assertTrue(policy.require_clash)

    def test_hard_clash_flip_uses_policy_not_host_flag(self) -> None:
        policy = build_signoff_policy(
            profile="production",
            clash_affects_pass=False,
        )
        hard = (
            ClashResult(
                element_a_guid="a",
                element_b_guid="b",
                distance=0.0,
                clash_type="hard",
                description="overlap",
            ),
        )
        passed = True
        if policy.clash_affects_pass:
            hard_clashes = tuple(
                clash for clash in hard if getattr(clash, "clash_type", "hard") != "clearance"
            )
            if hard_clashes:
                passed = False
        self.assertFalse(passed)


class HitlPreviousStateSsotTests(unittest.TestCase):
    def test_latest_hitl_state_from_store(self) -> None:
        events = [
            ReviewEvent(
                event_id="1",
                report_id="r" * 32,
                event_type="escalated",
                created_at="2026-07-20T00:00:00Z",
                finding_id="f1",
                resulting_state="escalated",
            ),
            ReviewEvent(
                event_id="2",
                report_id="r" * 32,
                event_type="opened",
                created_at="2026-07-20T00:01:00Z",
                finding_id="f1",
                previous_state="escalated",
                resulting_state="opened",
            ),
        ]
        self.assertEqual(latest_hitl_state(events, "f1", None), "opened")
        self.assertIsNone(latest_hitl_state(events, "other", None))

    def test_client_previous_state_mismatch_returns_400(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp)
            settings = Settings(
                application_name="aerobim-hitl-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=storage,
                debug=True,
                api_bearer_token="secret-token",
                api_tenant_id="tenant-a",
                enforce_object_acl=True,
                allow_anonymous_dev=False,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            report_id = uuid4().hex
            ifc_path = storage / "tenants" / "tenant-a" / "uploads" / "m.ifc"
            ifc_path.parent.mkdir(parents=True)
            ifc_path.write_text("ISO-10303-21;\n", encoding="utf-8")
            store = container.resolve(Tokens.AUDIT_REPORT_STORE)
            store.save(
                ValidationReport(
                    report_id=report_id,
                    request_id="hitl-req",
                    ifc_path=ifc_path,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(0, 0, 0, 0, True),
                    tenant_id="tenant-a",
                )
            )
            review_store = container.resolve(Tokens.REVIEW_EVENT_STORE)
            review_store.append(
                ReviewEvent(
                    event_id="seed1",
                    report_id=report_id,
                    event_type="escalated",
                    created_at=datetime.now(tz=UTC).isoformat(),
                    finding_id="finding-1",
                    resulting_state="escalated",
                    sequence_number=1,
                )
            )
            response = client.post(
                f"/v1/reports/{report_id}/review-events",
                headers={"Authorization": "Bearer secret-token"},
                json={
                    "event_type": "opened",
                    "finding_id": "finding-1",
                    "actor": "expert-1",
                    "previous_state": "opened",
                },
            )
            self.assertEqual(response.status_code, 400, response.text)
            self.assertIn("previous_state", response.text)


class EvidenceHtmlEnforcedTests(unittest.TestCase):
    def test_render_uses_enforced_passed(self) -> None:
        report = SimpleNamespace(
            report_id="rep-1",
            issues=(),
            summary=SimpleNamespace(
                passed=True,
                error_count=0,
                warning_count=0,
                issue_count=0,
            ),
        )
        html = _render_bundle_html(
            report=report,
            pack_id="pack-1",
            derived="FAIL",
            coverage={"fields": {}},
            code_version="test@0",
            enforced_passed=False,
        )
        self.assertIn("summary.passed=FAILED", html)
        self.assertNotIn("summary.passed=PASSED", html)


class QuotaFailClosedTests(unittest.TestCase):
    def test_corrupt_quota_raises_when_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemUploadQuotaStore(Path(tmp), fail_closed=True)
            path = store._path("tenant-a", store._day())  # noqa: SLF001
            path.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                store.snapshot("tenant-a")

    def test_corrupt_quota_resets_when_soft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemUploadQuotaStore(Path(tmp), fail_closed=False)
            path = store._path("tenant-a", store._day())  # noqa: SLF001
            path.write_text("{not-json", encoding="utf-8")
            snap = store.snapshot("tenant-a")
            self.assertEqual(snap.upload_count, 0)


class ReportIntegrityHashTests(unittest.TestCase):
    def test_tampered_report_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = FilesystemAuditStore(root, fail_closed=False)
            ifc = root / "tenants" / "t1" / "uploads" / "m.ifc"
            ifc.parent.mkdir(parents=True)
            ifc.write_text("ISO-10303-21;\n", encoding="utf-8")
            report_id = uuid4().hex
            store.save(
                ValidationReport(
                    report_id=report_id,
                    request_id="integrity",
                    ifc_path=ifc,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(0, 0, 0, 0, True),
                    tenant_id="t1",
                )
            )
            report_path = root / "reports" / f"{report_id}.json"
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            payload["summary"]["passed"] = False
            report_path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertIsNone(store.get(report_id))


class CancelDiscardTests(unittest.TestCase):
    def test_discard_removes_report_and_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = FilesystemAuditStore(root)
            ifc = root / "tenants" / "t1" / "uploads" / "m.ifc"
            ifc.parent.mkdir(parents=True)
            ifc.write_text("ISO-10303-21;\n", encoding="utf-8")
            report_id = uuid4().hex
            store.save(
                ValidationReport(
                    report_id=report_id,
                    request_id="discard",
                    ifc_path=ifc,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(0, 0, 0, 0, True),
                    tenant_id="t1",
                )
            )
            self.assertIsNotNone(store.get(report_id))
            self.assertTrue(store.discard(report_id))
            self.assertIsNone(store.get(report_id))
            self.assertFalse((root / "reports" / f"{report_id}.json").exists())
            self.assertFalse((root / "reports" / f"{report_id}.committed.json").exists())


class SoftSpfSchemaTests(unittest.TestCase):
    def test_soft_spf_is_not_verified(self) -> None:
        from aerobim.application.use_cases.analyze_project_package import (
            AnalyzeProjectPackageUseCase,
        )
        from aerobim.domain.models import CapabilityState
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

        uc = AnalyzeProjectPackageUseCase(
            requirement_extractor=StructuredRequirementExtractor(),
            narrative_rule_synthesizer=NarrativeRuleSynthesizer(),
            drawing_analyzer=StructuredDrawingAnalyzer(),
            ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=InMemoryAuditStore(),
            require_bsi_schema=False,
        )
        caps = uc._build_capabilities(  # noqa: SLF001
            requirements=(),
            ifc_issues=[],
            ids_path=None,
            ids_issues=[],
            clash_capability=None,
            drawing_sources=(),
            drawing_annotation_count=0,
            schema_issues=[],
            ids_audit_issues=[],
            schema_request_id="spf-pregate-only",
        )
        self.assertIs(caps.ifc_schema.status, CapabilityState.NOT_VERIFIED)


class ListReportsTenantScopeTests(unittest.TestCase):
    def test_soft_acl_list_filters_by_principal_tenant(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp)
            settings = Settings(
                application_name="aerobim-list-tenant",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=storage,
                debug=True,
                api_bearer_token="secret-token",
                api_tenant_id="tenant-a",
                enforce_object_acl=False,
                allow_anonymous_dev=False,
            )
            container = bootstrap_container(settings)
            store = container.resolve(Tokens.AUDIT_REPORT_STORE)
            ifc_a = storage / "tenants" / "tenant-a" / "uploads" / "a.ifc"
            ifc_b = storage / "tenants" / "tenant-b" / "uploads" / "b.ifc"
            for path in (ifc_a, ifc_b):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ISO-10303-21;\n", encoding="utf-8")
            id_a = uuid4().hex
            id_b = uuid4().hex
            store.save(
                ValidationReport(
                    report_id=id_a,
                    request_id="list-a",
                    ifc_path=ifc_a,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(0, 0, 0, 0, True),
                    tenant_id="tenant-a",
                )
            )
            store.save(
                ValidationReport(
                    report_id=id_b,
                    request_id="list-b",
                    ifc_path=ifc_b,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(0, 0, 0, 0, True),
                    tenant_id="tenant-b",
                )
            )
            client = TestClient(create_http_app(container))
            response = client.get(
                "/v1/reports",
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            ids = {item["report_id"] for item in body["reports"]}
            self.assertIn(id_a, ids)
            self.assertNotIn(id_b, ids)
            self.assertEqual(body["count"], 1)


class QuotaReleaseTests(unittest.TestCase):
    def test_release_rolls_back_reserve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemUploadQuotaStore(
                Path(tmp),
                max_uploads_per_day=10,
                max_bytes_per_day=10_000,
            )
            store.reserve("tenant-a", size_bytes=100)
            snap = store.release("tenant-a", size_bytes=100)
            self.assertEqual(snap.upload_count, 0)
            self.assertEqual(snap.bytes_used, 0)


class SoftAuthoritativeStampTests(unittest.TestCase):
    def test_soft_validate_passed_is_non_authoritative(self) -> None:
        from aerobim.application.use_cases.validate_ifc_against_ids import (
            ValidateIfcAgainstIdsUseCase,
        )
        from aerobim.domain.models import (
            ParsedRequirement,
            RequirementSource,
            ValidationRequest,
        )
        from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore

        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "m.ifc"
            ifc.write_text("ISO-10303-21;\nENDSEC;\n", encoding="utf-8")

            extractor = MagicMock()
            extractor.extract.return_value = [
                ParsedRequirement(
                    rule_id="r1",
                    ifc_entity="IfcWall",
                    property_set="Pset_WallCommon",
                    property_name="FireRating",
                    expected_value="REI60",
                )
            ]
            validator = MagicMock()
            validator.validate.return_value = []

            uc = ValidateIfcAgainstIdsUseCase(
                requirement_extractor=extractor,
                ifc_validator=validator,
                audit_report_store=InMemoryAuditStore(),
                signoff_profile="development",
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="soft-auth",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(text="IfcWall.FireRating = REI60"),
                )
            )
            self.assertTrue(report.summary.passed)
            self.assertFalse(report.summary.authoritative)


class DatastoreUrlSsrfTests(unittest.TestCase):
    def test_localhost_and_unix_allowed(self) -> None:
        from aerobim.core.security.outbound_url import assert_safe_datastore_url

        self.assertEqual(
            assert_safe_datastore_url("redis://127.0.0.1:6379/0"),
            "redis://127.0.0.1:6379/0",
        )
        self.assertEqual(
            assert_safe_datastore_url("postgresql+asyncpg://user:pass@localhost/db"),
            "postgresql+asyncpg://user:pass@localhost/db",
        )
        self.assertEqual(
            assert_safe_datastore_url("redis+unix:///var/run/redis.sock"),
            "redis+unix:///var/run/redis.sock",
        )

    def test_private_remote_blocked(self) -> None:
        from aerobim.core.security.outbound_url import (
            UnsafeOutboundUrlError,
            assert_safe_datastore_url,
        )

        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_datastore_url("redis://10.0.0.5:6379/0", resolve_dns=False)
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_datastore_url(
                "postgresql+asyncpg://u:p@169.254.169.254/db",
                resolve_dns=False,
            )


class HardCrossDocSeverityTests(unittest.TestCase):
    def test_hard_profile_forces_cross_doc_error(self) -> None:
        from aerobim.application.use_cases.analyze_project_package import (
            AnalyzeProjectPackageUseCase,
        )
        from aerobim.domain.models import Severity
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

        uc = AnalyzeProjectPackageUseCase(
            requirement_extractor=StructuredRequirementExtractor(),
            narrative_rule_synthesizer=NarrativeRuleSynthesizer(),
            drawing_analyzer=StructuredDrawingAnalyzer(),
            ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=InMemoryAuditStore(),
            cross_doc_severity="warning",
            signoff_profile="production",
        )
        self.assertIs(uc._cross_doc_severity, Severity.ERROR)  # noqa: SLF001
        self.assertTrue(uc._hard_signoff_profile)  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
