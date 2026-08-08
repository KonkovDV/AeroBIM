"""Report export routes: JSON, HTML, BCF ZIP and OpenCDE BCF API push."""

from dataclasses import asdict
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response

from aerobim.core.di.tokens import Tokens
from aerobim.domain.object_acl import AuthPrincipal
from aerobim.presentation.http.context import (
    BCF_PROJECT_ID_RE,
    ApiContext,
    attachment_content_disposition,
)
from aerobim.presentation.http.report_html import render_report_html
from aerobim.presentation.http.schemas import PushBcfApiRequest


def build_exports_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()
    audit_store = ctx.audit_store

    @router.get("/v1/reports/{report_id}/export/json")
    def export_report_json(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> JSONResponse:
        ctx.validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)
        return JSONResponse(
            content=ctx.serialize_public_report(report),
            headers={"Content-Disposition": attachment_content_disposition(f"{report_id}.json")},
        )

    @router.get("/v1/reports/{report_id}/export/html")
    def export_report_html(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> HTMLResponse:
        ctx.validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)
        data: dict[str, Any] = ctx.serialize_public_report(report)
        html = render_report_html(report_id, data)
        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": attachment_content_disposition(f"{report_id}.html")},
        )

    @router.get("/v1/reports/{report_id}/export/bcf", response_model=None)
    def export_report_bcf(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
        version: str = "2.1",
    ) -> Response:
        """Export report as BCF ZIP.

        Query parameter ``version`` selects the BCF schema version:
        - ``2.1`` (default) — stable BCF 2.1 export.
        - ``3`` or ``3.0`` — experimental BCF 3.0 export (buildingSMART BCF 3.0).
        """
        ctx.validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)

        if version in {"3", "3.0"}:
            from aerobim.infrastructure.adapters.bcf3_exporter import export_bcf3

            bcf_bytes = export_bcf3(report)
        else:
            from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

            bcf_bytes = export_bcf(report)

        return Response(
            content=bcf_bytes,
            media_type="application/x-bcfzip",
            headers={"Content-Disposition": attachment_content_disposition(f"{report_id}.bcf")},
        )

    @router.post("/v1/reports/{report_id}/export/bcf-api/push")
    def push_report_bcf_api(
        report_id: str,
        payload: Annotated[PushBcfApiRequest, Body()],
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        """Push report topics to a remote OpenCDE BCF API 3.0 hub."""
        ctx.validate_report_id(report_id)
        project_id = (payload.project_id or ctx.settings.bcf_api_project_id or "").strip()
        if not project_id:
            raise HTTPException(
                status_code=400,
                detail="project_id is required (body or AEROBIM_BCF_API_PROJECT_ID)",
            )
        if not BCF_PROJECT_ID_RE.match(project_id):
            raise HTTPException(
                status_code=400,
                detail="project_id must be a UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)",
            )
        configured_project = (ctx.settings.bcf_api_project_id or "").strip()
        if configured_project and project_id.lower() != configured_project.lower():
            raise HTTPException(
                status_code=403,
                detail="project_id does not match AEROBIM_BCF_API_PROJECT_ID",
            )
        if not ctx.container.is_registered(Tokens.PUSH_REPORT_TO_BCF_API_USE_CASE):
            raise HTTPException(status_code=503, detail="BCF API push use case is not registered")

        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        ctx.assert_report_access(report, principal)

        push_use_case = ctx.container.resolve(Tokens.PUSH_REPORT_TO_BCF_API_USE_CASE)
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

    return router
