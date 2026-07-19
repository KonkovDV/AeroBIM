# pyright: reportUnusedFunction=false, reportUnknownVariableType=false

import hashlib
import json
import re as _re
import secrets
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from aerobim.application.services.iso19650_metadata import enrich_iso19650_metadata
from aerobim.application.services.loin_metadata_resolver import LoinMetadataResolver
from aerobim.application.services.review_kpi import summarize_review_events
from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens
from aerobim.core.security.path_jail import (
    PathJailError,
    assert_path_under_tenant_prefix,
    reject_symlinks,
    resolve_storage_path,
    safe_storage_token,
    tenant_storage_prefix,
)
from aerobim.core.security.upload_content import UploadContentError, validate_upload_content
from aerobim.core.security.upload_quota import (
    FilesystemUploadQuotaStore,
    UploadQuotaExceeded,
)
from aerobim.core.security.zip_limits import ZipBombError, inspect_zip_path
from aerobim.domain.models import (
    DrawingSource,
    ReportListFilters,
    RequirementSource,
    ReviewEvent,
    SourceKind,
    ValidationRequest,
)
from aerobim.domain.object_acl import (
    AuthPrincipal,
    principal_may_access_job,
    principal_may_access_norm_pack,
    principal_may_access_report,
)
from aerobim.domain.review_state_machine import HitlTransitionError, assert_hitl_transition
from aerobim.domain.system_capabilities import build_system_capabilities_payload
from aerobim.infrastructure.adapters.openrebar_evidence_verifier import (
    build_openrebar_provenance_digest,
)
from aerobim.infrastructure.security.oidc_token_validator import OidcValidationError

_REPORT_ID_RE = _re.compile(r"^[a-f0-9]{32}$")
_DRAWING_ASSET_ID_RE = _re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_BCF_PROJECT_ID_RE = _re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_LOIN_RESOLVER = LoinMetadataResolver()
_UPLOAD_HASH_CHUNK = 1024 * 1024
_UPLOAD_SNIFF_BYTES = 4096


def _attachment_content_disposition(filename: str) -> str:
    """RFC 6266-ish attachment header; strip CR/LF and quotes from filename."""
    safe = (
        filename.replace('"', "")
        .replace("\r", "")
        .replace("\n", "")
        .replace("\\", "_")
        .replace("/", "_")
    )
    return f'attachment; filename="{safe}"'


class ValidateIfcRequest(BaseModel):
    request_id: str | None = None
    ifc_path: str = Field(max_length=2048)
    requirement_text: str = Field(default="", max_length=50_000)
    requirement_path: str | None = Field(default=None, max_length=2048)
    ids_path: str | None = Field(default=None, max_length=2048)
    project_name: str | None = Field(default=None, max_length=256)
    discipline: str | None = Field(default=None, max_length=128)
    stage: str | None = Field(default=None, max_length=64)
    information_container_id: str | None = Field(default=None, max_length=256)
    revision: str | None = Field(default=None, max_length=64)
    doc_status: Literal["WIP", "Shared", "Published", "Archived"] | None = None


class DrawingPayload(BaseModel):
    text: str = Field(default="", max_length=50_000)
    path: str | None = Field(default=None, max_length=2048)
    sheet_id: str | None = Field(default=None, max_length=128)
    format: str | None = Field(default=None, max_length=32)


class AnalyzeProjectPackageRequest(BaseModel):
    request_id: str | None = None
    ifc_path: str = Field(max_length=2048)
    requirement_text: str = Field(default="", max_length=50_000)
    requirement_path: str | None = Field(default=None, max_length=2048)
    ids_path: str | None = Field(default=None, max_length=2048)
    technical_spec_text: str = Field(default="", max_length=50_000)
    technical_spec_path: str | None = Field(default=None, max_length=2048)
    calculation_text: str = Field(default="", max_length=50_000)
    calculation_path: str | None = Field(default=None, max_length=2048)
    drawings: list[DrawingPayload] = Field(default_factory=list, max_length=64)
    norm_rule_pack_paths: list[str] = Field(default_factory=list, max_length=16)
    pd_section_path: str | None = Field(default=None, max_length=2048)
    rd_section_path: str | None = Field(default=None, max_length=2048)
    reinforcement_report_path: str | None = Field(default=None, max_length=2048)
    reinforcement_handoff_path: str | None = Field(default=None, max_length=2048)
    reinforcement_source_digest: str | None = Field(default=None, max_length=128)
    reinforcement_waste_warning_threshold_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    reinforcement_provenance_mode: Literal["advisory", "enforced"] = "advisory"
    project_name: str | None = Field(default=None, max_length=256)
    discipline: str | None = Field(default=None, max_length=128)
    stage: str | None = Field(default=None, max_length=64)
    information_container_id: str | None = Field(default=None, max_length=256)
    revision: str | None = Field(default=None, max_length=64)
    doc_status: Literal["WIP", "Shared", "Published", "Archived"] | None = None
    tenant_id: str | None = Field(default=None, max_length=128)
    project_id: str | None = Field(default=None, max_length=256)


class OpenRebarDigestRequest(BaseModel):
    reinforcement_report_path: str = Field(max_length=2048)


class PushBcfApiRequest(BaseModel):
    project_id: str | None = Field(
        default=None,
        max_length=128,
        description="BCF API project id; defaults to AEROBIM_BCF_API_PROJECT_ID",
    )


class ReviewEventRequest(BaseModel):
    event_type: Literal[
        "opened",
        "accepted",
        "rejected",
        "edited_remark",
        "edited",
        "triaged",
        "norm_rule_proposed",
        "norm_rule_edited",
        "drawing_region_escalated",
        "escalated",
        "waived",
        "superseded",
    ]
    issue_rule_id: str | None = Field(default=None, max_length=256)
    actor: str | None = Field(default=None, max_length=128)
    note: str | None = Field(default=None, max_length=2000)
    latency_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    previous_state: str | None = Field(default=None, max_length=64)
    finding_id: str | None = Field(default=None, max_length=64)
    idempotency_key: str | None = Field(default=None, max_length=256)


class NormRuleHitlEventRequest(BaseModel):
    event_type: Literal["norm_rule_proposed", "norm_rule_edited"]
    base_pack_path: str = Field(min_length=1, max_length=512)
    rule_diff: dict[str, object]
    proposed_by: str | None = Field(default=None, max_length=128)
    target_approval_status: Literal["synthetic", "draft", "customer_approved"] | None = None
    approval_ref: str | None = Field(default=None, max_length=512)
    report_id: str | None = Field(default=None, max_length=64)


def create_http_app(container: Container):
    try:
        from fastapi import (
            BackgroundTasks,
            Body,
            Depends,
            FastAPI,
            File,
            Header,
            HTTPException,
            Response,
            UploadFile,
        )
        from fastapi.middleware.cors import CORSMiddleware
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install FastAPI and Pydantic to run the HTTP API") from exc

    from aerobim.presentation.http.correlation import add_correlation_middleware

    settings = container.resolve(Tokens.SETTINGS)
    logger = container.resolve(Tokens.LOGGER)
    validate_use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
    analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
    audit_store = container.resolve(Tokens.AUDIT_REPORT_STORE)
    oidc_validator = None
    if container.is_registered(Tokens.OIDC_TOKEN_VALIDATOR):
        oidc_validator = container.resolve(Tokens.OIDC_TOKEN_VALIDATOR)
    object_store = None
    if container.is_registered(Tokens.OBJECT_STORE):
        object_store = container.resolve(Tokens.OBJECT_STORE)
    upload_quota_store = FilesystemUploadQuotaStore(
        settings.storage_dir,
        max_uploads_per_day=settings.max_uploads_per_tenant_day,
        max_bytes_per_day=settings.max_upload_bytes_per_tenant_day,
    )

    app = FastAPI(title="aerobim-backend", version="0.2.0")

    # -- Middleware stack (order matters: outermost first) --
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    add_correlation_middleware(app)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "service": settings.application_name,
            "environment": settings.environment,
            "status": "ok",
        }

    def _resolve_safe_path(
        user_path: str,
        *,
        principal: AuthPrincipal | None = None,
    ) -> Path:
        """Resolve user-supplied path strictly within storage_dir; reject symlinks.

        When object ACL is enforced, paths must stay under ``tenants/{tenant}/``.
        """
        try:
            resolved = resolve_storage_path(user_path, base=settings.storage_dir)
            if settings.enforce_object_acl:
                if principal is None or not (principal.tenant_id or "").strip():
                    raise HTTPException(
                        status_code=403,
                        detail="Object ACL requires authenticated tenant for path access",
                    )
                assert_path_under_tenant_prefix(
                    resolved,
                    base=settings.storage_dir,
                    tenant_id=principal.tenant_id or "",
                )
            return resolved
        except PathJailError as exc:
            detail = str(exc)
            status = 403 if "tenant storage prefix" in detail else 400
            raise HTTPException(status_code=status, detail=detail) from exc

    def _enforce_ifc_size(ifc_path: Path) -> None:
        if not ifc_path.is_file():
            return
        size = ifc_path.stat().st_size
        if size > settings.max_ifc_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"IFC file exceeds size limit ({size} bytes > {settings.max_ifc_bytes} bytes)"
                ),
            )

    def _require_bearer_auth(
        authorization: Annotated[str | None, Header()] = None,
    ) -> AuthPrincipal:
        configured_token = settings.api_bearer_token
        oidc_ready = oidc_validator is not None

        if configured_token is None and not oidc_ready:
            if settings.is_dev_environment and settings.allow_anonymous_dev:
                return AuthPrincipal(tenant_id=settings.api_tenant_id, subject="anonymous-dev")
            if settings.is_dev_environment:
                raise HTTPException(
                    status_code=401,
                    detail=(
                        "API auth required: set AEROBIM_API_BEARER_TOKEN "
                        "or AEROBIM_ALLOW_ANONYMOUS_DEV=true for local anonymous access"
                    ),
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise HTTPException(
                status_code=503,
                detail=(
                    "API auth is required outside development "
                    "(set AEROBIM_API_BEARER_TOKEN and/or OIDC settings)"
                ),
            )

        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if configured_token is not None and secrets.compare_digest(token, configured_token):
            return AuthPrincipal(tenant_id=settings.api_tenant_id, subject="api-bearer")

        if oidc_ready:
            assert oidc_validator is not None
            try:
                claims = oidc_validator.validate(token)
                claim_name = (settings.oidc_tenant_claim or "tenant_id").strip() or "tenant_id"
                tenant_claim = claims.get(claim_name)
                tenant = str(tenant_claim).strip() if tenant_claim else settings.api_tenant_id
                subject = claims.get("sub")
                return AuthPrincipal(
                    tenant_id=tenant,
                    subject=str(subject) if subject is not None else None,
                )
            except OidcValidationError as exc:
                if configured_token is None:
                    raise HTTPException(
                        status_code=401,
                        detail=str(exc),
                        headers={"WWW-Authenticate": "Bearer"},
                    ) from exc

        raise HTTPException(
            status_code=401,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def _assert_report_access(report, principal: AuthPrincipal) -> None:
        if principal_may_access_report(
            enforce_object_acl=settings.enforce_object_acl,
            principal=principal,
            report=report,
        ):
            return
        # RT-POST-02: identical to missing — do not confirm cross-tenant existence.
        raise HTTPException(
            status_code=404,
            detail=f"Report {getattr(report, 'report_id', '')} not found",
        )

    def _assert_job_access(job, principal: AuthPrincipal) -> None:
        if principal_may_access_job(
            enforce_object_acl=settings.enforce_object_acl,
            principal=principal,
            job=job,
        ):
            return
        raise HTTPException(
            status_code=404,
            detail=f"Analyze project-package job {getattr(job, 'job_id', '')} not found",
        )

    def _assert_norm_pack_access(principal: AuthPrincipal, *, tenant_id: str | None) -> None:
        if principal_may_access_norm_pack(
            enforce_object_acl=settings.enforce_object_acl,
            principal=principal,
            tenant_id=tenant_id,
        ):
            return
        raise HTTPException(
            status_code=404,
            detail="Norm pack not found",
        )

    def _resolve_bound_tenant(
        principal: AuthPrincipal,
        *,
        payload_tenant_id: str | None = None,
    ) -> str | None:
        """Bind request tenant from principal; block client spoof when ACL is on."""

        principal_tenant = (principal.tenant_id or "").strip() or None
        if settings.enforce_object_acl:
            if principal_tenant is None:
                raise HTTPException(
                    status_code=403,
                    detail="Object ACL requires authenticated tenant binding",
                )
            return principal_tenant
        payload_tenant = (payload_tenant_id or "").strip() or None
        return principal_tenant or payload_tenant

    def _validate_report_id(report_id: str) -> None:
        if not _REPORT_ID_RE.match(report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")

    def _validate_job_id(job_id: str) -> None:
        if not _REPORT_ID_RE.match(job_id):
            raise HTTPException(status_code=400, detail="Invalid job ID format")

    def _enrich_issue_export(issue: dict[str, object]) -> dict[str, object]:
        rule_id = str(issue.get("rule_id", ""))
        loin = _LOIN_RESOLVER.resolve(rule_id)
        if loin is None:
            return issue
        return {
            **issue,
            "loin_purpose": loin.purpose,
            "loin_milestone": loin.milestone,
            "loin_actor": loin.actor,
            "loin_information_level": loin.information_level,
        }

    def _serialize_public_report(report) -> dict[str, Any]:
        data = asdict(report)
        data.pop("ifc_path", None)
        data.pop("ifc_object_key", None)
        drawing_assets = []
        for asset in data.get("drawing_assets", []):
            asset.pop("object_key", None)
            asset.pop("source_path", None)
            drawing_assets.append(asset)
        data["drawing_assets"] = drawing_assets
        data["issues"] = [
            _enrich_issue_export(issue) if isinstance(issue, dict) else issue
            for issue in data.get("issues", ())
        ]
        data["iso19650"] = enrich_iso19650_metadata(report)
        return data

    def _resolve_report_ifc_source(report_id: str) -> tuple[str, bytes | Path]:
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        if report.ifc_object_key and object_store is not None:
            payload = object_store.get_bytes(report.ifc_object_key)
            if payload is None:
                raise HTTPException(
                    status_code=404, detail=f"IFC source for report {report_id} not found"
                )
            return report.ifc_path.name, payload

        candidate = report.ifc_path
        base = settings.storage_dir.resolve()
        resolved = candidate.resolve() if candidate.is_absolute() else (base / candidate).resolve()
        if not resolved.is_relative_to(base):
            raise HTTPException(
                status_code=409,
                detail="Stored IFC source escapes storage boundary",
            )
        try:
            reject_symlinks(resolved, base=base)
        except PathJailError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if not resolved.exists():
            raise HTTPException(
                status_code=404, detail=f"IFC source for report {report_id} not found"
            )
        return report.ifc_path.name, resolved

    def _validate_drawing_asset_id(asset_id: str) -> None:
        if not _DRAWING_ASSET_ID_RE.match(asset_id):
            raise HTTPException(status_code=400, detail="Invalid drawing asset ID format")

    def _resolve_report_drawing_asset_preview(report_id: str, asset_id: str):
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        drawing_asset = next(
            (asset for asset in report.drawing_assets if asset.asset_id == asset_id), None
        )
        if drawing_asset is None or not drawing_asset.stored_filename:
            raise HTTPException(status_code=404, detail=f"Drawing asset {asset_id} not found")

        if drawing_asset.object_key and object_store is not None:
            payload = object_store.get_bytes(drawing_asset.object_key)
            if payload is None:
                raise HTTPException(
                    status_code=404, detail=f"Drawing asset preview for {asset_id} not found"
                )
            return drawing_asset, payload

        asset_root = (settings.storage_dir / "drawing-assets" / report_id).resolve()
        resolved = (asset_root / drawing_asset.stored_filename).resolve()
        if not resolved.is_relative_to(asset_root):
            raise HTTPException(
                status_code=409, detail="Stored drawing asset escapes storage boundary"
            )
        if not resolved.exists():
            raise HTTPException(
                status_code=404, detail=f"Drawing asset preview for {asset_id} not found"
            )
        return drawing_asset, resolved

    def _build_requirement_source(
        text: str,
        path: str | None,
        source_kind: SourceKind,
        *,
        revision: str | None = None,
        stage: str | None = None,
        doc_status: str | None = None,
        source_id: str | None = None,
        principal: AuthPrincipal | None = None,
    ) -> RequirementSource:
        return RequirementSource(
            text=text,
            path=_resolve_safe_path(path, principal=principal) if path else None,
            source_kind=source_kind,
            source_id=source_id or f"{source_kind.value}-input",
            revision=revision,
            stage=stage,
            doc_type=source_kind.value,
            doc_status=doc_status,
        )

    def _load_openrebar_report_payload(report_path: Path) -> dict[str, object]:
        if not report_path.exists():
            raise FileNotFoundError(report_path)
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid OpenRebar reinforcement report JSON: {report_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("OpenRebar reinforcement report must be a JSON object")
        return payload

    def _load_openrebar_handoff_payload(handoff_path: Path) -> dict[str, object]:
        if not handoff_path.exists():
            raise FileNotFoundError(handoff_path)
        try:
            payload = json.loads(handoff_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid OpenRebar handoff JSON: {handoff_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("OpenRebar handoff manifest must be a JSON object")
        return payload

    def _compute_file_sha256(file_path: Path) -> str:
        hasher = hashlib.sha256()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _resolve_openrebar_provenance_inputs(
        payload: AnalyzeProjectPackageRequest,
        *,
        principal: AuthPrincipal | None = None,
    ) -> tuple[Path | None, str | None]:
        if payload.reinforcement_handoff_path:
            if payload.reinforcement_report_path or payload.reinforcement_source_digest:
                raise ValueError(
                    "reinforcement_handoff_path cannot be combined with "
                    "reinforcement_report_path or reinforcement_source_digest"
                )

            handoff_path = _resolve_safe_path(
                payload.reinforcement_handoff_path, principal=principal
            )
            handoff_payload = _load_openrebar_handoff_payload(handoff_path)
            raw_report_path = handoff_payload.get("reinforcement_report_path")
            if not isinstance(raw_report_path, str) or not raw_report_path.strip():
                raise ValueError("OpenRebar handoff manifest must define reinforcement_report_path")

            report_path = _resolve_safe_path(raw_report_path.strip(), principal=principal)
            manifest_sha = handoff_payload.get("report_sha256")
            if manifest_sha is not None:
                if not isinstance(manifest_sha, str) or not manifest_sha.strip():
                    raise ValueError(
                        "OpenRebar handoff manifest report_sha256 must be a non-empty string"
                    )
                observed_sha = _compute_file_sha256(report_path)
                if observed_sha != manifest_sha.strip().lower():
                    raise ValueError("OpenRebar handoff report_sha256 mismatch")

            report_payload = _load_openrebar_report_payload(report_path)
            return report_path, build_openrebar_provenance_digest(report_payload)

        reinforcement_report_path = (
            _resolve_safe_path(payload.reinforcement_report_path, principal=principal)
            if payload.reinforcement_report_path
            else None
        )
        reinforcement_source_digest = (
            payload.reinforcement_source_digest.strip().lower()
            if payload.reinforcement_source_digest
            else None
        )
        return reinforcement_report_path, reinforcement_source_digest

    def _build_project_package_request(
        payload: AnalyzeProjectPackageRequest,
        *,
        tenant_id: str | None = None,
        principal: AuthPrincipal | None = None,
    ) -> ValidationRequest:
        reinforcement_report_path, reinforcement_source_digest = (
            _resolve_openrebar_provenance_inputs(payload, principal=principal)
        )
        ifc_resolved = _resolve_safe_path(payload.ifc_path, principal=principal)
        _enforce_ifc_size(ifc_resolved)
        return ValidationRequest(
            request_id=payload.request_id or uuid4().hex,
            ifc_path=ifc_resolved,
            requirement_source=_build_requirement_source(
                payload.requirement_text,
                payload.requirement_path,
                SourceKind.STRUCTURED_TEXT,
                revision=payload.revision,
                stage=payload.stage,
                doc_status=payload.doc_status,
                principal=principal,
            ),
            ids_path=(
                _resolve_safe_path(payload.ids_path, principal=principal)
                if payload.ids_path
                else None
            ),
            technical_spec_source=_build_requirement_source(
                payload.technical_spec_text,
                payload.technical_spec_path,
                SourceKind.TECHNICAL_SPECIFICATION,
                revision=payload.revision,
                stage=payload.stage,
                doc_status=payload.doc_status,
                principal=principal,
            )
            if payload.technical_spec_text or payload.technical_spec_path
            else None,
            calculation_source=_build_requirement_source(
                payload.calculation_text,
                payload.calculation_path,
                SourceKind.CALCULATION,
                revision=payload.revision,
                stage=payload.stage,
                doc_status=payload.doc_status,
                principal=principal,
            )
            if payload.calculation_text or payload.calculation_path
            else None,
            drawing_sources=tuple(
                DrawingSource(
                    text=drawing.text,
                    path=(
                        _resolve_safe_path(drawing.path, principal=principal)
                        if drawing.path
                        else None
                    ),
                    sheet_id=drawing.sheet_id,
                    format=drawing.format,
                )
                for drawing in payload.drawings
            ),
            norm_rule_pack_paths=tuple(
                _resolve_safe_path(path, principal=principal)
                for path in payload.norm_rule_pack_paths
            ),
            pd_section_path=(
                _resolve_safe_path(payload.pd_section_path, principal=principal)
                if payload.pd_section_path
                else None
            ),
            rd_section_path=(
                _resolve_safe_path(payload.rd_section_path, principal=principal)
                if payload.rd_section_path
                else None
            ),
            reinforcement_report_path=reinforcement_report_path,
            reinforcement_source_digest=reinforcement_source_digest,
            reinforcement_waste_warning_threshold_percent=(
                payload.reinforcement_waste_warning_threshold_percent
            ),
            reinforcement_provenance_mode=payload.reinforcement_provenance_mode,
            project_name=payload.project_name,
            discipline=payload.discipline,
            stage=payload.stage,
            information_container_id=payload.information_container_id,
            revision=payload.revision,
            doc_status=payload.doc_status,
            tenant_id=tenant_id,
            project_id=payload.project_id,
        )

    def _serialize_analyze_project_package_job(job) -> dict[str, object]:
        payload = asdict(job)
        payload["status"] = job.status.value
        payload["status_url"] = f"/v1/analyze/project-package/jobs/{job.job_id}"
        payload["report_url"] = f"/v1/reports/{job.report_id}" if job.report_id else None
        return payload

    @app.post("/v1/uploads")
    async def upload_document(
        file: Annotated[UploadFile, File(...)],
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        """Multipart document ingest into the storage jail (TZ P0).

        Returns a storage-relative ``path`` suitable for ``ifc_path`` / drawing paths
        on subsequent analyze calls. Validates extension + magic bytes and enforces
        ``max_upload_bytes`` for all document types. Content is quarantined until
        checks pass, then promoted under ``tenants/{tenant}/uploads/``.
        """
        tenant_key = (
            principal.tenant_id or principal.subject or "anonymous"
        ).strip() or "anonymous"
        tenant_seg = safe_storage_token(tenant_key)
        raw_name = (file.filename or "upload.bin").replace("\\", "/").split("/")[-1]
        safe_name = (
            raw_name.replace("\r", "").replace("\n", "").replace('"', "").strip() or "upload.bin"
        )[:180]
        upload_id = uuid4().hex
        relative_path = f"{tenant_storage_prefix(tenant_seg)}uploads/{upload_id}/{safe_name}"
        quarantine = (
            settings.storage_dir / "quarantine" / tenant_seg / upload_id / safe_name
        ).resolve()
        target = (settings.storage_dir / relative_path).resolve()
        base = settings.storage_dir.resolve()
        quarantine.parent.mkdir(parents=True, exist_ok=True)
        try:
            reject_symlinks(quarantine.parent, base=base)
        except PathJailError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        max_bytes = settings.max_upload_bytes
        total = 0
        digest = hashlib.sha256()
        sniff_buf = bytearray()
        try:
            with quarantine.open("wb") as handle:
                while True:
                    chunk = await file.read(_UPLOAD_HASH_CHUNK)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise HTTPException(
                            status_code=413,
                            detail=(
                                f"Upload exceeds size limit ({total} bytes > {max_bytes} bytes)"
                            ),
                        )
                    digest.update(chunk)
                    if len(sniff_buf) < _UPLOAD_SNIFF_BYTES:
                        need = _UPLOAD_SNIFF_BYTES - len(sniff_buf)
                        sniff_buf.extend(chunk[:need])
                    handle.write(chunk)
        except HTTPException:
            quarantine.unlink(missing_ok=True)
            raise
        except OSError as exc:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Upload write failed: {exc}") from exc

        if total == 0:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Empty upload")

        try:
            upload_quota_store.assert_can_accept(tenant_key, size_bytes=total)
        except UploadQuotaExceeded as exc:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=429, detail=str(exc)) from exc

        try:
            sniffed = validate_upload_content(
                filename=safe_name,
                payload=bytes(sniff_buf)
                if sniff_buf
                else quarantine.read_bytes()[:_UPLOAD_SNIFF_BYTES],
                declared_content_type=file.content_type,
            )
            if sniffed.kind == "zip" or safe_name.lower().endswith(
                (".zip", ".ifczip", ".docx", ".xlsx", ".pptx")
            ):
                inspect_zip_path(quarantine)
        except UploadContentError as exc:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        except ZipBombError as exc:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        # Promote out of quarantine only after content + zip checks pass.
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            reject_symlinks(target.parent, base=base)
            quarantine.replace(target)
        except (OSError, PathJailError) as exc:
            quarantine.unlink(missing_ok=True)
            raise HTTPException(
                status_code=500, detail=f"Quarantine promote failed: {exc}"
            ) from exc

        if object_store is not None:
            payload = target.read_bytes()
            object_store.put_bytes(
                relative_path.replace("\\", "/"),
                payload,
                content_type=sniffed.mime or file.content_type,
            )
            del payload

        quota = upload_quota_store.record(tenant_key, size_bytes=total)
        return {
            "upload_id": upload_id,
            "filename": safe_name,
            "path": relative_path.replace("\\", "/"),
            "size_bytes": total,
            "content_type": sniffed.mime or file.content_type,
            "sniffed_kind": sniffed.kind,
            "sha256": digest.hexdigest(),
            "tenant_id": tenant_key,
            "quota": {
                "day": quota.day,
                "upload_count": quota.upload_count,
                "bytes_used": quota.bytes_used,
                "max_uploads": quota.max_uploads,
                "max_bytes": quota.max_bytes,
            },
        }

    @app.post("/v1/validate/ifc")
    def validate_ifc(
        payload: Annotated[ValidateIfcRequest, Body()],
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        request_id = payload.request_id or uuid4().hex
        logger.info("validate_ifc started", request_id=request_id, ifc_path=payload.ifc_path)
        try:
            ifc_resolved = _resolve_safe_path(payload.ifc_path, principal=principal)
            _enforce_ifc_size(ifc_resolved)

            report = validate_use_case.execute(
                ValidationRequest(
                    request_id=request_id,
                    ifc_path=ifc_resolved,
                    requirement_source=_build_requirement_source(
                        payload.requirement_text,
                        payload.requirement_path,
                        SourceKind.STRUCTURED_TEXT,
                        principal=principal,
                    ),
                    ids_path=(
                        _resolve_safe_path(payload.ids_path, principal=principal)
                        if payload.ids_path
                        else None
                    ),
                    project_name=payload.project_name,
                    discipline=payload.discipline,
                    stage=payload.stage,
                    information_container_id=payload.information_container_id,
                    revision=payload.revision,
                    doc_status=payload.doc_status,
                    tenant_id=_resolve_bound_tenant(principal),
                )
            )
        except FileNotFoundError as exc:
            logger.warning("validate_ifc file not found", request_id=request_id, detail=str(exc))
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            logger.warning("validate_ifc bad request", request_id=request_id, detail=str(exc))
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            logger.error("validate_ifc runtime error", request_id=request_id, detail=str(exc))
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        logger.info(
            "validate_ifc completed",
            request_id=request_id,
            report_id=report.report_id,
            passed=report.summary.passed,
            issues=report.summary.issue_count,
        )
        return _serialize_public_report(report)

    @app.post("/v1/analyze/project-package")
    def analyze_project_package(
        payload: Annotated[AnalyzeProjectPackageRequest, Body()],
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        try:
            request = _build_project_package_request(
                payload,
                tenant_id=_resolve_bound_tenant(
                    principal,
                    payload_tenant_id=payload.tenant_id,
                ),
                principal=principal,
            )
            report = analyze_use_case.execute(request)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        return _serialize_public_report(report)

    @app.post("/v1/analyze/project-package/reinforcement-digest")
    def analyze_project_package_reinforcement_digest(
        payload: Annotated[OpenRebarDigestRequest, Body()],
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        try:
            report_path = _resolve_safe_path(payload.reinforcement_report_path, principal=principal)
            report_payload = _load_openrebar_report_payload(report_path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        metadata_payload = report_payload.get("metadata")
        metadata = metadata_payload if isinstance(metadata_payload, dict) else {}
        return {
            "reinforcement_report_path": str(report_path),
            "provenance_digest": build_openrebar_provenance_digest(report_payload),
            "contract_id": report_payload.get("contractId"),
            "schema_version": report_payload.get("schemaVersion"),
            "project_code": metadata.get("projectCode"),
            "slab_id": metadata.get("slabId"),
            "claim_labels": {
                "calculation_match": "сверка результатов (provenance/numeric match) — PARTIAL",
                "calculation_correctness": "независимая проверка корректности — НЕ РЕАЛИЗОВАНО",
            },
        }

    @app.post("/v1/analyze/project-package/submit", status_code=202)
    def submit_analyze_project_package(
        payload: Annotated[AnalyzeProjectPackageRequest, Body()],
        background_tasks: BackgroundTasks,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, object]:
        try:
            request = _build_project_package_request(
                payload,
                tenant_id=_resolve_bound_tenant(
                    principal,
                    payload_tenant_id=payload.tenant_id,
                ),
                principal=principal,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        key = idempotency_key.strip() if idempotency_key and idempotency_key.strip() else None
        if key is not None and len(key) > 128:
            raise HTTPException(status_code=400, detail="Idempotency-Key must be ≤128 characters")

        from aerobim.application.use_cases.analyze_project_package_jobs import (
            JobConcurrencyLimitError,
        )

        submit_job_use_case = container.resolve(Tokens.SUBMIT_ANALYZE_PROJECT_PACKAGE_JOB_USE_CASE)
        job_runner = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_RUNNER)
        try:
            job = submit_job_use_case.execute(
                request,
                idempotency_key=key,
                max_concurrent_per_tenant=settings.max_concurrent_analyze_jobs_per_tenant,
            )
        except JobConcurrencyLimitError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        if job.status.value == "queued":
            background_tasks.add_task(job_runner.run, job.job_id, request)
        return _serialize_analyze_project_package_job(job)

    @app.get("/v1/analyze/project-package/jobs/{job_id}")
    def get_analyze_project_package_job(
        job_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        _validate_job_id(job_id)
        get_job_status_use_case = container.resolve(
            Tokens.GET_ANALYZE_PROJECT_PACKAGE_JOB_STATUS_USE_CASE
        )
        job = get_job_status_use_case.execute(job_id)
        if job is None:
            raise HTTPException(
                status_code=404, detail=f"Analyze project-package job {job_id} not found"
            )
        _assert_job_access(job, principal)
        return _serialize_analyze_project_package_job(job)

    @app.post("/v1/analyze/project-package/jobs/{job_id}/cancel")
    def cancel_analyze_project_package_job(
        job_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        _validate_job_id(job_id)
        get_job_status_use_case = container.resolve(
            Tokens.GET_ANALYZE_PROJECT_PACKAGE_JOB_STATUS_USE_CASE
        )
        existing = get_job_status_use_case.execute(job_id)
        if existing is None:
            raise HTTPException(
                status_code=404, detail=f"Analyze project-package job {job_id} not found"
            )
        _assert_job_access(existing, principal)
        job_store = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
        job = job_store.request_cancel(job_id)
        if job is None:
            raise HTTPException(
                status_code=404, detail=f"Analyze project-package job {job_id} not found"
            )
        return _serialize_analyze_project_package_job(job)

    @app.get("/v1/system/capabilities")
    def get_system_capabilities(
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        """Static honesty surface for DWG/CV/MEP/calculation claim boundaries."""

        return build_system_capabilities_payload()

    @app.get("/v1/reports")
    def list_reports(
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
        project: str | None = None,
        discipline: str | None = None,
        passed: bool | None = None,
    ) -> dict[str, object]:
        entries = audit_store.list_reports(
            ReportListFilters(
                project=project,
                discipline=discipline,
                passed=passed,
            )
        )
        if settings.enforce_object_acl:
            principal_tenant = (principal.tenant_id or "").strip().casefold()
            if not principal_tenant:
                entries = []
            else:
                # list_reports returns summaries; reload for tenant binding when enforced.
                filtered = []
                for entry in entries:
                    report = audit_store.get(entry.report_id)
                    if report is None:
                        continue
                    if principal_may_access_report(
                        enforce_object_acl=True,
                        principal=principal,
                        report=report,
                    ):
                        filtered.append(entry)
                entries = filtered
        return {"reports": [asdict(e) for e in entries], "count": len(entries)}

    @app.get("/v1/reports/{report_id}")
    def get_report(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)
        return _serialize_public_report(report)

    @app.post("/v1/reports/{report_id}/review-events")
    def append_review_event(
        report_id: str,
        payload: ReviewEventRequest,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)
        review_store = container.resolve(Tokens.REVIEW_EVENT_STORE)
        resulting_state: str | None = None
        # Norm-pack events are a separate lifecycle; finding HITL transitions are validated.
        if payload.event_type not in {"norm_rule_proposed", "norm_rule_edited"}:
            try:
                resulting_state = assert_hitl_transition(
                    current=payload.previous_state,
                    event_type=payload.event_type,
                    actor=payload.actor,
                    note=payload.note,
                )
            except HitlTransitionError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        idem = (payload.idempotency_key or "").strip()
        if not idem:
            idem_seed = "|".join(
                [
                    report_id,
                    payload.event_type,
                    payload.issue_rule_id or "",
                    payload.finding_id or "",
                    payload.actor or "",
                    payload.note or "",
                    payload.previous_state or "",
                ]
            )
            idem = "api:" + hashlib.sha256(idem_seed.encode("utf-8")).hexdigest()[:40]
        event_id = hashlib.sha256(idem.encode("utf-8")).hexdigest()[:32]
        existing = review_store.list_for_report(report_id)
        event = ReviewEvent(
            event_id=event_id,
            report_id=report_id,
            event_type=payload.event_type,
            created_at=datetime.now(tz=UTC).isoformat(),
            issue_rule_id=payload.issue_rule_id,
            actor=payload.actor,
            note=payload.note,
            latency_ms=payload.latency_ms,
            idempotency_key=idem,
            sequence_number=len(existing) + 1,
            previous_state=payload.previous_state,
            resulting_state=resulting_state,
            finding_id=payload.finding_id,
        )
        review_store.append(event)
        return {"event": asdict(event)}

    @app.post("/v1/norm-packs/{pack_id}/rule-events")
    def post_norm_rule_hitl_event(
        pack_id: str,
        payload: NormRuleHitlEventRequest,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        if not pack_id.strip() or len(pack_id) > 128:
            raise HTTPException(status_code=400, detail="Invalid pack_id")
        tenant_id = _resolve_bound_tenant(principal)
        _assert_norm_pack_access(principal, tenant_id=tenant_id)
        if payload.report_id:
            _validate_report_id(payload.report_id)
            linked = audit_store.get(payload.report_id)
            if linked is None:
                raise HTTPException(status_code=404, detail=f"Report {payload.report_id} not found")
            _assert_report_access(linked, principal)
        use_case = container.resolve(Tokens.APPLY_NORM_RULE_HITL_EVENT_USE_CASE)
        base_path = _resolve_safe_path(payload.base_pack_path, principal=principal)
        try:
            record, event = use_case.execute(
                pack_id=pack_id,
                base_pack_path=base_path,
                event_type=payload.event_type,
                rule_diff=payload.rule_diff,
                proposed_by=payload.proposed_by,
                target_approval_status=payload.target_approval_status,
                approval_ref=payload.approval_ref,
                report_id=payload.report_id,
                tenant_id=tenant_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"version": asdict(record), "event": asdict(event)}

    @app.get("/v1/norm-packs/{pack_id}/versions")
    def list_norm_pack_versions(
        pack_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        if not pack_id.strip() or len(pack_id) > 128:
            raise HTTPException(status_code=400, detail="Invalid pack_id")
        tenant_id = _resolve_bound_tenant(principal)
        _assert_norm_pack_access(principal, tenant_id=tenant_id)
        store = container.resolve(Tokens.NORM_RULE_PACK_VERSION_STORE)
        versions = store.list_versions(pack_id, tenant_id=tenant_id)
        return {"pack_id": pack_id, "versions": [asdict(item) for item in versions]}

    @app.get("/v1/reports/{report_id}/review-events")
    def list_review_events(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)
        review_store = container.resolve(Tokens.REVIEW_EVENT_STORE)
        events = review_store.list_for_report(report_id)
        return {"events": [asdict(e) for e in events], "count": len(events)}

    @app.get("/v1/reports/{report_id}/review-kpi")
    def get_review_kpi(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)
        review_store = container.resolve(Tokens.REVIEW_EVENT_STORE)
        events = review_store.list_for_report(report_id)
        return {"report_id": report_id, "kpi": summarize_review_events(events)}

    @app.get("/v1/reports/{report_id}/source/ifc")
    def get_report_ifc_source(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ):  # noqa: ANN201
        from fastapi.responses import FileResponse

        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)
        filename, source_payload = _resolve_report_ifc_source(report_id)
        if isinstance(source_payload, bytes):
            download_name = filename or f"{report_id}.ifc"
            return Response(
                content=source_payload,
                media_type="application/octet-stream",
                headers={"content-disposition": f'attachment; filename="{download_name}"'},
            )
        return FileResponse(
            path=source_payload,
            media_type="application/octet-stream",
            filename=filename or f"{report_id}.ifc",
        )

    @app.get("/v1/reports/{report_id}/drawing-assets/{asset_id}/preview")
    def get_report_drawing_asset_preview(
        report_id: str,
        asset_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ):  # noqa: ANN201
        from fastapi.responses import FileResponse

        _validate_report_id(report_id)
        _validate_drawing_asset_id(asset_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)
        drawing_asset, preview_payload = _resolve_report_drawing_asset_preview(report_id, asset_id)
        if isinstance(preview_payload, bytes):
            download_name = drawing_asset.stored_filename or f"{asset_id}.png"
            return Response(
                content=preview_payload,
                media_type=drawing_asset.media_type,
                headers={"content-disposition": f'attachment; filename="{download_name}"'},
            )
        return FileResponse(
            path=preview_payload,
            media_type=drawing_asset.media_type,
            filename=drawing_asset.stored_filename,
        )

    @app.get("/v1/reports/{report_id}/export/json")
    def export_report_json(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ):  # noqa: ANN201
        from fastapi.responses import JSONResponse

        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)
        return JSONResponse(
            content=_serialize_public_report(report),
            headers={"Content-Disposition": _attachment_content_disposition(f"{report_id}.json")},
        )

    @app.get("/v1/reports/{report_id}/export/html")
    def export_report_html(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ):  # noqa: ANN201
        from fastapi.responses import HTMLResponse

        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)
        data: dict[str, Any] = _serialize_public_report(report)
        summary: dict[str, Any] = data["summary"]
        status_class = "pass" if summary["passed"] else "fail"
        status_label = "PASSED" if summary["passed"] else "FAILED"

        # Group issues by category for expert reviewer workflow
        from collections import defaultdict

        category_issues: dict[str, list[dict]] = defaultdict(list)
        for issue in data.get("issues", ()):
            cat = issue.get("category", "ifc-validation")
            category_issues[cat].append(issue)

        def _build_issue_rows(issues: list[dict]) -> str:
            rows = ""
            sorted_issues = sorted(issues, key=lambda i: i.get("priority", 0), reverse=True)
            for issue in sorted_issues:
                sev = issue.get("severity", "")
                exp = issue.get("expected_value", "")
                obs = issue.get("observed_value", "")
                unit = issue.get("unit", "")
                pz = issue.get("problem_zone")
                pz_html = ""
                if pz:
                    sheet = _esc(pz.get("sheet_id") or "")
                    x = pz.get("x")
                    y = pz.get("y")
                    if sheet and x is not None and y is not None:
                        pz_html = f"<br><small class='pz'>Лист: {sheet} ({x:.1f}, {y:.1f})</small>"
                ev_obs = (
                    f"<td>{_esc(obs)}{_esc(' ' + unit if unit and obs else '')}</td>"
                    if obs
                    else "<td>—</td>"
                )
                ev_exp = (
                    f"<td>{_esc(exp)}{_esc(' ' + unit if unit and exp else '')}</td>"
                    if exp
                    else "<td>—</td>"
                )
                pri = issue.get("priority", 0)
                pri_class = "pri-high" if pri >= 45 else "pri-med" if pri >= 25 else "pri-low"
                conf = issue.get("confidence")
                conf_display = f"{conf:.2f}" if conf is not None else "—"
                loin_bits = []
                for key, label in (
                    ("loin_purpose", "purpose"),
                    ("loin_milestone", "milestone"),
                    ("loin_actor", "actor"),
                    ("loin_information_level", "level"),
                ):
                    value = issue.get(key)
                    if value:
                        loin_bits.append(f"{label}={_esc(str(value))}")
                loin_html = (
                    f"<br><small class='loin'>{' · '.join(loin_bits)}</small>" if loin_bits else ""
                )
                norm_bits: list[str] = []
                approval = issue.get("approval_status")
                if approval:
                    norm_bits.append(f"badge={_esc(str(approval))}")
                for key, label in (
                    ("norm_source", "src"),
                    ("norm_edition", "ed"),
                    ("norm_clause", "§"),
                    ("approval_ref", "ref"),
                ):
                    value = issue.get(key)
                    if value:
                        norm_bits.append(f"{label}={_esc(str(value))}")
                norm_html = (
                    f"<br><small class='norm-badge'>{' · '.join(norm_bits)}</small>"
                    if norm_bits
                    else ""
                )
                finding_id = issue.get("finding_id") or ""
                source_id = issue.get("source_id") or ""
                evidence_refs = issue.get("evidence_refs") or ()
                if isinstance(evidence_refs, list | tuple):
                    refs_joined = ", ".join(str(ref) for ref in evidence_refs if ref)
                else:
                    refs_joined = str(evidence_refs)
                audit_bits: list[str] = []
                if finding_id:
                    audit_bits.append(f"finding_id={_esc(str(finding_id))}")
                if source_id:
                    audit_bits.append(f"source_id={_esc(str(source_id))}")
                if refs_joined:
                    audit_bits.append(f"evidence_refs={_esc(refs_joined)}")
                origin = issue.get("origin")
                if origin:
                    audit_bits.append(f"origin={_esc(str(origin))}")
                if not finding_id or not source_id or not refs_joined:
                    audit_bits.append("provenance=INCOMPLETE")
                audit_html = (
                    f"<br><small class='audit'>{' · '.join(audit_bits)}</small>"
                    if audit_bits
                    else ""
                )
                detail_html = f"{pz_html}{audit_html}" or "—"
                rows += (
                    f"<tr><td class='sev {_esc(sev)}'>{_esc(sev)}</td>"
                    f"<td class='{pri_class}'>{pri}</td>"
                    f"<td>{conf_display}</td>"
                    f"<td>{_esc(issue.get('rule_id', ''))}{loin_html}{norm_html}</td>"
                    f"<td>{_esc(issue.get('message', ''))}</td>"
                    f"{ev_exp}{ev_obs}"
                    f"<td>{_esc(issue.get('element_guid') or '')}</td>"
                    f"<td>{_esc(issue.get('target_ref') or '')}</td></tr>\n"
                    f"<tr class='detail'><td colspan='9'>{detail_html}</td></tr>\n"
                )
            return rows

        iso_fields = [
            ("Stage", data.get("stage")),
            ("CDE container", data.get("information_container_id")),
            ("Revision", data.get("revision")),
            ("Doc status", data.get("doc_status")),
        ]
        iso_rows = "".join(
            f"<tr><th>{_esc(label)}</th><td>{_esc(str(value))}</td></tr>"
            for label, value in iso_fields
            if value is not None
        )
        iso_section = ""
        if iso_rows:
            iso_section = (
                "<section class='cat'><h2>ISO 19650 context</h2>"
                "<table><tbody>"
                f"{iso_rows}"
                "</tbody></table></section>\n"
            )

        category_sections = ""
        cat_labels = {
            "ifc-validation": "IFC Model Validation",
            "ids-validation": "IDS Requirement Validation",
            "drawing-validation": "Drawing Annotation Validation",
            "cross-document": "Cross-Document Contradictions",
        }
        for cat, issues in sorted(category_issues.items()):
            label = cat_labels.get(cat, cat)
            rows = _build_issue_rows(issues)
            category_sections += (
                f"<section class='cat'><h2>{label} ({len(issues)})</h2>"
                f"<table><thead><tr><th>Severity</th><th>Priority</th><th>Confidence</th><th>Rule</th><th>Message</th>"
                f"<th>Expected</th><th>Observed</th><th>GUID</th><th>Target</th></tr></thead>"
                f"<tbody>{rows}</tbody></table></section>\n"
            )

        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Validation Report {_esc(report_id)}</title>
<style>
:root{{--error:#c00;--warning:#b58900;--info:#555;--bg-pass:#d4edda;--bg-fail:#f8d7da}}
body{{font-family:system-ui,sans-serif;margin:2em;color:#222;line-height:1.5}}
h1{{font-size:1.5em;margin-bottom:.3em}}
h2{{font-size:1.1em;margin:1.2em 0 .5em}}
.summary{{margin:1em 0;padding:1em;border-radius:6px;font-size:1.05em}}
.pass{{background:var(--bg-pass);color:#155724}}
.fail{{background:var(--bg-fail);color:#721c24}}
section.cat{{margin-top:1.5em}}
table{{border-collapse:collapse;width:100%;margin-top:.5em;font-size:.95em}}
th,td{{border:1px solid #ccc;padding:.4em .8em;text-align:left;vertical-align:top}}
th{{background:#f5f5f5}}
td.error,td.sev.error{{color:var(--error);font-weight:600}}
td.warning,td.sev.warning{{color:var(--warning);font-weight:600}}
td.info{{color:var(--info)}}
tr.detail td{{border-top:none;padding-top:0;color:#666;font-size:.85em}}
small.pz{{color:#555}}
.meta{{margin-top:2em;font-size:.85em;color:#888}}
td.pri-high{{color:var(--error);font-weight:700}}
td.pri-med{{color:var(--warning);font-weight:600}}
td.pri-low{{color:var(--info)}}
</style></head><body>
<h1>Validation Report</h1>
<div class="summary {status_class}">
<strong>{status_label}</strong> &mdash;
{summary["issue_count"]} issue(s): {summary["error_count"]} error(s),
{summary["warning_count"]} warning(s) &middot;
{summary["requirement_count"]} requirement(s)
</div>
{iso_section}{category_sections}
<p class="meta">
Report ID: {_esc(report_id)} &middot;
Project: {_esc(str(data.get("project_name") or "—"))} &middot;
Discipline: {_esc(str(data.get("discipline") or "—"))} &middot;
Created: {_esc(str(data.get("created_at") or ""))}
</p>
</body></html>"""
        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": _attachment_content_disposition(f"{report_id}.html")},
        )

    @app.get("/v1/reports/{report_id}/export/bcf")
    def export_report_bcf(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
        version: str = "2.1",
    ):  # noqa: ANN201
        """Export report as BCF ZIP.

        Query parameter ``version`` selects the BCF schema version:
        - ``2.1`` (default) — stable BCF 2.1 export.
        - ``3`` or ``3.0`` — experimental BCF 3.0 export (buildingSMART BCF 3.0).
        """
        from fastapi.responses import Response

        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)

        if version in {"3", "3.0"}:
            from aerobim.infrastructure.adapters.bcf3_exporter import export_bcf3

            bcf_bytes = export_bcf3(report)
        else:
            from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

            bcf_bytes = export_bcf(report)

        return Response(
            content=bcf_bytes,
            media_type="application/x-bcfzip",
            headers={"Content-Disposition": _attachment_content_disposition(f"{report_id}.bcf")},
        )

    @app.post("/v1/reports/{report_id}/export/bcf-api/push")
    def push_report_bcf_api(
        report_id: str,
        payload: Annotated[PushBcfApiRequest, Body()],
        principal: Annotated[AuthPrincipal, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        """Push report topics to a remote OpenCDE BCF API 3.0 hub."""
        _validate_report_id(report_id)
        project_id = (payload.project_id or settings.bcf_api_project_id or "").strip()
        if not project_id:
            raise HTTPException(
                status_code=400,
                detail="project_id is required (body or AEROBIM_BCF_API_PROJECT_ID)",
            )
        if not _BCF_PROJECT_ID_RE.match(project_id):
            raise HTTPException(
                status_code=400,
                detail="project_id must be a UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)",
            )
        configured_project = (settings.bcf_api_project_id or "").strip()
        if configured_project and project_id.lower() != configured_project.lower():
            raise HTTPException(
                status_code=403,
                detail="project_id does not match AEROBIM_BCF_API_PROJECT_ID",
            )
        if not container.is_registered(Tokens.PUSH_REPORT_TO_BCF_API_USE_CASE):
            raise HTTPException(status_code=503, detail="BCF API push use case is not registered")

        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        _assert_report_access(report, principal)

        push_use_case = container.resolve(Tokens.PUSH_REPORT_TO_BCF_API_USE_CASE)
        try:
            result = push_use_case.execute(report_id, project_id=project_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        return {
            "project_id": result.project_id,
            "attempted": result.attempted,
            "succeeded": result.succeeded,
            "failed": result.failed,
            "topics": [asdict(topic) for topic in result.topics],
        }

    return app


def _esc(value: str) -> str:
    """HTML-escape user-controlled values for element text and attributes."""
    import html

    return html.escape(str(value), quote=True)
