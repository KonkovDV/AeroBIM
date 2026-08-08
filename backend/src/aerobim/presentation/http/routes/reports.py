"""Report listing, retrieval, review events/KPI and source/preview routes."""

import hashlib
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse

from aerobim.application.services.review_kpi import summarize_review_events
from aerobim.core.di.tokens import Tokens
from aerobim.core.security.path_jail import PathJailError, reject_symlinks
from aerobim.domain.check_coverage import coverage_from_report, derive_report_scope
from aerobim.domain.models import ReportListFilters
from aerobim.domain.object_acl import AuthPrincipal, principal_may_access_report
from aerobim.presentation.http.context import (
    ApiContext,
    attachment_content_disposition,
    safe_preview_media_type,
)
from aerobim.presentation.http.schemas import ReviewEventRequest


def build_reports_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()
    settings = ctx.settings
    audit_store = ctx.audit_store

    @router.get("/v1/reports")
    def list_reports(
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
        project: str | None = None,
        discipline: str | None = None,
        passed: bool | None = None,
    ) -> dict[str, object]:
        # RTATOM-H02/H03: when principal has tenant_id, always scope list — even with ACL soft-off.
        principal_tenant = (principal.tenant_id or "").strip() or None
        entries = audit_store.list_reports(
            ReportListFilters(
                project=project,
                discipline=discipline,
                passed=passed,
                tenant_id=principal_tenant,
            )
        )
        if settings.enforce_object_acl:
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

    @router.get("/v1/reports/{report_id}")
    def get_report(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        ctx.validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)
        return ctx.serialize_public_report(report)

    @router.get("/v1/reports/{report_id}/coverage")
    def get_report_coverage(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        # Read-only, verdict-neutral: per-source check-coverage derived on-the-fly from
        # the stored report ('no findings' != 'not checked'). Never sets summary.passed.
        ctx.validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)
        return coverage_from_report(report, scope=derive_report_scope(report)).to_dict()

    @router.post("/v1/reports/{report_id}/review-events")
    def append_review_event(
        report_id: str,
        payload: ReviewEventRequest,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        from aerobim.domain.object_acl import principal_may_append_hitl_event
        from aerobim.domain.review_event_append import HitlStateConflictError, ReviewEventAppendSpec
        from aerobim.domain.review_state_machine import HitlTransitionError
        from aerobim.presentation.http.errors import public_hitl_forbidden_detail

        ctx.validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)
        if not principal_may_append_hitl_event(
            enforce_hitl_reviewer_auth=settings.enforce_hitl_reviewer_auth,
            require_hitl_reviewer_roles=settings.require_hitl_reviewer_roles,
            principal=principal,
            event_type=payload.event_type,
        ):
            raise HTTPException(status_code=403, detail=public_hitl_forbidden_detail())
        review_store = ctx.container.resolve(Tokens.REVIEW_EVENT_STORE)
        actor = (principal.subject or "").strip() or payload.actor
        idem = (payload.idempotency_key or "").strip()
        if not idem:
            idem_seed = "|".join(
                [
                    report_id,
                    payload.event_type,
                    payload.issue_rule_id or "",
                    payload.finding_id or "",
                    actor or "",
                    payload.note or "",
                    (payload.previous_state or "").strip(),
                ]
            )
            idem = "api:" + hashlib.sha256(idem_seed.encode("utf-8")).hexdigest()[:40]
        event_id = hashlib.sha256(idem.encode("utf-8")).hexdigest()[:32]
        try:
            event = review_store.append_api_event(
                ReviewEventAppendSpec(
                    report_id=report_id,
                    event_type=payload.event_type,
                    created_at=datetime.now(tz=UTC).isoformat(),
                    issue_rule_id=payload.issue_rule_id,
                    actor=actor,
                    note=payload.note,
                    latency_ms=payload.latency_ms,
                    finding_id=payload.finding_id,
                    previous_state=payload.previous_state,
                    idempotency_key=idem,
                    event_id=event_id,
                )
            )
        except HitlStateConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except HitlTransitionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"event": asdict(event)}

    @router.get("/v1/reports/{report_id}/review-events")
    def list_review_events(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        ctx.validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)
        review_store = ctx.container.resolve(Tokens.REVIEW_EVENT_STORE)
        events = review_store.list_for_report(report_id)
        return {"events": [asdict(e) for e in events], "count": len(events)}

    @router.get("/v1/reports/{report_id}/review-kpi")
    def get_review_kpi(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        ctx.validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)
        review_store = ctx.container.resolve(Tokens.REVIEW_EVENT_STORE)
        events = review_store.list_for_report(report_id)
        return {"report_id": report_id, "kpi": summarize_review_events(events)}

    @router.get("/v1/reports/{report_id}/source/ifc")
    def get_report_ifc_source(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> Response | FileResponse:
        ctx.validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)
        filename, source_payload = ctx.resolve_report_ifc_source(report_id, principal=principal)
        if isinstance(source_payload, bytes):
            download_name = filename or f"{report_id}.ifc"
            return Response(
                content=source_payload,
                media_type="application/octet-stream",
                headers={"Content-Disposition": attachment_content_disposition(download_name)},
            )
        try:
            reject_symlinks(Path(source_payload), base=settings.storage_dir.resolve())
        except PathJailError as exc:
            raise HTTPException(status_code=404, detail="IFC source not found") from exc
        return FileResponse(
            path=source_payload,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": attachment_content_disposition(
                    filename or f"{report_id}.ifc"
                )
            },
        )

    @router.get("/v1/reports/{report_id}/drawing-assets/{asset_id}/preview")
    def get_report_drawing_asset_preview(
        report_id: str,
        asset_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> Response | FileResponse:
        ctx.validate_report_id(report_id)
        ctx.validate_drawing_asset_id(asset_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)
        drawing_asset, preview_payload = ctx.resolve_report_drawing_asset_preview(
            report_id, asset_id, principal=principal
        )
        media_type = safe_preview_media_type(drawing_asset.media_type)
        if isinstance(preview_payload, bytes):
            download_name = drawing_asset.stored_filename or f"{asset_id}.png"
            return Response(
                content=preview_payload,
                media_type=media_type,
                headers={"Content-Disposition": attachment_content_disposition(download_name)},
            )
        try:
            reject_symlinks(Path(preview_payload), base=settings.storage_dir.resolve())
        except PathJailError as exc:
            raise HTTPException(status_code=404, detail="Drawing preview not found") from exc
        return FileResponse(
            path=preview_payload,
            media_type=media_type,
            headers={
                "Content-Disposition": attachment_content_disposition(
                    drawing_asset.stored_filename or f"{asset_id}.png"
                )
            },
        )

    return router
