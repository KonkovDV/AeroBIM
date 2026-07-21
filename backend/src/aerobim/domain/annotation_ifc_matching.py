"""Annotation ↔ IFC target linking for provenance (deterministic, no LLM)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aerobim.domain.drawing_region_hitl import annotation_bbox_xyxy, intersection_over_union
from aerobim.domain.models import DrawingAnnotation, DrawingRegionRef, ParsedRequirement

MatchBasis = Literal["target_ref", "sheet+measure", "region_overlap"]


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
    if requirement.target_ref and requirement.target_ref.lower() != annotation.target_ref.lower():
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
            links.append(
                AnnotationIfcLink(
                    annotation_id=annotation.annotation_id,
                    sheet_id=annotation.sheet_id,
                    target_ref=annotation.target_ref,
                    ifc_guid=None,
                    match_basis="region_overlap",
                    confidence=round(min(0.95, best_iou), 4),
                    evidence_ref=(
                        f"region:{best_region.sheet_id}:"
                        f"{','.join(str(v) for v in best_region.bbox_xyxy)}"
                    ),
                )
            )
        else:
            links.append(link_annotation_to_ifc_target(annotation, requirements=requirements))
    return links


__all__ = [
    "AnnotationIfcLink",
    "link_annotation_to_ifc_target",
    "match_annotations_to_regions",
]
