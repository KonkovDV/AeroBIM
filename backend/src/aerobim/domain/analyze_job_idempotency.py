"""Analyze-job idempotency: payload fingerprint + stored-row reconstruct.

Same ``Idempotency-Key`` with a different request identity is a conflict (409),
not a silent replay. Fingerprint is path/id identity, not file-bytes and not
an SLA. JOB-01 runner remains in-process BackgroundTasks.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus, ValidationRequest


class IdempotencyPayloadConflictError(RuntimeError):
    """Same Idempotency-Key already bound to a different analyze payload."""


def _path_key(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def analyze_job_payload_fingerprint(request: ValidationRequest) -> str:
    """Stable SHA-256 of the submitted package identity (paths and ids)."""

    def _source_id(source: object | None) -> str:
        if source is None:
            return ""
        return str(getattr(source, "source_id", None) or "")

    def _kind(source: object | None) -> str:
        if source is None:
            return ""
        kind = getattr(source, "source_kind", None)
        value = getattr(kind, "value", kind)
        return str(value or "")

    drawings = sorted(
        (
            {
                "path": _path_key(getattr(item, "path", None)),
                "sheet_id": str(getattr(item, "sheet_id", None) or ""),
                "format": str(getattr(item, "format", None) or ""),
            }
            for item in request.drawing_sources
        ),
        key=lambda row: (row["path"], row["sheet_id"], row["format"]),
    )
    payload = {
        "ifc_path": _path_key(request.ifc_path),
        "ids_path": _path_key(request.ids_path),
        "requirement_path": _path_key(request.requirement_source.path),
        "requirement_kind": _kind(request.requirement_source),
        "requirement_id": _source_id(request.requirement_source),
        "technical_spec_path": _path_key(
            request.technical_spec_source.path if request.technical_spec_source else None
        ),
        "calculation_path": _path_key(
            request.calculation_source.path if request.calculation_source else None
        ),
        "drawings": drawings,
        "reinforcement_report_path": _path_key(request.reinforcement_report_path),
        "reinforcement_source_digest": str(request.reinforcement_source_digest or ""),
        "origin": str(request.origin or ""),
        "project_name": str(request.project_name or ""),
        "discipline": str(request.discipline or ""),
        "stage": str(request.stage or ""),
        "information_container_id": str(request.information_container_id or ""),
        "revision": str(request.revision or ""),
        "project_id": str(request.project_id or ""),
        "norm_rule_pack_paths": sorted(_path_key(path) for path in request.norm_rule_pack_paths),
        "pd_section_path": _path_key(request.pd_section_path),
        "rd_section_path": _path_key(request.rd_section_path),
        "signature_envelope_path": _path_key(request.signature_envelope_path),
        "package_inventory_path": _path_key(request.package_inventory_path),
        "require_signature_audit": bool(request.require_signature_audit),
        "require_package_completeness": bool(request.require_package_completeness),
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def fingerprints_conflict(stored: str | None, incoming: str | None) -> bool:
    """Legacy rows with no fingerprint cannot be conflicted. Both set and unequal → yes."""

    if not stored or not incoming:
        return False
    return stored != incoming


def job_from_stored_mapping(item: Mapping[str, Any]) -> AnalyzeProjectPackageJob:
    """Rebuild a job row from Redis/snapshot JSON (unknown extra keys ignored)."""

    return AnalyzeProjectPackageJob(
        job_id=str(item["job_id"]),
        request_id=str(item["request_id"]),
        status=JobStatus(str(item["status"])),
        created_at=str(item["created_at"]),
        started_at=(str(item["started_at"]) if item.get("started_at") else None),
        completed_at=(str(item["completed_at"]) if item.get("completed_at") else None),
        report_id=str(item["report_id"]) if item.get("report_id") else None,
        error_message=(
            str(item["error_message"]) if item.get("error_message") is not None else None
        ),
        idempotency_key=(str(item["idempotency_key"]) if item.get("idempotency_key") else None),
        heartbeat_at=(str(item["heartbeat_at"]) if item.get("heartbeat_at") else None),
        lease_expires_at=(str(item["lease_expires_at"]) if item.get("lease_expires_at") else None),
        retry_count=int(item.get("retry_count") or 0),
        stage_progress=(str(item["stage_progress"]) if item.get("stage_progress") else None),
        cancel_requested=bool(item.get("cancel_requested") or False),
        tenant_id=(str(item["tenant_id"]) if item.get("tenant_id") else None),
        payload_fingerprint=(
            str(item["payload_fingerprint"]) if item.get("payload_fingerprint") else None
        ),
    )
