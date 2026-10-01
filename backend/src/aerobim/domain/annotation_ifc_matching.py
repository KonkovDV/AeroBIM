"""Annotation ↔ IFC target linking for provenance (deterministic, no LLM)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Literal, Protocol

from aerobim.domain.drawing_region_hitl import annotation_bbox_xyxy, intersection_over_union
from aerobim.domain.models import DrawingAnnotation, DrawingRegionRef, ParsedRequirement
from aerobim.domain.target_ref import target_ref_matches

MatchBasis = Literal["target_ref", "sheet+measure", "region_overlap"]


class _GuidLookup(Protocol):
    def lookup(self, global_id: str) -> object | None: ...


@dataclass(frozen=True)
class AnnotationIfcLink:
    annotation_id: str
    sheet_id: str
    target_ref: str
    ifc_guid: str | None
    match_basis: MatchBasis
    confidence: float
    evidence_ref: str

    def as_dict(self) -> dict[str, object]:
        return {
            "annotation_id": self.annotation_id,
            "sheet_id": self.sheet_id,
            "target_ref": self.target_ref,
            "ifc_guid": self.ifc_guid,
            "match_basis": self.match_basis,
            "confidence": self.confidence,
            "evidence_ref": self.evidence_ref,
        }


def _requirement_matches_annotation(
    requirement: ParsedRequirement,
    annotation: DrawingAnnotation,
) -> bool:
    """Empty / ALL requirement.target_ref is unrestricted (matches any annotation ref)."""
    if not target_ref_matches(requirement.target_ref, annotation.target_ref):
        return False
    if (
        requirement.property_name
        and requirement.property_name.lower() != annotation.measure_name.lower()
    ):
        return False
    if requirement.instructions and requirement.instructions.startswith("sheet="):
        expected_sheet = requirement.instructions.split("=", maxsplit=1)[1].strip().lower()
        if annotation.sheet_id.lower() != expected_sheet:
            return False
    return True


def link_annotation_to_ifc_target(
    annotation: DrawingAnnotation,
    *,
    requirements: tuple[ParsedRequirement, ...] | list[ParsedRequirement] = (),
) -> AnnotationIfcLink:
    """Derive annotation↔IFC *candidate* link — never invents verified IFC guids.

    ``ifc_guid`` stays None until a later model presence check. Claimed GUIDs from
    problem_zone appear only in ``evidence_ref`` as ``claimed_guid:``.
    """

    basis: MatchBasis = "target_ref"
    confidence = 0.55
    claimed_guid: str | None = None
    zone = annotation.problem_zone
    if zone is not None and zone.element_guid:
        claimed_guid = zone.element_guid.strip()
        confidence = min(0.4, confidence)

    for requirement in requirements:
        if _requirement_matches_annotation(requirement, annotation):
            confidence = max(confidence, min(0.55, float(requirement.confidence or 0.55)))
            if requirement.target_ref and requirement.ifc_entity:
                basis = "sheet+measure"
            break

    evidence = f"drawing:{annotation.sheet_id}:{annotation.target_ref}"
    if claimed_guid:
        evidence = f"claimed_guid:{claimed_guid}#{annotation.target_ref}"
    return AnnotationIfcLink(
        annotation_id=annotation.annotation_id,
        sheet_id=annotation.sheet_id,
        target_ref=annotation.target_ref,
        ifc_guid=None,
        match_basis=basis,
        confidence=confidence,
        evidence_ref=evidence,
    )


def match_annotations_to_regions(
    annotations: tuple[DrawingAnnotation, ...] | list[DrawingAnnotation],
    regions: tuple[DrawingRegionRef, ...] | list[DrawingRegionRef],
    *,
    requirements: tuple[ParsedRequirement, ...] | list[ParsedRequirement] = (),
    iou_threshold: float = 0.25,
) -> list[AnnotationIfcLink]:
    """Region overlap links are geometric hints only — never flip verdict alone."""

    links: list[AnnotationIfcLink] = []
    for annotation in annotations:
        ann_bbox = annotation_bbox_xyxy(annotation)
        if ann_bbox is None:
            links.append(link_annotation_to_ifc_target(annotation, requirements=requirements))
            continue
        best_iou = 0.0
        best_region: DrawingRegionRef | None = None
        for region in regions:
            if region.sheet_id != annotation.sheet_id:
                continue
            iou = intersection_over_union(ann_bbox, region.bbox_xyxy)
            if iou > best_iou:
                best_iou = iou
                best_region = region
        if best_region is not None and best_iou >= iou_threshold:
            evidence = (
                f"region:{best_region.sheet_id}:{','.join(str(v) for v in best_region.bbox_xyxy)}"
            )
            zone = annotation.problem_zone
            if zone is not None and zone.element_guid:
                claimed = zone.element_guid.strip()
                if claimed:
                    evidence = f"claimed_guid:{claimed}#{evidence}"
            links.append(
                AnnotationIfcLink(
                    annotation_id=annotation.annotation_id,
                    sheet_id=annotation.sheet_id,
                    target_ref=annotation.target_ref,
                    ifc_guid=None,
                    match_basis="region_overlap",
                    confidence=round(min(0.95, best_iou), 4),
                    evidence_ref=evidence,
                )
            )
        else:
            links.append(link_annotation_to_ifc_target(annotation, requirements=requirements))
    return links


def claimed_guid_from_evidence(evidence_ref: str) -> str | None:
    """Parse ``claimed_guid:<guid>#...`` provenance; never invents GUIDs."""

    if not evidence_ref.startswith("claimed_guid:"):
        return None
    rest = evidence_ref.removeprefix("claimed_guid:")
    guid = rest.split("#", maxsplit=1)[0].strip()
    return guid or None


def confirm_link_against_spatial_index(
    link: AnnotationIfcLink,
    spatial_index: _GuidLookup,
    *,
    annotation_bbox: tuple[float, float, float, float] | None = None,
    iou_tolerance: float = 0.0,
) -> AnnotationIfcLink:
    """Set ``ifc_guid`` only when claimed GUID is present in the model index.

    Optional geometric gate: when ``annotation_bbox`` is set and the index exposes
    ``bbox_xyxy_for``, require IoU >= ``iou_tolerance`` (if tolerance > 0).
    Region-overlap / target_ref candidates stay ``ifc_guid=None``. Missing or
    wrong claimed GUIDs keep provenance evidence unchanged and leave guid unset.
    Pre-set ``ifc_guid`` values are never trusted without ``claimed_guid:`` evidence.
    """

    claimed = claimed_guid_from_evidence(link.evidence_ref)
    if not claimed:
        if link.ifc_guid is not None:
            return replace(link, ifc_guid=None)
        return link
    if spatial_index.lookup(claimed) is None:
        return replace(link, ifc_guid=None)

    if iou_tolerance > 0.0 and annotation_bbox is not None:
        bbox_for = getattr(spatial_index, "bbox_xyxy_for", None)
        if callable(bbox_for):
            element_bbox = bbox_for(claimed)
            if element_bbox is None:
                return replace(
                    link,
                    ifc_guid=None,
                    evidence_ref=f"{link.evidence_ref}|geo_unavailable",
                )
            iou = intersection_over_union(annotation_bbox, element_bbox)
            if iou < iou_tolerance:
                return replace(
                    link,
                    ifc_guid=None,
                    evidence_ref=(
                        f"{link.evidence_ref}|geo_mismatch:iou={iou:.4f}<{iou_tolerance}"
                    ),
                )
            return replace(
                link,
                ifc_guid=claimed,
                evidence_ref=f"{link.evidence_ref}|geo_ok:iou={iou:.4f}",
            )

    return replace(link, ifc_guid=claimed)


def confirm_annotation_ifc_links(
    links: Sequence[AnnotationIfcLink],
    spatial_index: _GuidLookup | None,
    *,
    annotation_bboxes: dict[str, tuple[float, float, float, float]] | None = None,
    iou_tolerance: float = 0.0,
) -> list[AnnotationIfcLink]:
    if spatial_index is None:
        # Index unavailable: never keep a pre-set ifc_guid (P2-04 / HD8-P204-01).
        return [
            replace(link, ifc_guid=None) if link.ifc_guid is not None else link for link in links
        ]
    bboxes = annotation_bboxes or {}
    return [
        confirm_link_against_spatial_index(
            link,
            spatial_index,
            annotation_bbox=bboxes.get(link.annotation_id),
            iou_tolerance=iou_tolerance,
        )
        for link in links
    ]


__all__ = [
    "AnnotationIfcLink",
    "claimed_guid_from_evidence",
    "confirm_annotation_ifc_links",
    "confirm_link_against_spatial_index",
    "link_annotation_to_ifc_target",
    "match_annotations_to_regions",
]
