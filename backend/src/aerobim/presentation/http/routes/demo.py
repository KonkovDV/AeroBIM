"""Development-only demo fixture seed so the review shell can be shown live.

Production returns 404. Uses the git vertical-slice pack (IFC + IDS + ТЗ +
drawing), not customer packs. Checkpoint GO (regulatory_measurement_mvp;
customer_go false).
"""

import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from aerobim.core.security.path_jail import PathJailError, resolve_repo_relative_path
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.ifc_size_policy import IfcAnalyzeCapError, IfcDiskBackendError
from aerobim.domain.models import DrawingSource, RequirementSource, SourceKind, ValidationRequest
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

_DEMO_MANIFEST = Path("samples") / "demo" / "vertical-slice-2026-08-11" / "manifest.json"


def _resolved_sample(root: Path, user_path: str) -> Path:
    """Resolve a demo-manifest path strictly under ``{repo}/samples/``."""

    samples_base = (root / "samples").resolve()
    try:
        resolved = resolve_repo_relative_path(str(user_path), repo_root=root)
    except PathJailError as exc:
        raise ValueError("demo fixture path escapes samples jail") from exc
    if not resolved.is_relative_to(samples_base):
        raise ValueError("demo fixture path escapes samples jail")
    if not resolved.is_file():
        raise FileNotFoundError("demo fixture file not found")
    return resolved


def _copy_under_storage(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest.resolve()


def _copy_named(src: Path, dest_dir: Path) -> Path:
    if not src.is_file():
        raise FileNotFoundError(str(src))
    return _copy_under_storage(src, dest_dir / src.name)


def _requirement_from_copy(
    src: Path,
    dest_dir: Path,
    *,
    kind: SourceKind,
    source_id: str,
) -> RequirementSource:
    dest = _copy_named(src, dest_dir)
    return RequirementSource(
        text=dest.read_text(encoding="utf-8"),
        path=dest,
        source_kind=kind,
        source_id=source_id,
    )


def materialize_demo_pack(storage: Path, root: Path) -> ValidationRequest:
    """Copy the vertical-slice files under storage and build an analyze request."""

    manifest_path = _resolved_sample(root, _DEMO_MANIFEST.as_posix())
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("demo manifest must be a JSON object")
    raw_request = payload.get("request")
    if not isinstance(raw_request, dict):
        raise ValueError("demo manifest request must be a JSON object")

    dest_dir = storage / "demo-fixture"
    ifc_src = _resolved_sample(root, str(raw_request["ifc_path"]))
    ids_src = _resolved_sample(root, str(raw_request["ids_path"]))
    dest_ifc = _copy_named(ifc_src, dest_dir)
    dest_ids = _copy_named(ids_src, dest_dir)

    requirement = _requirement_from_copy(
        _resolved_sample(root, str(raw_request["requirement_path"])),
        dest_dir,
        kind=SourceKind.STRUCTURED_TEXT,
        source_id="demo-requirements",
    )
    technical_spec = _requirement_from_copy(
        _resolved_sample(root, str(raw_request["technical_spec_path"])),
        dest_dir,
        kind=SourceKind.TECHNICAL_SPECIFICATION,
        source_id="demo-technical-specification",
    )
    calculation = _requirement_from_copy(
        _resolved_sample(root, str(raw_request["calculation_path"])),
        dest_dir,
        kind=SourceKind.CALCULATION,
        source_id="demo-calculation",
    )

    drawings: list[DrawingSource] = []
    raw_drawings = raw_request.get("drawings") or []
    if not isinstance(raw_drawings, list):
        raise ValueError("demo manifest drawings must be a list")
    for item in raw_drawings:
        if not isinstance(item, dict):
            raise ValueError("demo drawing entry must be an object")
        dest = _copy_named(_resolved_sample(root, str(item["path"])), dest_dir)
        drawing_format = str(item.get("format") or dest.suffix.lstrip(".") or "pdf")
        drawings.append(
            DrawingSource(
                text="",
                path=dest,
                sheet_id=str(item["sheet_id"]) if item.get("sheet_id") else None,
                format=drawing_format,
            )
        )

    return ValidationRequest(
        request_id=uuid4().hex,
        ifc_path=dest_ifc,
        requirement_source=requirement,
        technical_spec_source=technical_spec,
        calculation_source=calculation,
        drawing_sources=tuple(drawings),
        ids_path=dest_ids,
        project_name="Учебный комплект (фикстура)",
        discipline=str(payload.get("discipline") or "architecture"),
        stage=str(payload.get("stage") or "demo"),
        origin="demo_fixture",
    )


def _first_fire_finding_id(issues: object) -> str | None:
    if not isinstance(issues, list | tuple):
        return None
    for issue in issues:
        if getattr(issue, "rule_id", None) == "REQ-FIRE-001":
            finding_id = getattr(issue, "finding_id", None)
            if finding_id:
                return str(finding_id)
    return None


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
        """Analyze the git vertical-slice pack into the audit store.

        Not customer data. Not product accuracy. Expected ``summary.passed=false``.
        """
        _require_dev()
        try:
            request = materialize_demo_pack(ctx.settings.storage_dir.resolve(), repo_root())
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=public_not_found_detail()) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=public_bad_request_detail()) from exc

        if request.ifc_path is not None:
            ctx.enforce_ifc_size(request.ifc_path)
        request = replace(request, tenant_id=ctx.resolve_bound_tenant(principal))
        request_id = request.request_id
        try:
            report = ctx.analyze_use_case.execute(request)
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

        first_asset = report.drawing_assets[0].asset_id if report.drawing_assets else None
        return {
            "fixture": True,
            "checkpoint": CHECKPOINT,
            "closes_rt001": False,
            "closes_rt002": False,
            "closes_rt003": False,
            "note": (
                "Git vertical-slice fixture. Not customer accuracy. "
                "summary.passed false is expected."
            ),
            "report_id": report.report_id,
            "issue_count": report.summary.issue_count,
            "drawing_asset_id": first_asset,
            "finding_id": _first_fire_finding_id(report.issues),
        }

    return router
