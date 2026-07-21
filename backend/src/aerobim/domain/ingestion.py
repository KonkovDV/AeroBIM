"""INGESTION contour helpers: document identity and revision-merge guard."""

from __future__ import annotations

from collections.abc import Sequence

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
    """Emit explicit VERSION_MISMATCH / AMBIGUOUS issues — never silently merge revisions."""

    identities = [identity_from_requirement_source(source) for source in sources if source]
    issues: list[ValidationIssue] = []
    seen_pairs: set[tuple[str, str, str, str]] = set()
    for index, left in enumerate(identities):
        for right in identities[index + 1 :]:
            if not revisions_conflict(left, right):
                continue
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
    "detect_annotation_sheet_identity_drift",
    "detect_missing_drawing_sheet_identity",
    "detect_revision_merge_conflicts",
    "drawing_sheet_identity",
    "identity_from_requirement_source",
    "revisions_conflict",
    "same_logical_document",
    "stamp_requirement_source",
]
