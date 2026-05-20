# pyright: reportUnusedFunction=false, reportUnknownVariableType=false

import hashlib
import json
import re as _re
import secrets
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from aerobim.application.services.loin_metadata_resolver import LoinMetadataResolver
from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import DrawingSource, RequirementSource, SourceKind, ValidationRequest
from aerobim.infrastructure.adapters.openrebar_evidence_verifier import (
    build_openrebar_provenance_digest,
)

_REPORT_ID_RE = _re.compile(r"^[a-f0-9]{32}$")
_DRAWING_ASSET_ID_RE = _re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_LOIN_RESOLVER = LoinMetadataResolver()


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


class OpenRebarDigestRequest(BaseModel):
    reinforcement_report_path: str = Field(max_length=2048)


def create_http_app(container: Container):
    try:
        from fastapi import BackgroundTasks, Body, Depends, FastAPI, Header, HTTPException, Response
        from fastapi.middleware.cors import CORSMiddleware
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install FastAPI and Pydantic to run the HTTP API") from exc

    from aerobim.presentation.http.correlation import add_correlation_middleware

    settings = container.resolve(Tokens.SETTINGS)
    logger = container.resolve(Tokens.LOGGER)
    validate_use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
    analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
    audit_store = container.resolve(Tokens.AUDIT_REPORT_STORE)
    object_store = None
    if container.is_registered(Tokens.OBJECT_STORE):
        object_store = container.resolve(Tokens.OBJECT_STORE)

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

    def _require_bearer_auth(authorization: Annotated[str | None, Header()] = None) -> None:
        configured_token = settings.api_bearer_token
        if configured_token is None:
            return

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

        if not secrets.compare_digest(token, configured_token):
            raise HTTPException(
                status_code=401,
                detail="Invalid API token",
                headers={"WWW-Authenticate": "Bearer"},
            )

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
    ) -> RequirementSource:
        return RequirementSource(
            text=text,
            path=_resolve_safe_path(path) if path else None,
            source_kind=source_kind,
            source_id=f"{source_kind.value}-input",
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
    ) -> tuple[Path | None, str | None]:
        if payload.reinforcement_handoff_path:
            if payload.reinforcement_report_path or payload.reinforcement_source_digest:
                raise ValueError(
                    "reinforcement_handoff_path cannot be combined with "
                    "reinforcement_report_path or reinforcement_source_digest"
                )

            handoff_path = _resolve_safe_path(payload.reinforcement_handoff_path)
            handoff_payload = _load_openrebar_handoff_payload(handoff_path)
            raw_report_path = handoff_payload.get("reinforcement_report_path")
            if not isinstance(raw_report_path, str) or not raw_report_path.strip():
                raise ValueError("OpenRebar handoff manifest must define reinforcement_report_path")

            report_path = _resolve_safe_path(raw_report_path.strip())
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
            _resolve_safe_path(payload.reinforcement_report_path)
            if payload.reinforcement_report_path
            else None
        )
        reinforcement_source_digest = (
            payload.reinforcement_source_digest.strip().lower()
            if payload.reinforcement_source_digest
            else None
        )
        return reinforcement_report_path, reinforcement_source_digest

    def _build_project_package_request(payload: AnalyzeProjectPackageRequest) -> ValidationRequest:
        reinforcement_report_path, reinforcement_source_digest = (
            _resolve_openrebar_provenance_inputs(payload)
        )
        return ValidationRequest(
            request_id=payload.request_id or uuid4().hex,
            ifc_path=_resolve_safe_path(payload.ifc_path),
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
        )

    def _serialize_analyze_project_package_job(job) -> dict[str, object]:
        payload = asdict(job)
        payload["status"] = job.status.value
        payload["status_url"] = f"/v1/analyze/project-package/jobs/{job.job_id}"
        payload["report_url"] = f"/v1/reports/{job.report_id}" if job.report_id else None
        return payload

    @app.post("/v1/validate/ifc")
    def validate_ifc(
        payload: Annotated[ValidateIfcRequest, Body()],
        _auth: Annotated[None, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
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
                    stage=payload.stage,
                    information_container_id=payload.information_container_id,
                    revision=payload.revision,
                    doc_status=payload.doc_status,
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
        _auth: Annotated[None, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        try:
            request = _build_project_package_request(payload)
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
        _auth: Annotated[None, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        try:
            report_path = _resolve_safe_path(payload.reinforcement_report_path)
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
        }

    @app.post("/v1/analyze/project-package/submit", status_code=202)
    def submit_analyze_project_package(
        payload: Annotated[AnalyzeProjectPackageRequest, Body()],
        background_tasks: BackgroundTasks,
        _auth: Annotated[None, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        try:
            request = _build_project_package_request(payload)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        submit_job_use_case = container.resolve(Tokens.SUBMIT_ANALYZE_PROJECT_PACKAGE_JOB_USE_CASE)
        job_runner = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_RUNNER)
        job = submit_job_use_case.execute(request)
        background_tasks.add_task(job_runner.run, job.job_id, request)
        return _serialize_analyze_project_package_job(job)

    @app.get("/v1/analyze/project-package/jobs/{job_id}")
    def get_analyze_project_package_job(
        job_id: str,
        _auth: Annotated[None, Depends(_require_bearer_auth)],
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
        return _serialize_analyze_project_package_job(job)

    @app.get("/v1/reports")
    def list_reports(
        project: str | None = None,
        discipline: str | None = None,
        passed: bool | None = None,
        _auth: Annotated[None, Depends(_require_bearer_auth)] = None,
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
    def get_report(
        report_id: str,
        _auth: Annotated[None, Depends(_require_bearer_auth)],
    ) -> dict[str, object]:
        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        return _serialize_public_report(report)

    @app.get("/v1/reports/{report_id}/source/ifc")
    def get_report_ifc_source(
        report_id: str,
        _auth: Annotated[None, Depends(_require_bearer_auth)],
    ):  # noqa: ANN201
        from fastapi.responses import FileResponse

        _validate_report_id(report_id)
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
        _auth: Annotated[None, Depends(_require_bearer_auth)],
    ):  # noqa: ANN201
        from fastapi.responses import FileResponse

        _validate_report_id(report_id)
        _validate_drawing_asset_id(asset_id)
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
        _auth: Annotated[None, Depends(_require_bearer_auth)],
    ):  # noqa: ANN201
        from fastapi.responses import JSONResponse

        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        return JSONResponse(
            content=_serialize_public_report(report),
            headers={"Content-Disposition": f'attachment; filename="{report_id}.json"'},
        )

    @app.get("/v1/reports/{report_id}/export/html")
    def export_report_html(
        report_id: str,
        _auth: Annotated[None, Depends(_require_bearer_auth)],
    ):  # noqa: ANN201
        from fastapi.responses import HTMLResponse

        _validate_report_id(report_id)
        report = audit_store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
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
                ):
                    value = issue.get(key)
                    if value:
                        loin_bits.append(f"{label}={_esc(str(value))}")
                loin_html = (
                    f"<br><small class='loin'>{' · '.join(loin_bits)}</small>" if loin_bits else ""
                )
                rows += (
                    f"<tr><td class='sev {_esc(sev)}'>{_esc(sev)}</td>"
                    f"<td class='{pri_class}'>{pri}</td>"
                    f"<td>{conf_display}</td>"
                    f"<td>{_esc(issue.get('rule_id', ''))}{loin_html}</td>"
                    f"<td>{_esc(issue.get('message', ''))}</td>"
                    f"{ev_exp}{ev_obs}"
                    f"<td>{_esc(issue.get('element_guid') or '')}</td>"
                    f"<td>{_esc(issue.get('target_ref') or '')}</td></tr>\n"
                    f"<tr class='detail'><td colspan='9'>{pz_html}</td></tr>\n"
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
            headers={"Content-Disposition": f'attachment; filename="{report_id}.html"'},
        )

    @app.get("/v1/reports/{report_id}/export/bcf")
    def export_report_bcf(
        report_id: str,
        _auth: Annotated[None, Depends(_require_bearer_auth)],
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

        if version in {"3", "3.0"}:
            from aerobim.infrastructure.adapters.bcf3_exporter import export_bcf3

            bcf_bytes = export_bcf3(report)
        else:
            from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

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
