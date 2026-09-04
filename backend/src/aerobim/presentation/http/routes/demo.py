"""Development-only demo fixture seed so the review shell can be shown live.

Production returns 404. Uses git samples, not customer packs. Checkpoint GO
(regulatory_measurement_mvp; customer_go false).
"""

import shutil
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.ifc_size_policy import IfcAnalyzeCapError, IfcDiskBackendError
from aerobim.domain.models import SourceKind, ValidationRequest
from aerobim.domain.object_acl import AuthPrincipal
from aerobim.domain.stage_timeout import StageTimeoutExceeded
from aerobim.presentation.http.context import ApiContext
from aerobim.presentation.http.errors import (
    public_bad_request_detail,
    public_ifc_analyze_cap_body,
    public_ifc_disk_backend_detail,
    public_not_found_detail,
    public_service_unavailable_detail,
)
from aerobim.tools.seed_smoke_report import repo_root


def _copy_under_storage(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest.resolve()


def build_demo_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter(include_in_schema=False)
    logger = ctx.logger

    def _require_dev() -> None:
        if not ctx.settings.is_dev_environment:
            raise HTTPException(status_code=404, detail=public_not_found_detail())

    @router.post("/v1/demo/seed-fixture")
    def seed_demo_fixture(
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        """Analyze the git walls+IDS fixture into the audit store.

        Not customer data. Not product accuracy. Expected ``summary.passed=false``.
        """
        _require_dev()
        root = repo_root()
        ifc_src = root / "samples" / "ifc" / "walls-multi-entity.ifc"
        ids_src = root / "samples" / "ids" / "walls-multi-entity.ids"
        if not ifc_src.is_file() or not ids_src.is_file():
            raise HTTPException(status_code=404, detail=public_not_found_detail())

        storage = ctx.settings.storage_dir.resolve()
        dest_ifc = _copy_under_storage(ifc_src, storage / "demo-fixture" / "walls-multi-entity.ifc")
        dest_ids = _copy_under_storage(ids_src, storage / "demo-fixture" / "walls-multi-entity.ids")
        ctx.enforce_ifc_size(dest_ifc)

        request_id = uuid4().hex
        try:
            report = ctx.validate_use_case.execute(
                ValidationRequest(
                    request_id=request_id,
                    ifc_path=dest_ifc,
                    requirement_source=ctx.build_requirement_source(
                        "",
                        None,
                        SourceKind.STRUCTURED_TEXT,
                        principal=principal,
                    ),
                    ids_path=dest_ids,
                    project_name="Учебный комплект (фикстура)",
                    discipline="KR",
                    origin="demo_fixture",
                    tenant_id=ctx.resolve_bound_tenant(principal),
                )
            )
        except FileNotFoundError as exc:
            logger.warning("demo seed file not found", request_id=request_id)
            raise HTTPException(status_code=404, detail="file not found") from exc
        except IfcAnalyzeCapError as exc:
            raise HTTPException(status_code=413, detail=public_ifc_analyze_cap_body()) from exc
        except IfcDiskBackendError as exc:
            raise HTTPException(status_code=503, detail=public_ifc_disk_backend_detail()) from exc
        except ValueError as exc:
            logger.warning("demo seed bad request", request_id=request_id, detail=str(exc))
            raise HTTPException(status_code=400, detail=public_bad_request_detail()) from exc
        except StageTimeoutExceeded as exc:
            logger.error("demo seed stage timeout", request_id=request_id)
            raise HTTPException(
                status_code=504, detail=public_service_unavailable_detail()
            ) from exc
        except RuntimeError as exc:
            logger.error("demo seed runtime", request_id=request_id, detail=str(exc))
            raise HTTPException(
                status_code=503, detail=public_service_unavailable_detail()
            ) from exc

        return {
            "fixture": True,
            "checkpoint": CHECKPOINT,
            "closes_rt001": False,
            "closes_rt002": False,
            "closes_rt003": False,
            "note": ("Git fixture. Not customer accuracy. summary.passed false is expected."),
            "report_id": report.report_id,
            "issue_count": report.summary.issue_count,
        }

    return router
