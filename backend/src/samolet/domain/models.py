from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SourceKind(StrEnum):
    STRUCTURED_TEXT = "structured-text"
    INLINE_TEXT = "inline-text"
    TECHNICAL_SPECIFICATION = "technical-specification"
    CALCULATION = "calculation"
    DRAWING = "drawing"
    IDS = "ids"


class RuleScope(StrEnum):
    IFC_PROPERTY = "ifc-property"
    IFC_QUANTITY = "ifc-quantity"
    DRAWING_ANNOTATION = "drawing-annotation"


class ComparisonOperator(StrEnum):
    EQUALS = "eq"
    GREATER_OR_EQUAL = "gte"
    LESS_OR_EQUAL = "lte"
    EXISTS = "exists"


class FindingCategory(StrEnum):
    IFC_VALIDATION = "ifc-validation"
    IDS_VALIDATION = "ids-validation"
    DRAWING_VALIDATION = "drawing-validation"
    CROSS_DOCUMENT = "cross-document"


@dataclass(frozen=True)
class RequirementSource:
    text: str = ""
    path: Path | None = None
    source_kind: SourceKind = SourceKind.STRUCTURED_TEXT
    source_id: str | None = None


@dataclass(frozen=True)
class DrawingSource:
    text: str = ""
    path: Path | None = None
    sheet_id: str | None = None
    format: str | None = None


@dataclass(frozen=True)
class ProblemZone:
    sheet_id: str | None = None
    page_number: int | None = None
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    element_guid: str | None = None


@dataclass(frozen=True)
class GeneratedRemark:
    title: str
    body: str


@dataclass(frozen=True)
class DrawingAnnotation:
    annotation_id: str
    sheet_id: str
    target_ref: str
    measure_name: str
    observed_value: str
    unit: str | None = None
    problem_zone: ProblemZone | None = None
    source: str = "drawing-text"


@dataclass(frozen=True)
class ParsedRequirement:
    rule_id: str
    ifc_entity: str | None = None
    rule_scope: RuleScope = RuleScope.IFC_PROPERTY
    target_ref: str | None = None
    property_set: str | None = None
    property_name: str | None = None
    operator: ComparisonOperator = ComparisonOperator.EQUALS
    expected_value: str | None = None
    unit: str | None = None
    source: str = SourceKind.STRUCTURED_TEXT.value
    source_kind: SourceKind = SourceKind.STRUCTURED_TEXT
    evidence_text: str | None = None
    instructions: str | None = None
    evidence_modality: str | None = None


@dataclass(frozen=True)
class ValidationIssue:
    rule_id: str
    severity: Severity
    message: str
    ifc_entity: str | None = None
    category: FindingCategory = FindingCategory.IFC_VALIDATION
    target_ref: str | None = None
    property_set: str | None = None
    property_name: str | None = None
    operator: ComparisonOperator | None = None
    expected_value: str | None = None
    observed_value: str | None = None
    unit: str | None = None
    element_guid: str | None = None
    problem_zone: ProblemZone | None = None
    remark: GeneratedRemark | None = None


@dataclass(frozen=True)
class ValidationSummary:
    requirement_count: int
    issue_count: int
    error_count: int
    warning_count: int
    passed: bool
    drawing_annotation_count: int = 0
    generated_remark_count: int = 0


@dataclass(frozen=True)
class ValidationRequest:
    request_id: str
    ifc_path: Path
    requirement_source: RequirementSource
    technical_spec_source: RequirementSource | None = None
    calculation_source: RequirementSource | None = None
    drawing_sources: tuple[DrawingSource, ...] = ()
    ids_path: Path | None = None
    origin: str = "api"


@dataclass(frozen=True)
class ValidationReport:
    report_id: str
    request_id: str
    ifc_path: Path
    created_at: str
    requirements: tuple[ParsedRequirement, ...]
    issues: tuple[ValidationIssue, ...]
    summary: ValidationSummary
    drawing_annotations: tuple[DrawingAnnotation, ...] = ()


@dataclass(frozen=True)
class ReportSummaryEntry:
    report_id: str
    request_id: str
    created_at: str
    passed: bool
    issue_count: int


@dataclass(frozen=True)
class ClashResult:
    """A single spatial clash between two IFC elements."""

    element_a_guid: str
    element_b_guid: str
    clash_type: str  # "hard" | "clearance"
    distance: float  # penetration depth or clearance gap (metres)
    description: str
