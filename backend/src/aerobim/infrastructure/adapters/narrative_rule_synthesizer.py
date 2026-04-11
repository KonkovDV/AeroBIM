from __future__ import annotations

import re
from pathlib import Path

from aerobim.domain.models import (
    ComparisonOperator,
    ParsedRequirement,
    RequirementSource,
    RuleScope,
)


class NarrativeRuleSynthesizer:
    _area_pattern = re.compile(
        r"(?i)(?:room|space|помещени[ея])\s+(?P<target>[A-Za-zА-Яа-я0-9_-]+).*?(?:площад[ьи]|area).*?(?:не\s+менее|at\s+least|>=)\s+(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>м2|m2|sqm)"
    )
    _fire_rating_pattern = re.compile(
        r"(?i)(?:ifcwall|wall|стен[аы]).*?(?:fire\s+rating|огнестойк[а-я]+).*?(?:must\s+be|должн[ао]\s+быть|=)\s*(?P<value>[A-Za-z0-9_-]+)"
    )
    _drawing_dimension_pattern = re.compile(
        r"(?i)(?:sheet|лист)\s+(?P<sheet>[A-Za-zА-Яа-я0-9_-]+).*?(?:thickness|толщин[аы]|dimension|размер)\s+(?P<target>[A-Za-zА-Яа-я0-9_-]+).*?(?:не\s+менее|at\s+least|>=)\s+(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>мм|mm)"
    )

    def synthesize(self, source: RequirementSource) -> list[ParsedRequirement]:
        raw_text = source.text.strip()
        if not raw_text and source.path is not None:
            raw_text = self._load_text(source.path)

        requirements: list[ParsedRequirement] = []
        for line_number, line in enumerate(raw_text.splitlines(), start=1):
            normalized = line.strip()
            if not normalized:
                continue

            area_match = self._area_pattern.search(normalized)
            if area_match:
                requirements.append(
                    ParsedRequirement(
                        rule_id=self._build_rule_id(source, line_number, "area"),
                        ifc_entity="IFCSPACE",
                        rule_scope=RuleScope.IFC_QUANTITY,
                        target_ref=area_match.group("target"),
                        property_set="Qto_SpaceBaseQuantities",
                        property_name="NetFloorArea",
                        operator=ComparisonOperator.GREATER_OR_EQUAL,
                        expected_value=self._normalize_number(area_match.group("value")),
                        unit=area_match.group("unit"),
                        source=str(source.path) if source.path else source.source_kind.value,
                        source_kind=source.source_kind,
                        evidence_text=normalized,
                    )
                )
                continue

            fire_rating_match = self._fire_rating_pattern.search(normalized)
            if fire_rating_match:
                requirements.append(
                    ParsedRequirement(
                        rule_id=self._build_rule_id(source, line_number, "fire-rating"),
                        ifc_entity="IFCWALL",
                        rule_scope=RuleScope.IFC_PROPERTY,
                        property_set="Pset_WallCommon",
                        property_name="FireRating",
                        operator=ComparisonOperator.EQUALS,
                        expected_value=fire_rating_match.group("value"),
                        source=str(source.path) if source.path else source.source_kind.value,
                        source_kind=source.source_kind,
                        evidence_text=normalized,
                    )
                )
                continue

            drawing_dimension_match = self._drawing_dimension_pattern.search(normalized)
            if drawing_dimension_match:
                requirements.append(
                    ParsedRequirement(
                        rule_id=self._build_rule_id(source, line_number, "drawing-dimension"),
                        ifc_entity="IFCWALL",
                        rule_scope=RuleScope.DRAWING_ANNOTATION,
                        target_ref=drawing_dimension_match.group("target"),
                        property_name="thickness",
                        operator=ComparisonOperator.GREATER_OR_EQUAL,
                        expected_value=self._normalize_number(drawing_dimension_match.group("value")),
                        unit=drawing_dimension_match.group("unit"),
                        source=str(source.path) if source.path else source.source_kind.value,
                        source_kind=source.source_kind,
                        evidence_text=normalized,
                        instructions=f"sheet={drawing_dimension_match.group('sheet')}",
                        evidence_modality="drawing",
                    )
                )

        return requirements

    def _load_text(self, source_path: Path) -> str:
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        return source_path.read_text(encoding="utf-8")

    def _build_rule_id(self, source: RequirementSource, line_number: int, suffix: str) -> str:
        prefix = source.source_id or source.source_kind.value
        safe_prefix = prefix.replace(" ", "-")
        return f"{safe_prefix}-{suffix}-{line_number:03d}"

    def _normalize_number(self, raw: str) -> str:
        return raw.replace(",", ".").strip()