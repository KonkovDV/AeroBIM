"""Drawing annotation validation against normalized rules (extracted from use case).

ISO 12006-3 aligned comparison: exact float equality is replaced with
``abs(a - b) <= ε`` where ε depends on the measurement unit.
"""

from __future__ import annotations

from collections.abc import Sequence

from aerobim.application.services.cross_document_contradictions import to_float
from aerobim.domain.models import (
    ComparisonOperator,
    DrawingAnnotation,
    FindingCategory,
    ParsedRequirement,
    RuleScope,
    Severity,
    ToleranceConfig,
    ValidationIssue,
    issue_from_requirement,
)
from aerobim.domain.quantity import parse_quantity, si_compare


class DrawingAnnotationValidator:
    """Validate drawing annotations against DRAWING_ANNOTATION scoped rules."""

    def __init__(self, tolerance: ToleranceConfig) -> None:
        self._tolerance = tolerance

    def validate(
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
                if self.matches_annotation(requirement, annotation)
            ]
            if not matching_annotations:
                issues.append(
                    issue_from_requirement(
                        requirement,
                        severity=Severity.ERROR,
                        message="No drawing annotations matched the normalized rule",
                        category=FindingCategory.DRAWING_VALIDATION,
                    )
                )
                continue

            for annotation in matching_annotations:
                if self.compare_values(
                    annotation.observed_value,
                    requirement.expected_value,
                    requirement.operator,
                    unit=requirement.unit or annotation.unit,
                ):
                    continue
                issues.append(
                    issue_from_requirement(
                        requirement,
                        severity=Severity.ERROR,
                        message="Drawing annotation does not match the normalized rule",
                        category=FindingCategory.DRAWING_VALIDATION,
                        target_ref=annotation.target_ref,
                        observed_value=annotation.observed_value,
                        problem_zone=annotation.problem_zone,
                        unit=requirement.unit or annotation.unit,
                    )
                )

        return issues

    def matches_annotation(
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

    def compare_values(
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

        observed_number = to_float(observed_value)
        expected_number = to_float(expected_value)

        if observed_number is not None and expected_number is not None:
            observed_q = parse_quantity(observed_number, unit or "")
            expected_q = parse_quantity(expected_number, unit or "")
            if (
                observed_q.ucum_code
                and expected_q.ucum_code
                and observed_q.dimension == expected_q.dimension
                and observed_q.si_value is not None
                and expected_q.si_value is not None
            ):
                # ToleranceConfig ε is expressed in the declared unit; scale to SI.
                eps_native = self._tolerance.epsilon_for_unit(unit)
                scale = abs(observed_q.si_value / observed_number) if observed_number else 1.0
                eps_si = eps_native * scale
                if operator is ComparisonOperator.GREATER_OR_EQUAL:
                    return observed_q.si_value >= expected_q.si_value - eps_si
                if operator is ComparisonOperator.LESS_OR_EQUAL:
                    return observed_q.si_value <= expected_q.si_value + eps_si
                return si_compare(observed_q, expected_q, epsilon=eps_si)

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
