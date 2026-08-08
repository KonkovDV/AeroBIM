"""Validation and project-package analysis routes (sync + async job flow)."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Header, HTTPException

from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import SourceKind, ValidationRequest
from aerobim.domain.object_acl import AuthPrincipal
from aerobim.domain.stage_timeout import StageTimeoutExceeded
from aerobim.infrastructure.adapters.openrebar_evidence_verifier import (
    build_openrebar_provenance_digest,
)
from aerobim.presentation.http.context import ApiContext
from aerobim.presentation.http.errors import (
    public_bad_request_detail,
    public_service_unavailable_detail,
    public_sync_analyze_disabled_detail,
)
from aerobim.presentation.http.package_request_builders import (
    load_openrebar_report_payload,
)
from aerobim.presentation.http.schemas import (
    AnalyzeProjectPackageRequest,
    OpenRebarDigestRequest,
    ValidateIfcRequest,
)


def build_analyze_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()
    logger = ctx.logger

    @router.post("/v1/validate/ifc")
    def validate_ifc(
        payload: Annotated[ValidateIfcRequest, Body()],
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        request_id = payload.request_id or uuid4().hex
        logger.info("validate_ifc started", request_id=request_id, ifc_path=payload.ifc_path)
        try:
            ifc_resolved = ctx.resolve_safe_path(payload.ifc_path, principal=principal)
            ctx.enforce_ifc_size(ifc_resolved)

            report = ctx.validate_use_case.execute(
                ValidationRequest(
                    request_id=request_id,
                    ifc_path=ifc_resolved,
                    requirement_source=ctx.build_requirement_source(
                        payload.requirement_text,
                        payload.requirement_path,
                        SourceKind.STRUCTURED_TEXT,
                        principal=principal,
                    ),
                    ids_path=(
                        ctx.resolve_safe_path(payload.ids_path, principal=principal)
                        if payload.ids_path
                        else None
                    ),
                    project_name=payload.project_name,
                    discipline=payload.discipline,
                    stage=payload.stage,
                    information_container_id=payload.information_container_id,
                    revision=payload.revision,
                    doc_status=payload.doc_status,
                    tenant_id=ctx.resolve_bound_tenant(principal),
                )
            )
        except FileNotFoundError as exc:
            logger.warning("validate_ifc file not found", request_id=request_id, detail=str(exc))
            raise HTTPException(status_code=404, detail="file not found") from exc
        except ValueError as exc:
            logger.warning("validate_ifc bad request", request_id=request_id, detail=str(exc))
            raise HTTPException(status_code=400, detail=public_bad_request_detail()) from exc
        except RuntimeError as exc:
            logger.error("validate_ifc runtime error", request_id=request_id, detail=str(exc))
            raise HTTPException(
                status_code=503, detail=public_service_unavailable_detail()
            ) from exc

        logger.info(
            "validate_ifc completed",
            request_id=request_id,
            report_id=report.report_id,
            passed=report.summary.passed,
            issues=report.summary.issue_count,
        )
        return ctx.serialize_public_report(report)

    @router.post("/v1/analyze/project-package")
    def analyze_project_package(
        payload: Annotated[AnalyzeProjectPackageRequest, Body()],
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        if ctx.settings.disable_sync_package_analyze:
            raise HTTPException(
                status_code=409,
                detail=public_sync_analyze_disabled_detail(),
            )
        try:
            request = ctx.build_project_package_request(
                payload,
                tenant_id=ctx.resolve_bound_tenant(
                    principal,
                    payload_tenant_id=payload.tenant_id,
                ),
                principal=principal,
            )
            report = ctx.analyze_use_case.execute(request)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="file not found") from exc
        except ValueError as exc:
            logger.warning("analyze_project_package bad request", detail=str(exc))
            raise HTTPException(status_code=400, detail=public_bad_request_detail()) from exc
        except StageTimeoutExceeded as exc:
            logger.error("analyze_project_package stage timeout", detail=str(exc))
            raise HTTPException(
                status_code=504,
                detail=public_service_unavailable_detail(),
            ) from exc
        except RuntimeError as exc:
            logger.error("analyze_project_package runtime error", detail=str(exc))
            raise HTTPException(
                status_code=503, detail=public_service_unavailable_detail()
            ) from exc

        return ctx.serialize_public_report(report)

    @router.post("/v1/analyze/project-package/reinforcement-digest")
    def analyze_project_package_reinforcement_digest(
        payload: Annotated[OpenRebarDigestRequest, Body()],
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        try:
            report_path = ctx.resolve_safe_path(
                payload.reinforcement_report_path, principal=principal
            )
            report_payload = load_openrebar_report_payload(report_path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="file not found") from exc
        except ValueError as exc:
            logger.warning("reinforcement_digest bad request", detail=str(exc))
            raise HTTPException(status_code=400, detail=public_bad_request_detail()) from exc
        metadata_payload = report_payload.get("metadata")
        metadata = metadata_payload if isinstance(metadata_payload, dict) else {}
        # Storage-relative path only — never absolute host paths in API responses.
        storage_rel = payload.reinforcement_report_path.replace("\\", "/")
        return {
            "reinforcement_report_path": storage_rel,
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

    @router.post("/v1/analyze/project-package/submit", status_code=202)
    def submit_analyze_project_package(
        payload: Annotated[AnalyzeProjectPackageRequest, Body()],
        background_tasks: BackgroundTasks,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, object]:
        try:
            request = ctx.build_project_package_request(
                payload,
                tenant_id=ctx.resolve_bound_tenant(
                    principal,
                    payload_tenant_id=payload.tenant_id,
                ),
                principal=principal,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="file not found") from exc
        except ValueError as exc:
            logger.warning("submit_analyze_project_package bad request", detail=str(exc))
            raise HTTPException(status_code=400, detail=public_bad_request_detail()) from exc
        if idempotency_key is not None and len(idempotency_key) > 128:
            raise HTTPException(status_code=400, detail="Idempotency-Key must be ≤128 characters")

        from aerobim.application.use_cases.analyze_project_package_jobs import (
            JobConcurrencyLimitError,
        )

        submit_job_use_case = ctx.container.resolve(
            Tokens.SUBMIT_ANALYZE_PROJECT_PACKAGE_JOB_USE_CASE
        )
        job_runner = ctx.container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_RUNNER)
        try:
            job = submit_job_use_case.execute(
                request,
                idempotency_key=idempotency_key,
                max_concurrent_per_tenant=ctx.settings.max_concurrent_analyze_jobs_per_tenant,
            )
        except JobConcurrencyLimitError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        if job.status.value == "queued":
            background_tasks.add_task(job_runner.run, job.job_id, request)
        return ctx.serialize_analyze_project_package_job(job)

    @router.get("/v1/analyze/project-package/jobs/{job_id}")
    def get_analyze_project_package_job(
        job_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        ctx.validate_job_id(job_id)
        get_job_status_use_case = ctx.container.resolve(
            Tokens.GET_ANALYZE_PROJECT_PACKAGE_JOB_STATUS_USE_CASE
        )
        job = get_job_status_use_case.execute(job_id)
        if job is None:
            raise HTTPException(
                status_code=404, detail=f"Analyze project-package job {job_id} not found"
            )
        ctx.assert_job_access(job, principal)
        return ctx.serialize_analyze_project_package_job(job)

    @router.post("/v1/analyze/project-package/jobs/{job_id}/cancel")
    def cancel_analyze_project_package_job(
        job_id: str,
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        ctx.validate_job_id(job_id)
        get_job_status_use_case = ctx.container.resolve(
            Tokens.GET_ANALYZE_PROJECT_PACKAGE_JOB_STATUS_USE_CASE
        )
        existing = get_job_status_use_case.execute(job_id)
        if existing is None:
            raise HTTPException(
                status_code=404, detail=f"Analyze project-package job {job_id} not found"
            )
        ctx.assert_job_access(existing, principal)
        job_store = ctx.container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
        job = job_store.request_cancel(job_id)
        if job is None:
            raise HTTPException(
                status_code=404, detail=f"Analyze project-package job {job_id} not found"
            )
        return ctx.serialize_analyze_project_package_job(job)

    return router
