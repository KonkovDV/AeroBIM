# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from samolet.domain.models import (
    ComparisonOperator,
    FindingCategory,
    ParsedRequirement,
    RuleScope,
    Severity,
    ValidationIssue,
)


class IfcOpenShellValidator:
    def validate(
        self,
        ifc_path: Path,
        requirements: Sequence[ParsedRequirement],
    ) -> list[ValidationIssue]:
        if not ifc_path.exists():
            raise FileNotFoundError(ifc_path)

        try:
            import ifcopenshell
            from ifcopenshell.util.element import get_psets
        except ModuleNotFoundError as exc:
            raise RuntimeError("Install ifcopenshell to run IFC validation") from exc

        model = ifcopenshell.open(str(ifc_path))
        issues: list[ValidationIssue] = []

        for requirement in requirements:
            if requirement.rule_scope is RuleScope.DRAWING_ANNOTATION:
                continue

            if not requirement.ifc_entity:
                continue

            matching_elements = list(model.by_type(requirement.ifc_entity))
            if requirement.target_ref:
                matching_elements = [
                    element for element in matching_elements if self._matches_target_ref(element, requirement.target_ref)
                ]

            if not matching_elements:
                issues.append(
                    ValidationIssue(
                        rule_id=requirement.rule_id,
                        severity=Severity.ERROR,
                        message=f"No elements found for entity {requirement.ifc_entity}",
                        ifc_entity=requirement.ifc_entity,
                        category=FindingCategory.IFC_VALIDATION,
                        target_ref=requirement.target_ref,
                        property_set=requirement.property_set,
                        property_name=requirement.property_name,
                        operator=requirement.operator,
                        expected_value=requirement.expected_value,
                        unit=requirement.unit,
                    )
                )
                continue

            if not requirement.property_set or not requirement.property_name:
                continue

            property_found = False
            for element in matching_elements:
                properties = get_psets(element)
                property_group = properties.get(requirement.property_set)
                if not isinstance(property_group, dict):
                    continue

                observed_value = property_group.get(requirement.property_name)
                if observed_value is None:
                    continue

                property_found = True
                if not self._matches_requirement(observed_value, requirement):
                    issues.append(
                        ValidationIssue(
                            rule_id=requirement.rule_id,
                            severity=Severity.ERROR,
                            message=(
                                f"Property {requirement.property_set}.{requirement.property_name} "
                                f"does not match the expected value"
                            ),
                            ifc_entity=requirement.ifc_entity,
                            category=FindingCategory.IFC_VALIDATION,
                            target_ref=requirement.target_ref,
                            property_set=requirement.property_set,
                            property_name=requirement.property_name,
                            operator=requirement.operator,
                            expected_value=requirement.expected_value,
                            observed_value=str(observed_value),
                            unit=requirement.unit,
                            element_guid=self._extract_guid(element),
                        )
                    )

            if not property_found:
                issues.append(
                    ValidationIssue(
                        rule_id=requirement.rule_id,
                        severity=Severity.ERROR,
                        message=(
                            f"Property {requirement.property_set}.{requirement.property_name} "
                            f"was not found on any {requirement.ifc_entity} elements"
                        ),
                        ifc_entity=requirement.ifc_entity,
                        category=FindingCategory.IFC_VALIDATION,
                        target_ref=requirement.target_ref,
                        property_set=requirement.property_set,
                        property_name=requirement.property_name,
                        operator=requirement.operator,
                        expected_value=requirement.expected_value,
                        unit=requirement.unit,
                    )
                )

        return issues

    def _extract_guid(self, element: Any) -> str | None:
        global_id = getattr(element, "GlobalId", None)
        return str(global_id) if global_id else None

    def _matches_target_ref(self, element: Any, target_ref: str) -> bool:
        normalized_target = target_ref.strip().lower()
        for attribute_name in ("GlobalId", "Name", "LongName", "Tag", "ObjectType", "Description"):
            value = getattr(element, attribute_name, None)
            if value is not None and str(value).strip().lower() == normalized_target:
                return True
        return False

    def _matches_requirement(self, observed_value: Any, requirement: ParsedRequirement) -> bool:
        if requirement.operator is ComparisonOperator.EXISTS:
            return observed_value is not None

        if requirement.expected_value is None:
            return observed_value is not None

        if requirement.rule_scope is RuleScope.IFC_QUANTITY or requirement.operator in {
            ComparisonOperator.GREATER_OR_EQUAL,
            ComparisonOperator.LESS_OR_EQUAL,
        }:
            observed_number = self._to_float(observed_value)
            expected_number = self._to_float(requirement.expected_value)
            if observed_number is None or expected_number is None:
                return str(observed_value) == requirement.expected_value
            if requirement.operator is ComparisonOperator.GREATER_OR_EQUAL:
                return observed_number >= expected_number
            if requirement.operator is ComparisonOperator.LESS_OR_EQUAL:
                return observed_number <= expected_number

        return str(observed_value) == requirement.expected_value

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(str(value).replace(",", ".").strip())
        except ValueError:
            return None
