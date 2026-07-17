# pyright: reportMissingImports=false

"""IFC quantity сверка adapter — Qto area/volume vs declared claims."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from aerobim.domain.consistency import QuantityClaim
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue
from aerobim.domain.quantity import QuantityValue, parse_quantity, si_compare


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

        from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model

        model = open_ifc_model(ifc_path)
        issues: list[ValidationIssue] = []
        for claim in declared:
            observed = self._find_observed(model, get_psets, claim)
            if observed is None:
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
            if not si_compare(claim.declared, observed, epsilon=1e-3):
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

    def _find_observed(
        self,
        model: Any,
        get_psets: Any,
        claim: QuantityClaim,
    ) -> QuantityValue | None:
        if claim.ifc_entity:
            try:
                entities = tuple(model.by_type(claim.ifc_entity))
            except Exception:  # noqa: BLE001
                entities = ()
        else:
            entities = tuple(model.by_type("IfcProduct"))

        want = claim.quantity_name.strip().casefold()
        for element in entities:
            if claim.target_ref:
                name = str(getattr(element, "Name", "") or "")
                tag = str(getattr(element, "Tag", "") or "")
                guid = str(getattr(element, "GlobalId", "") or "")
                if claim.target_ref not in {name, tag, guid}:
                    continue
            psets = get_psets(element)
            for _pset_name, props in psets.items():
                if not isinstance(props, dict):
                    continue
                for prop_name, prop_value in props.items():
                    prop_cf = prop_name.strip().casefold()
                    if prop_cf != want and want not in prop_cf and prop_cf not in want:
                        continue
                    parsed = self._coerce_quantity(prop_value, claim.declared.unit)
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
