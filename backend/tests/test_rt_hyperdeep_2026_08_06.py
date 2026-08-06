"""Red Team hyperdeep fixes 2026-08-06 — classifier, storage jail, ACL 404, policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.application.services.analyze_orchestrators import (
    EvidenceAssembler,
    _advisory_object_kind,
)
from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.core.security.path_jail import (
    PathJailError,
    safe_storage_token,
    tenant_storage_prefix,
)
from aerobim.core.security.upload_quota import FilesystemUploadQuotaStore, UploadQuotaExceeded
from aerobim.domain.advisory_remark_compose import build_remark_llm_request
from aerobim.domain.llm_advisory import MockLlmProvider
from aerobim.domain.models import RequirementSource, ValidationRequest
from aerobim.infrastructure.adapters.openai_compat_llm_provider import OpenAICompatLlmProvider


class ClassifierPublicFixtureTests(unittest.TestCase):
    def test_customer_filename_with_fixture_substring_is_confidential(self) -> None:
        request = ValidationRequest(
            request_id="rt-clf-1",
            ifc_path=Path("tenants/acme/uploads/office_fixture_v2.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="acme",
        )
        self.assertEqual(_advisory_object_kind(request), "ifc")

    def test_samples_prefix_is_public_fixture(self) -> None:
        request = ValidationRequest(
            request_id="rt-clf-2",
            ifc_path=Path("samples/ifc/wall.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="tenant-a",
        )
        self.assertEqual(_advisory_object_kind(request), "public_fixture")

    def test_absolute_deploy_under_samples_with_tenants_stays_confidential(self) -> None:
        # RT-WH-01: D:\work\samples\AeroBIM\var\…\tenants\… must not become public_fixture.
        request = ValidationRequest(
            request_id="rt-clf-abs",
            ifc_path=Path(r"D:/work/samples/AeroBIM/var/reports/tenants/acme/uploads/model.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="acme",
        )
        self.assertEqual(_advisory_object_kind(request), "ifc")

    def test_samples_customer_corpus_is_never_public(self) -> None:
        request = ValidationRequest(
            request_id="rt-clf-cust",
            ifc_path=Path("samples/customer/nda-pack/model.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="acme",
        )
        self.assertEqual(_advisory_object_kind(request), "ifc")

    def test_absolute_repo_samples_ifc_is_public_fixture(self) -> None:
        request = ValidationRequest(
            request_id="rt-clf-abs-ok",
            ifc_path=Path(r"C:/plans/AeroBIM/samples/ifc/wall.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="tenant-a",
        )
        self.assertEqual(_advisory_object_kind(request), "public_fixture")

    def test_llm_data_policy_default_denies_synthetic(self) -> None:
        from aerobim.domain.llm_advisory import LlmDataPolicy

        self.assertIs(LlmDataPolicy().allow_synthetic_public, False)

    def test_yandex_blocked_on_customer_fixture_named_upload(self) -> None:
        provider = OpenAICompatLlmProvider(
            base_url="http://127.0.0.1:9/v1",
            model="qwen",
            provider="yandex-ai-studio",
            model_revision="pin",
            transport=lambda *_a, **_k: b"{}",
        )

        class _Host:
            def __init__(self) -> None:
                self._llm_advisory_provider = provider
                self._hybrid_route_gate = HybridRouteGate()
                self._remark_locale = "ru"

            def _overlay_llm_remarks(self, *a, **k):  # noqa: ANN002, ANN003
                raise AssertionError("overlay must not run for confidential IFC")

        assembler = EvidenceAssembler(_Host())  # type: ignore[arg-type]
        request = ValidationRequest(
            request_id="rt-clf-3",
            ifc_path=Path("tenants/acme/uploads/office_fixture_v2.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="acme",
        )
        allowed, trace = assembler._evaluate_llm_overlay_gate(request)
        self.assertFalse(allowed)
        assert trace is not None
        self.assertEqual(trace["status"], "blocked")


class StorageTokenJailTests(unittest.TestCase):
    def test_dotdot_token_rejected(self) -> None:
        with self.assertRaises(PathJailError):
            safe_storage_token("..")
        with self.assertRaises(PathJailError):
            safe_storage_token(".")

    def test_dot_in_tenant_is_encoded(self) -> None:
        self.assertEqual(safe_storage_token("a.b"), "a!2eb")

    def test_slash_vs_encoded_no_double_encode_collision(self) -> None:
        # tenant_storage_prefix encodes once; a/b and a!2fb must not collide.
        slash = tenant_storage_prefix("a/b")
        literal = tenant_storage_prefix("a!2fb")
        self.assertEqual(slash, "tenants/a!2fb/")
        self.assertEqual(literal, "tenants/a!212fb/")
        self.assertNotEqual(slash, literal)

    def test_quota_rejects_dotdot_tenant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemUploadQuotaStore(Path(tmp), max_uploads_per_day=10)
            with self.assertRaises(UploadQuotaExceeded):
                store.reserve("..", size_bytes=1)


class LlmDataPolicyFailClosedTests(unittest.TestCase):
    def test_compose_defaults_block_without_synthetic_flag(self) -> None:
        request = build_remark_llm_request(
            request_id="rt-pol-1",
            findings=({"finding_id": "f1", "element_guid": "GUID"},),
            allow_customer_data=False,
        )
        self.assertFalse(request.data_policy.allow_synthetic_public)
        response = MockLlmProvider(provider="mock", model="mock").generate(request)
        self.assertEqual(response.status, "blocked_by_policy")

    def test_synthetic_public_allows_open_corpus(self) -> None:
        request = build_remark_llm_request(
            request_id="rt-pol-2",
            findings=({"finding_id": "f1"},),
            allow_customer_data=False,
            allow_synthetic_public=True,
        )
        response = MockLlmProvider(provider="mock", model="mock").generate(request)
        self.assertEqual(response.status, "advisory")


if __name__ == "__main__":
    unittest.main()
