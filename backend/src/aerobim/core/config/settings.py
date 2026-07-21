from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_DEBUG_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
)


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _read_optional_int(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    return int(raw)


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


_DEV_ENVIRONMENTS = frozenset({"development", "dev", "test"})
_DEFAULT_MAX_IFC_BYTES = 256 * 1024 * 1024  # aligned with bSI Validation Service
# Baked pilot/production quotas when env unset (RTATOM-I20 / A2.3).
_PILOT_DEFAULT_MAX_UPLOADS_PER_DAY = 100
_PILOT_DEFAULT_MAX_BYTES_PER_DAY = 10 * 1024 * 1024 * 1024  # 10 GiB
_PILOT_DEFAULT_MAX_CONCURRENT_JOBS = 4


@dataclass(frozen=True)
class Settings:
    application_name: str
    environment: str
    host: str
    port: int
    storage_dir: Path
    debug: bool
    cors_origins: tuple[str, ...] = ()
    api_bearer_token: str | None = None
    cross_doc_contradiction_severity: str = "warning"
    """Severity for cross-document contradictions: ``error`` | ``warning`` | ``info``."""
    priority_profile: str = "default"
    """Reviewer priority profile: ``default`` or ``samolet`` (TechLab fire/cross-doc boost)."""
    db_url: str | None = None
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_prefix: str = "aerobim"
    report_ttl_days: int | None = None
    clash_affects_pass: bool = False
    """When true, hard clashes (or clash capability failure) set ``summary.passed=False``."""
    require_clash: bool = False
    """When true, missing/skipped clash capability is treated as FAILED (no green pass)."""
    require_bsi_schema: bool = False
    """When true, bSI/schema submit failures are ERROR and block pass via issues."""
    signoff_profile: str = "development"
    """Capability policy profile: development|fixture|samolet_pilot|production."""
    require_mep_system_clash: bool = False
    """When true, MEP capability must be OK; NOT_VERIFIED/FAILED blocks summary.passed."""
    audit_fail_closed: bool = False
    """When true, corrupt review-event JSONL raises instead of silent skip."""
    enforce_object_acl: bool = False
    """When true, report artifacts require matching tenant_id on the auth principal."""
    api_tenant_id: str | None = None
    """Tenant bound to the static bearer token (``AEROBIM_API_TENANT_ID``)."""
    max_ifc_bytes: int = _DEFAULT_MAX_IFC_BYTES
    """Maximum accepted IFC file size in bytes (default 256 MiB)."""
    max_upload_bytes: int = _DEFAULT_MAX_IFC_BYTES
    """Maximum accepted multipart upload size in bytes (all document types)."""
    max_uploads_per_tenant_day: int | None = None
    """Optional per-tenant daily upload count quota (``AEROBIM_MAX_UPLOADS_PER_TENANT_DAY``)."""
    max_upload_bytes_per_tenant_day: int | None = None
    """Optional per-tenant daily upload bytes quota.

    Env: ``AEROBIM_MAX_UPLOAD_BYTES_PER_TENANT_DAY``.
    """
    max_concurrent_analyze_jobs_per_tenant: int | None = None
    """Optional cap on QUEUED+RUNNING analyze jobs per tenant.

    Env: ``AEROBIM_MAX_CONCURRENT_ANALYZE_JOBS_PER_TENANT``.
    """
    # OpenCDE BCF API 3.0 push (optional)
    bcf_api_base_url: str | None = None
    bcf_api_token: str | None = None
    bcf_api_project_id: str | None = None
    bcf_api_version: str = "3.0"
    # OIDC / JWT (optional; accepted alongside static bearer)
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    oidc_jwks_extra_hosts: tuple[str, ...] = ()
    """Extra JWKS hostnames allowed when they differ from the issuer host.

    Env: ``AEROBIM_OIDC_JWKS_EXTRA_HOSTS`` (comma-separated).
    """
    oidc_tenant_claim: str = "tenant_id"
    """JWT claim used for tenant binding. No silent fallback to tid/org_id."""
    # Optional Redis for durable async jobs
    redis_url: str | None = None
    # Optional bSI Validation Service / local schema certificate
    bsi_validation_url: str | None = None
    bsi_api_token: str | None = None
    bsi_local_cert: bool = False
    """When true (and remote URL unset), emit a local schema-pack certificate id."""
    remark_locale: str = "ru"
    """Product remark language: ``ru`` | ``en`` (``AEROBIM_REMARK_LOCALE``)."""
    norm_rule_pack_path: str | None = None
    """Storage-relative path to a default norm/rule pack (``AEROBIM_NORM_RULE_PACK``).

    Used as the customer-pack fallback when a request/manifest does not list any
    ``norm_rule_pack_paths``. If configured but missing at analysis time, the
    ``norm_rule_packs`` capability fails closed (never a silent skip)."""
    allow_anonymous_dev: bool = False
    """Allow unauthenticated /v1 access in development/test only.

    Default is **False** (fail-closed). Opt in explicitly for local TestClient /
    demo paths via ``allow_anonymous_dev=True`` or ``AEROBIM_ALLOW_ANONYMOUS_DEV=true``.
    """
    oda_cad_enabled: bool = False
    """Legal-gated ODA/Teigha DWG path (``AEROBIM_ODA_CAD_ENABLED``). Default off."""
    mep_system_clash_enabled: bool = False
    """Opt-in system-aware MEP clash (``AEROBIM_MEP_SYSTEM_CLASH_ENABLED``)."""
    mep_scope_memo_ref: str | None = None
    """Signed scope memo ref required with MEP system clash (``AEROBIM_MEP_SCOPE_MEMO_REF``)."""
    mep_federated_scope_path: str | None = None
    """JSON scope manifest for federated MEP IFC paths (``AEROBIM_MEP_FEDERATED_SCOPE_PATH``)."""
    ifc_parse_cache_dir: str | None = None
    """Optional IFC parse cache directory (``AEROBIM_IFC_PARSE_CACHE_DIR``) — NFR SLA."""
    hybrid_drawing_enabled: bool = True
    """Use HybridDrawingAnalyzer for DrawingAnalyzerPort when True."""

    @property
    def is_dev_environment(self) -> bool:
        return self.environment.strip().lower() in _DEV_ENVIRONMENTS

    @property
    def oidc_enabled(self) -> bool:
        return bool(self.oidc_issuer and self.oidc_audience and self.oidc_jwks_url)

    def require_secure_auth(self) -> None:
        """Fail closed: non-dev deployments must configure bearer and/or OIDC."""
        if self.is_dev_environment:
            return
        if self.api_bearer_token or self.oidc_enabled:
            return
        raise RuntimeError(
            "Non-development deployments require AEROBIM_API_BEARER_TOKEN "
            "and/or OIDC settings (AEROBIM_OIDC_ISSUER, AEROBIM_OIDC_AUDIENCE, "
            f"AEROBIM_OIDC_JWKS_URL); AEROBIM_ENV={self.environment!r}"
        )

    def require_oidc_runtime_deps(self) -> None:
        """Fail closed when OIDC is configured but PyJWT is not installed."""
        if not self.oidc_enabled:
            return
        try:
            import jwt  # noqa: F401
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "OIDC is configured but PyJWT is not installed; "
                "install the 'enterprise' extra or unset AEROBIM_OIDC_*"
            ) from exc

    @classmethod
    def from_env(cls) -> Settings:
        debug = _read_bool("AEROBIM_DEBUG", False)
        raw_origins = os.getenv("AEROBIM_CORS_ORIGINS", "")
        if raw_origins:
            origins = tuple(o.strip() for o in raw_origins.split(",") if o.strip())
        elif debug:
            origins = _DEBUG_CORS_ORIGINS
        else:
            origins = ()
        env_name = (os.getenv("AEROBIM_ENV") or "development").strip().lower()
        if any(origin == "*" for origin in origins) and env_name not in _DEV_ENVIRONMENTS:
            raise RuntimeError(
                "AEROBIM_CORS_ORIGINS must not include '*' outside development/test "
                f"(AEROBIM_ENV={env_name!r})"
            )
        raw_severity = (os.getenv("AEROBIM_CROSS_DOC_SEVERITY") or "warning").strip().lower()
        cross_doc_severity = (
            raw_severity if raw_severity in {"error", "warning", "info"} else "warning"
        )
        raw_profile = (os.getenv("AEROBIM_PRIORITY_PROFILE") or "default").strip().lower()
        priority_profile = raw_profile if raw_profile in {"default", "samolet"} else "default"

        def _optional_bool(name: str) -> bool | None:
            if name not in os.environ:
                return None
            return _read_bool(name, False)

        # Non-dev defaults ACL on when unset (legacy); profile may still override.
        acl_default = False if env_name in _DEV_ENVIRONMENTS else True
        # Inline profile map keeps core free of application imports (layer boundary).
        # RT-POST-01: non-dev without explicit profile must not silently use soft development.
        signoff_raw_env = os.getenv("AEROBIM_SIGNOFF_PROFILE")
        if signoff_raw_env is None or not str(signoff_raw_env).strip():
            signoff_profile = "development" if env_name in _DEV_ENVIRONMENTS else "production"
        else:
            raw_signoff = str(signoff_raw_env).strip().lower()
            if raw_signoff in {"samolet", "samolet_pilot", "pilot"}:
                signoff_profile = "samolet_pilot"
            elif raw_signoff in {"production", "prod"}:
                signoff_profile = "production"
            elif raw_signoff in {"fixture", "fixtures"}:
                signoff_profile = "fixture"
            else:
                signoff_profile = "development"
        # Non-dev deployments must not soft-open Shared-gate via development/fixture profile.
        if env_name not in _DEV_ENVIRONMENTS and signoff_profile in {"development", "fixture"}:
            raise RuntimeError(
                f"AEROBIM_SIGNOFF_PROFILE={signoff_profile!r} is not allowed when "
                f"AEROBIM_ENV={env_name!r}; use 'production' or 'samolet_pilot'"
            )
        profile_gate = signoff_profile in {"samolet_pilot", "production"}
        # Pilot/production are fail-closed: env cannot weaken required gates.
        if profile_gate:
            require_clash = True
            clash_affects_pass = True
            require_bsi_schema = True
            require_mep_system_clash = True
            enforce_object_acl = True
            audit_fail_closed = True
        else:
            require_clash = bool(_optional_bool("AEROBIM_REQUIRE_CLASH") or False)
            clash_affects_pass = bool(_optional_bool("AEROBIM_CLASH_AFFECTS_PASS") or False)
            require_bsi_schema = bool(_optional_bool("AEROBIM_REQUIRE_BSI_SCHEMA") or False)
            require_mep_system_clash = bool(
                _optional_bool("AEROBIM_REQUIRE_MEP_SYSTEM_CLASH") or False
            )
            if "AEROBIM_ENFORCE_OBJECT_ACL" in os.environ:
                enforce_object_acl = bool(_optional_bool("AEROBIM_ENFORCE_OBJECT_ACL"))
            else:
                enforce_object_acl = acl_default
            audit_fail_closed = bool(_optional_bool("AEROBIM_AUDIT_FAIL_CLOSED") or False)
        # Local SPF certificate is development-only; never under pilot/production.
        bsi_local_cert = _read_bool("AEROBIM_BSI_LOCAL_CERT", False) and not profile_gate
        # Hard profiles always escalate cross-doc contradictions (RTATOM-G05).
        if profile_gate:
            cross_doc_severity = "error"

        max_uploads_per_tenant_day = _read_optional_int("AEROBIM_MAX_UPLOADS_PER_TENANT_DAY")
        max_upload_bytes_per_tenant_day = _read_optional_int(
            "AEROBIM_MAX_UPLOAD_BYTES_PER_TENANT_DAY"
        )
        max_concurrent_analyze_jobs_per_tenant = _read_optional_int(
            "AEROBIM_MAX_CONCURRENT_ANALYZE_JOBS_PER_TENANT"
        )
        # Bake reasonable pilot quotas when unset under hard profiles (RTATOM-I20).
        if profile_gate:
            if max_uploads_per_tenant_day is None:
                max_uploads_per_tenant_day = _PILOT_DEFAULT_MAX_UPLOADS_PER_DAY
            if max_upload_bytes_per_tenant_day is None:
                max_upload_bytes_per_tenant_day = _PILOT_DEFAULT_MAX_BYTES_PER_DAY
            if max_concurrent_analyze_jobs_per_tenant is None:
                max_concurrent_analyze_jobs_per_tenant = _PILOT_DEFAULT_MAX_CONCURRENT_JOBS

        settings = cls(
            application_name=os.getenv("AEROBIM_APP_NAME", "aerobim-backend"),
            environment=os.getenv("AEROBIM_ENV", "development"),
            host=os.getenv("AEROBIM_HOST", "127.0.0.1"),
            port=_read_int("AEROBIM_PORT", 8080),
            storage_dir=Path(os.getenv("AEROBIM_STORAGE_DIR", "var/reports")),
            debug=debug,
            cors_origins=origins,
            api_bearer_token=(os.getenv("AEROBIM_API_BEARER_TOKEN") or "").strip() or None,
            cross_doc_contradiction_severity=cross_doc_severity,
            priority_profile=priority_profile,
            db_url=(os.getenv("AEROBIM_DB_URL") or "").strip() or None,
            s3_endpoint_url=(os.getenv("AEROBIM_S3_ENDPOINT_URL") or "").strip() or None,
            s3_bucket=(os.getenv("AEROBIM_S3_BUCKET") or "").strip() or None,
            s3_region=(os.getenv("AEROBIM_S3_REGION") or "us-east-1").strip() or "us-east-1",
            s3_access_key_id=(os.getenv("AEROBIM_S3_ACCESS_KEY_ID") or "").strip() or None,
            s3_secret_access_key=(os.getenv("AEROBIM_S3_SECRET_ACCESS_KEY") or "").strip() or None,
            s3_prefix=(os.getenv("AEROBIM_S3_PREFIX") or "aerobim").strip() or "aerobim",
            report_ttl_days=_read_optional_int("AEROBIM_REPORT_TTL_DAYS"),
            clash_affects_pass=clash_affects_pass,
            require_clash=require_clash,
            require_bsi_schema=require_bsi_schema,
            signoff_profile=signoff_profile,
            require_mep_system_clash=require_mep_system_clash,
            audit_fail_closed=audit_fail_closed,
            enforce_object_acl=enforce_object_acl,
            api_tenant_id=(os.getenv("AEROBIM_API_TENANT_ID") or "").strip() or None,
            max_ifc_bytes=_read_int("AEROBIM_MAX_IFC_BYTES", _DEFAULT_MAX_IFC_BYTES),
            max_upload_bytes=_read_int(
                "AEROBIM_MAX_UPLOAD_BYTES",
                _read_int("AEROBIM_MAX_IFC_BYTES", _DEFAULT_MAX_IFC_BYTES),
            ),
            max_uploads_per_tenant_day=max_uploads_per_tenant_day,
            max_upload_bytes_per_tenant_day=max_upload_bytes_per_tenant_day,
            max_concurrent_analyze_jobs_per_tenant=max_concurrent_analyze_jobs_per_tenant,
            bcf_api_base_url=(os.getenv("AEROBIM_BCF_API_BASE_URL") or "").strip() or None,
            bcf_api_token=(os.getenv("AEROBIM_BCF_API_TOKEN") or "").strip() or None,
            bcf_api_project_id=(os.getenv("AEROBIM_BCF_API_PROJECT_ID") or "").strip() or None,
            bcf_api_version=(os.getenv("AEROBIM_BCF_API_VERSION") or "3.0").strip() or "3.0",
            oidc_issuer=(os.getenv("AEROBIM_OIDC_ISSUER") or "").strip() or None,
            oidc_audience=(os.getenv("AEROBIM_OIDC_AUDIENCE") or "").strip() or None,
            oidc_jwks_url=(os.getenv("AEROBIM_OIDC_JWKS_URL") or "").strip() or None,
            oidc_jwks_extra_hosts=tuple(
                host.strip()
                for host in (os.getenv("AEROBIM_OIDC_JWKS_EXTRA_HOSTS") or "").split(",")
                if host.strip()
            ),
            oidc_tenant_claim=(
                (os.getenv("AEROBIM_OIDC_TENANT_CLAIM") or "tenant_id").strip() or "tenant_id"
            ),
            redis_url=(os.getenv("AEROBIM_REDIS_URL") or "").strip() or None,
            bsi_validation_url=(os.getenv("AEROBIM_BSI_VALIDATION_URL") or "").strip() or None,
            bsi_api_token=(os.getenv("AEROBIM_BSI_API_TOKEN") or "").strip() or None,
            bsi_local_cert=bsi_local_cert,
            remark_locale=(os.getenv("AEROBIM_REMARK_LOCALE") or "ru").strip().lower() or "ru",
            norm_rule_pack_path=(os.getenv("AEROBIM_NORM_RULE_PACK") or "").strip() or None,
            allow_anonymous_dev=_read_bool("AEROBIM_ALLOW_ANONYMOUS_DEV", False),
            oda_cad_enabled=_read_bool("AEROBIM_ODA_CAD_ENABLED", False),
            mep_system_clash_enabled=_read_bool("AEROBIM_MEP_SYSTEM_CLASH_ENABLED", False),
            mep_scope_memo_ref=(os.getenv("AEROBIM_MEP_SCOPE_MEMO_REF") or "").strip() or None,
            mep_federated_scope_path=(
                (os.getenv("AEROBIM_MEP_FEDERATED_SCOPE_PATH") or "").strip() or None
            ),
            ifc_parse_cache_dir=(os.getenv("AEROBIM_IFC_PARSE_CACHE_DIR") or "").strip() or None,
            hybrid_drawing_enabled=_read_bool("AEROBIM_HYBRID_DRAWING_ENABLED", True),
        )
        # SSRF gate for config-sourced outbound endpoints (fail closed at boot).
        from aerobim.core.security.outbound_url import (
            UnsafeOutboundUrlError,
            assert_oidc_jwks_host_bound,
            assert_safe_datastore_url,
            assert_safe_outbound_url,
        )

        if settings.oidc_issuer and settings.oidc_jwks_url:
            try:
                assert_oidc_jwks_host_bound(
                    settings.oidc_issuer,
                    settings.oidc_jwks_url,
                    settings.oidc_jwks_extra_hosts,
                )
            except UnsafeOutboundUrlError as exc:
                raise RuntimeError(f"OIDC JWKS host binding failed: {exc}") from exc

        for label, candidate in (
            ("AEROBIM_OIDC_JWKS_URL", settings.oidc_jwks_url),
            ("AEROBIM_BSI_VALIDATION_URL", settings.bsi_validation_url),
            ("AEROBIM_BCF_API_BASE_URL", settings.bcf_api_base_url),
            ("AEROBIM_S3_ENDPOINT_URL", settings.s3_endpoint_url),
        ):
            if not candidate:
                continue
            try:
                # S3 custom endpoints often use http:// on local MinIO — allow http there.
                is_s3 = label == "AEROBIM_S3_ENDPOINT_URL"
                allow_http = is_s3 and env_name in _DEV_ENVIRONMENTS
                # Non-dev: resolve DNS at boot for S3 endpoints (RT B02).
                resolve_dns = is_s3 and env_name not in _DEV_ENVIRONMENTS
                assert_safe_outbound_url(
                    candidate,
                    allow_http=allow_http,
                    resolve_dns=resolve_dns,
                )
            except UnsafeOutboundUrlError as exc:
                raise RuntimeError(f"Unsafe outbound URL in {label}: {exc}") from exc
        # Redis / Postgres URLs: SSRF gate when not localhost / unix socket (RTATOM-I09/I10).
        for label, candidate in (
            ("AEROBIM_REDIS_URL", settings.redis_url),
            ("AEROBIM_DB_URL", settings.db_url),
        ):
            if not candidate:
                continue
            try:
                assert_safe_datastore_url(candidate)
            except UnsafeOutboundUrlError as exc:
                raise RuntimeError(f"Unsafe datastore URL in {label}: {exc}") from exc
        settings.require_secure_auth()
        settings.require_oidc_runtime_deps()
        return settings
