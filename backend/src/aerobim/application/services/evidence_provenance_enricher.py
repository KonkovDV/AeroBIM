"""Build EvidenceRecord rows for issues that already have a finding_id.

EvidenceAssembler appends the summary dict to tool_traces. The records
themselves are not stored on the issue and do not change summary.passed.

package_id uses file hashes only when the caller passes them. A hash of
source_id is not a hash of the file bytes. engine_version is left empty,
so FindingProvenance.is_reproducible stays false.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

from aerobim.domain.evidence_provenance import (
    EvidenceLocator,
    EvidenceLocatorType,
    EvidenceRecord,
    ExtractionMethod,
    FindingProvenance,
)
from aerobim.domain.models import ValidationIssue, ValidationRequest
from aerobim.domain.package_manifest import PackageFileEntry, PackageManifest

_UNRECORDED_RULE_VERSION = "unrecorded"


def _configuration_hash(signoff_profile: str, priority_profile: str) -> str:
    payload = json.dumps(
        {"signoff_profile": signoff_profile, "priority_profile": priority_profile},
        sort_keys=True,
    ).encode()
    return hashlib.sha256(payload).hexdigest()[:24]


def _derive_package_id(
    request: ValidationRequest,
    file_entries: Sequence[PackageFileEntry],
) -> tuple[str, str]:
    """Return (package_id, basis).

    Empty file_entries must not call compute_package_id: that id would
    ignore the IFC bytes and collide across packages.
    """
    if file_entries:
        tenant = (request.tenant_id or "").strip()
        project = (request.project_id or request.project_name or "").strip()
        revision = (request.revision or "").strip() or "unversioned"
        package_id = PackageManifest.compute_package_id(
            tenant_id=tenant,
            project_id=project,
            revision_id=revision,
            file_entries=list(file_entries),
        )
        return package_id, "file-hashes"
    req_id = (request.request_id or "").strip() or "unknown"
    return hashlib.sha256(req_id.encode()).hexdigest()[:40], "request_id"


def _derive_norm_pack_meta(request: ValidationRequest) -> tuple[str, str, str]:
    paths = request.norm_rule_pack_paths
    if not paths:
        return ("builtin", "0", hashlib.sha256(b"builtin").hexdigest()[:24])
    names = "|".join(sorted(str(path) for path in paths))
    pack_hash = hashlib.sha256(names.encode()).hexdigest()[:24]
    return (str(paths[0]), "unrecorded", pack_hash)


def _extraction_method(issue: ValidationIssue) -> ExtractionMethod:
    origin = (issue.origin or "").lower()
    if "advisory" in origin or "llm" in origin or "ai" in origin:
        return ExtractionMethod.AI_ADVISORY
    category = issue.category.value.lower()
    if "drawing" in category or "annotation" in category:
        return ExtractionMethod.OCR_EXTRACTED
    if "cross" in category:
        return ExtractionMethod.CROSS_DOC_MATCH
    if "ids" in category:
        return ExtractionMethod.IDS_VALIDATOR
    return ExtractionMethod.DETERMINISTIC_PARSER


def _build_locator(issue: ValidationIssue) -> EvidenceLocator:
    guid = issue.element_guid
    prop_set = issue.property_set
    prop_name = issue.property_name
    zone = issue.problem_zone
    if guid and prop_set:
        return EvidenceLocator(
            locator_type=EvidenceLocatorType.IFC_PROPERTY,
            ifc_guid=guid,
            ifc_property_set=prop_set,
            ifc_property_name=prop_name,
        )
    if guid:
        return EvidenceLocator(
            locator_type=EvidenceLocatorType.IFC_ELEMENT,
            ifc_guid=guid,
        )
    if zone is not None:
        sheet_id = zone.sheet_id
        return EvidenceLocator(
            locator_type=EvidenceLocatorType.DOCUMENT_PAGE,
            document_page=zone.page_number,
            document_sheet=str(sheet_id) if sheet_id is not None else None,
        )
    return EvidenceLocator(locator_type=EvidenceLocatorType.IFC_ELEMENT)


def build_evidence_records(
    issues: Sequence[ValidationIssue],
    request: ValidationRequest,
    *,
    signoff_profile: str = "development",
    priority_profile: str = "default",
    file_entries: Sequence[PackageFileEntry] = (),
) -> tuple[list[EvidenceRecord], list[FindingProvenance], dict[str, Any]]:
    """One record per issue that already has rule_id and finding_id."""
    package_id, package_id_basis = _derive_package_id(request, file_entries)
    config_hash = _configuration_hash(signoff_profile, priority_profile)
    norm_pack_id, norm_pack_ver, norm_pack_hash = _derive_norm_pack_meta(request)
    tenant_id = (request.tenant_id or "").strip() or "unknown"
    project_id = (request.project_id or request.project_name or "").strip() or "unknown"
    revision_id = (request.revision or "").strip() or "unversioned"

    records: list[EvidenceRecord] = []
    provenances: list[FindingProvenance] = []
    skipped = 0

    for issue in issues:
        rule_id = (issue.rule_id or "").strip()
        finding_id = (issue.finding_id or "").strip()
        if not rule_id or not finding_id:
            skipped += 1
            continue

        method = _extraction_method(issue)
        source_id = (issue.source_id or "").strip()
        logical_path = source_id or rule_id
        source_hash = hashlib.sha256(logical_path.encode()).hexdigest()[:40]
        evidence_key = f"{finding_id}:{package_id}:{rule_id}".encode()
        record = EvidenceRecord(
            evidence_id=hashlib.sha256(evidence_key).hexdigest()[:24],
            finding_id=finding_id,
            package_id=package_id,
            file_logical_path=logical_path,
            source_hash=source_hash,
            locator=_build_locator(issue),
            actual_value=issue.observed_value,
            expected_value=issue.expected_value,
            extraction_method=method,
            rule_id=rule_id,
            rule_version=_UNRECORDED_RULE_VERSION,
            norm_pack_id=norm_pack_id,
            norm_pack_version=norm_pack_ver,
            norm_pack_hash=norm_pack_hash,
            engine_version="",
            configuration_hash=config_hash,
            confidence=float(issue.confidence) if issue.confidence is not None else None,
            is_ai_advisory=method == ExtractionMethod.AI_ADVISORY,
            supplementary={"source_hash_basis": "source_id string, not file bytes"},
        )
        provenance = FindingProvenance(
            finding_id=finding_id,
            rule_id=rule_id,
            rule_version=_UNRECORDED_RULE_VERSION,
            norm_pack_id=norm_pack_id,
            norm_pack_version=norm_pack_ver,
            norm_pack_hash=norm_pack_hash,
            package_id=package_id,
            revision_id=revision_id,
            tenant_id=tenant_id,
            project_id=project_id,
            engine_version="",
            configuration_hash=config_hash,
            evidence_refs=list(issue.evidence_refs) or [record.evidence_id],
            is_ai_advisory=record.is_ai_advisory,
        )
        records.append(record)
        provenances.append(provenance)

    summary: dict[str, Any] = {
        "tool": "evidence_provenance_enricher",
        "status": "ok",
        "package_id": package_id,
        "package_id_basis": package_id_basis,
        "package_id_includes_file_hashes": package_id_basis == "file-hashes",
        "engine_version": "",
        "engine_version_recorded": False,
        "configuration_hash": config_hash,
        "norm_pack_id": norm_pack_id,
        "norm_pack_hash": norm_pack_hash,
        "source_hash_basis": "source_id string, not file bytes",
        "stored_on_report": False,
        "issues_total": len(issues),
        "records_built": len(records),
        "skipped_no_finding_id": skipped,
        "errors": [],
        "verdict_impact": "none",
    }
    return records, provenances, summary


__all__ = ["build_evidence_records"]
