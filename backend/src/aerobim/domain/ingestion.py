"""INGESTION contour helpers: document identity and revision-merge guard."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from aerobim.domain.architecture import DocumentIdentity
from aerobim.domain.models import (
    ConflictKind,
    DrawingAnnotation,
    DrawingSource,
    FindingCategory,
    RequirementSource,
    Severity,
    ValidationIssue,
)


def identity_from_requirement_source(source: RequirementSource) -> DocumentIdentity:
    """Build DocumentIdentity from an ingested requirement source (additive fields)."""

    return DocumentIdentity(
        source_id=source.source_id or source.source_kind.value,
        doc_type=source.doc_type or source.source_kind.value,
        revision=source.revision,
        status=source.doc_status,
        stage=source.stage,
        sha256=source.sha256,
    )


def same_logical_document(left: DocumentIdentity, right: DocumentIdentity) -> bool:
    """True when two identities describe the same logical document (ignore revision)."""

    return (
        left.source_id.casefold() == right.source_id.casefold()
        and left.doc_type.casefold() == right.doc_type.casefold()
    )


def revisions_conflict(left: DocumentIdentity, right: DocumentIdentity) -> bool:
    """True when same logical document has conflicting or one-sided revision markers."""

    if not same_logical_document(left, right):
        return False
    left_rev = (left.revision or "").strip()
    right_rev = (right.revision or "").strip()
    if bool(left_rev) != bool(right_rev):
        # One side missing revision → AMBIGUOUS / requires HITL, never silent merge.
        return True
    if not left_rev:
        return False
    return left_rev.casefold() != right_rev.casefold()


def _conflict_kind_for(left: DocumentIdentity, right: DocumentIdentity) -> ConflictKind:
    left_rev = (left.revision or "").strip()
    right_rev = (right.revision or "").strip()
    if bool(left_rev) != bool(right_rev):
        return ConflictKind.AMBIGUOUS_MAPPING
    return ConflictKind.VERSION_MISMATCH


def detect_revision_merge_conflicts(
    sources: list[RequirementSource],
) -> list[ValidationIssue]:
    """Emit explicit VERSION_MISMATCH / AMBIGUOUS issues — never silently merge revisions.

    TR-242: divergent content for one identity is also not a silent merge. Two sources that
    are the SAME logical document with the SAME-or-absent revision but DIFFERENT content
    hashes surface as an AMBIGUOUS_MAPPING warning (HITL), so two different files cannot
    quietly collapse into one "revision".
    """

    identities = [identity_from_requirement_source(source) for source in sources if source]
    issues: list[ValidationIssue] = []
    seen_pairs: set[tuple[str, str, str, str]] = set()
    seen_hash_pairs: set[tuple[str, str, str, str]] = set()
    for index, left in enumerate(identities):
        for right in identities[index + 1 :]:
            if not same_logical_document(left, right):
                continue
            if revisions_conflict(left, right):
                key = (
                    left.source_id.casefold(),
                    left.doc_type.casefold(),
                    left.revision or "",
                    right.revision or "",
                )
                if key in seen_pairs or (key[0], key[1], key[3], key[2]) in seen_pairs:
                    continue
                seen_pairs.add(key)
                kind = _conflict_kind_for(left, right)
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-REVISION-MERGE",
                        severity=Severity.ERROR,
                        message=(
                            f"Silent revision merge blocked: document "
                            f"{left.doc_type}/{left.source_id} compares "
                            f"revision {left.revision!r} vs {right.revision!r}"
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        conflict_kind=kind,
                        source_id=left.source_id,
                        evidence_modality="ingestion",
                    )
                )
                continue
            left_hash = (left.sha256 or "").strip().casefold()
            right_hash = (right.sha256 or "").strip().casefold()
            if not left_hash or not right_hash or left_hash == right_hash:
                continue
            lo, hi = sorted((left_hash, right_hash))
            hash_key = (left.source_id.casefold(), left.doc_type.casefold(), lo, hi)
            if hash_key in seen_hash_pairs:
                continue
            seen_hash_pairs.add(hash_key)
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-REVISION-HASH",
                    severity=Severity.WARNING,
                    message=(
                        f"Divergent content for one document revision: "
                        f"{left.doc_type}/{left.source_id} revision {left.revision!r} "
                        "has two different content hashes (requires HITL; not a silent merge)"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    conflict_kind=ConflictKind.AMBIGUOUS_MAPPING,
                    source_id=left.source_id,
                    evidence_modality="ingestion",
                )
            )
    return issues


PACKAGE_IDENTITY_CLAIM_BOUNDARY = (
    "Fixture package identity compare only; not CDE version management; "
    "not customer package evidence."
)


def _norm_token(value: str | None) -> str:
    return (value or "").strip()


def _optional_token(item: Mapping[str, object], key: str) -> str | None:
    if item.get(key) is None:
        return None
    return _norm_token(str(item[key]))


def identities_from_mapping(items: Sequence[Mapping[str, object]]) -> list[DocumentIdentity]:
    """Build DocumentIdentity rows from a JSON-like package compare payload."""

    identities: list[DocumentIdentity] = []
    for item in items:
        identities.append(
            DocumentIdentity(
                source_id=str(item.get("source_id") or "").strip(),
                doc_type=str(item.get("doc_type") or "").strip(),
                revision=_optional_token(item, "revision"),
                status=_optional_token(item, "status"),
                stage=_optional_token(item, "stage"),
                sha256=_optional_token(item, "sha256"),
            )
        )
    return identities


def _index_identities(
    identities: Sequence[DocumentIdentity],
    *,
    side: str,
) -> tuple[dict[str, DocumentIdentity], list[ValidationIssue]]:
    index: dict[str, DocumentIdentity] = {}
    issues: list[ValidationIssue] = []
    duplicate_keys: set[str] = set()
    for identity in identities:
        key = _norm_token(identity.source_id).casefold()
        if not key:
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-PACKAGE-DOC-IDENTITY-MISSING",
                    severity=Severity.WARNING,
                    message=(
                        f"{side} package has a document without source_id; "
                        f"{PACKAGE_IDENTITY_CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    conflict_kind=ConflictKind.AMBIGUOUS_MAPPING,
                    evidence_modality="ingestion",
                )
            )
            continue
        if key in index:
            if key not in duplicate_keys:
                duplicate_keys.add(key)
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-PACKAGE-DOC-DUPLICATE",
                        severity=Severity.WARNING,
                        message=(
                            f"{side} package lists source_id {identity.source_id!r} "
                            f"more than once; {PACKAGE_IDENTITY_CLAIM_BOUNDARY}"
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        conflict_kind=ConflictKind.AMBIGUOUS_MAPPING,
                        source_id=identity.source_id,
                        evidence_modality="ingestion",
                    )
                )
            continue
        index[key] = identity
    return index, issues


def compare_package_document_identities(
    previous: Sequence[DocumentIdentity],
    current: Sequence[DocumentIdentity],
) -> list[ValidationIssue]:
    """Compare two package identity lists by ``source_id``.

    Matching IDs emit ``DOC_TYPE_MISMATCH``, ``STAGE_MISMATCH``, and
    ``VERSION_MISMATCH``. Added/removed IDs are listed. This is fixture/engine
    coverage for TZ «сравнение версий и типов» — not CDE import.
    """

    previous_index, issues = _index_identities(previous, side="previous")
    current_index, current_issues = _index_identities(current, side="current")
    issues.extend(current_issues)

    for key in sorted(previous_index.keys() | current_index.keys()):
        left = previous_index.get(key)
        right = current_index.get(key)
        if left is None and right is not None:
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-PACKAGE-DOC-ADDED",
                    severity=Severity.INFO,
                    message=(
                        f"Document {right.doc_type}/{right.source_id} is present in "
                        f"current package only; {PACKAGE_IDENTITY_CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id=right.source_id,
                    evidence_modality="ingestion",
                )
            )
            continue
        if right is None and left is not None:
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-PACKAGE-DOC-REMOVED",
                    severity=Severity.WARNING,
                    message=(
                        f"Document {left.doc_type}/{left.source_id} is present in "
                        f"previous package only; {PACKAGE_IDENTITY_CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id=left.source_id,
                    evidence_modality="ingestion",
                )
            )
            continue
        if left is None or right is None:
            continue
        if left.doc_type.casefold() != right.doc_type.casefold():
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-PACKAGE-DOC-TYPE-MISMATCH",
                    severity=Severity.ERROR,
                    message=(
                        f"Document type mismatch for {left.source_id}: "
                        f"{left.doc_type!r} vs {right.doc_type!r}; "
                        f"{PACKAGE_IDENTITY_CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    conflict_kind=ConflictKind.DOC_TYPE_MISMATCH,
                    source_id=left.source_id,
                    evidence_modality="ingestion",
                    expected_value=left.doc_type,
                    observed_value=right.doc_type,
                )
            )
        if _norm_token(left.stage).casefold() != _norm_token(right.stage).casefold():
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-PACKAGE-STAGE-MISMATCH",
                    severity=Severity.ERROR,
                    message=(
                        f"Stage mismatch for {left.source_id}: "
                        f"{left.stage!r} vs {right.stage!r}; "
                        f"{PACKAGE_IDENTITY_CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    conflict_kind=ConflictKind.STAGE_MISMATCH,
                    source_id=left.source_id,
                    evidence_modality="ingestion",
                    expected_value=left.stage,
                    observed_value=right.stage,
                )
            )
        if _norm_token(left.revision).casefold() != _norm_token(right.revision).casefold():
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-PACKAGE-VERSION-MISMATCH",
                    severity=Severity.ERROR,
                    message=(
                        f"Revision mismatch for {left.source_id}: "
                        f"{left.revision!r} vs {right.revision!r}; "
                        f"{PACKAGE_IDENTITY_CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    conflict_kind=ConflictKind.VERSION_MISMATCH,
                    source_id=left.source_id,
                    evidence_modality="ingestion",
                    expected_value=left.revision,
                    observed_value=right.revision,
                )
            )
    return issues


def drawing_sheet_identity(source: DrawingSource) -> str | None:
    """Resolve stable sheet identity for 2D provenance (sheet_id preferred)."""

    sheet = (source.sheet_id or "").strip()
    if sheet:
        return sheet
    if source.path is not None:
        stem = source.path.stem.strip()
        if stem:
            return stem
    return None


def detect_missing_drawing_sheet_identity(
    sources: Sequence[DrawingSource],
) -> list[ValidationIssue]:
    """Warn when raster/CAD drawings lack sheet identity — HITL escalation path."""

    issues: list[ValidationIssue] = []
    for index, source in enumerate(sources):
        if drawing_sheet_identity(source) is not None:
            continue
        label = source.path.name if source.path is not None else f"drawing-{index}"
        issues.append(
            ValidationIssue(
                rule_id="AEROBIM-SHEET-IDENTITY",
                severity=Severity.WARNING,
                message=(
                    f"Drawing source {label!r} lacks sheet_id/path identity; "
                    "annotation↔IFC matching may require HITL"
                ),
                category=FindingCategory.DRAWING_VALIDATION,
                source_id=label,
                evidence_modality="drawing",
                evidence_refs=(f"drawing:{label}",),
            )
        )
    return issues


def detect_annotation_sheet_identity_drift(
    sources: Sequence[DrawingSource],
    annotations: Sequence[DrawingAnnotation],
) -> list[ValidationIssue]:
    """Warn when annotation sheet_id is not among known drawing identities."""

    known = {
        identity.casefold()
        for source in sources
        if (identity := drawing_sheet_identity(source)) is not None
    }
    if not known or not annotations:
        return []
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for annotation in annotations:
        sheet = (annotation.sheet_id or "").strip()
        if not sheet:
            continue
        key = sheet.casefold()
        if key in known or key in seen:
            continue
        seen.add(key)
        issues.append(
            ValidationIssue(
                rule_id="AEROBIM-SHEET-IDENTITY-DRIFT",
                severity=Severity.WARNING,
                message=(
                    f"Annotation sheet_id {sheet!r} not found among drawing sources; "
                    "region/IFC matching may require HITL"
                ),
                category=FindingCategory.DRAWING_VALIDATION,
                source_id=sheet,
                evidence_modality="drawing",
                evidence_refs=(f"annotation:{annotation.annotation_id}", f"sheet:{sheet}"),
            )
        )
    return issues


def stamp_requirement_source(
    source: RequirementSource,
    *,
    revision: str | None = None,
    stage: str | None = None,
    doc_type: str | None = None,
    sha256: str | None = None,
    doc_status: str | None = None,
    source_id: str | None = None,
) -> RequirementSource:
    """Return a copy with identity fields filled (Optional/None-safe)."""

    return RequirementSource(
        text=source.text,
        path=source.path,
        source_kind=source.source_kind,
        source_id=source_id if source_id is not None else source.source_id,
        revision=revision if revision is not None else source.revision,
        stage=stage if stage is not None else source.stage,
        doc_type=doc_type if doc_type is not None else source.doc_type,
        sha256=sha256 if sha256 is not None else source.sha256,
        doc_status=doc_status if doc_status is not None else source.doc_status,
    )


__all__ = [
    "PACKAGE_IDENTITY_CLAIM_BOUNDARY",
    "compare_package_document_identities",
    "detect_annotation_sheet_identity_drift",
    "detect_missing_drawing_sheet_identity",
    "detect_revision_merge_conflicts",
    "drawing_sheet_identity",
    "identities_from_mapping",
    "identity_from_requirement_source",
    "revisions_conflict",
    "same_logical_document",
    "stamp_requirement_source",
]
