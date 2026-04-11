from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from uuid import uuid4

from aerobim.domain.models import (
    ComparisonOperator,
    DrawingAnnotation,
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
        cross_document_issues = tuple(self._detect_cross_document_contradictions(requirements))
        clash_results = tuple(
            self._clash_detector.detect(request.ifc_path) if self._clash_detector else []
        )
        issues_with_remarks = tuple(
            self._attach_remarks(
                [*ifc_issues, *drawing_issues, *cross_document_issues, *ids_issues]
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
            clash_results=clash_results,
        )
        self._audit_report_store.save(report)
        return report

    def _collect_ids_issues(self, request: ValidationRequest) -> list[ValidationIssue]:
        if request.ids_path is None:
            return []
        if self._ids_validator is None:
            raise RuntimeError("IDS validation requested but no ids validator is configured")
        return self._ids_validator.validate(request.ids_path, request.ifc_path)

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
        IFC entity + property pair, emit a CROSS_DOCUMENT issue.
        """
        issues: list[ValidationIssue] = []
        keyed: dict[tuple[str, str], list[ParsedRequirement]] = {}

        for req in requirements:
            if not req.ifc_entity or not req.property_name:
                continue
            key = (req.ifc_entity.upper(), req.property_name.lower())
            keyed.setdefault(key, []).append(req)

        for (entity, prop), reqs in keyed.items():
            if len(reqs) < 2:
                continue
            seen_values: dict[str, ParsedRequirement] = {}
            for req in reqs:
                if req.expected_value is None:
                    continue
                val = req.expected_value.strip()
                if val in seen_values:
                    continue
                for prev_val, prev_req in seen_values.items():
                    if prev_req.source_kind == req.source_kind:
                        continue
                    issues.append(
                        ValidationIssue(
                            rule_id=f"CROSS-DOC-{entity}-{prop}",
                            severity=Severity.WARNING,
                            message=(
                                f"Cross-document contradiction: {entity}.{prop} "
                                f"expects '{prev_val}' (from {prev_req.source_kind.value}) "
                                f"but '{val}' (from {req.source_kind.value})"
                            ),
                            ifc_entity=entity,
                            category=FindingCategory.CROSS_DOCUMENT,
                            property_name=prop,
                            expected_value=prev_val,
                            observed_value=val,
                        )
                    )
                seen_values[val] = req

        return issues

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
