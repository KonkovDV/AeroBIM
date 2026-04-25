from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from uuid import uuid4

from aerobim.domain.models import (
    ComparisonOperator,
    ConflictKind,
    DrawingAnnotation,
    DrawingAsset,
    DrawingSource,
    FindingCategory,
    ParsedRequirement,
    RuleScope,
    Severity,
    ToleranceConfig,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
    ValidationSummary,
)
from aerobim.domain.ports import (
    AuditReportStore,
    ClashDetector,
    DrawingAnalyzer,
    IdsValidator,
    IfcValidator,
    NarrativeRuleSynthesizer,
    RemarkGenerator,
    RequirementExtractor,
    VisionDrawingAnalyzer,
)

_VISION_DRAWING_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
_VISION_DRAWING_FORMATS = {"pdf", "png", "jpg", "jpeg", "webp", "image", "raster"}
_DRAWING_ASSET_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg"}
_OPENREBAR_REPORT_CONTRACT_ID = "OpenRebar.reinforcement.report.v1"
_OPENREBAR_WARNING_SEVERITY_CLASS: dict[str, str] = {
    "OPENREBAR-CONTRACT": "critical",
    "OPENREBAR-PROVENANCE-DIGEST": "critical",
    "OPENREBAR-PROVENANCE-REFERENCE-MISSING": "critical",
    "OPENREBAR-OPT-FALLBACK": "major",
    "OPENREBAR-OPT-STRATEGY": "major",
    "OPENREBAR-WASTE-METRIC-MISSING": "major",
    "OPENREBAR-WASTE-THRESHOLD": "major",
    "OPENREBAR-PROJECT-CODE": "minor",
}
_OPENREBAR_ENFORCED_ESCALATION_CLASSES = {"critical", "major"}
_CROSS_DOC_UNIT_TO_SI_FACTOR: dict[str, tuple[str, float]] = {
    "m": ("m", 1.0),
    "м": ("m", 1.0),
    "mm": ("m", 0.001),
    "мм": ("m", 0.001),
    "cm": ("m", 0.01),
    "см": ("m", 0.01),
    "ft": ("m", 0.3048),
    "feet": ("m", 0.3048),
    "foot": ("m", 0.3048),
    "in": ("m", 0.0254),
    "inch": ("m", 0.0254),
    "inches": ("m", 0.0254),
    "m2": ("m2", 1.0),
    "м2": ("m2", 1.0),
    "m²": ("m2", 1.0),
    "м²": ("m2", 1.0),
    "sqm": ("m2", 1.0),
    "sq.m": ("m2", 1.0),
    "m3": ("m3", 1.0),
    "м3": ("m3", 1.0),
    "m³": ("m3", 1.0),
    "м³": ("m3", 1.0),
}


def build_openrebar_provenance_digest(report_payload: Mapping[str, object]) -> str:
    canonical_payload = {
        "contractId": report_payload.get("contractId"),
        "schemaVersion": report_payload.get("schemaVersion"),
        "generatedAtUtc": report_payload.get("generatedAtUtc"),
        "isolineFileName": report_payload.get("isolineFileName"),
        "isolineFileFormat": report_payload.get("isolineFileFormat"),
        "metadata": report_payload.get("metadata"),
        "normativeProfile": report_payload.get("normativeProfile"),
        "analysisProvenance": report_payload.get("analysisProvenance"),
        "summary": report_payload.get("summary"),
    }
    normalized = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class AnalyzeProjectPackageUseCase:
    def __init__(
        self,
        requirement_extractor: RequirementExtractor,
        narrative_rule_synthesizer: NarrativeRuleSynthesizer,
        drawing_analyzer: DrawingAnalyzer,
        ifc_validator: IfcValidator,
        remark_generator: RemarkGenerator,
        audit_report_store: AuditReportStore,
        ids_validator: IdsValidator | None = None,
        vision_drawing_analyzer: VisionDrawingAnalyzer | None = None,
        tolerance: ToleranceConfig | None = None,
        clash_detector: ClashDetector | None = None,
        cross_doc_severity: str = "warning",
    ) -> None:
        self._requirement_extractor = requirement_extractor
        self._narrative_rule_synthesizer = narrative_rule_synthesizer
        self._drawing_analyzer = drawing_analyzer
        self._ifc_validator = ifc_validator
        self._ids_validator = ids_validator
        self._vision_drawing_analyzer = vision_drawing_analyzer
        self._remark_generator = remark_generator
        self._audit_report_store = audit_report_store
        self._tolerance = tolerance or ToleranceConfig()
        self._clash_detector = clash_detector
        _valid_severities = {"error", "warning", "info"}
        self._cross_doc_severity = Severity(
            cross_doc_severity if cross_doc_severity in _valid_severities else "warning"
        )

    def execute(self, request: ValidationRequest) -> ValidationReport:
        structured_requirements = list(
            self._requirement_extractor.extract(request.requirement_source)
        )
        synthesized_requirements = self._collect_synthesized_requirements(request)
        requirements = tuple([*structured_requirements, *synthesized_requirements])
        ids_issues = tuple(self._collect_ids_issues(request))
        if not requirements and request.ids_path is None:
            raise ValueError(
                "No requirements were extracted or synthesized from the provided sources"
            )

        drawing_annotations = tuple(self._collect_drawing_annotations(request))
        ifc_issues = (
            tuple(self._ifc_validator.validate(request.ifc_path, requirements))
            if requirements
            else ()
        )
        drawing_issues = tuple(
            self._validate_drawing_annotations(requirements, drawing_annotations)
        )
        drawing_assets = tuple(self._collect_drawing_assets(request))
        cross_document_issues = tuple(self._detect_cross_document_contradictions(requirements))
        reinforcement_provenance_issues = tuple(
            self._apply_openrebar_provenance_policy(
                self._collect_openrebar_provenance_issues(request),
                request.reinforcement_provenance_mode,
            )
        )
        clash_results = tuple(
            self._clash_detector.detect(request.ifc_path) if self._clash_detector else []
        )
        issues_with_remarks = tuple(
            self._attach_remarks(
                [
                    *ifc_issues,
                    *drawing_issues,
                    *cross_document_issues,
                    *reinforcement_provenance_issues,
                    *ids_issues,
                ]
            )
        )

        severity_counts = Counter(issue.severity for issue in issues_with_remarks)
        error_count = severity_counts[Severity.ERROR]
        warning_count = severity_counts[Severity.WARNING]

        report = ValidationReport(
            report_id=uuid4().hex,
            request_id=request.request_id,
            ifc_path=request.ifc_path,
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=requirements,
            issues=issues_with_remarks,
            summary=ValidationSummary(
                requirement_count=len(requirements),
                issue_count=len(issues_with_remarks),
                error_count=error_count,
                warning_count=warning_count,
                passed=error_count == 0,
                drawing_annotation_count=len(drawing_annotations),
                generated_remark_count=sum(
                    1 for issue in issues_with_remarks if issue.remark is not None
                ),
            ),
            drawing_annotations=drawing_annotations,
            drawing_assets=drawing_assets,
            clash_results=clash_results,
            project_name=request.project_name,
            discipline=request.discipline,
        )
        self._audit_report_store.save(report)
        persisted_report = self._audit_report_store.get(report.report_id)
        return persisted_report or report

    def _collect_ids_issues(self, request: ValidationRequest) -> list[ValidationIssue]:
        if request.ids_path is None:
            return []
        if self._ids_validator is None:
            raise RuntimeError("IDS validation requested but no ids validator is configured")
        return self._ids_validator.validate(request.ids_path, request.ifc_path)

    def _collect_openrebar_provenance_issues(
        self,
        request: ValidationRequest,
    ) -> list[ValidationIssue]:
        if request.reinforcement_report_path is None:
            return []

        report_path = request.reinforcement_report_path
        if not report_path.exists():
            raise FileNotFoundError(report_path)

        try:
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid OpenRebar reinforcement report JSON: {report_path}") from exc

        if not isinstance(report_payload, dict):
            raise ValueError("OpenRebar reinforcement report must be a JSON object")

        issues: list[ValidationIssue] = []
        contract_id = str(report_payload.get("contractId", "")).strip()
        metadata = report_payload.get("metadata")
        metadata_dict = metadata if isinstance(metadata, dict) else {}
        project_code = str(metadata_dict.get("projectCode", "")).strip()
        slab_id = str(metadata_dict.get("slabId", "")).strip() or None

        if contract_id != _OPENREBAR_REPORT_CONTRACT_ID:
            issues.append(
                ValidationIssue(
                    rule_id="OPENREBAR-CONTRACT",
                    severity=Severity.WARNING,
                    message=(
                        "OpenRebar report contractId is unexpected; downstream "
                        "integration guarantees may not hold."
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    target_ref=slab_id,
                    property_name="contractId",
                    expected_value=_OPENREBAR_REPORT_CONTRACT_ID,
                    observed_value=contract_id or "<missing>",
                )
            )

        optimization = report_payload.get("analysisProvenance")
        optimization_dict = optimization if isinstance(optimization, dict) else {}
        optimization_node = optimization_dict.get("optimization")
        optimization_payload = optimization_node if isinstance(optimization_node, dict) else {}
        fallback_solver_used = optimization_payload.get("anyFallbackMasterSolverUsed")
        master_problem_strategy = str(optimization_payload.get("masterProblemStrategy", "")).strip()

        if fallback_solver_used is True:
            issues.append(
                ValidationIssue(
                    rule_id="OPENREBAR-OPT-FALLBACK",
                    severity=Severity.WARNING,
                    message=(
                        "OpenRebar optimization used a fallback master solver; "
                        "waste metrics may deviate from the preferred HiGHS path."
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    target_ref=slab_id,
                    property_name=("analysisProvenance.optimization.anyFallbackMasterSolverUsed"),
                    expected_value="false",
                    observed_value="true",
                )
            )

        if "highs" not in master_problem_strategy.lower():
            issues.append(
                ValidationIssue(
                    rule_id="OPENREBAR-OPT-STRATEGY",
                    severity=Severity.WARNING,
                    message=(
                        "OpenRebar optimization master strategy does not indicate "
                        "HiGHS-backed solving."
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    target_ref=slab_id,
                    property_name="analysisProvenance.optimization.masterProblemStrategy",
                    expected_value="contains: highs",
                    observed_value=master_problem_strategy or "<missing>",
                )
            )

        if request.project_name and project_code:
            if request.project_name.strip().lower() != project_code.lower():
                issues.append(
                    ValidationIssue(
                        rule_id="OPENREBAR-PROJECT-CODE",
                        severity=Severity.WARNING,
                        message=(
                            "OpenRebar report projectCode differs from current "
                            "AeroBIM project context."
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=slab_id,
                        property_name="metadata.projectCode",
                        expected_value=request.project_name,
                        observed_value=project_code,
                    )
                )

        observed_digest = build_openrebar_provenance_digest(report_payload)
        if request.reinforcement_source_digest:
            expected_digest = request.reinforcement_source_digest.strip().lower()
            if expected_digest and expected_digest != observed_digest:
                issues.append(
                    ValidationIssue(
                        rule_id="OPENREBAR-PROVENANCE-DIGEST",
                        severity=Severity.WARNING,
                        message=(
                            "OpenRebar provenance digest mismatch: reinforcement "
                            "model may be stale relative to current source package."
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=slab_id,
                        property_name="reinforcementSourceDigest",
                        expected_value=expected_digest,
                        observed_value=observed_digest,
                    )
                )
        else:
            issues.append(
                ValidationIssue(
                    rule_id="OPENREBAR-PROVENANCE-REFERENCE-MISSING",
                    severity=Severity.WARNING,
                    message=(
                        "OpenRebar reference digest is missing; stale reinforcement "
                        "detection is disabled for this run."
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    target_ref=slab_id,
                    property_name="reinforcementSourceDigest",
                    expected_value="provided",
                    observed_value=observed_digest,
                )
            )

        threshold = request.reinforcement_waste_warning_threshold_percent
        if threshold is not None:
            summary_payload = report_payload.get("summary")
            summary_dict = summary_payload if isinstance(summary_payload, dict) else {}
            raw_total_waste = summary_dict.get("totalWastePercent")
            total_waste = (
                float(raw_total_waste)
                if isinstance(raw_total_waste, int | float)
                else self._to_float(str(raw_total_waste))
                if raw_total_waste is not None
                else None
            )

            if total_waste is None:
                issues.append(
                    ValidationIssue(
                        rule_id="OPENREBAR-WASTE-METRIC-MISSING",
                        severity=Severity.WARNING,
                        message=(
                            "OpenRebar report summary does not contain a parseable "
                            "totalWastePercent value."
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=slab_id,
                        property_name="summary.totalWastePercent",
                        expected_value="numeric",
                        observed_value="<missing>",
                    )
                )
            elif total_waste > threshold:
                issues.append(
                    ValidationIssue(
                        rule_id="OPENREBAR-WASTE-THRESHOLD",
                        severity=Severity.WARNING,
                        message=(
                            "OpenRebar total waste exceeds the configured AeroBIM "
                            "warning threshold."
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=slab_id,
                        property_name="summary.totalWastePercent",
                        expected_value=f"<= {threshold:g}",
                        observed_value=f"{total_waste:g}",
                        unit="%",
                    )
                )

        return issues

    def _apply_openrebar_provenance_policy(
        self,
        issues: Sequence[ValidationIssue],
        mode: str,
    ) -> list[ValidationIssue]:
        if mode != "enforced":
            return list(issues)

        escalated: list[ValidationIssue] = []
        for issue in issues:
            if issue.severity != Severity.WARNING:
                escalated.append(issue)
                continue

            severity_class = _OPENREBAR_WARNING_SEVERITY_CLASS.get(issue.rule_id, "major")
            if severity_class not in _OPENREBAR_ENFORCED_ESCALATION_CLASSES:
                escalated.append(issue)
                continue

            escalated.append(
                ValidationIssue(
                    rule_id=issue.rule_id,
                    severity=Severity.ERROR,
                    message=issue.message,
                    ifc_entity=issue.ifc_entity,
                    category=issue.category,
                    target_ref=issue.target_ref,
                    property_set=issue.property_set,
                    property_name=issue.property_name,
                    operator=issue.operator,
                    expected_value=issue.expected_value,
                    observed_value=issue.observed_value,
                    unit=issue.unit,
                    element_guid=issue.element_guid,
                    problem_zone=issue.problem_zone,
                    remark=issue.remark,
                )
            )

        return escalated

    def _collect_synthesized_requirements(
        self, request: ValidationRequest
    ) -> list[ParsedRequirement]:
        synthesized: list[ParsedRequirement] = []
        for source in (request.technical_spec_source, request.calculation_source):
            if source is None:
                continue
            if not source.text.strip() and source.path is None:
                continue
            synthesized.extend(self._narrative_rule_synthesizer.synthesize(source))
        return synthesized

    def _collect_drawing_annotations(self, request: ValidationRequest) -> list[DrawingAnnotation]:
        annotations: list[DrawingAnnotation] = []
        for drawing_source in request.drawing_sources:
            if self._has_structured_drawing_input(drawing_source):
                annotations.extend(self._drawing_analyzer.analyze(drawing_source))
            if self._is_vision_drawing_source(drawing_source):
                annotations.extend(self._collect_vision_annotations(drawing_source))
        return annotations

    def _collect_drawing_assets(self, request: ValidationRequest) -> list[DrawingAsset]:
        assets: list[DrawingAsset] = []
        for index, drawing_source in enumerate(request.drawing_sources, start=1):
            if drawing_source.path is None:
                continue
            suffix = drawing_source.path.suffix.lower()
            if suffix not in _DRAWING_ASSET_SUFFIXES:
                continue
            assets.append(
                DrawingAsset(
                    asset_id=f"drawing-{index:03d}",
                    sheet_id=drawing_source.sheet_id or drawing_source.path.stem.upper(),
                    page_number=1 if suffix != ".pdf" else None,
                    media_type="application/pdf" if suffix == ".pdf" else "image/png",
                    source_path=drawing_source.path,
                )
            )
        return assets

    def _collect_vision_annotations(
        self,
        drawing_source: DrawingSource,
    ) -> list[DrawingAnnotation]:
        if drawing_source.path is None:
            raise ValueError("Vision drawing analysis requires a drawing file path")
        if self._vision_drawing_analyzer is None:
            raise RuntimeError(
                "Vision drawing analysis requested but no vision drawing analyzer is configured"
            )
        return self._vision_drawing_analyzer.analyze_image(
            drawing_source.path,
            sheet_id=drawing_source.sheet_id,
        )

    def _has_structured_drawing_input(self, drawing_source: DrawingSource) -> bool:
        if drawing_source.text.strip():
            return True
        if drawing_source.path is None:
            return False
        return drawing_source.path.suffix.lower() not in _VISION_DRAWING_SUFFIXES

    def _is_vision_drawing_source(self, drawing_source: DrawingSource) -> bool:
        if drawing_source.format and drawing_source.format.lower() in _VISION_DRAWING_FORMATS:
            return True
        if drawing_source.path is None:
            return False
        return drawing_source.path.suffix.lower() in _VISION_DRAWING_SUFFIXES

    def _detect_cross_document_contradictions(
        self,
        requirements: Sequence[ParsedRequirement],
    ) -> list[ValidationIssue]:
        """Compare requirements from different sources for the same (entity, property).

        When two sources specify conflicting expected values for the same
        IFC entity + property pair, emit a CROSS_DOCUMENT issue.  Numeric
        values are compared with ISO 12006-3 ε-tolerance so that rounding
        differences (e.g. 3.0 m vs 3000 mm) do not produce false positives.
        The severity of emitted issues is controlled by ``self._cross_doc_severity``
        (configurable via ``AEROBIM_CROSS_DOC_SEVERITY``).  The ``conflict_kind``
        field classifies the nature of the conflict for downstream policy filtering.
        """
        issues: list[ValidationIssue] = []
        keyed: dict[tuple[str, str, str], list[ParsedRequirement]] = {}

        for req in requirements:
            if not req.ifc_entity or not req.property_name:
                continue
            key = (
                req.ifc_entity.upper(),
                (req.property_set or "").lower(),
                req.property_name.lower(),
            )
            keyed.setdefault(key, []).append(req)

        for (entity, property_set, prop), reqs in keyed.items():
            if len(reqs) < 2:
                continue
            seen: list[ParsedRequirement] = []
            for req in reqs:
                if req.expected_value is None:
                    continue
                for prev_req in seen:
                    if prev_req.source_kind == req.source_kind:
                        continue
                    if self._values_conflict(
                        prev_req.expected_value,
                        prev_req.unit,
                        req.expected_value,
                        req.unit,
                    ):
                        prev_val = (prev_req.expected_value or "").strip()
                        val = (req.expected_value or "").strip()
                        property_label = (
                            f"{entity}.{property_set}.{prop}"
                            if property_set
                            else f"{entity}.{prop}"
                        )
                        conflict_kind = self._classify_conflict_kind(
                            prev_req.expected_value,
                            prev_req.unit,
                            req.expected_value,
                            req.unit,
                        )
                        issues.append(
                            ValidationIssue(
                                rule_id=f"CROSS-DOC-{entity}-{prop}",
                                severity=self._cross_doc_severity,
                                message=(
                                    f"Cross-document contradiction: {property_label} "
                                    f"expects '{prev_val}' (from {prev_req.source_kind.value}) "
                                    f"but '{val}' (from {req.source_kind.value})"
                                ),
                                ifc_entity=entity,
                                category=FindingCategory.CROSS_DOCUMENT,
                                property_set=prev_req.property_set or req.property_set,
                                property_name=prop,
                                expected_value=prev_val,
                                observed_value=val,
                                conflict_kind=conflict_kind,
                            )
                        )
                seen.append(req)

        return issues

    def _classify_conflict_kind(
        self,
        value_a: str | None,
        unit_a: str | None,
        value_b: str | None,
        unit_b: str | None,
    ) -> ConflictKind:
        """Classify a detected cross-document conflict into a ``ConflictKind``.

        Decision order:
        1. UNIT_MISMATCH — same dimensionality but inconsistent unit encoding.
        2. HARD_CONFLICT — values differ after full SI normalisation.
        3. AMBIGUOUS_MAPPING — non-numeric values with no unit context.
        """
        if value_a is None or value_b is None:
            return ConflictKind.AMBIGUOUS_MAPPING

        a_num = self._to_float(value_a.strip())
        b_num = self._to_float(value_b.strip())

        if a_num is not None and b_num is not None:
            norm_a = self._normalize_cross_document_numeric_value(a_num, unit_a)
            norm_b = self._normalize_cross_document_numeric_value(b_num, unit_b)
            if norm_a is not None and norm_b is not None:
                val_a_si, unit_a_si = norm_a
                val_b_si, unit_b_si = norm_b
                if unit_a_si != unit_b_si:
                    return ConflictKind.UNIT_MISMATCH
                # Same SI dimension — values differ beyond tolerance
                return ConflictKind.HARD_CONFLICT
            # One or both units unknown — numeric conflict without SI context
            if unit_a and unit_b and unit_a.strip().lower() != unit_b.strip().lower():
                return ConflictKind.UNIT_MISMATCH
            return ConflictKind.HARD_CONFLICT

        # Non-numeric conflict
        return ConflictKind.HARD_CONFLICT

    def _values_conflict(
        self,
        value_a: str | None,
        unit_a: str | None,
        value_b: str | None,
        unit_b: str | None,
    ) -> bool:
        """Return True when two expected values are materially different.

        Numeric pairs are compared with ε-tolerance from ``ToleranceConfig``;
        non-numeric pairs use case-insensitive string comparison.
        """
        if value_a is None or value_b is None:
            return False
        a_str = value_a.strip()
        b_str = value_b.strip()
        if a_str.lower() == b_str.lower():
            return False

        a_num = self._to_float(a_str)
        b_num = self._to_float(b_str)
        if a_num is not None and b_num is not None:
            normalized_a = self._normalize_cross_document_numeric_value(a_num, unit_a)
            normalized_b = self._normalize_cross_document_numeric_value(b_num, unit_b)
            if normalized_a is not None and normalized_b is not None:
                value_a_si, unit_a_si = normalized_a
                value_b_si, unit_b_si = normalized_b
                if unit_a_si != unit_b_si:
                    return True
                eps = self._tolerance.epsilon_for_unit(unit_a_si)
                return abs(value_a_si - value_b_si) > eps

            eps = self._tolerance.epsilon_for_unit(unit_a or unit_b)
            return abs(a_num - b_num) > eps

        return True

    def _normalize_cross_document_numeric_value(
        self,
        value: float,
        unit: str | None,
    ) -> tuple[float, str] | None:
        if unit is None:
            return None
        normalized = _CROSS_DOC_UNIT_TO_SI_FACTOR.get(unit.strip().lower())
        if normalized is None:
            return None
        canonical_unit, factor = normalized
        return value * factor, canonical_unit

    def _validate_drawing_annotations(
        self,
        requirements: Sequence[ParsedRequirement],
        drawing_annotations: Sequence[DrawingAnnotation],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        drawing_requirements = [
            requirement
            for requirement in requirements
            if requirement.rule_scope is RuleScope.DRAWING_ANNOTATION
        ]

        for requirement in drawing_requirements:
            matching_annotations = [
                annotation
                for annotation in drawing_annotations
                if self._matches_annotation(requirement, annotation)
            ]
            if not matching_annotations:
                issues.append(
                    ValidationIssue(
                        rule_id=requirement.rule_id,
                        severity=Severity.ERROR,
                        message="No drawing annotations matched the normalized rule",
                        ifc_entity=requirement.ifc_entity,
                        category=FindingCategory.DRAWING_VALIDATION,
                        target_ref=requirement.target_ref,
                        property_name=requirement.property_name,
                        operator=requirement.operator,
                        expected_value=requirement.expected_value,
                        unit=requirement.unit,
                    )
                )
                continue

            for annotation in matching_annotations:
                if self._compare_values(
                    annotation.observed_value,
                    requirement.expected_value,
                    requirement.operator,
                    unit=requirement.unit or annotation.unit,
                ):
                    continue
                issues.append(
                    ValidationIssue(
                        rule_id=requirement.rule_id,
                        severity=Severity.ERROR,
                        message="Drawing annotation does not match the normalized rule",
                        ifc_entity=requirement.ifc_entity,
                        category=FindingCategory.DRAWING_VALIDATION,
                        target_ref=annotation.target_ref,
                        property_name=requirement.property_name,
                        operator=requirement.operator,
                        expected_value=requirement.expected_value,
                        observed_value=annotation.observed_value,
                        unit=requirement.unit or annotation.unit,
                        problem_zone=annotation.problem_zone,
                    )
                )

        return issues

    def _attach_remarks(self, issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
        enriched: list[ValidationIssue] = []
        for issue in issues:
            enriched.append(
                ValidationIssue(
                    rule_id=issue.rule_id,
                    severity=issue.severity,
                    message=issue.message,
                    ifc_entity=issue.ifc_entity,
                    category=issue.category,
                    target_ref=issue.target_ref,
                    property_set=issue.property_set,
                    property_name=issue.property_name,
                    operator=issue.operator,
                    expected_value=issue.expected_value,
                    observed_value=issue.observed_value,
                    unit=issue.unit,
                    element_guid=issue.element_guid,
                    problem_zone=issue.problem_zone,
                    remark=self._remark_generator.generate(issue),
                )
            )
        return enriched

    def _matches_annotation(
        self, requirement: ParsedRequirement, annotation: DrawingAnnotation
    ) -> bool:
        if (
            requirement.target_ref
            and requirement.target_ref.lower() != annotation.target_ref.lower()
        ):
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

    def _compare_values(
        self,
        observed_value: str | None,
        expected_value: str | None,
        operator: ComparisonOperator,
        unit: str | None = None,
    ) -> bool:
        """Compare observed vs expected using fuzzy ε-tolerance for numerics.

        ISO 12006-3 aligned: exact float equality is replaced with
        ``abs(a - b) <= ε`` where ε depends on the measurement unit.
        This eliminates false positives from millimetre-level rounding
        differences that are inevitable in real BIM data.
        """
        if operator is ComparisonOperator.EXISTS:
            return observed_value is not None
        if observed_value is None or expected_value is None:
            return False

        observed_number = self._to_float(observed_value)
        expected_number = self._to_float(expected_value)

        if observed_number is not None and expected_number is not None:
            eps = self._tolerance.epsilon_for_unit(unit)
            if operator is ComparisonOperator.GREATER_OR_EQUAL:
                return observed_number >= expected_number - eps
            if operator is ComparisonOperator.LESS_OR_EQUAL:
                return observed_number <= expected_number + eps
            # EQUALS with tolerance band
            return abs(observed_number - expected_number) <= eps

        # Non-numeric fallback: exact string comparison
        if operator in {ComparisonOperator.GREATER_OR_EQUAL, ComparisonOperator.LESS_OR_EQUAL}:
            return observed_value == expected_value
        return observed_value == expected_value

    def _to_float(self, raw: str) -> float | None:
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            return None
