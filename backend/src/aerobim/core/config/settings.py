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
    allow_anonymous_dev: bool = True
    """When constructing Settings in-process (tests), default True for convenience.

    ``Settings.from_env()`` defaults this to **False** unless
    ``AEROBIM_ALLOW_ANONYMOUS_DEV=true`` — local/process env stacks must set a
    bearer token (or explicitly opt into anonymous)."""
    oda_cad_enabled: bool = False
    """Legal-gated ODA/Teigha DWG path (``AEROBIM_ODA_CAD_ENABLED``). Default off."""
    mep_system_clash_enabled: bool = False
    """Opt-in system-aware MEP clash (``AEROBIM_MEP_SYSTEM_CLASH_ENABLED``)."""
    mep_scope_memo_ref: str | None = None
    """Signed scope memo ref required with MEP system clash (``AEROBIM_MEP_SCOPE_MEMO_REF``)."""
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

        env_name = (os.getenv("AEROBIM_ENV") or "development").strip().lower()
        # Non-dev defaults ACL on when unset (legacy); profile may still override.
        acl_default = False if env_name in _DEV_ENVIRONMENTS else True
        # Inline profile map keeps core free of application imports (layer boundary).
        raw_signoff = (os.getenv("AEROBIM_SIGNOFF_PROFILE") or "development").strip().lower()
        if raw_signoff in {"samolet", "samolet_pilot", "pilot"}:
            signoff_profile = "samolet_pilot"
        elif raw_signoff in {"production", "prod"}:
            signoff_profile = "production"
        elif raw_signoff in {"fixture", "fixtures"}:
            signoff_profile = "fixture"
        else:
            signoff_profile = "development"
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
            max_uploads_per_tenant_day=_read_optional_int("AEROBIM_MAX_UPLOADS_PER_TENANT_DAY"),
            max_upload_bytes_per_tenant_day=_read_optional_int(
                "AEROBIM_MAX_UPLOAD_BYTES_PER_TENANT_DAY"
            ),
            max_concurrent_analyze_jobs_per_tenant=_read_optional_int(
                "AEROBIM_MAX_CONCURRENT_ANALYZE_JOBS_PER_TENANT"
            ),
            bcf_api_base_url=(os.getenv("AEROBIM_BCF_API_BASE_URL") or "").strip() or None,
            bcf_api_token=(os.getenv("AEROBIM_BCF_API_TOKEN") or "").strip() or None,
            bcf_api_project_id=(os.getenv("AEROBIM_BCF_API_PROJECT_ID") or "").strip() or None,
            bcf_api_version=(os.getenv("AEROBIM_BCF_API_VERSION") or "3.0").strip() or "3.0",
            oidc_issuer=(os.getenv("AEROBIM_OIDC_ISSUER") or "").strip() or None,
            oidc_audience=(os.getenv("AEROBIM_OIDC_AUDIENCE") or "").strip() or None,
            oidc_jwks_url=(os.getenv("AEROBIM_OIDC_JWKS_URL") or "").strip() or None,
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
            ifc_parse_cache_dir=(os.getenv("AEROBIM_IFC_PARSE_CACHE_DIR") or "").strip() or None,
            hybrid_drawing_enabled=_read_bool("AEROBIM_HYBRID_DRAWING_ENABLED", True),
        )
        settings.require_secure_auth()
        return settings
