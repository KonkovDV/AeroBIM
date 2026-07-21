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
    issue_from_requirement,
)

# Maps requirement unit string → (IFC unit type, factor to convert that unit to SI).
_UNIT_TO_SI_FACTOR: dict[str, tuple[str, float]] = {
    # length → metres
    "m": ("LENGTHUNIT", 1.0),
    "м": ("LENGTHUNIT", 1.0),
    "mm": ("LENGTHUNIT", 0.001),
    "мм": ("LENGTHUNIT", 0.001),
    "cm": ("LENGTHUNIT", 0.01),
    "см": ("LENGTHUNIT", 0.01),
    "ft": ("LENGTHUNIT", 0.3048),
    "feet": ("LENGTHUNIT", 0.3048),
    "foot": ("LENGTHUNIT", 0.3048),
    "in": ("LENGTHUNIT", 0.0254),
    "inch": ("LENGTHUNIT", 0.0254),
    "inches": ("LENGTHUNIT", 0.0254),
    # area → m²
    "m2": ("AREAUNIT", 1.0),
    "м2": ("AREAUNIT", 1.0),
    "m²": ("AREAUNIT", 1.0),
    "м²": ("AREAUNIT", 1.0),
    "sqm": ("AREAUNIT", 1.0),
    "sq.m": ("AREAUNIT", 1.0),
    # volume → m³
    "m3": ("VOLUMEUNIT", 1.0),
    "м3": ("VOLUMEUNIT", 1.0),
    "m³": ("VOLUMEUNIT", 1.0),
    "м³": ("VOLUMEUNIT", 1.0),
}


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
            from ifcopenshell.util.element import get_psets
        except ModuleNotFoundError as exc:
            raise RuntimeError("Install ifcopenshell to run IFC validation") from exc

        from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_session

        session = open_ifc_session(ifc_path)
        model = session.model
        unit_scales, unit_scales_ok = self._get_unit_scales(model)
        issues: list[ValidationIssue] = []
        entity_cache: dict[str, tuple[Any, ...]] = {}
        target_cache: dict[tuple[str, str], tuple[Any, ...]] = {}
        pset_cache: dict[object, dict[str, Any]] = {}

        from aerobim.domain.ifc_globalid import collect_global_id_integrity_issues

        try:
            roots = tuple(model.by_type("IfcRoot"))
        except Exception:  # noqa: BLE001 — schema without IfcRoot must not abort property checks
            roots = ()
        issues.extend(
            collect_global_id_integrity_issues(
                roots,
                source_id=ifc_path.name,
            )
        )

        if not unit_scales_ok:
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-UNIT-SCALE",
                    severity=Severity.ERROR,
                    message=(
                        "IFC unit scale extraction failed; numeric comparisons that "
                        "require project-unit conversion were gated"
                    ),
                    category=FindingCategory.IFC_VALIDATION,
                )
            )

        for requirement in requirements:
            if requirement.rule_scope is RuleScope.DRAWING_ANNOTATION:
                continue

            if not requirement.ifc_entity:
                if requirement.rule_scope in {RuleScope.IFC_PROPERTY, RuleScope.IFC_QUANTITY}:
                    issues.append(
                        issue_from_requirement(
                            requirement,
                            severity=Severity.WARNING,
                            message="Incomplete IFC rule: missing ifc_entity",
                            category=FindingCategory.IFC_VALIDATION,
                        )
                    )
                continue

            matching_elements = self._get_matching_elements(
                model,
                requirement.ifc_entity,
                requirement.target_ref,
                entity_cache,
                target_cache,
                spatial_index=session.spatial_index,
            )

            if not matching_elements:
                issues.append(
                    issue_from_requirement(
                        requirement,
                        severity=Severity.ERROR,
                        message=f"No elements found for entity {requirement.ifc_entity}",
                        category=FindingCategory.IFC_VALIDATION,
                    )
                )
                continue

            if not requirement.property_set or not requirement.property_name:
                issues.append(
                    issue_from_requirement(
                        requirement,
                        severity=Severity.WARNING,
                        message=(
                            "Incomplete IFC rule: missing property_set or property_name; "
                            "rule was not evaluated against model properties"
                        ),
                        category=FindingCategory.IFC_VALIDATION,
                    )
                )
                continue

            if (
                not unit_scales_ok
                and requirement.unit
                and requirement.unit.strip().lower() in _UNIT_TO_SI_FACTOR
            ):
                issues.append(
                    issue_from_requirement(
                        requirement,
                        severity=Severity.ERROR,
                        message=(
                            f"Property {requirement.property_set}.{requirement.property_name} "
                            "could not be compared because IFC unit scales are unavailable"
                        ),
                        category=FindingCategory.IFC_VALIDATION,
                    )
                )
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
                if not self._matches_requirement(observed_value, requirement, unit_scales):
                    reported_observed = self._normalize_observed_for_report(
                        observed_value, requirement.unit, unit_scales
                    )
                    issues.append(
                        issue_from_requirement(
                            requirement,
                            severity=Severity.ERROR,
                            message=(
                                f"Property {requirement.property_set}.{requirement.property_name} "
                                f"does not match the expected value"
                            ),
                            category=FindingCategory.IFC_VALIDATION,
                            observed_value=reported_observed,
                            element_guid=self._extract_guid(element),
                        )
                    )

            if not property_found:
                issues.append(
                    issue_from_requirement(
                        requirement,
                        severity=Severity.ERROR,
                        message=(
                            f"Property {requirement.property_set}.{requirement.property_name} "
                            f"was not found on any {requirement.ifc_entity} elements"
                        ),
                        category=FindingCategory.IFC_VALIDATION,
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
        *,
        spatial_index: Any | None = None,
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
            fast = self._fast_guid_lookup(
                model,
                entity_key=entity_key,
                target_ref=target_ref,
                spatial_index=spatial_index,
            )
            if fast is not None:
                filtered_elements = fast
            else:
                filtered_elements = tuple(
                    element for element in elements if self._matches_target_ref(element, target_ref)
                )
            target_cache[target_key] = filtered_elements
        return list(filtered_elements)

    def _fast_guid_lookup(
        self,
        model: Any,
        *,
        entity_key: str,
        target_ref: str,
        spatial_index: Any | None,
    ) -> tuple[Any, ...] | None:
        """O(1) guid path when spatial index confirms entity type — avoids full by_type scan."""

        if spatial_index is None:
            return None
        guid = target_ref.strip()
        if len(guid) != 22:
            return None
        hit = spatial_index.lookup(guid)
        if hit is None or hit.ifc_type.upper() != entity_key:
            return None
        try:
            element = model.by_guid(guid)
        except Exception:  # noqa: BLE001
            return None
        if element is None:
            return None
        return (element,)

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

    def _get_unit_scales(self, model: Any) -> tuple[dict[str, float], bool]:
        """Extract SI conversion factors from the IFC model's ``UnitsInContext``."""
        try:
            from ifcopenshell.util.unit import calculate_unit_scale

            return (
                {
                    "LENGTHUNIT": calculate_unit_scale(model, "LENGTHUNIT"),
                    "AREAUNIT": calculate_unit_scale(model, "AREAUNIT"),
                    "VOLUMEUNIT": calculate_unit_scale(model, "VOLUMEUNIT"),
                },
                True,
            )
        except Exception:  # noqa: BLE001
            return {"LENGTHUNIT": 1.0, "AREAUNIT": 1.0, "VOLUMEUNIT": 1.0}, False

    def _normalize_pair(
        self,
        observed: float,
        expected: float,
        unit: str | None,
        unit_scales: dict[str, float],
    ) -> tuple[float, float]:
        """Convert *observed* (IFC project units) and *expected* to SI."""
        if unit is None:
            return observed, expected
        mapping = _UNIT_TO_SI_FACTOR.get(unit.strip().lower())
        if mapping is None:
            return observed, expected
        ifc_unit_type, expected_to_si = mapping
        ifc_to_si = unit_scales.get(ifc_unit_type, 1.0)
        return observed * ifc_to_si, expected * expected_to_si

    def _normalize_observed_for_report(
        self,
        observed_value: Any,
        unit: str | None,
        unit_scales: dict[str, float],
    ) -> str:
        """Convert *observed_value* to the requirement's unit for human-readable reports."""
        number = self._to_float(observed_value)
        if number is None or unit is None:
            return str(observed_value)
        mapping = _UNIT_TO_SI_FACTOR.get(unit.strip().lower())
        if mapping is None:
            return str(observed_value)
        ifc_unit_type, expected_to_si = mapping
        if expected_to_si == 0:
            return str(observed_value)
        ifc_to_si = unit_scales.get(ifc_unit_type, 1.0)
        return str(number * ifc_to_si / expected_to_si)

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

    def _matches_requirement(
        self,
        observed_value: Any,
        requirement: ParsedRequirement,
        unit_scales: dict[str, float],
    ) -> bool:
        if requirement.operator is ComparisonOperator.EXISTS:
            return observed_value is not None

        if requirement.expected_value is None:
            return observed_value is not None

        observed_number = self._to_float(observed_value)
        expected_number = self._to_float(requirement.expected_value)

        if observed_number is not None and expected_number is not None:
            obs_si, exp_si = self._normalize_pair(
                observed_number, expected_number, requirement.unit, unit_scales
            )
            eps = self._tolerance.epsilon_for_unit(requirement.unit)
            if requirement.operator is ComparisonOperator.GREATER_OR_EQUAL:
                return obs_si >= exp_si - eps
            if requirement.operator is ComparisonOperator.LESS_OR_EQUAL:
                return obs_si <= exp_si + eps
            # EQUALS: tolerance band |obs - exp| <= ε
            return abs(obs_si - exp_si) <= eps

        # Non-numeric fallback: exact string comparison
        return str(observed_value) == requirement.expected_value

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(str(value).replace(",", ".").strip())
        except ValueError:
            return None
