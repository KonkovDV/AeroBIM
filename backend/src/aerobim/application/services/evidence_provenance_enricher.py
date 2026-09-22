"""P0-G: Wire EvidenceRecord / FindingProvenance into the assemble path.

This module is the *only* place where `domain.evidence_provenance` types are
created at runtime.  It is called by `EvidenceAssembler.assemble()` **after**
`ensure_finding_provenance()` has already stamped every `ValidationIssue` with
a stable `finding_id`, `source_id`, and `evidence_refs`.

Design decisions
----------------
- **Non-breaking**: the function returns a plain dict that is appended to
  `tool_traces`; `ValidationReport` shape is unchanged.
- **No I/O**: pure transformation; no network/disk access; safe to call in hot path.
- **Graceful**: any per-issue error is recorded in the summary rather than
  aborting the whole report.
- **Deterministic package_id**: if tenant/project/revision are available we derive
  a stable `package_id` via `PackageManifest.compute_package_id`.  For fixture /<br />
  dev runs without those fields we fall back to `request_id` so tests stay green.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from aerobim.domain.evidence_provenance import (
    EvidenceLocator,
    EvidenceLocatorType,
    EvidenceRecord,
    ExtractionMethod,
    FindingProvenance,
)
from aerobim.domain.models import FindingCategory, ValidationIssue, ValidationRequest

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_AI_CATEGORIES = frozenset(
    {
        FindingCategory.ADVISORY,
    }
    if hasattr(FindingCategory, "ADVISORY")
    else set()
)


def _engine_version() -> str:
    """Semver from env or 'dev'.  Never raises."""
    for var in ("AEROBIM_VERSION", "AEROBIM_GIT_SHA", "GITHUB_SHA"):
        v = (os.environ.get(var) or "").strip()
        if v:
            return v[:40]
    return "dev"


def _configuration_hash(signoff_profile: str, priority_profile: str) -> str:
    """Stable sha256 over runtime configuration that affects rule evaluation."""
    payload = json.dumps(
        {"signoff_profile": signoff_profile, "priority_profile": priority_profile},
        sort_keys=True,
    ).encode()
    return hashlib.sha256(payload).hexdigest()[:24]


def _derive_package_id(request: ValidationRequest) -> str:
    """Best-effort deterministic package_id.

    Uses PackageManifest.compute_package_id when enough context is present;
    otherwise falls back to sha256(request_id) so fixture runs stay stable.
    """
    tenant = (getattr(request, "tenant_id", None) or "").strip()
    project = (getattr(request, "project_id", None) or getattr(request, "project_name", None) or "").strip()
    revision = (getattr(request, "revision", None) or "").strip()

    if tenant and project:
        try:
            from aerobim.domain.package_manifest import PackageManifest

            return PackageManifest.compute_package_id(
                tenant_id=tenant,
                project_id=project,
                revision_id=revision or "unversioned",
                file_entries=[],
            )
        except Exception:  # pragma: no cover
            pass

    # Fallback: deterministic from request_id
    req_id = (getattr(request, "request_id", None) or "").strip() or "unknown"
    return hashlib.sha256(req_id.encode()).hexdigest()[:40]


def _derive_norm_pack_meta(request: ValidationRequest) -> tuple[str, str, str]:
    """Returns (norm_pack_id, norm_pack_version, norm_pack_hash)."""
    paths = getattr(request, "norm_rule_pack_paths", None) or []
    if not paths:
        return ("builtin", "0", hashlib.sha256(b"builtin").hexdigest()[:24])
    # Use first pack path as identity; hash all names for stability
    first = str(paths[0])
    all_names = "|".join(sorted(str(p) for p in paths))
    pack_hash = hashlib.sha256(all_names.encode()).hexdigest()[:24]
    return (first, "norm_pack_v1", pack_hash)


def _extraction_method(issue: ValidationIssue) -> ExtractionMethod:
    """Classify how the value was extracted from the origin field."""
    origin = (getattr(issue, "origin", None) or "").lower()
    if "advisory" in origin or "llm" in origin or "ai" in origin:
        return ExtractionMethod.AI_ADVISORY

    category = getattr(issue, "category", None)
    if category is not None:
        cat_val = category.value if hasattr(category, "value") else str(category)
        if "drawing" in cat_val.lower() or "annotation" in cat_val.lower():
            return ExtractionMethod.OCR_EXTRACTED
        if "cross" in cat_val.lower():
            return ExtractionMethod.CROSS_DOC_MATCH
        if "ids" in cat_val.lower():
            return ExtractionMethod.IDS_VALIDATOR

    return ExtractionMethod.DETERMINISTIC_PARSER


def _build_locator(issue: ValidationIssue) -> EvidenceLocator:
    """Build a machine-addressable locator from issue fields."""
    guid = getattr(issue, "element_guid", None)
    prop_set = getattr(issue, "property_set", None)
    prop_name = getattr(issue, "property_name", None)
    zone = getattr(issue, "problem_zone", None)

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
        sheet_id = getattr(zone, "sheet_id", None)
        page = getattr(zone, "page", None)
        return EvidenceLocator(
            locator_type=EvidenceLocatorType.DOCUMENT_PAGE,
            document_page=page,
            document_sheet=str(sheet_id) if sheet_id is not None else None,
        )
    return EvidenceLocator(locator_type=EvidenceLocatorType.IFC_ELEMENT)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_evidence_records(
    issues: Sequence[ValidationIssue],
    request: ValidationRequest,
    *,
    signoff_profile: str = "development",
    priority_profile: str = "default",
) -> tuple[list[EvidenceRecord], list[FindingProvenance], dict[str, Any]]:
    """Create EvidenceRecord + FindingProvenance for every persistable issue.

    Returns
    -------
    records
        One EvidenceRecord per *persistable* issue.  Issues without rule_id or
        finding_id are silently skipped (they were not stamped by
        ``ensure_finding_provenance`` and are not ready for persistence).
    provenances
        One FindingProvenance per record.
    summary
        Serialisable dict suitable for embedding in ``tool_traces``.
    """
    package_id = _derive_package_id(request)
    engine_ver = _engine_version()
    config_hash = _configuration_hash(signoff_profile, priority_profile)
    norm_pack_id, norm_pack_ver, norm_pack_hash = _derive_norm_pack_meta(request)
    tenant_id = (getattr(request, "tenant_id", None) or "").strip() or "unknown"
    project_id = (
        getattr(request, "project_id", None) or getattr(request, "project_name", None) or ""
    ).strip() or "unknown"
    revision_id = (getattr(request, "revision", None) or "").strip() or "unversioned"

    records: list[EvidenceRecord] = []
    provenances: list[FindingProvenance] = []
    skipped = 0
    errors: list[str] = []

    for issue in issues:
        rule_id = (getattr(issue, "rule_id", None) or "").strip()
        finding_id = (getattr(issue, "finding_id", None) or "").strip()
        source_id = (getattr(issue, "source_id", None) or "").strip()
        evidence_refs = list(getattr(issue, "evidence_refs", None) or [])

        if not rule_id or not finding_id:
            skipped += 1
            continue

        method = _extraction_method(issue)
        locator = _build_locator(issue)
        is_ai = method == ExtractionMethod.AI_ADVISORY
        confidence = getattr(issue, "confidence", None)

        # logical_path: use source_id as the best available file pointer
        logical_path = source_id or rule_id
        # source_hash: hash of source_id so the pointer is stable
        source_hash = hashlib.sha256(logical_path.encode()).hexdigest()[:40]

        try:
            record = EvidenceRecord(
                evidence_id=hashlib.sha256(
                    f"{finding_id}:{package_id}:{rule_id}".encode()
                ).hexdigest()[:24],
                finding_id=finding_id,
                package_id=package_id,
                file_logical_path=logical_path,
                source_hash=source_hash,
                locator=locator,
                actual_value=getattr(issue, "observed_value", None),
                expected_value=getattr(issue, "expected_value", None),
                extraction_method=method,
                rule_id=rule_id,
                rule_version="deterministic-engine",
                norm_pack_id=norm_pack_id,
                norm_pack_version=norm_pack_ver,
                norm_pack_hash=norm_pack_hash,
                engine_version=engine_ver,
                configuration_hash=config_hash,
                timestamp=datetime.now(tz=UTC),
                confidence=float(confidence) if confidence is not None else None,
                is_ai_advisory=is_ai,
            )
            provenance = FindingProvenance(
                finding_id=finding_id,
                rule_id=rule_id,
                rule_version="deterministic-engine",
                norm_pack_id=norm_pack_id,
                norm_pack_version=norm_pack_ver,
                norm_pack_hash=norm_pack_hash,
                package_id=package_id,
                revision_id=revision_id,
                tenant_id=tenant_id,
                project_id=project_id,
                engine_version=engine_ver,
                configuration_hash=config_hash,
                evidence_refs=evidence_refs or [record.evidence_id],
                is_ai_advisory=is_ai,
            )
            records.append(record)
            provenances.append(provenance)
        except Exception as exc:  # pragma: no cover
            errors.append(f"{finding_id}: {exc}")

    summary: dict[str, Any] = {
        "tool": "evidence_provenance_enricher",
        "status": "ok" if not errors else "partial",
        "package_id": package_id,
        "engine_version": engine_ver,
        "configuration_hash": config_hash,
        "norm_pack_id": norm_pack_id,
        "norm_pack_hash": norm_pack_hash,
        "issues_total": len(issues),
        "records_built": len(records),
        "skipped_no_finding_id": skipped,
        "errors": errors,
        "verdict_impact": "none",
        "claim": "P0-G evidence-first; EvidenceRecord provenance_id is stable across runs",
    }
    return records, provenances, summary


__all__ = [
    "build_evidence_records",
]
