# pyright: reportMissingImports=false

"""IFC quantity сверка adapter — Qto area/volume vs declared claims."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from aerobim.domain.consistency import QuantityClaim
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue
from aerobim.domain.quantity import QuantityValue, parse_quantity, si_compare
from aerobim.domain.target_ref import element_matches_named_target_ref, is_unrestricted_target_ref


class IfcQuantityConsistencyAdapter:
    """Compare declared QuantityClaim values to IFC quantity sets (match, not correctness)."""

    def check(
        self,
        ifc_path: Path,
        declared: Sequence[QuantityClaim],
    ) -> list[ValidationIssue]:
        if not declared:
            return []
        if not ifc_path.exists():
            raise FileNotFoundError(ifc_path)

        try:
            from ifcopenshell.util.element import get_psets
        except ModuleNotFoundError as exc:
            raise RuntimeError("Install ifcopenshell for quantity consistency") from exc

        from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_session

        session = open_ifc_session(ifc_path)
        model = session.model
        issues: list[ValidationIssue] = []
        for claim in declared:
            observed_list = self._find_all_observed(model, get_psets, claim)
            if not observed_list:
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-QTY-MISSING",
                        severity=Severity.WARNING,
                        message=(
                            f"Declared quantity {claim.quantity_name!r} for "
                            f"{claim.target_ref or claim.ifc_entity or 'element'} "
                            "not found in IFC Qto/Pset"
                        ),
                        category=FindingCategory.IFC_VALIDATION,
                        ifc_entity=claim.ifc_entity,
                        target_ref=claim.target_ref,
                        property_name=claim.quantity_name,
                        expected_value=str(claim.declared.value),
                        unit=claim.declared.unit,
                        source_id=claim.source_id or "quantity-consistency",
                    )
                )
                continue
            mismatch_count = sum(
                1
                for observed in observed_list
                if not si_compare(claim.declared, observed, epsilon=1e-3)
            )
            if mismatch_count == 0:
                continue
            total = len(observed_list)
            # ALL (or duplicate names) collapse to one coverage row. A single
            # named hit keeps the declared-vs-ifc detail.
            if is_unrestricted_target_ref(claim.target_ref) or total > 1:
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-QTY-MISMATCH",
                        severity=Severity.WARNING,
                        message=(
                            f"Quantity mismatch for {claim.quantity_name} on "
                            f"{mismatch_count} of {total} "
                            f"{claim.ifc_entity or 'element'} instances"
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        ifc_entity=claim.ifc_entity,
                        target_ref=claim.target_ref,
                        property_name=claim.quantity_name,
                        expected_value=str(claim.declared.value),
                        observed_value=str(mismatch_count),
                        unit=claim.declared.unit,
                        source_id=claim.source_id or "quantity-consistency",
                    )
                )
                continue
            observed = observed_list[0]
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-QTY-MISMATCH",
                    severity=Severity.WARNING,
                    message=(
                        f"Quantity mismatch for {claim.quantity_name}: "
                        f"declared={claim.declared.value} {claim.declared.unit}, "
                        f"ifc={observed.value} {observed.unit}"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    ifc_entity=claim.ifc_entity,
                    target_ref=claim.target_ref,
                    property_name=claim.quantity_name,
                    expected_value=str(claim.declared.value),
                    observed_value=str(observed.value),
                    unit=claim.declared.unit,
                    source_id=claim.source_id or "quantity-consistency",
                )
            )
        return issues

    def _find_all_observed(
        self,
        model: Any,
        get_psets: Any,
        claim: QuantityClaim,
    ) -> list[QuantityValue]:
        if claim.ifc_entity:
            try:
                entities = tuple(model.by_type(claim.ifc_entity))
            except Exception:
                entities = ()
        else:
            entities = tuple(model.by_type("IfcProduct"))

        want = claim.quantity_name.strip().casefold()
        found: list[QuantityValue] = []
        # Empty / ALL target_ref matches every instance of the type.
        for element in entities:
            if not element_matches_named_target_ref(element, claim.target_ref):
                continue
            parsed = self._quantity_on_element(get_psets, element, want, claim.declared.unit)
            if parsed is not None:
                found.append(parsed)
        return found

    def _quantity_on_element(
        self,
        get_psets: Any,
        element: Any,
        want: str,
        fallback_unit: str,
    ) -> QuantityValue | None:
        psets = get_psets(element)
        for _pset_name, props in psets.items():
            if not isinstance(props, dict):
                continue
            for prop_name, prop_value in props.items():
                prop_cf = prop_name.strip().casefold()
                if prop_cf != want and want not in prop_cf and prop_cf not in want:
                    continue
                parsed = self._coerce_quantity(prop_value, fallback_unit)
                if parsed is not None:
                    return parsed
        return None

    def _coerce_quantity(self, raw: object, fallback_unit: str) -> QuantityValue | None:
        if isinstance(raw, bool):
            return None
        if isinstance(raw, int | float):
            return parse_quantity(float(raw), fallback_unit or "m2")
        if isinstance(raw, str):
            text = raw.strip().replace(",", ".")
            parts = text.split()
            if not parts:
                return None
            try:
                value = float(parts[0])
            except ValueError:
                return None
            unit = parts[1] if len(parts) > 1 else fallback_unit
            return parse_quantity(value, unit or "m2")
        return None
