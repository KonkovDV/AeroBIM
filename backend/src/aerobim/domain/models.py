from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

from aerobim.domain.norm_assist import IdsCompileDraft
from aerobim.domain.quantity import QuantityValue

DocStatus = Literal["WIP", "Shared", "Published", "Archived"]
NormApprovalStatus = Literal["synthetic", "draft", "customer_approved"]


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


class RulePackStatus(StrEnum):
    """Approval state of a machine-readable acceptance-criteria pack."""

    SYNTHETIC_TEMPLATE = "synthetic-template"
    DRAFT = "draft"
    APPROVED = "approved"
    RETIRED = "retired"


def approval_status_from_pack(status: RulePackStatus) -> NormApprovalStatus:
    """Map pack manifest status onto the jury-facing approval badge vocabulary."""

    if status is RulePackStatus.APPROVED:
        return "customer_approved"
    if status is RulePackStatus.DRAFT:
        return "draft"
    return "synthetic"


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
    SPATIAL = "spatial"
    """Geometry / clearance / clash predicates — never IDS alphanumeric facets."""


class CapabilityState(StrEnum):
    """Runtime status of an optional validation capability."""

    OK = "ok"
    SKIPPED = "skipped"
    FAILED = "failed"
    MISSING = "missing"
    """Declared product gap — never treat as silent PASS."""
    NOT_VERIFIED = "not_verified"
    """Scaffold or unproven capability (e.g. MEP system clash)."""
    NOT_IMPLEMENTED = "not_implemented"
    """Explicit non-delivery (e.g. independent calculation correctness)."""


@dataclass(frozen=True)
class CapabilityStatus:
    status: CapabilityState
    reason: str | None = None
    external_ref: str | None = None
    """Optional external certificate / validation-request id (e.g. bSI public_id)."""


@dataclass(frozen=True)
class ReportCapabilities:
    """Explicit capability outcomes so silent degradation cannot look like PASS."""

    clash: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "clash detection not evaluated"
    )
    ids: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "IDS validation not requested"
    )
    ifc_validation: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "IFC property validation not evaluated"
    )
    unit_scale: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "IFC unit scale not evaluated"
    )
    raster: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "raster drawing analysis not evaluated"
    )
    ifc_schema: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "IFC schema pre-gate not evaluated"
    )
    norm_rule_packs: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "norm rule packs not requested"
    )
    section_pairing: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "PD/RD section pairing not requested"
    )
    dwg_dxf: CapabilityStatus = CapabilityStatus(
        CapabilityState.MISSING, "DWG/DXF native analysis not implemented"
    )
    cv_human_level: CapabilityStatus = CapabilityStatus(
        CapabilityState.MISSING, "Human-level CV/drawing understanding not implemented"
    )
    mep_system_clash: CapabilityStatus = CapabilityStatus(
        CapabilityState.NOT_VERIFIED,
        "MEP system graph provider DI-wired but unconfigured (MEP-CLASH-001); "
        "federated MEP IFC + scope memo required",
    )
    calculation_match: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "numeric calculation match not evaluated"
    )
    calculation_correctness: CapabilityStatus = CapabilityStatus(
        CapabilityState.NOT_IMPLEMENTED,
        "Independent calculation correctness verification not implemented",
    )
    quantity: CapabilityStatus = CapabilityStatus(
        CapabilityState.SKIPPED, "quantity consistency not evaluated"
    )


class ConflictKind(StrEnum):
    """Semantic classification of cross-document contradiction kind.

    Assigned in single-request analysis: HARD, UNIT_MISMATCH, SOFT, AMBIGUOUS.
    STAGE_MISMATCH / VERSION_MISMATCH are reserved for multi-package CDE compare.
    """

    HARD_CONFLICT = "hard-conflict"
    """Two sources specify materially different values for the same property
    after unit normalisation, with no plausible non-conflicting interpretation."""

    UNIT_MISMATCH = "unit-mismatch"
    """Values appear to conflict but the primary driver is inconsistent or
    ambiguous unit encoding between source documents."""

    STAGE_MISMATCH = "stage-mismatch"
    """Reserved: sources belong to different delivery stages (e.g. SD vs DD)."""

    VERSION_MISMATCH = "version-mismatch"
    """Same logical document compared across distinct revisions (ingestion guard)."""

    SOFT_CONFLICT_WITHIN_TOLERANCE = "soft-conflict-within-tolerance"
    """Numeric values differ in presentation but SI comparison is within ε."""

    AMBIGUOUS_MAPPING = "ambiguous-mapping"
    """Property names or entity references are too ambiguous to determine whether
    the two requirements address the same physical property."""


@dataclass(frozen=True)
class RequirementSource:
    text: str = ""
    path: Path | None = None
    source_kind: SourceKind = SourceKind.STRUCTURED_TEXT
    source_id: str | None = None
    revision: str | None = None
    stage: str | None = None
    doc_type: str | None = None
    sha256: str | None = None
    doc_status: str | None = None


@dataclass(frozen=True)
class DrawingSource:
    text: str = ""
    path: Path | None = None
    sheet_id: str | None = None
    format: str | None = None
    revision: str | None = None
    sha256: str | None = None
    doc_type: str | None = None


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
class DrawingRegionRef:
    """Normalized drawing region for UI highlight overlays (OCR/detector/VLM)."""

    sheet_id: str
    bbox_xyxy: tuple[float, float, float, float]
    confidence: float
    modality: str  # ocr | detector | vlm | vector
    hitl_required: bool = False
    """I8c: low-confidence / unmatched region queued for expert review."""
    hitl_reason: str | None = None
    coordinate_system: str | None = None
    """Explicit coordinate system, e.g. ``page-pixel`` or ``normalized-0-1``."""
    page_width: float | None = None
    page_height: float | None = None


@dataclass(frozen=True)
class DivergenceRecord:
    """Audit when advisory AI contradicts or invents a finding vs the engine."""

    finding_key: str
    engine_verdict: str
    advisory_verdict: str
    resolution: Literal["engine_wins"] = "engine_wins"


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
    confidence: float | None = None
    """Extraction confidence in [0.0, 1.0]. None means uncalibrated / legacy."""
    quantity: QuantityValue | None = None
    bsdd_uri: str | None = None
    norm_source: str | None = None
    """Human-readable norm identifier, e.g. ``СП 54.13330``."""
    norm_edition: str | None = None
    """Edition / year of the cited norm."""
    norm_clause: str | None = None
    """Clause / item reference inside the norm."""
    approval_status: NormApprovalStatus | None = None
    """Pack-level approval badge stamped onto each rule (default synthetic)."""
    approval_ref: str | None = None
    """Customer approval id / scope memo reference; required when customer_approved."""


@dataclass(frozen=True)
class NormRulePack:
    """Validated rule-pack metadata plus deterministic parsed requirements.

    ``confidence`` on individual rules describes extraction certainty only.  The
    pack status remains the authority for whether the criteria were approved by
    a customer; loading a draft or synthetic template does not make it normative.
    """

    pack_id: str
    version: str
    title: str
    typology: str
    disciplines: tuple[str, ...]
    status: RulePackStatus
    rules: tuple[ParsedRequirement, ...]
    source_path: Path
    sha256: str
    approval_reference: str | None = None


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
    priority: int = 0
    """Computed priority score for expert reviewer workflow.
    Higher = more urgent. Derived from severity + category + conflict_kind."""
    source_id: str | None = None
    """Identifier of the source document or container that produced this issue.
    Maps to RequirementSource.source_id for traceability."""
    evidence_modality: str | None = None
    """Modality of the evidence that triggered this issue (e.g. "structured-text",
    "drawing", "technical-specification"). Maps to ParsedRequirement.evidence_modality."""
    confidence: float | None = None
    """Extraction confidence in [0.0, 1.0]. None means uncalibrated / legacy."""
    norm_source: str | None = None
    norm_edition: str | None = None
    norm_clause: str | None = None
    approval_status: NormApprovalStatus | None = None
    approval_ref: str | None = None
    rase_elements: tuple[str, ...] = ()
    """Advisory R/A/S/E tags (I8b); never drives summary.passed."""
    finding_id: str | None = None
    """Stable finding identity required before persistence."""
    evidence_refs: tuple[str, ...] = ()
    """Opaque evidence pointers (source@rev#locator). Empty is not persistable."""
    tenant_id: str | None = None
    project_id: str | None = None
    origin: Literal["deterministic", "advisory"] | None = None
    """Contour ownership: deterministic engine vs advisory AI. Never drives passed."""
    match_method: str | None = None
    """Cross-document match method, e.g. ``entity+pset+prop`` or ``entity+prop``."""


def issue_from_requirement(
    requirement: ParsedRequirement,
    *,
    severity: Severity,
    message: str,
    category: FindingCategory = FindingCategory.IFC_VALIDATION,
    observed_value: str | None = None,
    element_guid: str | None = None,
    problem_zone: ProblemZone | None = None,
    ifc_entity: str | None = None,
    target_ref: str | None = None,
    property_set: str | None = None,
    property_name: str | None = None,
    unit: str | None = None,
) -> ValidationIssue:
    """Build an issue that carries requirement→finding norm provenance."""

    from aerobim.domain.rase import infer_rase_elements

    return ValidationIssue(
        rule_id=requirement.rule_id,
        severity=severity,
        message=message,
        ifc_entity=ifc_entity if ifc_entity is not None else requirement.ifc_entity,
        category=category,
        target_ref=target_ref if target_ref is not None else requirement.target_ref,
        property_set=property_set if property_set is not None else requirement.property_set,
        property_name=property_name if property_name is not None else requirement.property_name,
        operator=requirement.operator,
        expected_value=requirement.expected_value,
        observed_value=observed_value,
        unit=unit if unit is not None else requirement.unit,
        element_guid=element_guid,
        problem_zone=problem_zone,
        source_id=requirement.source,
        evidence_modality=requirement.evidence_modality,
        confidence=requirement.confidence,
        norm_source=requirement.norm_source,
        norm_edition=requirement.norm_edition,
        norm_clause=requirement.norm_clause,
        approval_status=requirement.approval_status,
        approval_ref=requirement.approval_ref,
        rase_elements=infer_rase_elements(requirement),
    )


def compute_issue_priority(issue: ValidationIssue, profile: str = "default") -> int:
    """Compute reviewer priority (delegates to ``review_priority`` module)."""
    from aerobim.domain.review_priority import compute_issue_priority as _score

    return _score(issue, profile=profile)


@dataclass(frozen=True)
class ValidationSummary:
    requirement_count: int
    issue_count: int
    error_count: int
    warning_count: int
    passed: bool
    drawing_annotation_count: int = 0
    generated_remark_count: int = 0
    authoritative: bool = True
    """False when soft-profile ``passed`` must not be treated as Shared-gate production verdict."""


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
    stage: str | None = None
    information_container_id: str | None = None
    revision: str | None = None
    doc_status: DocStatus | None = None
    norm_rule_pack_paths: tuple[Path, ...] = ()
    pd_section_path: Path | None = None
    rd_section_path: Path | None = None
    tenant_id: str | None = None
    project_id: str | None = None


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
    capabilities: ReportCapabilities | None = None
    schema_validation_request_id: str | None = None
    """bSI Validation Service ``public_id`` (or local schema pack id) when submitted."""
    project_name: str | None = None
    discipline: str | None = None
    stage: str | None = None
    information_container_id: str | None = None
    revision: str | None = None
    doc_status: DocStatus | None = None
    tenant_id: str | None = None
    project_id: str | None = None
    divergences: tuple[DivergenceRecord, ...] = ()
    """DeterminismGate audit trail; never flips summary.passed alone."""
    advisory_ids_draft: IdsCompileDraft | None = None
    """Agent/compiler IDS draft — advisory until human promotes to ids_path."""
    drawing_regions: tuple[DrawingRegionRef, ...] = ()
    """Multimodal/OCR region refs for frontend highlight overlays."""
    schema_version: str = "1.0.0"
    """Persisted report schema version for backward-compatible reload/migrations."""


@dataclass(frozen=True)
class ReportListFilters:
    project: str | None = None
    discipline: str | None = None
    passed: bool | None = None
    tenant_id: str | None = None
    """When set, stores must scope results to this tenant (BOLA / soft-ACL honesty)."""


@dataclass(frozen=True)
class ReportSummaryEntry:
    report_id: str
    request_id: str
    created_at: str
    passed: bool
    issue_count: int
    project_name: str | None = None
    discipline: str | None = None
    tenant_id: str | None = None


@dataclass(frozen=True)
class ReviewEvent:
    """Human-in-the-loop review telemetry (W3.5) — never affects ``summary.passed``."""

    event_id: str
    report_id: str
    event_type: Literal[
        "opened",
        "accepted",
        "rejected",
        "edited_remark",
        "edited",
        "triaged",
        "norm_rule_proposed",
        "norm_rule_edited",
        "drawing_region_escalated",
        "escalated",
        "waived",
        "superseded",
    ]
    created_at: str
    issue_rule_id: str | None = None
    actor: str | None = None
    note: str | None = None
    latency_ms: int | None = None
    """Milliseconds from report open to this event when measurable."""
    pack_id: str | None = None
    """Optional norm-pack id for HITL rule-pack events (P0.3)."""
    resulting_pack_version: str | None = None
    target_approval_status: NormApprovalStatus | None = None
    approval_ref: str | None = None
    rule_diff_json: str | None = None
    """JSON object describing the proposed/edited rule fields."""
    idempotency_key: str | None = None
    """Stable key for de-duplicating system escalations across re-analysis."""
    sequence_number: int | None = None
    """Monotonic per-report append order (1-based)."""
    previous_state: str | None = None
    resulting_state: str | None = None
    finding_id: str | None = None
    """Optional finding this review event attaches to."""


@dataclass(frozen=True)
class NormPackVersionInfo:
    """Immutable norm-pack version pointer (ObjectStore-backed)."""

    pack_id: str
    version: str
    object_key: str
    created_at: str
    created_by: str | None = None
    parent_version: str | None = None
    approval_status: NormApprovalStatus | None = None
    approval_ref: str | None = None
    tenant_id: str | None = None
    """Owning tenant; versions are namespaced per tenant under ACL."""


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


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
    idempotency_key: str | None = None
    """Client-supplied key: create returns the existing non-terminal job when present."""
    heartbeat_at: str | None = None
    lease_expires_at: str | None = None
    retry_count: int = 0
    stage_progress: str | None = None
    cancel_requested: bool = False
    tenant_id: str | None = None
    """Owning tenant; required for object ACL on job get/cancel."""


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
