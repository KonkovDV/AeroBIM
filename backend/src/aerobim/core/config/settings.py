from __future__ import annotations

import logging
import os
from dataclasses import dataclass, replace
from pathlib import Path

_DEBUG_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
)


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


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


def _read_vlm_enabled() -> bool:
    """Prefer AEROBIM_VLM_ENABLED; keep AEROBIM_KIMI_K3_ENABLED as deprecated alias."""
    if os.getenv("AEROBIM_VLM_ENABLED") is not None:
        return _read_bool("AEROBIM_VLM_ENABLED", False)
    return _read_bool("AEROBIM_KIMI_K3_ENABLED", False)


def _env_prefer(*names: str, default: str = "") -> str:
    """First non-empty env among names (primary first, deprecated aliases later)."""
    for name in names:
        value = (os.getenv(name) or "").strip()
        if value:
            return value
    return default


def _read_optional_int_prefer(*names: str) -> int | None:
    for name in names:
        raw = os.getenv(name)
        if raw is None or not str(raw).strip():
            continue
        return int(raw)
    return None


def _read_llm_advisory_enabled() -> bool:
    """Prefer AEROBIM_LLM_ADVISORY_ENABLED; keep AEROBIM_LLM_LOCAL_ENABLED as alias.

    Name ``LOCAL`` contradicted cloud Studio / egress use. Prefer ADVISORY;
    LOCAL remains until end of KT#3 (remove after 2026-09-21), then delete.
    """

    if os.getenv("AEROBIM_LLM_ADVISORY_ENABLED") is not None:
        return _read_bool("AEROBIM_LLM_ADVISORY_ENABLED", False)
    return _read_bool("AEROBIM_LLM_LOCAL_ENABLED", False)


# End of TechLab KT#3 window (3–21 Sep 2026). Delete LOCAL env alias after this date.
_LLM_LOCAL_ALIAS_REMOVE_AFTER = "2026-09-21"


def _warn_deprecated_llm_local_alias() -> None:
    """Emit once-per-process warning if legacy LOCAL env is still set."""

    if os.getenv("AEROBIM_LLM_LOCAL_ENABLED") is None:
        return
    logging.getLogger(__name__).warning(
        "AEROBIM_LLM_LOCAL_ENABLED is deprecated; use AEROBIM_LLM_ADVISORY_ENABLED. "
        "Alias will be removed after KT#3 (target %s). "
        "Scripts and docs still on LOCAL will silently diverge.",
        _LLM_LOCAL_ALIAS_REMOVE_AFTER,
    )


_DEV_ENVIRONMENTS = frozenset({"development", "dev", "test"})
_DEFAULT_MAX_IFC_BYTES = 256 * 1024 * 1024  # aligned with bSI Validation Service
# Baked pilot/production quotas when env unset (RTATOM-I20 / A2.3).
_PILOT_DEFAULT_MAX_UPLOADS_PER_DAY = 100
_PILOT_DEFAULT_MAX_BYTES_PER_DAY = 10 * 1024 * 1024 * 1024  # 10 GiB
_PILOT_DEFAULT_MAX_CONCURRENT_JOBS = 4
_DEFAULT_HTTP_RATE_LIMIT_PER_MINUTE = 120

_DEFAULT_LLM_ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        # Yandex AI Studio OpenAI-compat (RF). On-prem adds via AEROBIM_LLM_ALLOWED_HOSTS.
        "ai.api.cloud.yandex.net",
        "llm.api.cloud.yandex.net",
    }
)
_FORBIDDEN_LLM_HOST_MARKERS: tuple[str, ...] = (
    "aliyuncs.com",
    "dashscope",
    "api.openai.com",
    "openai.com",
    "api.anthropic.com",
)


def _parse_llm_allowed_hosts(raw: str | None) -> frozenset[str]:
    hosts = set(_DEFAULT_LLM_ALLOWED_HOSTS)
    if raw:
        for part in raw.split(","):
            host = part.strip().lower()
            if host:
                hosts.add(host)
    return frozenset(hosts)


def assert_llm_base_host_allowed(url: str, allowed_hosts: frozenset[str]) -> None:
    """Fail-closed host allowlist — SSRF alone must not authorize Alibaba Max."""

    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").lower()
    if not host:
        raise RuntimeError("AEROBIM_LLM_BASE_URL must include a hostname")
    if any(marker in host for marker in _FORBIDDEN_LLM_HOST_MARKERS):
        raise RuntimeError(
            f"AEROBIM_LLM_BASE_URL host {host!r} is forbidden "
            "(Alibaba/OpenAI/Anthropic public clouds are not authorized; "
            "use loopback vLLM or Yandex AI Studio / on-prem allowlist)"
        )
    if host not in allowed_hosts:
        raise RuntimeError(
            f"AEROBIM_LLM_BASE_URL host {host!r} is not on the allowlist "
            "(built-in + AEROBIM_LLM_ALLOWED_HOSTS). "
            "Add the on-prem / Studio hostname explicitly; never rely on SSRF alone."
        )


_FORBIDDEN_MODEL_ALIASES = frozenset({"latest", "rc"})


def assert_llm_model_pin_no_aliases(*parts: str | None) -> None:
    """Reject ``/latest`` and ``/rc`` aliases (D-5).

    Explicit catalog versions and **unversioned** ``gpt://folder/model`` URIs are
    allowed. Operators must never write ``latest``/``rc`` by hand; the vendor may
    still echo ``…/latest`` in the response — record that as ``vendor_model_uri``.
    """

    for part in parts:
        if not part:
            continue
        tail = str(part).rstrip("/").split("/")[-1].strip().lower()
        if tail in _FORBIDDEN_MODEL_ALIASES:
            raise RuntimeError(
                f"LLM model pin must not use alias {tail!r}; "
                "use an unversioned gpt://folder/model URI or an explicit catalog version "
                "(never write /latest or /rc)"
            )


def resolve_llm_model_uri(
    *,
    model: str,
    revision: str | None = None,
    folder_id: str | None = None,
) -> str:
    """Build Yandex ``gpt://folder/model[/version]`` URI when parts are separate.

    Floating aliases ``latest`` / ``rc`` are rejected in the *configured* URI.
    Unversioned ``gpt://folder/model`` is allowed when the catalog has no version
    segment (Studio Qwen); pin honesty then relies on ``vendor_model_uri`` + hashes
    from the live response (P₂ drift check).
    """

    rev = (revision or "").strip() or None
    if rev:
        assert_llm_model_pin_no_aliases(rev)
    raw = (model or "").strip()
    folder = (folder_id or "").strip() or None
    if not raw:
        return raw
    if raw.startswith("gpt://"):
        if not rev:
            assert_llm_model_pin_no_aliases(raw)
            return raw
        parts = raw.rstrip("/").split("/")
        if parts and parts[-1].lower() in _FORBIDDEN_MODEL_ALIASES | {rev.lower()}:
            parts[-1] = rev
            resolved = "/".join(parts)
        else:
            resolved = f"{raw.rstrip('/')}/{rev}"
        assert_llm_model_pin_no_aliases(resolved)
        return resolved
    assert_llm_model_pin_no_aliases(raw)
    if folder and rev:
        resolved = f"gpt://{folder}/{raw.strip('/')}/{rev}"
        assert_llm_model_pin_no_aliases(resolved)
        return resolved
    if folder:
        resolved = f"gpt://{folder}/{raw.strip('/')}"
        assert_llm_model_pin_no_aliases(resolved)
        return resolved
    return raw


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
    clash_skip_tiny: bool = True
    """Skip degenerate/tiny IFC products before IfcClash (``AEROBIM_CLASH_SKIP_TINY``)."""
    clash_min_aabb_volume_m3: float = 1e-6
    """AABB volume below which products are skipped when ``clash_skip_tiny`` is on."""
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
    http_rate_limit_per_minute: int = 0
    """Per-client rate limit for analyze/validate/upload POSTs and lab OIDC
    login/callback GETs (RT-RATE-001).

    Env: ``AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE``. ``0`` disables in development.
    Production/pilot default 120 when unset; explicit ``0`` under those profiles
    fails boot (HD2-RL-02).
    """
    http_trusted_proxy_ips: tuple[str, ...] = ()
    """Peer IPs allowed to supply ``X-Forwarded-For`` for rate-limit keys (HD2-RL-03).

    Env: ``AEROBIM_TRUSTED_PROXY_IPS`` (comma-separated). Empty = never trust XFF.
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
    oidc_roles_claim: str = "roles"
    """JWT claim for RBAC roles (supports dotted paths, e.g. realm_access.roles)."""
    oidc_bff_client_id: str | None = None
    """Lab-only OIDC BFF public client id (``AEROBIM_OIDC_BFF_CLIENT_ID``).

    With ``oidc_bff_authorize_url``, Phase 2.5 login may include an IdP authorize
    URL draft. Does **not** flip ``auth_bff`` to implemented / Checkpoint GO.
    """
    oidc_bff_authorize_url: str | None = None
    """Lab-only authorize endpoint (``AEROBIM_OIDC_BFF_AUTHORIZE_URL``)."""
    oidc_bff_redirect_uri_allowlist: tuple[str, ...] = ()
    """Exact ``redirect_uri`` allowlist for Phase 2.5 IdP URL drafts.

    Env: ``AEROBIM_OIDC_BFF_REDIRECT_URI_ALLOWLIST`` (comma-separated). Without a
    match, login still issues CSRF+PKCE but omits ``idp_redirect_url`` (no open
    redirect). Does not flip ``auth_bff`` to implemented.
    """
    oidc_bff_token_url: str | None = None
    """Lab-only token endpoint (``AEROBIM_OIDC_BFF_TOKEN_URL``). Phase 3."""
    oidc_bff_client_secret: str | None = None
    """Confidential BFF client secret (``AEROBIM_OIDC_BFF_CLIENT_SECRET``). Phase 3."""
    oidc_bff_cookie_secret: str | None = None
    """Session cookie HMAC secret (``AEROBIM_OIDC_BFF_COOKIE_SECRET``). Phase 3."""
    # Optional Redis for durable async jobs
    redis_url: str | None = None
    # Optional bSI Validation Service / local schema certificate
    bsi_validation_url: str | None = None
    bsi_api_token: str | None = None
    bsi_local_cert: bool = False
    """When true (and remote URL unset), emit a local schema-pack certificate id."""
    remark_locale: str = "ru"
    """Product remark language: ``ru`` | ``en`` (``AEROBIM_REMARK_LOCALE``)."""
    pdf_backend: str = "pdfium"
    """PDF engine: ``pdfium`` (default) | ``pymupdf`` (optional ``pdf-agpl``) | ``none``.

    LIC-001 Option B — production default is permissive pypdfium2/pdfminer.six.
    ``none`` disables PDF integrity probes; ``pymupdf`` requires the AGPL extra.
    """
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
    mep_aabb_filter_enabled: bool = True
    """Optional AABB broadphase for MEP matrix pairs (``AEROBIM_MEP_AABB_FILTER``).

    Default on: when IFC geometry yields AABBs, shrink candidate pairs. Still
    ``geometry_verified=False`` — AABB ≠ clash. When geometry missing, falls back
    to co_presence/connects edges.
    """
    ifc_parse_cache_dir: str | None = None
    """Optional IFC parse cache directory (``AEROBIM_IFC_PARSE_CACHE_DIR``) — NFR SLA."""
    hybrid_drawing_enabled: bool = True
    """Use HybridDrawingAnalyzer for DrawingAnalyzerPort when True."""
    vlm_enabled: bool = False
    """Opt-in advisory VLM drawing read (``AEROBIM_VLM_ENABLED``;
    alias ``AEROBIM_KIMI_K3_ENABLED``).

    Provider-agnostic (Yandex/Qwen, vLLM, or Moonshot Kimi profile). Advisory only
    (ADR-001 / TR-31): never sets ``summary.passed``. Default off.
    """
    vlm_api_base_url: str | None = None
    """OpenAI-compatible base URL for the advisory VLM endpoint (SSRF-gated)."""
    vlm_api_key: str | None = None
    """API key for the advisory VLM endpoint (never logged)."""
    vlm_model: str = "kimi-k3"
    """Advisory model id (e.g. ``gpt://…/qwen3.6-35b-a3b`` or ``kimi-k3``)."""
    vlm_reasoning_effort: str = "low"
    """reasoning_effort for kimi-k3 API (``low`` OCR-by-region / ``high`` cross-doc).

    Only sent for profiles that support it (kimi-k3 API); ignored for Yandex/vLLM.
    """
    vlm_max_image_bytes: int = 32 * 1024 * 1024
    """Max drawing-image bytes before the VLM pipeline fails closed (IMAGE_TOO_LARGE)."""
    vlm_cache_dir: str | None = None
    """Optional dir for the deterministic VLM response cache (§2.1 act replay).

    When set, advisory region reads are cached by (sha256 image + sha256 prompt +
    model) for byte-identical golden-hash replay. Advisory-only; off by default.
    """
    vlm_cache_namespace: str | None = None
    """Explicit tenant/project isolation scope for the VLM response cache (§5).

    MUST be a trusted deployment-config value derived from tenant_id / project_id
    — never taken from the request body, filename, sheet_id, or the model's
    response. When ``vlm_cache_dir`` is set but this is empty or path-unsafe, the
    persistent cache is DISABLED (fail-closed: a cache is never shared across
    tenants). Allowed chars: ``[A-Za-z0-9._-]``, 1-64 (no ``.``/``..``).
    """
    vlm_cache_ttl_days: int | None = None
    """Optional TTL (days) for cached VLM responses (§5.10).

    On read, an entry older than the TTL is treated as a miss and deleted
    (explicit deletion policy). ``None`` keeps entries until the dir is cleared.
    """
    vlm_cache_project: str | None = None
    """Optional project sub-scope for the VLM response cache (§7).

    Folded into the cache key + physical store dir under the tenant namespace so
    two projects of the same tenant never share cached answers. Same trusted-config
    rule as ``vlm_cache_namespace``; when set but path-unsafe the cache is DISABLED
    (fail-closed). Empty = no project boundary (tenant-level scope only).
    """
    hybrid_provider_config_path: str | None = None
    """Optional path to a JSON provider config for the Hybrid AI model router (P2).

    Deployment-config only (trusted). When set, the DI ``HYBRID_MODEL_ROUTER`` loads its
    ProviderRegistry from this file (enabling private/public model tiers); when unset the
    router stays LOCAL-ONLY fail-closed (no external egress). A set path that is
    missing/invalid fails closed LOUD at bootstrap (RuntimeError).
    """
    llm_local_enabled: bool = False
    """Opt-in local OpenAI-compat LLM (vLLM/Qwen) for advisory remark compose only."""
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_provider: str = "qwen-local"
    llm_model: str = "Qwen3.6-27B"
    llm_model_revision: str | None = None
    """Required pin when LLM enabled (vendor URI + version). Fail-closed at boot."""
    llm_model_sha256: str | None = None
    """Optional checkpoint hash recorded in advisory usage / audit (never a secret)."""
    llm_timeout_seconds: float = 60.0
    llm_max_tokens_per_call: int = 4_096
    llm_max_tokens_per_run: int = 100_000
    llm_max_tokens_per_day: int = 300_000
    llm_max_completion_tokens: int = 512
    """Hard caps for advisory LLM (Yandex grant / repair-loop fail-closed).

    Measured 2026-08-03 (think off): ~440 tokens/remark → ~44k/100 findings.
    Run cap **100_000** ≈ two packs with headroom — stops a runaway repair-loop
    that would otherwise burn five packs under the old 250k fuse.
    Day **300_000** while card-bound (no TRIAL_EXPIRED). Convert to ₽ only after
    console in/out tariff for ``qwen3.6-35b-a3b``.
    """
    llm_allowed_hosts: tuple[str, ...] = tuple(sorted(_DEFAULT_LLM_ALLOWED_HOSTS))
    """Hostname allowlist for AEROBIM_LLM_BASE_URL (fail-closed beyond SSRF)."""
    llm_folder_id: str | None = None
    """Yandex Cloud folder ID (x-folder-id + gpt:// URI composition)."""
    llm_auth_scheme: str = "Bearer"
    """Authorization scheme: ``Bearer`` (OpenAI SDK style) or ``Api-Key`` (YC curl docs)."""
    llm_send_seed: bool = True
    """When false, omit ``seed`` (Yandex Completions may 400 on undocumented seed)."""
    llm_response_format_mode: str = "json_object"
    """``json_schema`` (Yandex preferred) or ``json_object`` (local vLLM)."""
    llm_data_logging_enabled: bool = False
    """When false, send ``x-data-logging-enabled: false`` (Yandex vendor privacy header)."""
    llm_max_concurrent: int = 4
    """Semaphore for parallel Studio calls (cloud quota is shared; default 4 of 10).

    Bounds overlay_llm_remarks ThreadPool fan-out (hard-capped at 10 cloud quota).
    """
    llm_advisory_max_issues: int = 32
    """Max findings to overlay with AI drafts per analyze run (AEROBIM_LLM_ADVISORY_MAX_ISSUES).

    Default 32 ≈ 14k tokens at ~440/finding. Raise toward 100 after console
    tariff × budget check (full pack ≈ 44k tokens).
    """
    llm_429_retries: int = 3
    """Retries on HTTP 429 with linear backoff before fail-closed SKIPPED."""
    llm_budget_tz: str = "Europe/Moscow"
    """IANA timezone for day-roll of ``max_tokens_per_day`` (AEROBIM_LLM_BUDGET_TZ)."""
    llm_budget_ledger_path: Path | None = None
    """Shared JSON day ledger (AEROBIM_LLM_BUDGET_LEDGER). Required when LLM ready (RT-031)."""

    def vlm_advisory_ready(self) -> bool:
        """True only when advisory VLM is safe to invoke.

        Fail-closed tiers: under pilot/production profiles public/external VLM
        egress is **forbidden** (NDA data must not leave the contour) unless an
        approved on-prem path is wired. Dev/fixture may enable it for open data.
        Yandex Studio + default ``kimi-k3`` is refused (wrong request profile).
        """
        if not self.vlm_enabled:
            return False
        if self.signoff_profile in {"samolet_pilot", "production"}:
            return False
        if not (self.vlm_api_base_url and self.vlm_api_key):
            return False
        from aerobim.core.config.vlm_endpoint_gate import refuse_yandex_kimi_default_model

        if refuse_yandex_kimi_default_model(
            base_url=self.vlm_api_base_url,
            model=self.vlm_model,
            provider=self.llm_provider,
        ):
            return False
        return True

    def llm_local_ready(self) -> bool:
        """True when OpenAI-compat advisory LLM may be invoked.

        Fail-closed: disabled by default; requires enable + base URL.
        ``samolet_pilot`` / ``production`` hard-disable external advisory egress
        (customer closed contour). Pin: ``AEROBIM_LLM_MODEL_REVISION`` **or** an
        unversioned ``gpt://…/model`` URI without ``/latest``/``/rc``.
        Does not authorize Alibaba cloud Max.
        """

        if not self.llm_local_enabled:
            return False
        if self.signoff_profile in {"samolet_pilot", "production"}:
            return False
        if not self.llm_base_url:
            return False
        if (self.llm_model_revision or "").strip():
            return True
        model = (self.llm_model or "").strip()
        if model.startswith("gpt://"):
            try:
                assert_llm_model_pin_no_aliases(model)
            except RuntimeError:
                return False
            # gpt://folder/name  (3+ segments after scheme) — unversioned studio pin
            parts = model[len("gpt://") :].rstrip("/").split("/")
            return len(parts) >= 2
        return False

    @property
    def llm_advisory_enabled(self) -> bool:
        """Canonical name for the advisory-LLM enable flag (alias of llm_local_enabled)."""

        return self.llm_local_enabled

    @property
    def is_dev_environment(self) -> bool:
        return self.environment.strip().lower() in _DEV_ENVIRONMENTS

    @property
    def oidc_enabled(self) -> bool:
        return bool(self.oidc_issuer and self.oidc_audience and self.oidc_jwks_url)

    @property
    def oidc_bff_phase3_ready(self) -> bool:
        """True only when Phase 3 IdP + cookie secrets are fully configured."""

        return bool(
            self.oidc_bff_client_id
            and self.oidc_bff_authorize_url
            and self.oidc_bff_token_url
            and self.oidc_bff_client_secret
            and self.oidc_bff_cookie_secret
            and self.oidc_bff_redirect_uri_allowlist
        )

    @property
    def enforce_hitl_reviewer_auth(self) -> bool:
        """Block static bearer from expert HITL sign-off under pilot/production."""

        return self.signoff_profile in {"samolet_pilot", "production"}

    @property
    def disable_sync_package_analyze(self) -> bool:
        """Force async submit for heavy analyze under pilot/production."""

        return self.signoff_profile in {"samolet_pilot", "production"}

    @property
    def enforce_stage_timeouts(self) -> bool:
        """Fail closed when analyze contours exceed stage budgets."""

        return self.signoff_profile in {"samolet_pilot", "production"}

    @property
    def require_hitl_reviewer_roles(self) -> bool:
        """OIDC principals must carry reviewer/admin roles for expert HITL."""

        return self.signoff_profile in {"samolet_pilot", "production"}

    @property
    def enforce_norm_pack_rbac(self) -> bool:
        """Norm-pack mutations require editor/reviewer/admin OIDC roles."""

        return self.signoff_profile in {"samolet_pilot", "production"}

    def require_durable_runtime(self) -> None:
        """Fail closed: non-dev must not silently use in-memory jobs / in-process limits."""

        if self.is_dev_environment:
            return
        if not (self.redis_url or "").strip():
            raise RuntimeError(
                "Non-development deployments require AEROBIM_REDIS_URL "
                "for durable analyze jobs and shared rate limiting "
                f"(AEROBIM_ENV={self.environment!r})"
            )

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
        _warn_deprecated_llm_local_alias()
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

        rate_limit_raw = (os.getenv("AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE") or "").strip()
        if rate_limit_raw:
            http_rate_limit_per_minute = int(rate_limit_raw)
        elif profile_gate:
            http_rate_limit_per_minute = _DEFAULT_HTTP_RATE_LIMIT_PER_MINUTE
        else:
            http_rate_limit_per_minute = 0
        if profile_gate and http_rate_limit_per_minute <= 0:
            raise RuntimeError(
                "AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE must be > 0 under "
                "samolet_pilot/production (0 silently disables the limiter)"
            )
        http_trusted_proxy_ips = tuple(
            ip.strip()
            for ip in (os.getenv("AEROBIM_TRUSTED_PROXY_IPS") or "").split(",")
            if ip.strip()
        )

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
            clash_skip_tiny=_read_bool("AEROBIM_CLASH_SKIP_TINY", True),
            clash_min_aabb_volume_m3=_read_float("AEROBIM_CLASH_MIN_AABB_VOLUME_M3", 1e-6),
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
            http_rate_limit_per_minute=http_rate_limit_per_minute,
            http_trusted_proxy_ips=http_trusted_proxy_ips,
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
            oidc_roles_claim=(
                (os.getenv("AEROBIM_OIDC_ROLES_CLAIM") or "roles").strip() or "roles"
            ),
            oidc_bff_client_id=(os.getenv("AEROBIM_OIDC_BFF_CLIENT_ID") or "").strip() or None,
            oidc_bff_authorize_url=(
                (os.getenv("AEROBIM_OIDC_BFF_AUTHORIZE_URL") or "").strip() or None
            ),
            oidc_bff_redirect_uri_allowlist=tuple(
                uri.strip()
                for uri in (os.getenv("AEROBIM_OIDC_BFF_REDIRECT_URI_ALLOWLIST") or "").split(",")
                if uri.strip()
            ),
            oidc_bff_token_url=(os.getenv("AEROBIM_OIDC_BFF_TOKEN_URL") or "").strip() or None,
            oidc_bff_client_secret=(os.getenv("AEROBIM_OIDC_BFF_CLIENT_SECRET") or "").strip()
            or None,
            oidc_bff_cookie_secret=(os.getenv("AEROBIM_OIDC_BFF_COOKIE_SECRET") or "").strip()
            or None,
            redis_url=(os.getenv("AEROBIM_REDIS_URL") or "").strip() or None,
            bsi_validation_url=(os.getenv("AEROBIM_BSI_VALIDATION_URL") or "").strip() or None,
            bsi_api_token=(os.getenv("AEROBIM_BSI_API_TOKEN") or "").strip() or None,
            bsi_local_cert=bsi_local_cert,
            remark_locale=(os.getenv("AEROBIM_REMARK_LOCALE") or "ru").strip().lower() or "ru",
            pdf_backend=(os.getenv("AEROBIM_PDF_BACKEND") or "pdfium").strip().lower() or "pdfium",
            norm_rule_pack_path=(os.getenv("AEROBIM_NORM_RULE_PACK") or "").strip() or None,
            allow_anonymous_dev=_read_bool("AEROBIM_ALLOW_ANONYMOUS_DEV", False),
            oda_cad_enabled=_read_bool("AEROBIM_ODA_CAD_ENABLED", False),
            mep_system_clash_enabled=_read_bool("AEROBIM_MEP_SYSTEM_CLASH_ENABLED", False),
            mep_scope_memo_ref=(os.getenv("AEROBIM_MEP_SCOPE_MEMO_REF") or "").strip() or None,
            mep_federated_scope_path=(
                (os.getenv("AEROBIM_MEP_FEDERATED_SCOPE_PATH") or "").strip() or None
            ),
            mep_aabb_filter_enabled=_read_bool("AEROBIM_MEP_AABB_FILTER", True),
            ifc_parse_cache_dir=(os.getenv("AEROBIM_IFC_PARSE_CACHE_DIR") or "").strip() or None,
            hybrid_drawing_enabled=_read_bool("AEROBIM_HYBRID_DRAWING_ENABLED", True),
            vlm_enabled=_read_vlm_enabled(),
            vlm_api_base_url=_env_prefer("AEROBIM_VLM_API_BASE_URL", "AEROBIM_KIMI_API_BASE_URL")
            or None,
            vlm_api_key=_env_prefer("AEROBIM_VLM_API_KEY", "AEROBIM_KIMI_API_KEY") or None,
            vlm_model=_env_prefer("AEROBIM_VLM_MODEL", "AEROBIM_KIMI_MODEL", default="kimi-k3")
            or "kimi-k3",
            vlm_reasoning_effort=(
                _env_prefer(
                    "AEROBIM_VLM_REASONING_EFFORT",
                    "AEROBIM_KIMI_REASONING_EFFORT",
                    default="low",
                ).lower()
                or "low"
            ),
            vlm_max_image_bytes=_read_int(
                "AEROBIM_VLM_MAX_IMAGE_BYTES",
                _read_int("AEROBIM_KIMI_MAX_IMAGE_BYTES", 32 * 1024 * 1024),
            ),
            vlm_cache_dir=_env_prefer("AEROBIM_VLM_CACHE_DIR", "AEROBIM_KIMI_CACHE_DIR") or None,
            vlm_cache_namespace=_env_prefer(
                "AEROBIM_VLM_CACHE_NAMESPACE", "AEROBIM_KIMI_CACHE_NAMESPACE"
            )
            or None,
            vlm_cache_ttl_days=_read_optional_int_prefer(
                "AEROBIM_VLM_CACHE_TTL_DAYS", "AEROBIM_KIMI_CACHE_TTL_DAYS"
            ),
            vlm_cache_project=_env_prefer("AEROBIM_VLM_CACHE_PROJECT", "AEROBIM_KIMI_CACHE_PROJECT")
            or None,
            hybrid_provider_config_path=(
                (os.getenv("AEROBIM_HYBRID_PROVIDER_CONFIG") or "").strip() or None
            ),
            llm_local_enabled=_read_llm_advisory_enabled(),
            llm_base_url=(os.getenv("AEROBIM_LLM_BASE_URL") or "").strip() or None,
            llm_api_key=(os.getenv("AEROBIM_LLM_API_KEY") or "").strip() or None,
            llm_provider=(os.getenv("AEROBIM_LLM_PROVIDER") or "qwen-local").strip()
            or "qwen-local",
            llm_model=(os.getenv("AEROBIM_LLM_MODEL") or "Qwen3.6-27B").strip() or "Qwen3.6-27B",
            llm_model_revision=(os.getenv("AEROBIM_LLM_MODEL_REVISION") or "").strip() or None,
            llm_model_sha256=(os.getenv("AEROBIM_LLM_MODEL_SHA256") or "").strip() or None,
            llm_timeout_seconds=float(
                (os.getenv("AEROBIM_LLM_TIMEOUT_SECONDS") or "60").strip() or "60"
            ),
            llm_max_tokens_per_call=_read_int("AEROBIM_LLM_MAX_TOKENS_PER_CALL", 4_096),
            llm_max_tokens_per_run=_read_int("AEROBIM_LLM_MAX_TOKENS_PER_RUN", 100_000),
            llm_max_tokens_per_day=_read_int("AEROBIM_LLM_MAX_TOKENS_PER_DAY", 300_000),
            llm_max_completion_tokens=_read_int("AEROBIM_LLM_MAX_COMPLETION_TOKENS", 512),
            llm_allowed_hosts=tuple(
                sorted(_parse_llm_allowed_hosts(os.getenv("AEROBIM_LLM_ALLOWED_HOSTS")))
            ),
            llm_folder_id=(os.getenv("AEROBIM_LLM_FOLDER_ID") or "").strip() or None,
            llm_auth_scheme=(os.getenv("AEROBIM_LLM_AUTH_SCHEME") or "Bearer").strip() or "Bearer",
            llm_send_seed=_read_bool("AEROBIM_LLM_SEND_SEED", True),
            llm_response_format_mode=(
                os.getenv("AEROBIM_LLM_RESPONSE_FORMAT_MODE") or "json_object"
            ).strip()
            or "json_object",
            llm_data_logging_enabled=_read_bool("AEROBIM_LLM_DATA_LOGGING_ENABLED", False),
            llm_max_concurrent=_read_int("AEROBIM_LLM_MAX_CONCURRENT", 4),
            llm_advisory_max_issues=_read_int("AEROBIM_LLM_ADVISORY_MAX_ISSUES", 32),
            llm_429_retries=_read_int("AEROBIM_LLM_429_RETRIES", 3),
            llm_budget_tz=(os.getenv("AEROBIM_LLM_BUDGET_TZ") or "Europe/Moscow").strip()
            or "Europe/Moscow",
            llm_budget_ledger_path=(
                Path(raw_ledger)
                if (raw_ledger := (os.getenv("AEROBIM_LLM_BUDGET_LEDGER") or "").strip())
                else None
            ),
        )
        # Yandex AI Studio defaults when provider is selected (operator may still override).
        if settings.llm_provider.strip().lower() == "yandex-ai-studio":
            settings = replace(
                settings,
                llm_send_seed=_read_bool("AEROBIM_LLM_SEND_SEED", False),
                llm_response_format_mode=(
                    os.getenv("AEROBIM_LLM_RESPONSE_FORMAT_MODE") or "json_schema"
                ).strip()
                or "json_schema",
                llm_base_url=settings.llm_base_url or "https://llm.api.cloud.yandex.net/v1",
            )
        if settings.llm_local_enabled and not settings.llm_local_ready():
            if settings.signoff_profile in {"samolet_pilot", "production"}:
                # Profile hard-disables advisory egress; do not fail boot if flag left on.
                pass
            else:
                raise RuntimeError(
                    "AEROBIM_LLM_ADVISORY_ENABLED (or deprecated AEROBIM_LLM_LOCAL_ENABLED) "
                    "requires AEROBIM_LLM_BASE_URL and either "
                    "AEROBIM_LLM_MODEL_REVISION (explicit version) or an unversioned "
                    "gpt://<folder>/<model> URI without /latest or /rc"
                )
        if settings.llm_local_ready() and settings.llm_budget_ledger_path is None:
            raise RuntimeError(
                "AEROBIM_LLM_BUDGET_LEDGER is required when LLM advisory is ready "
                "(RT-031 fail-closed: shared day cap; process-local counters ×N workers)"
            )
        if settings.llm_local_enabled:
            try:
                resolved = resolve_llm_model_uri(
                    model=settings.llm_model,
                    revision=settings.llm_model_revision,
                    folder_id=settings.llm_folder_id,
                )
                assert_llm_model_pin_no_aliases(
                    settings.llm_model,
                    settings.llm_model_revision,
                    resolved,
                )
            except RuntimeError:
                raise
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
            ("AEROBIM_OIDC_BFF_TOKEN_URL", settings.oidc_bff_token_url),
            ("AEROBIM_BSI_VALIDATION_URL", settings.bsi_validation_url),
            ("AEROBIM_BCF_API_BASE_URL", settings.bcf_api_base_url),
            ("AEROBIM_S3_ENDPOINT_URL", settings.s3_endpoint_url),
            ("AEROBIM_VLM_API_BASE_URL", settings.vlm_api_base_url),
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
                raise RuntimeError(f"{label} failed SSRF gate: {exc}") from exc
            if label == "AEROBIM_VLM_API_BASE_URL":
                try:
                    assert_llm_base_host_allowed(
                        candidate,
                        frozenset(settings.llm_allowed_hosts),
                    )
                except RuntimeError as exc:
                    raise RuntimeError(f"{label} failed LLM host allowlist: {exc}") from exc

        if settings.llm_base_url:
            try:
                from urllib.parse import urlparse as _urlparse

                host = (_urlparse(settings.llm_base_url).hostname or "").lower()
                assert_llm_base_host_allowed(
                    settings.llm_base_url,
                    frozenset(settings.llm_allowed_hosts),
                )
                if host in {"localhost", "127.0.0.1", "::1"}:
                    assert_safe_datastore_url(settings.llm_base_url)
                else:
                    # Yandex AI Studio / remote private HTTPS endpoint.
                    assert_safe_outbound_url(
                        settings.llm_base_url,
                        allow_http=False,
                        resolve_dns=env_name not in _DEV_ENVIRONMENTS,
                    )
            except UnsafeOutboundUrlError as exc:
                raise RuntimeError(f"AEROBIM_LLM_BASE_URL failed SSRF gate: {exc}") from exc
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
        settings.require_durable_runtime()
        return settings
