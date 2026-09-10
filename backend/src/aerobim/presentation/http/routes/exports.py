"""Report export routes: JSON, HTML, BCF ZIP and OpenCDE BCF API push."""

from dataclasses import asdict
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response

from aerobim.core.di.tokens import Tokens
from aerobim.domain.check_coverage import coverage_from_report, derive_report_scope
from aerobim.domain.models import ValidationReport
from aerobim.domain.object_acl import AuthPrincipal
from aerobim.presentation.http.context import (
    BCF_PROJECT_ID_RE,
    ApiContext,
    attachment_content_disposition,
)
from aerobim.presentation.http.errors import (
    public_export_unavailable_detail,
    public_not_found_detail,
)
from aerobim.presentation.http.report_html import render_report_html
from aerobim.presentation.http.report_pdf import render_report_pdf_bytes
from aerobim.presentation.http.schemas import PushBcfApiRequest

_EXPORT_LOCALES = frozenset({"ru", "en"})


def _parse_export_locale(locale: str | None) -> str:
    value = (locale or "ru").strip().lower()
    if value not in _EXPORT_LOCALES:
        raise HTTPException(status_code=400, detail="locale must be ru or en")
    return value


def _overlay_export_locale(
    report: ValidationReport, data: dict[str, Any], locale: str
) -> dict[str, Any]:
    data["export_locale"] = locale
    if locale != "en":
        return data
    from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator

    generator = TemplateRemarkGenerator(locale="en")
    by_id = {issue.finding_id: issue for issue in report.issues if issue.finding_id}
    for item in data.get("issues") or []:
        if not isinstance(item, dict):
            continue
        finding_id = item.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id:
            continue
        source = by_id.get(finding_id)
        if source is None:
            item["remark_locale"] = "machine_fallback"
            continue
        try:
            english = generator.generate(source)
        except ValueError:
            item["remark_locale"] = "machine_fallback"
            continue
        remark = dict(item.get("remark") or {})
        remark["essence"] = english.essence
        remark["title"] = english.title
        remark["clause_cite"] = english.clause_cite
        remark["location_line"] = english.location_line
        remark["detail"] = english.detail
        item["remark"] = remark
        item["remark_locale"] = "en"
    return data


def build_exports_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()

    @router.get("/v1/reports/{report_id}/export/json")
    def export_report_json(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
        locale: str = Query("ru"),
    ) -> JSONResponse:
        ctx.validate_report_id(report_id)
        report = ctx.load_authorized_report(report_id, principal)
        chosen = _parse_export_locale(locale)
        payload = _overlay_export_locale(
            report, ctx.serialize_public_report(report, include_review=True), chosen
        )
        return JSONResponse(
            content=payload,
            headers={"Content-Disposition": attachment_content_disposition(f"{report_id}.json")},
        )

    @router.get("/v1/reports/{report_id}/export/html")
    def export_report_html(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
        locale: str = Query("ru"),
        against: str | None = Query(None),
    ) -> HTMLResponse:
        ctx.validate_report_id(report_id)
        report = ctx.load_authorized_report(report_id, principal)
        chosen = _parse_export_locale(locale)
        data: dict[str, Any] = ctx.serialize_public_report(report, include_review=True)
        scope = derive_report_scope(report)
        data["coverage"] = coverage_from_report(report, scope=scope).to_dict(report=report)
        data = _overlay_export_locale(report, data, chosen)
        if against:
            ctx.validate_report_id(against)
            if against == report_id:
                raise HTTPException(status_code=400, detail="against must be a different report_id")
            other = ctx.load_authorized_report(against, principal)
            from aerobim.domain.revision_diff import compare_report_revisions

            data["revision_diff"] = compare_report_revisions(report, other).to_dict()
        html = render_report_html(report_id, data, locale=chosen)
        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": attachment_content_disposition(f"{report_id}.html")},
        )

    @router.get("/v1/reports/{report_id}/export/pdf")
    def export_report_pdf(
        report_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
        locale: str = Query("ru"),
    ) -> Response:
        ctx.validate_report_id(report_id)
        report = ctx.load_authorized_report(report_id, principal)
        chosen = _parse_export_locale(locale)
        data: dict[str, Any] = ctx.serialize_public_report(report, include_review=True)
        scope = derive_report_scope(report)
        data["coverage"] = coverage_from_report(report, scope=scope).to_dict(report=report)
        data = _overlay_export_locale(report, data, chosen)
        pdf_bytes = render_report_pdf_bytes(report_id, data, locale=chosen)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": attachment_content_disposition(f"{report_id}.pdf")},
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
        report = ctx.load_authorized_report(report_id, principal)
        review_events = ()
        if ctx.container.is_registered(Tokens.REVIEW_EVENT_STORE):
            review_events = tuple(
                ctx.container.resolve(Tokens.REVIEW_EVENT_STORE).list_for_report(report_id)
            )
        normalized = (version or "").strip()
        if normalized in {"3", "3.0"}:
            from aerobim.infrastructure.adapters.bcf3_exporter import export_bcf3

            bcf_bytes = export_bcf3(report, review_events=review_events)
        elif normalized in {"2.1", "2"}:
            from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

            bcf_bytes = export_bcf(report, review_events=review_events)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported BCF version (use 2.1 or 3.0)",
            )

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
        ctx.load_authorized_report(report_id, principal)
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
            raise HTTPException(status_code=404, detail=public_not_found_detail())
        if not ctx.container.is_registered(Tokens.PUSH_REPORT_TO_BCF_API_USE_CASE):
            raise HTTPException(status_code=503, detail="BCF API push use case is not registered")

        push_use_case = ctx.container.resolve(Tokens.PUSH_REPORT_TO_BCF_API_USE_CASE)
        try:
            result = push_use_case.execute(report_id, project_id=project_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=public_not_found_detail()) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=public_export_unavailable_detail()) from exc

        return {
            "project_id": result.project_id,
            "attempted": result.attempted,
            "succeeded": result.succeeded,
            "failed": result.failed,
            "topics": [asdict(topic) for topic in result.topics],
        }

    return router
