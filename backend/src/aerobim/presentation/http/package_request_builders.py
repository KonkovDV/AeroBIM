"""Builders that turn HTTP payloads into domain ValidationRequest objects.

Extracted from api.py. Path resolution and size limits stay injected as
callables so route-level security policy (path jail + tenant ACL) is applied
by the caller, not re-implemented here.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from aerobim.core.security.path_jail import open_storage_file
from aerobim.domain.models import (
    DrawingSource,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.domain.object_acl import AuthPrincipal
from aerobim.infrastructure.adapters.openrebar_evidence_verifier import (
    build_openrebar_provenance_digest,
)
from aerobim.presentation.http.schemas import AnalyzeProjectPackageRequest

ResolvePath = Callable[..., Path]


def build_requirement_source(
    text: str,
    path: str | None,
    source_kind: SourceKind,
    *,
    resolve_path: ResolvePath,
    revision: str | None = None,
    stage: str | None = None,
    doc_status: str | None = None,
    source_id: str | None = None,
    principal: AuthPrincipal | None = None,
) -> RequirementSource:
    return RequirementSource(
        text=text,
        path=resolve_path(path, principal=principal) if path else None,
        source_kind=source_kind,
        source_id=source_id or f"{source_kind.value}-input",
        revision=revision,
        stage=stage,
        doc_type=source_kind.value,
        doc_status=doc_status,
    )


def load_openrebar_report_payload(report_path: Path) -> dict[str, object]:
    if not report_path.exists():
        raise FileNotFoundError(report_path)
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid OpenRebar reinforcement report JSON: {report_path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("OpenRebar reinforcement report must be a JSON object")
    return payload


def load_openrebar_handoff_payload(handoff_path: Path) -> dict[str, object]:
    if not handoff_path.exists():
        raise FileNotFoundError(handoff_path)
    try:
        payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid OpenRebar handoff JSON: {handoff_path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("OpenRebar handoff manifest must be a JSON object")
    return payload


def compute_file_sha256(file_path: Path, *, storage_dir: Path) -> str:
    hasher = hashlib.sha256()
    with open_storage_file(file_path, base=storage_dir, mode="rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_openrebar_provenance_inputs(
    payload: AnalyzeProjectPackageRequest,
    *,
    resolve_path: ResolvePath,
    storage_dir: Path,
    principal: AuthPrincipal | None = None,
) -> tuple[Path | None, str | None]:
    if payload.reinforcement_handoff_path:
        if payload.reinforcement_report_path or payload.reinforcement_source_digest:
            raise ValueError(
                "reinforcement_handoff_path cannot be combined with "
                "reinforcement_report_path or reinforcement_source_digest"
            )

        handoff_path = resolve_path(payload.reinforcement_handoff_path, principal=principal)
        handoff_payload = load_openrebar_handoff_payload(handoff_path)
        raw_report_path = handoff_payload.get("reinforcement_report_path")
        if not isinstance(raw_report_path, str) or not raw_report_path.strip():
            raise ValueError("OpenRebar handoff manifest must define reinforcement_report_path")

        report_path = resolve_path(raw_report_path.strip(), principal=principal)
        manifest_sha = handoff_payload.get("report_sha256")
        if manifest_sha is not None:
            if not isinstance(manifest_sha, str) or not manifest_sha.strip():
                raise ValueError(
                    "OpenRebar handoff manifest report_sha256 must be a non-empty string"
                )
            observed_sha = compute_file_sha256(report_path, storage_dir=storage_dir)
            if observed_sha != manifest_sha.strip().lower():
                raise ValueError("OpenRebar handoff report_sha256 mismatch")

        report_payload = load_openrebar_report_payload(report_path)
        return report_path, build_openrebar_provenance_digest(report_payload)

    reinforcement_report_path = (
        resolve_path(payload.reinforcement_report_path, principal=principal)
        if payload.reinforcement_report_path
        else None
    )
    reinforcement_source_digest = (
        payload.reinforcement_source_digest.strip().lower()
        if payload.reinforcement_source_digest
        else None
    )
    return reinforcement_report_path, reinforcement_source_digest


def build_project_package_request(
    payload: AnalyzeProjectPackageRequest,
    *,
    resolve_path: ResolvePath,
    enforce_ifc_size: Callable[[Path], None],
    storage_dir: Path,
    tenant_id: str | None = None,
    principal: AuthPrincipal | None = None,
) -> ValidationRequest:
    reinforcement_report_path, reinforcement_source_digest = resolve_openrebar_provenance_inputs(
        payload,
        resolve_path=resolve_path,
        storage_dir=storage_dir,
        principal=principal,
    )
    ifc_resolved = resolve_path(payload.ifc_path, principal=principal)
    enforce_ifc_size(ifc_resolved)
    return ValidationRequest(
        request_id=payload.request_id or uuid4().hex,
        ifc_path=ifc_resolved,
        requirement_source=build_requirement_source(
            payload.requirement_text,
            payload.requirement_path,
            SourceKind.STRUCTURED_TEXT,
            resolve_path=resolve_path,
            revision=payload.revision,
            stage=payload.stage,
            doc_status=payload.doc_status,
            principal=principal,
        ),
        ids_path=(
            resolve_path(payload.ids_path, principal=principal) if payload.ids_path else None
        ),
        technical_spec_source=build_requirement_source(
            payload.technical_spec_text,
            payload.technical_spec_path,
            SourceKind.TECHNICAL_SPECIFICATION,
            resolve_path=resolve_path,
            revision=payload.revision,
            stage=payload.stage,
            doc_status=payload.doc_status,
            principal=principal,
        )
        if payload.technical_spec_text or payload.technical_spec_path
        else None,
        calculation_source=build_requirement_source(
            payload.calculation_text,
            payload.calculation_path,
            SourceKind.CALCULATION,
            resolve_path=resolve_path,
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
                path=(resolve_path(drawing.path, principal=principal) if drawing.path else None),
                sheet_id=drawing.sheet_id,
                format=drawing.format,
            )
            for drawing in payload.drawings
        ),
        norm_rule_pack_paths=tuple(
            resolve_path(path, principal=principal) for path in payload.norm_rule_pack_paths
        ),
        pd_section_path=(
            resolve_path(payload.pd_section_path, principal=principal)
            if payload.pd_section_path
            else None
        ),
        rd_section_path=(
            resolve_path(payload.rd_section_path, principal=principal)
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
