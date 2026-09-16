"""IFC QTO wall width vs drawing text-layer thickness/width (source contradiction).

This is not a regulatory (SP) finding and not a project-TZ violation by itself.
It compares two pack sources of the same claimed revision. Missing values are
never coerced to zero. Ambiguous Name/Tag matches are not emitted as HARD.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ComparisonOperator,
    ConflictKind,
    DrawingAnnotation,
    DrawingSource,
    FindingCategory,
    ProblemZone,
    Severity,
    ValidationIssue,
)
from aerobim.domain.quantity import (
    QuantityValue,
    parse_localized_number,
    parse_quantity,
    si_compare,
)
from aerobim.domain.target_ref import is_unrestricted_target_ref

RULE_ID = "AEROBIM-PD-RD-WALL-WIDTH"
RULE_VERSION = "1.0.0"
RULE_INCOMPLETE = "AEROBIM-PD-RD-INCOMPLETE"
RULE_AMBIGUOUS = "AEROBIM-PD-RD-AMBIGUOUS"
RULE_REVISION_MIXED = "AEROBIM-PD-RD-REVISION-MIXED"
RULE_PARSER = "AEROBIM-PD-RD-PARSER-ERROR"
RULE_UNSUPPORTED = "AEROBIM-PD-RD-UNSUPPORTED-INPUT"

LENGTH_MEASURES = frozenset({"thickness", "width", "толщина", "ширина"})
QTO_WIDTH = "Width"
IFC_ENTITY = "IFCWALL"
# 0.1 mm in metres — drawing millimetre integers vs IFC millimetre QTO.
COMPARE_EPSILON_M = 1e-4
CLAIM_BOUNDARY = (
    "synthetic source-contradiction (IFC Qto Width vs drawing text-layer); "
    "not a SP/regulatory finding; not product accuracy; not PD/RD completeness"
)

_RASTER_SUFFIXES = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".webp"})
_CAD_SUFFIXES = frozenset({".dxf", ".dwg", ".rvt", ".nwd", ".nwc", ".rte", ".rfa"})
_TEXT_SUFFIXES = frozenset({".txt", ".json", ".md"})
_OFFICE_SUFFIXES = frozenset({".docx", ".xlsx", ".pptx", ".doc", ".xls", ".odt", ".ods"})
_SUPPORTED_DRAWING_SUFFIXES = _RASTER_SUFFIXES | _CAD_SUFFIXES | _TEXT_SUFFIXES | _OFFICE_SUFFIXES


@dataclass(frozen=True)
class IfcQuantityObservation:
    global_id: str
    name: str
    quantity_name: str
    value: QuantityValue
    ifc_entity: str = IFC_ENTITY
    ifc_path: Path | None = None
    ifc_sha256: str | None = None
    ifc_revision: str | None = None


@dataclass(frozen=True)
class DrawingIfcConsistencyResult:
    issues: tuple[ValidationIssue, ...]
    capability: CapabilityStatus | None
    ran: bool


def length_measure_annotations(
    annotations: Sequence[DrawingAnnotation],
) -> tuple[DrawingAnnotation, ...]:
    return tuple(
        annotation
        for annotation in annotations
        if (annotation.measure_name or "").strip().casefold() in LENGTH_MEASURES
    )


def parse_annotation_length(annotation: DrawingAnnotation) -> QuantityValue | None:
    """Return SI length or None. Empty / unparsed is None — never 0.0."""

    raw = (annotation.observed_value or "").strip()
    if not raw:
        return None
    number = parse_localized_number(raw)
    if number is None:
        return None
    unit = (annotation.unit or "").strip()
    if not unit:
        return None
    quantity = parse_quantity(number, unit)
    if quantity.si_value is None or quantity.dimension != "length":
        return None
    return quantity


def _revision_pair(
    ifc_revision: str | None, drawing_revision: str | None
) -> tuple[str | None, str | None]:
    left = (ifc_revision or "").strip() or None
    right = (drawing_revision or "").strip() or None
    return left, right


def mixed_revision_kind(
    ifc_revision: str | None, drawing_revision: str | None
) -> ConflictKind | None:
    left, right = _revision_pair(ifc_revision, drawing_revision)
    if left and right and left.casefold() != right.casefold():
        return ConflictKind.VERSION_MISMATCH
    if bool(left) != bool(right):
        return ConflictKind.AMBIGUOUS_MAPPING
    return None


def drawing_file_unsupported(source: DrawingSource) -> bool:
    if source.path is None:
        return False
    suffix = source.path.suffix.lower()
    if not suffix:
        return True
    return suffix not in _SUPPORTED_DRAWING_SUFFIXES


def _rule_ref() -> str:
    return f"rule:{RULE_ID}@{RULE_VERSION}"


def _issue(
    *,
    rule_id: str,
    severity: Severity,
    message: str,
    conflict_kind: ConflictKind | None,
    annotation: DrawingAnnotation | None = None,
    observation: IfcQuantityObservation | None = None,
    expected_value: str | None = None,
    observed_value: str | None = None,
    unit: str | None = None,
    evidence_refs: tuple[str, ...] = (),
    drawing_source: DrawingSource | None = None,
    ifc_revision: str | None = None,
    extra_evidence: tuple[str, ...] = (),
) -> ValidationIssue:
    zone = annotation.problem_zone if annotation is not None else None
    drawing_path = drawing_source.path if drawing_source is not None else None
    drawing_rev = drawing_source.revision if drawing_source is not None else None
    drawing_sha = drawing_source.sha256 if drawing_source is not None else None
    refs = [_rule_ref(), f"claim_boundary:{CLAIM_BOUNDARY}", *extra_evidence, *evidence_refs]
    if observation is not None and observation.ifc_sha256:
        rev = observation.ifc_revision or ifc_revision or "unspecified"
        refs.append(f"ifc:{observation.ifc_sha256}@{rev}#guid:{observation.global_id}")
    elif observation is not None:
        refs.append(f"ifc:guid:{observation.global_id}")
    if drawing_path is not None:
        rev = drawing_rev or "unspecified"
        digest = drawing_sha or drawing_path.name
        page = zone.page_number if zone is not None else None
        locator = f"page:{page}" if page is not None else "page:unknown"
        refs.append(f"drawing:{digest}@{rev}#{locator}")
    if annotation is not None:
        refs.append(f"sheet:{annotation.sheet_id}#{annotation.target_ref}")
    return ValidationIssue(
        rule_id=rule_id,
        severity=severity,
        message=message,
        ifc_entity=IFC_ENTITY,
        category=FindingCategory.CROSS_DOCUMENT,
        target_ref=annotation.target_ref if annotation is not None else None,
        property_set="Qto_WallBaseQuantities",
        property_name=QTO_WIDTH,
        operator=ComparisonOperator.EQUALS,
        expected_value=expected_value,
        observed_value=observed_value,
        unit=unit,
        element_guid=observation.global_id if observation is not None else None,
        problem_zone=zone,
        conflict_kind=conflict_kind,
        source_id="pd-rd-wall-width",
        evidence_modality="drawing+ifc",
        origin="deterministic",
        match_method="target_ref+qto_width",
        evidence_refs=tuple(dict.fromkeys(refs)),
        answer_nature="deterministic",
        gate_class="quality",
    )


def compare_drawing_length_to_ifc(
    *,
    annotations: Sequence[DrawingAnnotation],
    observations: Sequence[IfcQuantityObservation],
    drawing_sources: Sequence[DrawingSource] = (),
    ifc_revision: str | None = None,
    ifc_path: Path | None = None,
    ifc_sha256: str | None = None,
) -> DrawingIfcConsistencyResult:
    """Compare drawing thickness/width annotations to unique IFC wall Width QTO."""

    issues: list[ValidationIssue] = []
    length_anns = length_measure_annotations(annotations)
    sources_by_sheet = {
        (source.sheet_id or (source.path.stem.upper() if source.path is not None else "")): source
        for source in drawing_sources
    }

    for source in drawing_sources:
        if drawing_file_unsupported(source):
            suffix = source.path.suffix if source.path is not None else ""
            issues.append(
                _issue(
                    rule_id=RULE_UNSUPPORTED,
                    severity=Severity.WARNING,
                    message=(
                        "Невозможно проверить согласованность IFC и листа: "
                        f"формат {suffix or 'unknown'} не поддерживается этим пилотом "
                        "(не утверждение, что проект содержит нарушение)."
                    ),
                    conflict_kind=None,
                    drawing_source=source,
                    extra_evidence=("cannot_verify:unsupported_input",),
                )
            )

    if not length_anns and not issues:
        return DrawingIfcConsistencyResult(issues=(), capability=None, ran=False)

    mixed_kinds: list[ConflictKind] = []
    for source in drawing_sources:
        kind = mixed_revision_kind(ifc_revision, source.revision)
        if kind is not None:
            mixed_kinds.append(kind)

    if ConflictKind.VERSION_MISMATCH in mixed_kinds:
        issues.append(
            _issue(
                rule_id=RULE_REVISION_MIXED,
                severity=Severity.ERROR,
                message=(
                    "Смешанные ревизии IFC и документа: значения толщины не сравниваются "
                    "как комплект одной ревизии."
                ),
                conflict_kind=ConflictKind.VERSION_MISMATCH,
                drawing_source=drawing_sources[0] if drawing_sources else None,
                ifc_revision=ifc_revision,
                extra_evidence=(
                    f"ifc_revision:{ifc_revision or 'unspecified'}",
                    "drawing_revision:"
                    + (
                        drawing_sources[0].revision
                        if drawing_sources and drawing_sources[0].revision
                        else "unspecified"
                    ),
                ),
            )
        )
        return DrawingIfcConsistencyResult(
            issues=tuple(issues),
            capability=CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "IFC and drawing revisions differ; wall-width compare skipped",
            ),
            ran=True,
        )

    if ConflictKind.AMBIGUOUS_MAPPING in mixed_kinds:
        issues.append(
            _issue(
                rule_id=RULE_INCOMPLETE,
                severity=Severity.WARNING,
                message=(
                    "Ревизия указана только на одной стороне комплекта; "
                    "невозможно подтвердить, что IFC и лист одной ревизии "
                    "(не утверждение о нарушении)."
                ),
                conflict_kind=ConflictKind.AMBIGUOUS_MAPPING,
                drawing_source=drawing_sources[0] if drawing_sources else None,
                ifc_revision=ifc_revision,
                extra_evidence=("cannot_verify:one_sided_revision",),
            )
        )
        return DrawingIfcConsistencyResult(
            issues=tuple(issues),
            capability=CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "one-sided revision markers; wall-width compare skipped",
            ),
            ran=True,
        )

    if not length_anns:
        return DrawingIfcConsistencyResult(
            issues=tuple(issues),
            capability=CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "drawing input present but no comparable length annotation",
            )
            if issues
            else None,
            ran=bool(issues),
        )

    ran = True
    comparable = 0
    for annotation in length_anns:
        drawing_source = sources_by_sheet.get(annotation.sheet_id)
        if drawing_source is None and drawing_sources:
            drawing_source = drawing_sources[0]
        parsed = parse_annotation_length(annotation)
        if parsed is None:
            issues.append(
                _issue(
                    rule_id=RULE_INCOMPLETE,
                    severity=Severity.WARNING,
                    message=(
                        "Поле толщины/ширины на листе пустое или не разобрано; "
                        "не подставляется 0 и не считается успехом."
                    ),
                    conflict_kind=ConflictKind.UNPARSED_NUMERIC,
                    annotation=annotation,
                    drawing_source=drawing_source,
                    observed_value=annotation.observed_value,
                    unit=annotation.unit,
                    extra_evidence=("cannot_verify:missing_or_unparsed_drawing_value",),
                )
            )
            continue
        if is_unrestricted_target_ref(annotation.target_ref):
            issues.append(
                _issue(
                    rule_id=RULE_AMBIGUOUS,
                    severity=Severity.WARNING,
                    message=(
                        "Неоднозначное соответствие: аннотация без именного target_ref "
                        "не выдаётся как достоверное противоречие."
                    ),
                    conflict_kind=ConflictKind.AMBIGUOUS_MAPPING,
                    annotation=annotation,
                    drawing_source=drawing_source,
                    extra_evidence=("cannot_verify:unrestricted_target_ref",),
                )
            )
            continue
        matches = [
            item
            for item in observations
            if item.quantity_name.casefold() == QTO_WIDTH.casefold()
            and item.name.strip().casefold() == annotation.target_ref.strip().casefold()
        ]
        if not matches:
            issues.append(
                _issue(
                    rule_id=RULE_INCOMPLETE,
                    severity=Severity.WARNING,
                    message=(
                        f"В IFC нет однозначного {IFC_ENTITY} с Name/Tag "
                        f"{annotation.target_ref!r} и Qto Width; "
                        "проверка не завершена (не нарушение проекта)."
                    ),
                    conflict_kind=ConflictKind.AMBIGUOUS_MAPPING,
                    annotation=annotation,
                    drawing_source=drawing_source,
                    extra_evidence=("cannot_verify:no_unique_ifc_match",),
                )
            )
            continue
        if len(matches) > 1:
            guids = ",".join(item.global_id for item in matches)
            issues.append(
                _issue(
                    rule_id=RULE_AMBIGUOUS,
                    severity=Severity.WARNING,
                    message=(
                        f"Неоднозначное соответствие: {len(matches)} элементов "
                        f"{annotation.target_ref} в IFC; достоверное противоречие не выдаётся."
                    ),
                    conflict_kind=ConflictKind.AMBIGUOUS_MAPPING,
                    annotation=annotation,
                    drawing_source=drawing_source,
                    extra_evidence=(f"cannot_verify:ambiguous_ifc_match:{guids}",),
                )
            )
            continue
        observation = matches[0]
        if observation.value.si_value is None:
            issues.append(
                _issue(
                    rule_id=RULE_INCOMPLETE,
                    severity=Severity.WARNING,
                    message=("Qto Width в IFC не нормализуется в SI; значение не считается нулём."),
                    conflict_kind=ConflictKind.UNPARSED_NUMERIC,
                    annotation=annotation,
                    observation=observation,
                    drawing_source=drawing_source,
                    extra_evidence=("cannot_verify:ifc_width_not_si",),
                )
            )
            continue
        comparable += 1
        if si_compare(parsed, observation.value, epsilon=COMPARE_EPSILON_M):
            continue
        drawing_mm = parsed.si_value * 1000.0 if parsed.si_value is not None else None
        ifc_mm = (
            observation.value.si_value * 1000.0 if observation.value.si_value is not None else None
        )
        link = (
            f"Аннотация {annotation.target_ref} на листе {annotation.sheet_id} "
            f"сопоставлена IfcWall.Name/Tag={observation.name!r} "
            f"GlobalId={observation.global_id} по exact token match."
        )
        issues.append(
            _issue(
                rule_id=RULE_ID,
                severity=Severity.ERROR,
                message=(
                    "Противоречие между источниками (не нормативное замечание): "
                    f"лист {annotation.observed_value} {annotation.unit or ''} "
                    f"({drawing_mm:.3f} mm SI) vs IFC Qto_WallBaseQuantities.Width "
                    f"{observation.value.value} {observation.value.unit} "
                    f"({ifc_mm:.3f} mm SI). {link}"
                ),
                conflict_kind=ConflictKind.HARD_CONFLICT,
                annotation=annotation,
                observation=observation,
                expected_value=(
                    f"{observation.value.si_value * 1000.0:.3f} mm"
                    if observation.value.si_value is not None
                    else str(observation.value.value)
                ),
                observed_value=(
                    f"{parsed.si_value * 1000.0:.3f} mm"
                    if parsed.si_value is not None
                    else f"{annotation.observed_value} {annotation.unit or ''}".strip()
                ),
                unit="mm",
                drawing_source=drawing_source,
                ifc_revision=ifc_revision,
                extra_evidence=(
                    f"ifc_path:{ifc_path}" if ifc_path is not None else "ifc_path:unknown",
                    f"ifc_sha256:{ifc_sha256 or 'unknown'}",
                    f"drawing_value_si_m:{parsed.si_value}",
                    f"ifc_value_si_m:{observation.value.si_value}",
                    "finding_class:source_contradiction",
                ),
            )
        )

    if issues and comparable == 0:
        capability = CapabilityStatus(
            CapabilityState.NOT_VERIFIED,
            "wall-width compare did not complete a unique SI match",
        )
    else:
        capability = CapabilityStatus(
            CapabilityState.OK,
            "wall-width drawing↔IFC compare evaluated",
        )
    return DrawingIfcConsistencyResult(issues=tuple(issues), capability=capability, ran=ran)


def parser_failure_issue(source: DrawingSource, exc: BaseException) -> ValidationIssue:
    return ValidationIssue(
        rule_id=RULE_PARSER,
        severity=Severity.WARNING,
        message=(
            "Невозможно проверить лист: ошибка парсера "
            f"{type(exc).__name__}: {exc}. "
            "Это не утверждение, что проект содержит нарушение."
        ),
        category=FindingCategory.DRAWING_VALIDATION,
        source_id="pd-rd-wall-width",
        origin="deterministic",
        evidence_refs=(
            _rule_ref(),
            "cannot_verify:parser_error",
            f"claim_boundary:{CLAIM_BOUNDARY}",
        ),
        problem_zone=ProblemZone(
            sheet_id=source.sheet_id,
            page_number=1,
        ),
        answer_nature="deterministic",
        gate_class="quality",
    )


__all__ = [
    "CLAIM_BOUNDARY",
    "COMPARE_EPSILON_M",
    "DrawingIfcConsistencyResult",
    "IFC_ENTITY",
    "IfcQuantityObservation",
    "LENGTH_MEASURES",
    "QTO_WIDTH",
    "RULE_AMBIGUOUS",
    "RULE_ID",
    "RULE_INCOMPLETE",
    "RULE_PARSER",
    "RULE_REVISION_MIXED",
    "RULE_UNSUPPORTED",
    "RULE_VERSION",
    "compare_drawing_length_to_ifc",
    "drawing_file_unsupported",
    "length_measure_annotations",
    "mixed_revision_kind",
    "parse_annotation_length",
    "parser_failure_issue",
]
