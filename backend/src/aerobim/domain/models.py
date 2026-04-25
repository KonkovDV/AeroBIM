from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal


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


class ConflictKind(StrEnum):
    """Semantic classification of cross-document contradiction kind.

    Distinguishes genuine conflicts from artefacts of unit encoding, lifecycle
    stage, versioning, or ambiguous property mapping — so consumers can apply
    appropriate policies per kind rather than treating all contradictions equally.
    """

    HARD_CONFLICT = "hard-conflict"
    """Two sources specify materially different values for the same property
    after unit normalisation, with no plausible non-conflicting interpretation."""

    UNIT_MISMATCH = "unit-mismatch"
    """Values appear to conflict but the primary driver is inconsistent or
    ambiguous unit encoding between source documents."""

    STAGE_MISMATCH = "stage-mismatch"
    """Sources belong to different delivery stages (e.g. SD vs DD vs CD);
    contradiction may be intentional progression rather than an error."""

    VERSION_MISMATCH = "version-mismatch"
    """Sources carry explicit revision/version markers that differ; the conflict
    may resolve once both documents are updated to the same revision."""

    SOFT_CONFLICT_WITHIN_TOLERANCE = "soft-conflict-within-tolerance"
    """Numeric values differ but the difference falls within the configured
    ε-tolerance — flagged for visibility but not blocking."""

    AMBIGUOUS_MAPPING = "ambiguous-mapping"
    """Property names or entity references are too ambiguous to determine whether
    the two requirements address the same physical property."""


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
class DrawingAsset:
    asset_id: str
    sheet_id: str
    page_number: int | None = None
    media_type: str = "image/png"
    coordinate_width: float | None = None
    coordinate_height: float | None = None
    stored_filename: str | None = None
    object_key: str | None = None
    source_path: Path | None = None


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
    conflict_kind: ConflictKind | None = None
    """Populated for CROSS_DOCUMENT findings; classifies the nature of the
    contradiction so consumers can apply severity policies per conflict class."""


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
    reinforcement_report_path: Path | None = None
    reinforcement_source_digest: str | None = None
    reinforcement_waste_warning_threshold_percent: float | None = None
    reinforcement_provenance_mode: Literal["advisory", "enforced"] = "advisory"
    origin: str = "api"
    project_name: str | None = None
    discipline: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    report_id: str
    request_id: str
    ifc_path: Path
    created_at: str
    requirements: tuple[ParsedRequirement, ...]
    issues: tuple[ValidationIssue, ...]
    summary: ValidationSummary
    ifc_object_key: str | None = None
    drawing_annotations: tuple[DrawingAnnotation, ...] = ()
    drawing_assets: tuple[DrawingAsset, ...] = ()
    clash_results: tuple[ClashResult, ...] = ()
    project_name: str | None = None
    discipline: str | None = None


@dataclass(frozen=True)
class ReportSummaryEntry:
    report_id: str
    request_id: str
    created_at: str
    passed: bool
    issue_count: int
    project_name: str | None = None
    discipline: str | None = None


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class AnalyzeProjectPackageJob:
    job_id: str
    request_id: str
    status: JobStatus
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    report_id: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ClashResult:
    """A single spatial clash between two IFC elements."""

    element_a_guid: str
    element_b_guid: str
    clash_type: str  # "hard" | "clearance"
    distance: float  # penetration depth or clearance gap (metres)
    description: str


@dataclass(frozen=True)
class ToleranceConfig:
    """ISO 12006-3 aligned dimensional tolerance for numeric comparisons.

    In construction, exact float equality is meaningless due to measurement
    precision, rounding, and coordinate system differences.  This config
    controls the ε-band used by comparison operators.

    Defaults:
      - length_epsilon:          1 mm  = 0.001 m  (ISO 1101 general tolerance)
      - imperial_length_epsilon: 0.003           (small feet/inch tolerance band)
      - area_epsilon:            0.01 m²         (sub-centimetre precision)
      - angle_epsilon:           0.1             (degrees/radians project-level band)
      - default_epsilon:         1e-6            (dimensionless / fallback)
    """

    length_epsilon: float = 0.001
    imperial_length_epsilon: float = 0.003
    area_epsilon: float = 0.01
    angle_epsilon: float = 0.1
    default_epsilon: float = 1e-6

    def epsilon_for_unit(self, unit: str | None) -> float:
        """Return the appropriate ε based on the measurement unit."""
        if unit is None:
            return self.default_epsilon
        normalised = unit.strip().lower()
        if normalised in {"m", "м", "mm", "мм", "cm", "см"}:
            return self.length_epsilon
        if normalised in {"ft", "feet", "foot", "in", "inch", "inches"}:
            return self.imperial_length_epsilon
        if normalised in {"m2", "м2", "sqm", "sq.m", "m²", "м²"}:
            return self.area_epsilon
        if normalised in {"deg", "degree", "degrees", "°", "rad", "radian", "radians"}:
            return self.angle_epsilon
        return self.default_epsilon
