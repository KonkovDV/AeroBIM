# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from aerobim.domain.models import (
    ComparisonOperator,
    FindingCategory,
    ParsedRequirement,
    RuleScope,
    Severity,
    ToleranceConfig,
    ValidationIssue,
)


class IfcOpenShellValidator:
    def __init__(self, tolerance: ToleranceConfig | None = None) -> None:
        self._tolerance = tolerance or ToleranceConfig()

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
        entity_cache: dict[str, tuple[Any, ...]] = {}
        target_cache: dict[tuple[str, str], tuple[Any, ...]] = {}
        pset_cache: dict[object, dict[str, Any]] = {}

        for requirement in requirements:
            if requirement.rule_scope is RuleScope.DRAWING_ANNOTATION:
                continue

            if not requirement.ifc_entity:
                continue

            matching_elements = self._get_matching_elements(
                model,
                requirement.ifc_entity,
                requirement.target_ref,
                entity_cache,
                target_cache,
            )

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
                properties = self._get_element_psets(element, get_psets, pset_cache)
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

    def _get_matching_elements(
        self,
        model: Any,
        ifc_entity: str,
        target_ref: str | None,
        entity_cache: dict[str, tuple[Any, ...]],
        target_cache: dict[tuple[str, str], tuple[Any, ...]],
    ) -> list[Any]:
        entity_key = ifc_entity.strip().upper()
        elements = entity_cache.get(entity_key)
        if elements is None:
            elements = tuple(model.by_type(ifc_entity))
            entity_cache[entity_key] = elements

        if not target_ref:
            return list(elements)

        target_key = (entity_key, target_ref.strip().lower())
        filtered_elements = target_cache.get(target_key)
        if filtered_elements is None:
            filtered_elements = tuple(
                element for element in elements if self._matches_target_ref(element, target_ref)
            )
            target_cache[target_key] = filtered_elements
        return list(filtered_elements)

    def _get_element_psets(
        self,
        element: Any,
        get_psets: Any,
        pset_cache: dict[object, dict[str, Any]],
    ) -> dict[str, Any]:
        cache_key = self._element_cache_key(element)
        properties = pset_cache.get(cache_key)
        if properties is None:
            properties = get_psets(element)
            pset_cache[cache_key] = properties
        return properties

    def _element_cache_key(self, element: Any) -> object:
        element_id = getattr(element, "id", None)
        if callable(element_id):
            try:
                return ("id", element_id())
            except TypeError:
                pass

        global_id = getattr(element, "GlobalId", None)
        if global_id is not None:
            return ("guid", str(global_id))

        return ("object", id(element))

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

        observed_number = self._to_float(observed_value)
        expected_number = self._to_float(requirement.expected_value)

        if observed_number is not None and expected_number is not None:
            eps = self._tolerance.epsilon_for_unit(requirement.unit)
            if requirement.operator is ComparisonOperator.GREATER_OR_EQUAL:
                return observed_number >= expected_number - eps
            if requirement.operator is ComparisonOperator.LESS_OR_EQUAL:
                return observed_number <= expected_number + eps
            # EQUALS: tolerance band |obs - exp| <= ε
            return abs(observed_number - expected_number) <= eps

        # Non-numeric fallback: exact string comparison
        return str(observed_value) == requirement.expected_value

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(str(value).replace(",", ".").strip())
        except ValueError:
            return None
