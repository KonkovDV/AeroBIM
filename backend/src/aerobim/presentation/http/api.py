# pyright: reportUnusedFunction=false, reportUnknownVariableType=false

import re as _re
from dataclasses import asdict
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from pydantic import BaseModel, Field

from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import DrawingSource, RequirementSource, SourceKind, ValidationRequest

_REPORT_ID_RE = _re.compile(r"^[a-f0-9]{32}$")
_DRAWING_ASSET_ID_RE = _re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class ValidateIfcRequest(BaseModel):
    request_id: str | None = None
    ifc_path: str
    requirement_text: str = Field(default="", max_length=50_000)
    requirement_path: str | None = None
    ids_path: str | None = None
    project_name: str | None = None
    discipline: str | None = None


class DrawingPayload(BaseModel):
    text: str = Field(default="", max_length=50_000)
    path: str | None = None
    sheet_id: str | None = None
    format: str | None = None


class AnalyzeProjectPackageRequest(BaseModel):
    request_id: str | None = None
    ifc_path: str
    requirement_text: str = Field(default="", max_length=50_000)
    requirement_path: str | None = None
    ids_path: str | None = None
    technical_spec_text: str = Field(default="", max_length=50_000)
    technical_spec_path: str | None = None
    calculation_text: str = Field(default="", max_length=50_000)
    calculation_path: str | None = None
    drawings: list[DrawingPayload] = Field(default_factory=list)
    project_name: str | None = None
    discipline: str | None = None


def create_http_app(container: Container):
    try:
        from fastapi import Body, FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install FastAPI and Pydantic to run the HTTP API") from exc

    from aerobim.presentation.http.correlation import add_correlation_middleware

    settings = container.resolve(Tokens.SETTINGS)
    logger = container.resolve(Tokens.LOGGER)
    validate_use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
    analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
    audit_store = container.resolve(Tokens.AUDIT_REPORT_STORE)

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

    def _resolve_safe_path(user_path: str) -> Path:
        """Resolve user-supplied path strictly within storage_dir."""
        base = settings.storage_dir.resolve()
        resolved = (base / user_path).resolve()
        if not resolved.is_relative_to(base):
            raise HTTPException(status_code=400, detail="Path escapes storage boundary")
        return resolved

    def _validate_report_id(report_id: str) -> None:
        if not _REPORT_ID_RE.match(report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")

    def _resolve_report_ifc_path(report_id: str) -> Path:
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        candidate = report.ifc_path
        base = settings.storage_dir.resolve()
        resolved = candidate.resolve() if candidate.is_absolute() else (base / candidate).resolve()
        if not resolved.is_relative_to(base):
            raise HTTPException(
                status_code=409,
                detail="Stored IFC source escapes storage boundary",
            )
        if not resolved.exists():
            raise HTTPException(status_code=404, detail=f"IFC source for report {report_id} not found")
        return resolved

    def _validate_drawing_asset_id(asset_id: str) -> None:
        if not _DRAWING_ASSET_ID_RE.match(asset_id):
            raise HTTPException(status_code=400, detail="Invalid drawing asset ID format")

    def _resolve_report_drawing_asset_preview(report_id: str, asset_id: str):
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        drawing_asset = next((asset for asset in report.drawing_assets if asset.asset_id == asset_id), None)
        if drawing_asset is None or not drawing_asset.stored_filename:
            raise HTTPException(status_code=404, detail=f"Drawing asset {asset_id} not found")

        asset_root = (settings.storage_dir / "drawing-assets" / report_id).resolve()
        resolved = (asset_root / drawing_asset.stored_filename).resolve()
        if not resolved.is_relative_to(asset_root):
            raise HTTPException(status_code=409, detail="Stored drawing asset escapes storage boundary")
        if not resolved.exists():
            raise HTTPException(status_code=404, detail=f"Drawing asset preview for {asset_id} not found")
        return drawing_asset, resolved

    def _build_requirement_source(
        text: str,
        path: str | None,
        source_kind: SourceKind,
    ) -> RequirementSource:
        return RequirementSource(
            text=text,
            path=_resolve_safe_path(path) if path else None,
            source_kind=source_kind,
            source_id=f"{source_kind.value}-input",
        )

    @app.post("/v1/validate/ifc")
    def validate_ifc(payload: Annotated[ValidateIfcRequest, Body()]) -> dict[str, object]:
        request_id = payload.request_id or uuid4().hex
        logger.info("validate_ifc started", request_id=request_id, ifc_path=payload.ifc_path)
        try:
            ifc_resolved = _resolve_safe_path(payload.ifc_path)

            report = validate_use_case.execute(
                ValidationRequest(
                    request_id=request_id,
                    ifc_path=ifc_resolved,
                    requirement_source=_build_requirement_source(
                        payload.requirement_text,
                        payload.requirement_path,
                        SourceKind.STRUCTURED_TEXT,
                    ),
                    ids_path=_resolve_safe_path(payload.ids_path) if payload.ids_path else None,
                    project_name=payload.project_name,
                    discipline=payload.discipline,
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
        return asdict(report)

    @app.post("/v1/analyze/project-package")
    def analyze_project_package(
        payload: Annotated[AnalyzeProjectPackageRequest, Body()],
    ) -> dict[str, object]:
        try:
            ifc_resolved = _resolve_safe_path(payload.ifc_path)
            report = analyze_use_case.execute(
                ValidationRequest(
                    request_id=payload.request_id or uuid4().hex,
                    ifc_path=ifc_resolved,
                    requirement_source=_build_requirement_source(
                        payload.requirement_text,
                        payload.requirement_path,
                        SourceKind.STRUCTURED_TEXT,
                    ),
                    ids_path=_resolve_safe_path(payload.ids_path) if payload.ids_path else None,
                    technical_spec_source=_build_requirement_source(
                        payload.technical_spec_text,
                        payload.technical_spec_path,
                        SourceKind.TECHNICAL_SPECIFICATION,
                    )
                    if payload.technical_spec_text or payload.technical_spec_path
                    else None,
                    calculation_source=_build_requirement_source(
                        payload.calculation_text,
                        payload.calculation_path,
                        SourceKind.CALCULATION,
                    )
                    if payload.calculation_text or payload.calculation_path
                    else None,
                    drawing_sources=tuple(
                        DrawingSource(
                            text=drawing.text,
                            path=_resolve_safe_path(drawing.path) if drawing.path else None,
                            sheet_id=drawing.sheet_id,
                            format=drawing.format,
                        )
                        for drawing in payload.drawings
                    ),
                    project_name=payload.project_name,
                    discipline=payload.discipline,
                )
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        return asdict(report)

    @app.get("/v1/reports")
    def list_reports(
        project: str | None = None,
        discipline: str | None = None,
        passed: bool | None = None,
    ) -> dict[str, object]:
        entries = audit_store.list_reports()
        if project:
            normalized_project = project.strip().lower()
            entries = [
                entry
                for entry in entries
                if normalized_project in (entry.project_name or "").lower()
            ]
        if discipline:
            normalized_discipline = discipline.strip().lower()
            entries = [
                entry
                for entry in entries
                if normalized_discipline in (entry.discipline or "").lower()
            ]
        if passed is not None:
            entries = [entry for entry in entries if entry.passed is passed]
        return {"reports": [asdict(e) for e in entries], "count": len(entries)}

    @app.get("/v1/reports/{report_id}")
    def get_report(report_id: str) -> dict[str, object]:
        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        return asdict(report)

    @app.get("/v1/reports/{report_id}/source/ifc")
    def get_report_ifc_source(report_id: str):  # noqa: ANN201
        from fastapi.responses import FileResponse

        _validate_report_id(report_id)
        source_path = _resolve_report_ifc_path(report_id)
        return FileResponse(
            path=source_path,
            media_type="application/octet-stream",
            filename=f"{report_id}.ifc",
        )

    @app.get("/v1/reports/{report_id}/drawing-assets/{asset_id}/preview")
    def get_report_drawing_asset_preview(report_id: str, asset_id: str):  # noqa: ANN201
        from fastapi.responses import FileResponse

        _validate_report_id(report_id)
        _validate_drawing_asset_id(asset_id)
        drawing_asset, preview_path = _resolve_report_drawing_asset_preview(report_id, asset_id)
        return FileResponse(
            path=preview_path,
            media_type=drawing_asset.media_type,
            filename=drawing_asset.stored_filename,
        )

    @app.get("/v1/reports/{report_id}/export/json")
    def export_report_json(report_id: str):  # noqa: ANN201
        from fastapi.responses import JSONResponse

        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        return JSONResponse(
            content=asdict(report),
            headers={"Content-Disposition": f'attachment; filename="{report_id}.json"'},
        )

    @app.get("/v1/reports/{report_id}/export/html")
    def export_report_html(report_id: str):  # noqa: ANN201
        from fastapi.responses import HTMLResponse

        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        data = asdict(report)
        summary = data["summary"]
        status_class = "pass" if summary["passed"] else "fail"
        status_label = "PASSED" if summary["passed"] else "FAILED"

        issues_rows = ""
        for issue in data.get("issues", ()):
            sev = issue.get("severity", "")
            issues_rows += (
                f"<tr><td>{_esc(issue.get('rule_id', ''))}</td>"
                f"<td class='{_esc(sev)}'>{_esc(sev)}</td>"
                f"<td>{_esc(issue.get('message', ''))}</td>"
                f"<td>{_esc(issue.get('element_guid') or '')}</td></tr>\n"
            )

        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Report {_esc(report_id)}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:2em;color:#222}}
h1{{font-size:1.4em}}
.summary{{margin:1em 0;padding:1em;border-radius:6px}}
.pass{{background:#d4edda;color:#155724}}
.fail{{background:#f8d7da;color:#721c24}}
table{{border-collapse:collapse;width:100%;margin-top:1em}}
th,td{{border:1px solid #ccc;padding:.4em .8em;text-align:left}}
th{{background:#f5f5f5}}
td.error{{color:#c00;font-weight:600}}
td.warning{{color:#b58900}}
</style></head><body>
<h1>Validation Report</h1>
<div class="summary {status_class}">
<strong>{status_label}</strong> &mdash;
{summary["issue_count"]} issue(s),
{summary["error_count"]} error(s),
{summary["warning_count"]} warning(s),
{summary["requirement_count"]} requirement(s)
</div>
<table><thead><tr><th>Rule</th><th>Severity</th><th>Message</th><th>Element GUID</th></tr></thead>
<tbody>{issues_rows}</tbody></table>
<p style="margin-top:2em;font-size:.85em;color:#888">
Report ID: {_esc(report_id)} &middot;
Created: {_esc(data.get("created_at", ""))}
</p>
</body></html>"""
        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": f'attachment; filename="{report_id}.html"'},
        )

    @app.get("/v1/reports/{report_id}/export/bcf")
    def export_report_bcf(report_id: str):  # noqa: ANN201
        from fastapi.responses import Response

        from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        bcf_bytes = export_bcf(report)
        return Response(
            content=bcf_bytes,
            media_type="application/x-bcfzip",
            headers={"Content-Disposition": f'attachment; filename="{report_id}.bcf"'},
        )

    return app


def _esc(value: str) -> str:
    """Minimal HTML escaping for user-controlled values."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
