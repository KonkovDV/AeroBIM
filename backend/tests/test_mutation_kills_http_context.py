"""H1.1 mutation-kill tests for presentation/http/context.py (cosmic-ray survivors).

Direct unit tests of ``ApiContext`` over a stub container: the HTTP suites
exercise these branches end-to-end, but their oracles proved too coarse for
162 first-run survivors (auth fallbacks, ACL tenant binding, storage-source
resolution, status-code constants).

Final verification run (tests/mutation/context.toml, 564 mutants):
556 killed, 8 survived, 0 live gaps. All 8 survivors are documented
equivalent mutants: ``ReplaceBinaryOperator_Mul_Div`` on ``*`` keyword-only
markers (L196/263/278/352/373/428/490/512) — ``*`` -> ``/`` only changes the
calling convention and every caller passes keywords. cosmic-ray records many
kills as INCOMPETENT on ru-Windows (it crashes decoding cp1251 pytest output
of an already-failed suite); each was verified to have reached
TestOutcome.KILLED via ``work_results.output``.

Effective mutation score (equivalents excluded): 556/556 = 1.0 ≥ 0.85 target.
Each test names the mutants it kills.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    DrawingAsset,
    FindingCategory,
    GeneratedRemark,
    JobStatus,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.object_acl import AuthPrincipal
from aerobim.infrastructure.security.oidc_token_validator import OidcValidationError
from aerobim.presentation.http.context import (
    UPLOAD_HASH_CHUNK,
    UPLOAD_SNIFF_BYTES,
    ApiContext,
)


class _Logger:
    def __init__(self) -> None:
        self.warnings: list[str] = []

    def info(self, message: str, **context: object) -> None:
        pass

    def warning(self, message: str, **context: object) -> None:
        self.warnings.append(message)

    def error(self, message: str, **context: object) -> None:
        pass

    def debug(self, message: str, **context: object) -> None:
        pass


class _NoOpUseCase:
    def execute(self, request):
        raise RuntimeError("not used in these tests")


class _AuditStore:
    def __init__(self) -> None:
        self.reports: dict[str, ValidationReport] = {}

    def get(self, report_id: str):
        return self.reports.get(report_id)


class _ObjectStore:
    def __init__(self, blobs: dict[str, bytes] | None = None) -> None:
        self.blobs = blobs or {}

    def get_bytes(self, key):
        return self.blobs.get(key)


class _OidcValidator:
    def __init__(self, claims: dict | None = None, error: str | None = None) -> None:
        self.claims = claims or {}
        self.error = error

    def validate(self, token: str) -> dict:
        if self.error:
            raise OidcValidationError(self.error)
        return self.claims


def _make_ctx(
    storage: Path,
    *,
    oidc: _OidcValidator | None = None,
    object_store: _ObjectStore | None = None,
    logger: _Logger | None = None,
    **settings_kwargs,
) -> ApiContext:
    defaults = dict(
        application_name="aerobim-ctx-test",
        environment="test",
        host="127.0.0.1",
        port=8080,
        storage_dir=storage,
        debug=True,
    )
    defaults.update(settings_kwargs)
    settings = Settings(**defaults)
    container = Container()
    resolved_logger = logger or _Logger()
    container.register(Tokens.SETTINGS, lambda _: settings)
    container.register(Tokens.LOGGER, lambda _: resolved_logger)
    container.register(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE, lambda _: _NoOpUseCase())
    container.register(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE, lambda _: _NoOpUseCase())
    container.register(Tokens.AUDIT_REPORT_STORE, lambda _: _AuditStore())
    if oidc is not None:
        container.register(Tokens.OIDC_TOKEN_VALIDATOR, lambda _: oidc)
    if object_store is not None:
        container.register(Tokens.OBJECT_STORE, lambda _: object_store)
    return ApiContext(container)


def _report(
    *,
    tenant_id: str | None = None,
    ifc_path: str = "model.ifc",
    ifc_object_key: str | None = None,
    drawing_assets: tuple[DrawingAsset, ...] = (),
    issues: tuple[ValidationIssue, ...] = (),
) -> ValidationReport:
    return ValidationReport(
        report_id="c" * 32,
        request_id="req",
        ifc_path=Path(ifc_path),
        created_at=datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=issues,
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=len(issues),
            error_count=0,
            warning_count=0,
            passed=True,
        ),
        ifc_object_key=ifc_object_key,
        drawing_assets=drawing_assets,
        tenant_id=tenant_id,
    )


def _status(callable_, *args, **kwargs) -> HTTPException:
    try:
        callable_(*args, **kwargs)
    except HTTPException as exc:
        return exc
    raise AssertionError("expected HTTPException")


class UploadConstantContractTests(unittest.TestCase):
    """Kills NumberReplacer / operator mutants on the module constants (L53-54)."""

    def test_upload_hash_chunk_is_one_mebibyte(self) -> None:
        self.assertEqual(UPLOAD_HASH_CHUNK, 1048576)

    def test_upload_sniff_bytes_is_4096(self) -> None:
        self.assertEqual(UPLOAD_SNIFF_BYTES, 4096)


class AuthFallbackBranchTests(unittest.TestCase):
    """Unconfigured-auth branches (L117-135)."""

    def test_dev_without_anon_flag_is_401(self) -> None:
        # Kills ReplaceAndWithOr on `is_dev and allow_anonymous_dev` (L118)
        # and NumberReplacer on 401 (L122).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), environment="development", allow_anonymous_dev=False)
            exc = _status(ctx.require_bearer_auth, None)
            self.assertEqual(exc.status_code, 401)

    def test_nondev_without_config_is_503(self) -> None:
        # Kills AddNot on `if settings.is_dev_environment` (L120) and 503 (L130).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), environment="production", allow_anonymous_dev=True)
            exc = _status(ctx.require_bearer_auth, None)
            self.assertEqual(exc.status_code, 503)

    def test_dev_anonymous_enabled_returns_dev_principal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(
                Path(tmp),
                environment="development",
                allow_anonymous_dev=True,
                api_tenant_id="tenant-dev",
            )
            principal = ctx.require_bearer_auth(None)
            self.assertEqual(principal.subject, "anonymous-dev")
            self.assertEqual(principal.tenant_id, "tenant-dev")


class AuthSchemeParsingTests(unittest.TestCase):
    """Scheme comparison mutants on L144-153 (Gt/Lt/Is/OrWithAnd + 401 codes)."""

    def _ctx(self, tmp: Path) -> ApiContext:
        return _make_ctx(tmp, api_bearer_token="secret-token", api_tenant_id="tenant-a")

    def test_correct_token_with_basic_scheme_rejected(self) -> None:
        # Kills NotEq_Gt: "basic" > "bearer" is False, so the mutant accepts it.
        with tempfile.TemporaryDirectory() as tmp:
            exc = _status(self._ctx(Path(tmp)).require_bearer_auth, "Basic secret-token")
            self.assertEqual(exc.status_code, 401)
            self.assertEqual(exc.detail, "Invalid Authorization header format")

    def test_correct_token_with_token_scheme_rejected(self) -> None:
        # Kills NotEq_Lt: "token" < "bearer" is False, so the mutant accepts it.
        with tempfile.TemporaryDirectory() as tmp:
            exc = _status(self._ctx(Path(tmp)).require_bearer_auth, "Token secret-token")
            self.assertEqual(exc.status_code, 401)

    def test_scheme_without_token_gets_format_detail(self) -> None:
        # Kills ReplaceOrWithAnd on `!= "bearer" or not token` (L145): the
        # mutant falls through to the generic "Invalid API token" 401 instead.
        with tempfile.TemporaryDirectory() as tmp:
            exc = _status(self._ctx(Path(tmp)).require_bearer_auth, "Bearer")
            self.assertEqual(exc.status_code, 401)
            self.assertEqual(exc.detail, "Invalid Authorization header format")

    def test_uppercase_bearer_scheme_accepted(self) -> None:
        # Kills NotEq_Is: the partitioned scheme is a fresh string object, so
        # identity comparison against the literal rejects a valid header.
        with tempfile.TemporaryDirectory() as tmp:
            principal = self._ctx(Path(tmp)).require_bearer_auth("BEARER secret-token")
            self.assertEqual(principal.subject, "api-bearer")
            self.assertEqual(principal.tenant_id, "tenant-a")


class OidcBranchTests(unittest.TestCase):
    """OIDC principal binding (L155-189)."""

    def test_valid_oidc_token_binds_tenant_and_subject(self) -> None:
        # Kills the L156 assert mutants and L161/L172 AddNot / IsNot_Is.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(
                Path(tmp),
                oidc=_OidcValidator(claims={"tenant_id": "t-oidc", "sub": "sub-1"}),
            )
            principal = ctx.require_bearer_auth("Bearer some-jwt")
            self.assertEqual(principal.tenant_id, "t-oidc")
            self.assertEqual(principal.subject, "sub-1")

    def test_missing_subject_maps_to_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), oidc=_OidcValidator(claims={"tenant_id": "t-oidc"}))
            self.assertIsNone(ctx.require_bearer_auth("Bearer some-jwt").subject)

    def test_configured_tenant_claim_is_used(self) -> None:
        # Kills both ReplaceOrWithAnd mutants on the claim_name chain (L159):
        # they collapse the configured claim back to "tenant_id".
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(
                Path(tmp),
                oidc=_OidcValidator(claims={"custom_tenant": "t-custom"}),
                oidc_tenant_claim="custom_tenant",
            )
            principal = ctx.require_bearer_auth("Bearer some-jwt")
            self.assertEqual(principal.tenant_id, "t-custom")

    def test_blank_tenant_claim_is_401(self) -> None:
        # Kills AddNot / Delete_Not on `if not tenant` (L162) + 401 codes (L165).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), oidc=_OidcValidator(claims={"tenant_id": "   "}))
            exc = _status(ctx.require_bearer_auth, "Bearer some-jwt")
            self.assertEqual(exc.status_code, 401)

    def test_validator_error_maps_to_generic_401_and_logs(self) -> None:
        # Kills ExceptionReplacer on `except OidcValidationError` (L176): the
        # mutant leaks the raw validator error instead of HTTPException 401.
        with tempfile.TemporaryDirectory() as tmp:
            logger = _Logger()
            ctx = _make_ctx(Path(tmp), oidc=_OidcValidator(error="boom"), logger=logger)
            exc = _status(ctx.require_bearer_auth, "Bearer bad-jwt")
            self.assertEqual(exc.status_code, 401)
            self.assertEqual(exc.detail, "Invalid API token")
            self.assertTrue(logger.warnings)

    def test_wrong_bearer_token_without_oidc_is_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), api_bearer_token="secret-token")
            exc = _status(ctx.require_bearer_auth, "Bearer wrong")
            self.assertEqual(exc.status_code, 401)
            self.assertEqual(exc.detail, "Invalid API token")


class ResolveSafePathAclTests(unittest.TestCase):
    """Path jail + tenant scoping in resolve_safe_path (L193-221)."""

    def test_acl_off_resolves_under_storage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            resolved = ctx.resolve_safe_path("uploads/x.ifc")
            self.assertTrue(str(resolved).startswith(str(Path(tmp).resolve())))

    def test_acl_on_requires_principal_with_tenant(self) -> None:
        # Kills the L207 Is_IsNot / OrWithAnd / AddNot cluster + 403 (L209).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            self.assertEqual(_status(ctx.resolve_safe_path, "uploads/x.ifc").status_code, 403)
            exc = _status(
                ctx.resolve_safe_path,
                "uploads/x.ifc",
                principal=AuthPrincipal(tenant_id="   "),
            )
            self.assertEqual(exc.status_code, 403)

    def test_acl_on_allows_own_tenant_prefix(self) -> None:
        # Kills ReplaceOrWithAnd on `tenant_id=principal.tenant_id or ""` (L215).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            resolved = ctx.resolve_safe_path(
                "tenants/tenant-a/uploads/x.ifc",
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )
            self.assertIn("tenant-a", str(resolved))

    def test_acl_on_foreign_prefix_is_404_and_traversal_is_400(self) -> None:
        # Cross-tenant path probes must not oracle via 403 + prefix detail.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            foreign = _status(
                ctx.resolve_safe_path,
                "tenants/tenant-b/uploads/x.ifc",
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )
            self.assertEqual(foreign.status_code, 404)
            self.assertEqual(str(foreign.detail), "Object not found")
            traversal = _status(
                ctx.resolve_safe_path,
                "../outside.ifc",
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )
            self.assertEqual(traversal.status_code, 400)


class IfcSizeLimitBoundaryTests(unittest.TestCase):
    """Kills Gt_Eq / Gt_GtE / Gt_Is on the size check + 413 codes (L227-229)."""

    def test_exactly_at_limit_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), max_ifc_bytes=8)
            target = Path(tmp) / "at-limit.ifc"
            target.write_bytes(b"x" * 8)
            ctx.enforce_ifc_size(target)  # must not raise

    def test_one_byte_over_limit_is_413(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), max_ifc_bytes=8)
            target = Path(tmp) / "over.ifc"
            target.write_bytes(b"x" * 9)
            self.assertEqual(_status(ctx.enforce_ifc_size, target).status_code, 413)


class ResolveBoundTenantTests(unittest.TestCase):
    """Tenant binding rules (L275-292)."""

    def test_acl_on_returns_principal_tenant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            bound = ctx.resolve_bound_tenant(
                AuthPrincipal(tenant_id="tenant-a"), payload_tenant_id="spoof"
            )
            self.assertEqual(bound, "tenant-a")

    def test_acl_on_unbound_principal_is_403(self) -> None:
        # Kills Is_IsNot / AddNot on `if principal_tenant is None` (L285) + 403.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            exc = _status(ctx.resolve_bound_tenant, AuthPrincipal(tenant_id="  "))
            self.assertEqual(exc.status_code, 403)

    def test_acl_off_principal_wins_over_payload(self) -> None:
        # Kills ReplaceOrWithAnd on the return chain (L292).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            principal = AuthPrincipal(tenant_id="tenant-a")
            self.assertEqual(
                ctx.resolve_bound_tenant(principal, payload_tenant_id="tenant-x"),
                "tenant-a",
            )

    def test_acl_off_payload_fallback_and_none(self) -> None:
        # Kills ReplaceOrWithAnd on both strip chains (L283, L291).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            empty = AuthPrincipal(tenant_id="   ")
            self.assertEqual(
                ctx.resolve_bound_tenant(empty, payload_tenant_id="tenant-p"), "tenant-p"
            )
            self.assertIsNone(ctx.resolve_bound_tenant(empty, payload_tenant_id=None))


class ObjectKeyTenantScopeTests(unittest.TestCase):
    """assert_object_key_under_tenant (L349-368)."""

    def test_acl_off_is_noop_for_foreign_keys(self) -> None:
        # Kills AddNot / Delete_Not on `if not enforce_object_acl` (L357).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            ctx.assert_object_key_under_tenant(
                "tenants/tenant-b/x.ifc",
                report=_report(tenant_id="tenant-a"),
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )  # must not raise

    def test_acl_on_own_prefix_with_leading_slash_ok(self) -> None:
        # Kills ReplaceOrWithAnd on the lstrip chain (L366).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            ctx.assert_object_key_under_tenant(
                "/tenants/tenant-a/x.ifc",
                report=_report(tenant_id="tenant-a"),
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )  # must not raise

    def test_acl_on_foreign_prefix_is_404(self) -> None:
        # Kills AddNot / Delete_Not on startswith (L367) + 404 codes (L368).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            exc = _status(
                ctx.assert_object_key_under_tenant,
                "tenants/tenant-b/x.ifc",
                report=_report(tenant_id="tenant-a"),
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )
            self.assertEqual(exc.status_code, 404)

    def test_principal_tenant_used_when_report_unbound(self) -> None:
        # Kills both ReplaceOrWithAnd mutants on the tenant chain (L359).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            ctx.assert_object_key_under_tenant(
                "tenants/tenant-a/x.ifc",
                report=_report(tenant_id=None),
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )  # must not raise

    def test_no_tenant_at_all_is_404(self) -> None:
        # Kills AddNot / Delete_Not on `if not tenant` (L360) + 404 (L361).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            exc = _status(
                ctx.assert_object_key_under_tenant,
                "tenants/tenant-a/x.ifc",
                report=_report(tenant_id=None),
                principal=AuthPrincipal(tenant_id="  "),
            )
            self.assertEqual(exc.status_code, 404)

    def test_malformed_tenant_maps_to_404(self) -> None:
        # Kills ExceptionReplacer on `except PathJailError` (L364): the mutant
        # leaks PathJailError instead of the anti-enumeration 404.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            exc = _status(
                ctx.assert_object_key_under_tenant,
                "tenants/x/x.ifc",
                report=_report(tenant_id="bad\x00tenant"),
                principal=AuthPrincipal(tenant_id="bad\x00tenant"),
            )
            self.assertEqual(exc.status_code, 404)


class ObjectAclAssertionTests(unittest.TestCase):
    """assert_job_access / assert_norm_pack_access denial codes (L251-273)."""

    def test_cross_tenant_job_access_is_404(self) -> None:
        # Kills NumberReplacer on 404 (L259).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            job = AnalyzeProjectPackageJob(
                job_id="d" * 32,
                request_id="req",
                status=JobStatus.QUEUED,
                created_at=datetime.now(tz=UTC).isoformat(),
                tenant_id="tenant-b",
            )
            exc = _status(ctx.assert_job_access, job, AuthPrincipal(tenant_id="tenant-a"))
            self.assertEqual(exc.status_code, 404)

    def test_norm_pack_access_scoped_by_tenant(self) -> None:
        # Kills AddNot on the norm-pack guard (L264) + 404 codes (L271).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            principal = AuthPrincipal(tenant_id="tenant-a")
            ctx.assert_norm_pack_access(principal, tenant_id="tenant-a")  # must not raise
            exc = _status(ctx.assert_norm_pack_access, principal, tenant_id="tenant-b")
            self.assertEqual(exc.status_code, 404)


class ReportIfcSourceTests(unittest.TestCase):
    """resolve_report_ifc_source (L370-422)."""

    def test_unknown_report_is_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp))
            exc = _status(ctx.resolve_report_ifc_source, "f" * 32)
            self.assertEqual(exc.status_code, 404)

    def test_object_store_payload_returned(self) -> None:
        # Kills the L381 AndWithOr / IsNot_Is cluster and L387 payload check.
        with tempfile.TemporaryDirectory() as tmp:
            store = _ObjectStore({"tenants/tenant-a/model.ifc": b"IFC-BYTES"})
            ctx = _make_ctx(Path(tmp), object_store=store, enforce_object_acl=False)
            report = _report(ifc_object_key="tenants/tenant-a/model.ifc")
            ctx.audit_store.reports[report.report_id] = report
            name, payload = ctx.resolve_report_ifc_source(report.report_id)
            self.assertEqual(name, "model.ifc")
            self.assertEqual(payload, b"IFC-BYTES")

    def test_object_store_missing_payload_is_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), object_store=_ObjectStore(), enforce_object_acl=False)
            report = _report(ifc_object_key="tenants/tenant-a/gone.ifc")
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(ctx.resolve_report_ifc_source, report.report_id)
            self.assertEqual(exc.status_code, 404)

    def test_filesystem_branch_used_without_object_key(self) -> None:
        # Kills L381 AndWithOr: the mutant enters the store branch without a
        # key and 404s. Also kills the L395 `base / candidate` operator swaps.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), object_store=_ObjectStore(), enforce_object_acl=False)
            (Path(tmp) / "model.ifc").write_bytes(b"x")
            report = _report(ifc_path="model.ifc")
            ctx.audit_store.reports[report.report_id] = report
            name, resolved = ctx.resolve_report_ifc_source(report.report_id)
            self.assertEqual(name, "model.ifc")
            self.assertTrue(Path(resolved).is_file())

    def test_absolute_path_outside_storage_is_409(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            ctx = _make_ctx(Path(tmp_a), enforce_object_acl=False)
            outside = Path(tmp_b) / "foreign.ifc"
            outside.write_bytes(b"x")
            report = _report(ifc_path=str(outside))
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(ctx.resolve_report_ifc_source, report.report_id)
            self.assertEqual(exc.status_code, 409)

    def test_acl_off_ignores_report_tenant_prefix(self) -> None:
        # Kills AddNot on `if settings.enforce_object_acl` (L405): the mutant
        # applies tenant scoping with ACL off and 404s a legitimate source.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            (Path(tmp) / "model.ifc").write_bytes(b"x")
            report = _report(tenant_id="tenant-b", ifc_path="model.ifc")
            ctx.audit_store.reports[report.report_id] = report
            name, _resolved = ctx.resolve_report_ifc_source(report.report_id)
            self.assertEqual(name, "model.ifc")

    def test_acl_on_without_any_tenant_skips_prefix_check(self) -> None:
        # Kills AddNot on `if tenant` (L409): the mutant runs the prefix check
        # with an empty tenant and turns a valid source into 404.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            (Path(tmp) / "model.ifc").write_bytes(b"x")
            report = _report(tenant_id=None, ifc_path="model.ifc")
            ctx.audit_store.reports[report.report_id] = report
            name, _resolved = ctx.resolve_report_ifc_source(report.report_id)
            self.assertEqual(name, "model.ifc")

    def test_acl_on_foreign_stored_path_is_404(self) -> None:
        # Kills ExceptionReplacer on `except PathJailError` (L416) + L417 codes
        # + the L406-408 tenant chain mutants.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            target = Path(tmp) / "tenants" / "tenant-b" / "model.ifc"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            report = _report(tenant_id="tenant-a", ifc_path="tenants/tenant-b/model.ifc")
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(ctx.resolve_report_ifc_source, report.report_id)
            self.assertEqual(exc.status_code, 404)

    def test_missing_file_is_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            report = _report(ifc_path="missing.ifc")
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(ctx.resolve_report_ifc_source, report.report_id)
            self.assertEqual(exc.status_code, 404)

    def test_object_store_key_check_only_with_principal(self) -> None:
        # Kills AddNot / IsNot_Is on `if principal is not None` (L382).
        with tempfile.TemporaryDirectory() as tmp:
            store = _ObjectStore({"tenants/tenant-b/model.ifc": b"IFC"})
            ctx = _make_ctx(Path(tmp), object_store=store, enforce_object_acl=True)
            report = _report(tenant_id="tenant-b", ifc_object_key="tenants/tenant-b/model.ifc")
            ctx.audit_store.reports[report.report_id] = report
            # Without principal the tenant-scope check is skipped entirely.
            _name, payload = ctx.resolve_report_ifc_source(report.report_id)
            self.assertEqual(payload, b"IFC")
            # With a foreign principal the scoped check must 404 (report tenant
            # binds the prefix, principal only enables the check).
            report_foreign = _report(
                tenant_id="tenant-a", ifc_object_key="tenants/tenant-b/model.ifc"
            )
            ctx.audit_store.reports[report_foreign.report_id] = report_foreign
            exc = _status(
                ctx.resolve_report_ifc_source,
                report_foreign.report_id,
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )
            self.assertEqual(exc.status_code, 404)

    def test_symlink_rejection_maps_to_409(self) -> None:
        # Kills ExceptionReplacer on `except PathJailError` (L403) + 409 (L404).
        import aerobim.presentation.http.context as context_module
        from aerobim.core.security.path_jail import PathJailError

        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            (Path(tmp) / "model.ifc").write_bytes(b"x")
            report = _report(ifc_path="model.ifc")
            ctx.audit_store.reports[report.report_id] = report
            with patch.object(
                context_module,
                "reject_symlinks",
                side_effect=PathJailError("planted symlink"),
            ):
                exc = _status(ctx.resolve_report_ifc_source, report.report_id)
            self.assertEqual(exc.status_code, 409)

    def test_acl_on_principal_tenant_fallback_in_filesystem_branch(self) -> None:
        # Kills AddNot / Delete_Not on `if not tenant and principal is not None`
        # (L407) and ReplaceOrWithAnd on the principal strip chain (L408).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            target = Path(tmp) / "tenants" / "tenant-a" / "model.ifc"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            report = _report(tenant_id=None, ifc_path="tenants/tenant-a/model.ifc")
            ctx.audit_store.reports[report.report_id] = report
            name, _resolved = ctx.resolve_report_ifc_source(
                report.report_id, principal=AuthPrincipal(tenant_id="tenant-a")
            )
            self.assertEqual(name, "model.ifc")
            # Foreign principal binds the prefix check and must 404.
            exc = _status(
                ctx.resolve_report_ifc_source,
                report.report_id,
                principal=AuthPrincipal(tenant_id="tenant-b"),
            )
            self.assertEqual(exc.status_code, 404)
            # Principal without tenant leaves the check disabled (empty tenant).
            name2, _r2 = ctx.resolve_report_ifc_source(
                report.report_id, principal=AuthPrincipal(tenant_id=None)
            )
            self.assertEqual(name2, "model.ifc")


def _asset(
    asset_id: str,
    *,
    stored_filename: str | None = "page-1.png",
    object_key: str | None = None,
) -> DrawingAsset:
    return DrawingAsset(
        asset_id=asset_id,
        sheet_id="S-1",
        stored_filename=stored_filename,
        object_key=object_key,
    )


class DrawingAssetPreviewTests(unittest.TestCase):
    """resolve_report_drawing_asset_preview (L424-481)."""

    def test_unknown_report_is_404(self) -> None:
        # Kills NumberReplacer on the preview report lookup 404 (L434).
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp))
            exc = _status(ctx.resolve_report_drawing_asset_preview, "e" * 32, "A1")
            self.assertEqual(exc.status_code, 404)

    def test_asset_id_match_is_exact_not_ordered(self) -> None:
        # Kills Eq_GtE on the asset match (L437): "B" >= "A" would wrongly
        # serve asset B (whose preview file exists) for request A.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            report = _report(drawing_assets=(_asset("B"),))
            asset_dir = Path(tmp) / "drawing-assets" / report.report_id
            asset_dir.mkdir(parents=True)
            (asset_dir / "page-1.png").write_bytes(b"PNG")
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(ctx.resolve_report_drawing_asset_preview, report.report_id, "A")
            self.assertEqual(exc.status_code, 404)

    def test_object_store_payload_returned(self) -> None:
        # Kills the L442/L443/L448 branch cluster.
        with tempfile.TemporaryDirectory() as tmp:
            store = _ObjectStore({"tenants/tenant-a/asset.png": b"PNG"})
            ctx = _make_ctx(Path(tmp), object_store=store, enforce_object_acl=False)
            report = _report(
                drawing_assets=(_asset("A1", object_key="tenants/tenant-a/asset.png"),)
            )
            ctx.audit_store.reports[report.report_id] = report
            asset, payload = ctx.resolve_report_drawing_asset_preview(report.report_id, "A1")
            self.assertEqual(asset.asset_id, "A1")
            self.assertEqual(payload, b"PNG")

    def test_object_store_missing_payload_is_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), object_store=_ObjectStore(), enforce_object_acl=False)
            report = _report(drawing_assets=(_asset("A1", object_key="gone.png"),))
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(ctx.resolve_report_drawing_asset_preview, report.report_id, "A1")
            self.assertEqual(exc.status_code, 404)

    def test_filesystem_asset_resolved(self) -> None:
        # The object store is registered but the asset has no object_key:
        # kills ReplaceAndWithOr on `object_key and store is not None` (L442),
        # whose mutant enters the store branch and 404s a filesystem asset.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), object_store=_ObjectStore(), enforce_object_acl=False)
            report = _report(drawing_assets=(_asset("A1"),))
            asset_dir = Path(tmp) / "drawing-assets" / report.report_id
            asset_dir.mkdir(parents=True)
            (asset_dir / "page-1.png").write_bytes(b"PNG")
            ctx.audit_store.reports[report.report_id] = report
            asset, resolved = ctx.resolve_report_drawing_asset_preview(report.report_id, "A1")
            self.assertEqual(asset.asset_id, "A1")
            self.assertTrue(Path(resolved).is_file())

    def test_object_store_key_check_only_with_principal(self) -> None:
        # Kills AddNot / IsNot_Is on `if principal is not None` (L443).
        with tempfile.TemporaryDirectory() as tmp:
            store = _ObjectStore({"tenants/tenant-b/asset.png": b"PNG"})
            ctx = _make_ctx(Path(tmp), object_store=store, enforce_object_acl=True)
            report = _report(
                tenant_id="tenant-a",
                drawing_assets=(_asset("A1", object_key="tenants/tenant-b/asset.png"),),
            )
            ctx.audit_store.reports[report.report_id] = report
            # Without principal the scope check is skipped and bytes returned.
            _asset_obj, payload = ctx.resolve_report_drawing_asset_preview(report.report_id, "A1")
            self.assertEqual(payload, b"PNG")
            # With a principal the foreign key must 404.
            exc = _status(
                ctx.resolve_report_drawing_asset_preview,
                report.report_id,
                "A1",
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )
            self.assertEqual(exc.status_code, 404)

    def test_escaping_stored_filename_is_409(self) -> None:
        # Kills NumberReplacer on the escape 409 (L458). POSIX-style traversal
        # escapes on both platforms; a backslash variant is a plain filename
        # on Linux (404, not 409) and broke on CI.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            report = _report(drawing_assets=(_asset("A1", stored_filename="../../evil.png"),))
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(ctx.resolve_report_drawing_asset_preview, report.report_id, "A1")
            self.assertEqual(exc.status_code, 409)

    def test_symlink_rejection_maps_to_409(self) -> None:
        # Kills ExceptionReplacer on `except PathJailError` (L462) + 409 (L463).
        import aerobim.presentation.http.context as context_module
        from aerobim.core.security.path_jail import PathJailError

        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=False)
            report = _report(drawing_assets=(_asset("A1"),))
            asset_dir = Path(tmp) / "drawing-assets" / report.report_id
            asset_dir.mkdir(parents=True)
            (asset_dir / "page-1.png").write_bytes(b"PNG")
            ctx.audit_store.reports[report.report_id] = report
            with patch.object(
                context_module,
                "reject_symlinks",
                side_effect=PathJailError("planted symlink"),
            ):
                exc = _status(ctx.resolve_report_drawing_asset_preview, report.report_id, "A1")
            self.assertEqual(exc.status_code, 409)

    def test_acl_on_principal_tenant_fallback(self) -> None:
        # Kills the L466 AddNot/AndWithOr/IsNot_Is/Delete_Not cluster and the
        # L467 principal strip chain: report has no tenant, so the principal
        # binds the prefix check; drawing-assets/ is outside tenants/<t>/.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            report = _report(tenant_id=None, drawing_assets=(_asset("A1"),))
            asset_dir = Path(tmp) / "drawing-assets" / report.report_id
            asset_dir.mkdir(parents=True)
            (asset_dir / "page-1.png").write_bytes(b"PNG")
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(
                ctx.resolve_report_drawing_asset_preview,
                report.report_id,
                "A1",
                principal=AuthPrincipal(tenant_id="tenant-a"),
            )
            self.assertEqual(exc.status_code, 404)
            # Principal without tenant leaves the check disabled -> success.
            asset, _resolved = ctx.resolve_report_drawing_asset_preview(
                report.report_id, "A1", principal=AuthPrincipal(tenant_id=None)
            )
            self.assertEqual(asset.asset_id, "A1")

    def test_report_tenant_not_overridden_by_unbound_principal(self) -> None:
        """Kills ReplaceAndWithOr on ``not tenant and principal`` (L466).

        The report's own tenant must bind the preview prefix check even when
        the caller principal carries no tenant. The or-mutant overwrites the
        report tenant with the principal's empty one, silently disabling the
        check and serving a preview the original correctly hides (404: the
        drawing-assets/ tree lies outside tenants/tenant-a/).
        """
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            report = _report(tenant_id="tenant-a", drawing_assets=(_asset("A1"),))
            asset_dir = Path(tmp) / "drawing-assets" / report.report_id
            asset_dir.mkdir(parents=True)
            (asset_dir / "page-1.png").write_bytes(b"PNG")
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(
                ctx.resolve_report_drawing_asset_preview,
                report.report_id,
                "A1",
                principal=AuthPrincipal(tenant_id=None),
            )
            self.assertEqual(exc.status_code, 404)

    def test_acl_on_asset_outside_tenant_prefix_is_404(self) -> None:
        # Kills the L464-476 ACL cluster incl. ExceptionReplacer (L475): the
        # drawing-assets tree is not under tenants/<t>/, so the prefix check
        # must map PathJailError to the anti-enumeration 404.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp), enforce_object_acl=True)
            report = _report(tenant_id="tenant-a", drawing_assets=(_asset("A1"),))
            asset_dir = Path(tmp) / "drawing-assets" / report.report_id
            asset_dir.mkdir(parents=True)
            (asset_dir / "page-1.png").write_bytes(b"PNG")
            ctx.audit_store.reports[report.report_id] = report
            exc = _status(ctx.resolve_report_drawing_asset_preview, report.report_id, "A1")
            self.assertEqual(exc.status_code, 404)


class PublicReportSerializationTests(unittest.TestCase):
    def test_loin_enrichment_applied_to_dict_issues(self) -> None:
        # Kills AddNot on the isinstance guard (L334): the mutant stops
        # enriching dict issues, dropping the loin_* export fields.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp))
            issue = ValidationIssue(
                rule_id="CROSS-DOC-01",
                severity=Severity.WARNING,
                message="m",
                category=FindingCategory.IFC_VALIDATION,
                origin="deterministic",
            )
            report = _report(issues=(issue,))
            data = ctx.serialize_public_report(report)
            self.assertNotIn("ifc_path", data)
            self.assertNotIn("ifc_object_key", data)
            self.assertIn("loin_purpose", data["issues"][0])

    def test_ai_generated_remark_gets_content_marking_on_http_egress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(Path(tmp))
            issue = ValidationIssue(
                rule_id="R-AI-1",
                severity=Severity.ERROR,
                message="m",
                category=FindingCategory.IFC_VALIDATION,
                origin="deterministic",
                remark=GeneratedRemark(
                    title="AI",
                    body="draft",
                    ai_generated=True,
                    expert_confirmation_required=True,
                ),
            )
            report = _report(issues=(issue,))
            data = ctx.serialize_public_report(report)
            remark = data["issues"][0]["remark"]
            self.assertTrue(remark["ai_generated"])
            self.assertEqual(
                remark["content_marking"],
                "ai_generated=true;expert_confirmation_required=true",
            )


if __name__ == "__main__":
    unittest.main()
