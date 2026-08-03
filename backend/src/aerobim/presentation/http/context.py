"""Shared per-app HTTP context: auth dependency, path jail, ACL and serializers.

``ApiContext`` is built once per ``create_http_app`` call from the DI container
and passed to router factories. ``require_bearer_auth`` is a *bound method*
used directly as a FastAPI dependency (``Depends(ctx.require_bearer_auth)``),
which replaces the former closures inside the monolithic ``create_http_app``.

This module imports FastAPI at import time; ``api.py`` therefore imports it
lazily, after its "Install FastAPI" guard. No ``from __future__ import
annotations`` here: FastAPI must evaluate dependency annotations at runtime.
"""

import re as _re
import secrets
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any

from fastapi import Header, HTTPException

from aerobim.application.services.iso19650_metadata import enrich_iso19650_metadata
from aerobim.application.services.loin_metadata_resolver import LoinMetadataResolver
from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens
from aerobim.core.security.path_jail import (
    PathJailError,
    assert_path_under_tenant_prefix,
    reject_symlinks,
    resolve_storage_path,
    tenant_storage_prefix,
)
from aerobim.core.security.upload_quota import FilesystemUploadQuotaStore
from aerobim.domain.models import RequirementSource, SourceKind, ValidationRequest
from aerobim.domain.object_acl import (
    AuthPrincipal,
    principal_may_access_job,
    principal_may_access_norm_pack,
    principal_may_access_report,
)
from aerobim.infrastructure.security.oidc_token_validator import OidcValidationError
from aerobim.presentation.http.package_request_builders import (
    build_project_package_request,
    build_requirement_source,
)
from aerobim.presentation.http.schemas import AnalyzeProjectPackageRequest

REPORT_ID_RE = _re.compile(r"^[a-f0-9]{32}$")
DRAWING_ASSET_ID_RE = _re.compile(r"^[A-Za-z0-9_-]{1,128}$")
BCF_PROJECT_ID_RE = _re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
LOIN_RESOLVER = LoinMetadataResolver()
UPLOAD_HASH_CHUNK = 1024 * 1024
UPLOAD_SNIFF_BYTES = 4096

_ALLOWED_PREVIEW_MEDIA_TYPES = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
        "application/pdf",
    }
)

# Egress mark for AI remark drafts (HTTP JSON + BCF provenance must agree).
_AI_CONTENT_MARKING = "ai_generated=true;expert_confirmation_required=true"


def attachment_content_disposition(filename: str) -> str:
    """RFC 6266-ish attachment header; strip CR/LF and quotes from filename."""
    safe = (
        filename.replace('"', "")
        .replace("\r", "")
        .replace("\n", "")
        .replace("\\", "_")
        .replace("/", "_")
    )
    return f'attachment; filename="{safe}"'


def safe_preview_media_type(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    return value if value in _ALLOWED_PREVIEW_MEDIA_TYPES else "application/octet-stream"


class ApiContext:
    """Per-app dependencies and route helpers resolved from the DI container."""

    def __init__(self, container: Container) -> None:
        self.container = container
        self.settings = container.resolve(Tokens.SETTINGS)
        self.logger = container.resolve(Tokens.LOGGER)
        self.validate_use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
        self.analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
        self.audit_store = container.resolve(Tokens.AUDIT_REPORT_STORE)
        self.oidc_validator = None
        if container.is_registered(Tokens.OIDC_TOKEN_VALIDATOR):
            self.oidc_validator = container.resolve(Tokens.OIDC_TOKEN_VALIDATOR)
        self.object_store = None
        if container.is_registered(Tokens.OBJECT_STORE):
            self.object_store = container.resolve(Tokens.OBJECT_STORE)
        self.upload_quota_store = FilesystemUploadQuotaStore(
            self.settings.storage_dir,
            max_uploads_per_day=self.settings.max_uploads_per_tenant_day,
            max_bytes_per_day=self.settings.max_upload_bytes_per_tenant_day,
            fail_closed=self.settings.audit_fail_closed,
        )

    # -- Auth -------------------------------------------------------------

    def require_bearer_auth(
        self,
        authorization: Annotated[str | None, Header()] = None,
    ) -> AuthPrincipal:
        settings = self.settings
        configured_token = settings.api_bearer_token
        oidc_ready = self.oidc_validator is not None

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
            assert self.oidc_validator is not None
            try:
                claims = self.oidc_validator.validate(token)
                claim_name = (settings.oidc_tenant_claim or "tenant_id").strip() or "tenant_id"
                tenant_claim = claims.get(claim_name)
                tenant = str(tenant_claim).strip() if tenant_claim is not None else ""
                if not tenant:
                    # RT A07: never fall back to api_tenant_id for OIDC principals.
                    raise HTTPException(
                        status_code=401,
                        detail="OIDC token missing required tenant claim",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                subject = claims.get("sub")
                return AuthPrincipal(
                    tenant_id=tenant,
                    subject=str(subject) if subject is not None else None,
                )
            except HTTPException:
                raise
            except OidcValidationError as exc:
                # RT A13: never leak validator detail to clients.
                self.logger.warning("OIDC token validation failed", detail=str(exc))
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API token",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from exc

        raise HTTPException(
            status_code=401,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # -- Path jail / limits -------------------------------------------------

    def resolve_safe_path(
        self,
        user_path: str,
        *,
        principal: AuthPrincipal | None = None,
    ) -> Path:
        """Resolve user-supplied path strictly within storage_dir; reject symlinks.

        When object ACL is enforced, paths must stay under ``tenants/{tenant}/``.
        """
        settings = self.settings
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

    def enforce_ifc_size(self, ifc_path: Path) -> None:
        if not ifc_path.is_file():
            return
        size = ifc_path.stat().st_size
        if size > self.settings.max_ifc_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"IFC file exceeds size limit ({size} bytes > "
                    f"{self.settings.max_ifc_bytes} bytes)"
                ),
            )

    # -- Object ACL assertions ---------------------------------------------

    def assert_report_access(self, report, principal: AuthPrincipal) -> None:
        if principal_may_access_report(
            enforce_object_acl=self.settings.enforce_object_acl,
            principal=principal,
            report=report,
        ):
            return
        # RT-POST-02: identical to missing — do not confirm cross-tenant existence.
        raise HTTPException(
            status_code=404,
            detail=f"Report {getattr(report, 'report_id', '')} not found",
        )

    def assert_job_access(self, job, principal: AuthPrincipal) -> None:
        if principal_may_access_job(
            enforce_object_acl=self.settings.enforce_object_acl,
            principal=principal,
            job=job,
        ):
            return
        raise HTTPException(
            status_code=404,
            detail=f"Analyze project-package job {getattr(job, 'job_id', '')} not found",
        )

    def assert_norm_pack_access(self, principal: AuthPrincipal, *, tenant_id: str | None) -> None:
        if principal_may_access_norm_pack(
            enforce_object_acl=self.settings.enforce_object_acl,
            principal=principal,
            tenant_id=tenant_id,
        ):
            return
        raise HTTPException(
            status_code=404,
            detail="Norm pack not found",
        )

    def resolve_bound_tenant(
        self,
        principal: AuthPrincipal,
        *,
        payload_tenant_id: str | None = None,
    ) -> str | None:
        """Bind request tenant from principal; block client spoof when ACL is on."""

        principal_tenant = (principal.tenant_id or "").strip() or None
        if self.settings.enforce_object_acl:
            if principal_tenant is None:
                raise HTTPException(
                    status_code=403,
                    detail="Object ACL requires authenticated tenant binding",
                )
            return principal_tenant
        payload_tenant = (payload_tenant_id or "").strip() or None
        return principal_tenant or payload_tenant

    # -- Identifier validation ----------------------------------------------

    def validate_report_id(self, report_id: str) -> None:
        if not REPORT_ID_RE.match(report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")

    def validate_job_id(self, job_id: str) -> None:
        if not REPORT_ID_RE.match(job_id):
            raise HTTPException(status_code=400, detail="Invalid job ID format")

    def validate_drawing_asset_id(self, asset_id: str) -> None:
        if not DRAWING_ASSET_ID_RE.match(asset_id):
            raise HTTPException(status_code=400, detail="Invalid drawing asset ID format")

    # -- Serialization -------------------------------------------------------

    def _enrich_issue_export(self, issue: dict[str, object]) -> dict[str, object]:
        enriched = dict(issue)
        remark = enriched.get("remark")
        if isinstance(remark, dict) and remark.get("ai_generated"):
            enriched["remark"] = {
                **remark,
                "content_marking": remark.get("content_marking") or _AI_CONTENT_MARKING,
            }
        rule_id = str(enriched.get("rule_id", ""))
        loin = LOIN_RESOLVER.resolve(rule_id)
        if loin is None:
            return enriched
        return {
            **enriched,
            "loin_purpose": loin.purpose,
            "loin_milestone": loin.milestone,
            "loin_actor": loin.actor,
            "loin_information_level": loin.information_level,
        }

    def serialize_public_report(self, report) -> dict[str, Any]:
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
            self._enrich_issue_export(issue) if isinstance(issue, dict) else issue
            for issue in data.get("issues", ())
        ]
        data["iso19650"] = enrich_iso19650_metadata(report)
        return data

    def serialize_analyze_project_package_job(self, job) -> dict[str, object]:
        payload = asdict(job)
        payload["status"] = job.status.value
        payload["status_url"] = f"/v1/analyze/project-package/jobs/{job.job_id}"
        payload["report_url"] = f"/v1/reports/{job.report_id}" if job.report_id else None
        return payload

    # -- Report source resolution --------------------------------------------

    def assert_object_key_under_tenant(
        self,
        object_key: str,
        *,
        report,
        principal: AuthPrincipal,
    ) -> None:
        """When ACL is on, object keys must live under the tenant storage prefix."""
        if not self.settings.enforce_object_acl:
            return
        tenant = (getattr(report, "tenant_id", None) or principal.tenant_id or "").strip()
        if not tenant:
            raise HTTPException(status_code=404, detail="Object not found")
        try:
            prefix = tenant_storage_prefix(tenant)
        except PathJailError as exc:
            raise HTTPException(status_code=404, detail="Object not found") from exc
        key = (object_key or "").lstrip("/")
        if not key.startswith(prefix):
            raise HTTPException(status_code=404, detail="Object not found")

    def resolve_report_ifc_source(
        self,
        report_id: str,
        *,
        principal: AuthPrincipal | None = None,
    ) -> tuple[str, bytes | Path]:
        settings = self.settings
        report = self.audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        if report.ifc_object_key and self.object_store is not None:
            if principal is not None:
                self.assert_object_key_under_tenant(
                    report.ifc_object_key, report=report, principal=principal
                )
            payload = self.object_store.get_bytes(report.ifc_object_key)
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
        if settings.enforce_object_acl:
            tenant = (getattr(report, "tenant_id", None) or "").strip()
            if not tenant and principal is not None:
                tenant = (principal.tenant_id or "").strip()
            if tenant:
                try:
                    assert_path_under_tenant_prefix(
                        resolved,
                        base=base,
                        tenant_id=tenant,
                    )
                except PathJailError as exc:
                    raise HTTPException(status_code=404, detail="Object not found") from exc
        if not resolved.exists():
            raise HTTPException(
                status_code=404, detail=f"IFC source for report {report_id} not found"
            )
        return report.ifc_path.name, resolved

    def resolve_report_drawing_asset_preview(
        self,
        report_id: str,
        asset_id: str,
        *,
        principal: AuthPrincipal | None = None,
    ):
        settings = self.settings
        report = self.audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        drawing_asset = next(
            (asset for asset in report.drawing_assets if asset.asset_id == asset_id), None
        )
        if drawing_asset is None or not drawing_asset.stored_filename:
            raise HTTPException(status_code=404, detail=f"Drawing asset {asset_id} not found")

        if drawing_asset.object_key and self.object_store is not None:
            if principal is not None:
                self.assert_object_key_under_tenant(
                    drawing_asset.object_key, report=report, principal=principal
                )
            payload = self.object_store.get_bytes(drawing_asset.object_key)
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
        try:
            reject_symlinks(resolved, base=settings.storage_dir.resolve())
        except PathJailError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if settings.enforce_object_acl:
            tenant = (getattr(report, "tenant_id", None) or "").strip()
            if not tenant and principal is not None:
                tenant = (principal.tenant_id or "").strip()
            if tenant:
                try:
                    assert_path_under_tenant_prefix(
                        resolved,
                        base=settings.storage_dir.resolve(),
                        tenant_id=tenant,
                    )
                except PathJailError as exc:
                    raise HTTPException(status_code=404, detail="Object not found") from exc
        if not resolved.exists():
            raise HTTPException(
                status_code=404, detail=f"Drawing asset preview for {asset_id} not found"
            )
        return drawing_asset, resolved

    # -- Request builders ------------------------------------------------------

    def build_requirement_source(
        self,
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
        return build_requirement_source(
            text,
            path,
            source_kind,
            resolve_path=self.resolve_safe_path,
            revision=revision,
            stage=stage,
            doc_status=doc_status,
            source_id=source_id,
            principal=principal,
        )

    def build_project_package_request(
        self,
        payload: AnalyzeProjectPackageRequest,
        *,
        tenant_id: str | None = None,
        principal: AuthPrincipal | None = None,
    ) -> ValidationRequest:
        return build_project_package_request(
            payload,
            resolve_path=self.resolve_safe_path,
            enforce_ifc_size=self.enforce_ifc_size,
            storage_dir=self.settings.storage_dir,
            tenant_id=tenant_id,
            principal=principal,
        )
