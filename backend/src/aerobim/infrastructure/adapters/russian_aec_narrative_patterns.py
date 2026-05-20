"""Deterministic Russian AEC narrative extractors for benchmark ground-truth alignment.

Patterns are explicit and auditable (hybrid rule-based ACC per ITcon 2025 SLR).
Deterministic patterns only — suitable for pilot sign-off and extraction P/R evaluation.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from aerobim.domain.models import (
    ComparisonOperator,
    ParsedRequirement,
    RequirementSource,
    RuleScope,
)

_RuleFactory = Callable[[re.Match[str], RequirementSource, int, str], ParsedRequirement | None]


def _wall_thermal_transmittance(
    match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    return ParsedRequirement(
        rule_id=f"ru-thermal-u-{line_number:03d}",
        ifc_entity="IfcWall",
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set="Pset_WallCommon",
        property_name="ThermalTransmittance",
        operator=ComparisonOperator.GREATER_OR_EQUAL,
        expected_value=_normalize_number(match.group("value")),
        unit="m2K/W",
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _wall_thickness(
    match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    return ParsedRequirement(
        rule_id=f"ru-wall-thickness-{line_number:03d}",
        ifc_entity="IfcWall",
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set="Pset_WallCommon",
        property_name="Thickness",
        operator=ComparisonOperator.GREATER_OR_EQUAL,
        expected_value=_normalize_number(match.group("value")),
        unit="mm",
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _material_density(
    match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    return ParsedRequirement(
        rule_id=f"ru-material-density-{line_number:03d}",
        ifc_entity="IfcWall",
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set="Pset_MaterialCommon",
        property_name="Density",
        operator=ComparisonOperator.GREATER_OR_EQUAL,
        expected_value=_normalize_number(match.group("value")),
        unit="kg/m3",
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _thermal_conductivity(
    match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    lowered = line.lower()
    if "кровли" in lowered or "утеплителя кровли" in lowered:
        entity, pset = "IfcRoof", "Pset_MaterialThermal"
    elif "остекления" in lowered or "профиля" in lowered:
        entity, pset = "IfcWindow", "Pset_MaterialThermal"
    else:
        entity, pset = "IfcWall", "Pset_MaterialThermal"
    return ParsedRequirement(
        rule_id=f"ru-lambda-{entity.lower()}-{line_number:03d}",
        ifc_entity=entity,
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set=pset,
        property_name="ThermalConductivity",
        operator=ComparisonOperator.LESS_OR_EQUAL,
        expected_value=_normalize_number(match.group("value")),
        unit="W/mK",
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _combustibility_k0_from_line(
    match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    lowered = line.lower()
    if "кровли" in lowered:
        entity, pset = "IfcRoof", "Pset_RoofCommon"
    elif "остекления" in lowered:
        entity, pset = "IfcWindow", "Pset_WindowCommon"
    elif "отделки" in lowered:
        entity, pset = "IfcSpace", "Pset_SpaceCommon"
    else:
        entity, pset = "IfcWall", "Pset_WallCommon"
    return ParsedRequirement(
        rule_id=f"ru-combust-{entity.lower()}-{line_number:03d}",
        ifc_entity=entity,
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set=pset,
        property_name="CombustibilityClass",
        operator=ComparisonOperator.EQUALS,
        expected_value=match.group("value").upper(),
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _column_strength_class(
    match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    return ParsedRequirement(
        rule_id=f"ru-col-strength-{line_number:03d}",
        ifc_entity="IfcColumn",
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set="Pset_ConcreteElementGeneral",
        property_name="ConcreteStrengthClass",
        operator=ComparisonOperator.EQUALS,
        expected_value=match.group("value").upper().replace("С", "C"),
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _column_load_bearing(
    _match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    return ParsedRequirement(
        rule_id=f"ru-col-bearing-{line_number:03d}",
        ifc_entity="IfcColumn",
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set="Pset_ColumnCommon",
        property_name="LoadBearing",
        operator=ComparisonOperator.EQUALS,
        expected_value="true",
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _column_bar_diameter(
    match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    return ParsedRequirement(
        rule_id=f"ru-col-bar-{line_number:03d}",
        ifc_entity="IfcColumn",
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set="Pset_ReinforcementBarPitch",
        property_name="BarDiameter",
        operator=ComparisonOperator.GREATER_OR_EQUAL,
        expected_value=_normalize_number(match.group("value")),
        unit="mm",
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _column_concrete_density(
    match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    return ParsedRequirement(
        rule_id=f"ru-col-density-{line_number:03d}",
        ifc_entity="IfcColumn",
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set="Pset_MaterialCommon",
        property_name="Density",
        operator=ComparisonOperator.GREATER_OR_EQUAL,
        expected_value=_normalize_number(match.group("value")),
        unit="kg/m3",
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _column_cover_thickness(
    match: re.Match[str], source: RequirementSource, line_number: int, line: str
) -> ParsedRequirement:
    return ParsedRequirement(
        rule_id=f"ru-col-cover-{line_number:03d}",
        ifc_entity="IfcColumn",
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set="Pset_CoveringCommon",
        property_name="CoveringThickness",
        operator=ComparisonOperator.GREATER_OR_EQUAL,
        expected_value=_normalize_number(match.group("value")),
        unit="mm",
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


def _entity_thermal_transmittance(
    ifc_entity: str,
    property_set: str,
) -> _RuleFactory:
    def factory(
        match: re.Match[str], source: RequirementSource, line_number: int, line: str
    ) -> ParsedRequirement:
        return ParsedRequirement(
            rule_id=f"ru-thermal-{ifc_entity.lower()}-{line_number:03d}",
            ifc_entity=ifc_entity,
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set=property_set,
            property_name="ThermalTransmittance",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(match.group("value")),
            unit="m2K/W",
            source=str(source.path) if source.path else source.source_kind.value,
            source_kind=source.source_kind,
            evidence_text=line,
        )

    return factory


def _entity_thickness(
    ifc_entity: str,
    property_set: str,
    *,
    pattern_hint: str,
) -> _RuleFactory:
    def factory(
        match: re.Match[str], source: RequirementSource, line_number: int, line: str
    ) -> ParsedRequirement:
        return ParsedRequirement(
            rule_id=f"ru-thickness-{pattern_hint}-{line_number:03d}",
            ifc_entity=ifc_entity,
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set=property_set,
            property_name="Thickness",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(match.group("value")),
            unit="mm",
            source=str(source.path) if source.path else source.source_kind.value,
            source_kind=source.source_kind,
            evidence_text=line,
        )

    return factory


def _entity_density(
    ifc_entity: str,
    property_set: str,
) -> _RuleFactory:
    def factory(
        match: re.Match[str], source: RequirementSource, line_number: int, line: str
    ) -> ParsedRequirement:
        return ParsedRequirement(
            rule_id=f"ru-density-{ifc_entity.lower()}-{line_number:03d}",
            ifc_entity=ifc_entity,
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set=property_set,
            property_name="Density",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(match.group("value")),
            unit="kg/m3",
            source=str(source.path) if source.path else source.source_kind.value,
            source_kind=source.source_kind,
            evidence_text=line,
        )

    return factory


def _entity_concrete_class(
    ifc_entity: str,
    property_set: str,
) -> _RuleFactory:
    def factory(
        match: re.Match[str], source: RequirementSource, line_number: int, line: str
    ) -> ParsedRequirement:
        return ParsedRequirement(
            rule_id=f"ru-concrete-{ifc_entity.lower()}-{line_number:03d}",
            ifc_entity=ifc_entity,
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set=property_set,
            property_name="ConcreteStrengthClass",
            operator=ComparisonOperator.EQUALS,
            expected_value=match.group("value").upper().replace("С", "C"),
            source=str(source.path) if source.path else source.source_kind.value,
            source_kind=source.source_kind,
            evidence_text=line,
        )

    return factory


def _entity_combustibility_k0(
    ifc_entity: str,
    property_set: str,
) -> _RuleFactory:
    def factory(
        match: re.Match[str], source: RequirementSource, line_number: int, line: str
    ) -> ParsedRequirement:
        return ParsedRequirement(
            rule_id=f"ru-combust-{ifc_entity.lower()}-{line_number:03d}",
            ifc_entity=ifc_entity,
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set=property_set,
            property_name="CombustibilityClass",
            operator=ComparisonOperator.EQUALS,
            expected_value=match.group("value").upper(),
            source=str(source.path) if source.path else source.source_kind.value,
            source_kind=source.source_kind,
            evidence_text=line,
        )

    return factory


def _fire_rating_entity(
    match: re.Match[str],
    source: RequirementSource,
    line_number: int,
    line: str,
    *,
    ifc_entity: str,
    property_set: str,
) -> ParsedRequirement:
    rating = re.sub(r"\s+", "", match.group("rating").upper())
    return ParsedRequirement(
        rule_id=f"ru-fire-{ifc_entity.lower()}-{line_number:03d}",
        ifc_entity=ifc_entity,
        rule_scope=RuleScope.IFC_PROPERTY,
        property_set=property_set,
        property_name="FireRating",
        operator=ComparisonOperator.GREATER_OR_EQUAL,
        expected_value=rating,
        source=str(source.path) if source.path else source.source_kind.value,
        source_kind=source.source_kind,
        evidence_text=line,
    )


RUSSIAN_AEC_NARRATIVE_PATTERNS: list[tuple[re.Pattern[str], _RuleFactory]] = [
    (
        re.compile(
            r"(?i)сопротивлени[ея]\s+теплопередаче\s+не\s+менее\s+R\s*=\s*(?P<value>\d+(?:[.,]\d+)?)"
        ),
        _wall_thermal_transmittance,
    ),
    (
        re.compile(r"(?i)толщин[аы]\s+стен[ыы].*?(?P<value>\d+(?:[.,]\d+)?)\s*мм"),
        _wall_thickness,
    ),
    (
        re.compile(r"(?i)плотностью\s+(?P<value>\d+(?:[.,]\d+)?)\s*(?:–|-)?\s*\d*\s*кг/м"),
        _material_density,
    ),
    (
        re.compile(r"(?i)плотность\s+утеплителя\s+кровли\s*—\s*(?P<value>\d+(?:[.,]\d+)?)\s*кг/м"),
        _entity_density("IfcRoof", "Pset_MaterialCommon"),
    ),
    (
        re.compile(r"(?i)фундаментн[а-я]+\s+плита\s+класса\s+прочности\s+(?P<value>[СC]\d+/\d+)"),
        _entity_concrete_class("IfcFooting", "Pset_ConcreteElementGeneral"),
    ),
    (
        re.compile(r"(?i)λ\s*≤\s*(?P<value>\d+(?:[.,]\d+)?)\s*Вт"),
        _thermal_conductivity,
    ),
    (
        re.compile(r"(?i)класс\s+пожарной\s+опасности\s+[^—\n]*—\s*(?P<value>К\d+)"),
        _combustibility_k0_from_line,
    ),
    (
        re.compile(r"(?i)колонн[ыы].*?несущ"),
        _column_load_bearing,
    ),
    (
        re.compile(r"(?i)класса\s+прочности\s+(?P<value>[СC]\d+/\d+)"),
        _column_strength_class,
    ),
    (
        re.compile(r"(?i)^\d+\.\s*Колонны\s+железобетонные"),
        _column_load_bearing,
    ),
    (
        re.compile(r"(?i)фундамент.*?диаметр\s+(?P<value>\d+(?:[.,]\d+)?)\s*мм"),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-footing-bar-{n:03d}",
            ifc_entity="IfcFooting",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_ReinforcementBarPitch",
            property_name="BarDiameter",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="mm",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(r"(?i)колонн.*?диаметр\s+(?P<value>\d+(?:[.,]\d+)?)\s*(?:–|-)?"),
        _column_bar_diameter,
    ),
    (
        re.compile(
            r"(?i)защитный\s+слой\s+бетона\s+к\s+арматуре\s+фундамента\s*—\s*(?P<value>\d+(?:[.,]\d+)?)\s*мм"
        ),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-footing-cover-{n:03d}",
            ifc_entity="IfcFooting",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_CoveringCommon",
            property_name="CoveringThickness",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="mm",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(
            r"(?i)объёмный\s+вес\s+бетона\s+фундамента\s+не\s+менее\s+(?P<value>\d+(?:[.,]\d+)?)\s*кг/м"
        ),
        _entity_density("IfcFooting", "Pset_MaterialCommon"),
    ),
    (
        re.compile(r"(?i)объёмный\s+вес\s+бетона\s+не\s+менее\s+(?P<value>\d+(?:[.,]\d+)?)\s*кг/м"),
        _column_concrete_density,
    ),
    (
        re.compile(
            r"(?i)защитный\s+слой\s+бетона\s+к\s+арматуре\s*—\s*(?P<value>\d+(?:[.,]\d+)?)\s*мм"
        ),
        _column_cover_thickness,
    ),
    (
        re.compile(r"(?i)стен[ыы].*?огнестойкост[ьи]\s+не\s+менее\s+(?P<rating>REI\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcWall", property_set="Pset_WallCommon"
        ),
    ),
    (
        re.compile(r"(?i)двер[ьи].*?(?P<rating>EI\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcDoor", property_set="Pset_DoorCommon"
        ),
    ),
    (
        re.compile(r"(?i)перекрыти[яе].*?(?P<rating>REI\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcSlab", property_set="Pset_SlabCommon"
        ),
    ),
    (
        re.compile(r"(?i)окн[ао].*?(?P<rating>E\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcWindow", property_set="Pset_WindowCommon"
        ),
    ),
    (
        re.compile(r"(?i)лестничн[а-я]+.*?стен[ыы].*?(?P<rating>REI\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcWall", property_set="Pset_WallCommon"
        ),
    ),
    (
        re.compile(r"(?i)плит[ыы].*?огнестойкост[ьи]\s+не\s+менее\s+(?P<rating>REI\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcSlab", property_set="Pset_SlabCommon"
        ),
    ),
    (
        re.compile(r"(?i)толщин[аы]\s+плиты.*?—\s*(?P<value>\d+(?:[.,]\d+)?)\s*мм"),
        _entity_thickness("IfcSlab", "Pset_SlabCommon", pattern_hint="slab"),
    ),
    (
        re.compile(r"(?i)класс\s+бетона\s+плит\s*—\s*(?P<value>[СC]\d+/\d+)"),
        _entity_concrete_class("IfcSlab", "Pset_ConcreteElementGeneral"),
    ),
    (
        re.compile(r"(?i)нагрузка\s+не\s+менее\s+(?P<value>\d+(?:[.,]\d+)?)\s*кН/м²"),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-slab-load-{n:03d}",
            ifc_entity="IfcSlab",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_SlabCommon",
            property_name="LoadBearing",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="kN/m2",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(
            r"(?i)защитный\s+слой\s+бетона\s+к\s+арматуре\s+плиты\s*—\s*(?P<value>\d+(?:[.,]\d+)?)\s*мм"
        ),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-slab-cover-{n:03d}",
            ifc_entity="IfcSlab",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_CoveringCommon",
            property_name="CoveringThickness",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="mm",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(
            r"(?i)сопротивлени[ея]\s+теплопередаче\s+кровли\s+не\s+менее\s+R\s*=\s*(?P<value>\d+(?:[.,]\d+)?)"
        ),
        _entity_thermal_transmittance("IfcRoof", "Pset_RoofCommon"),
    ),
    (
        re.compile(
            r"(?i)толщина\s+утеплителя\s+кровли\s*—\s*не\s+менее\s+(?P<value>\d+(?:[.,]\d+)?)\s*мм"
        ),
        _entity_thickness("IfcRoof", "Pset_RoofCommon", pattern_hint="roof"),
    ),
    (
        re.compile(r"(?i)толщина\s+фундаментной\s+плиты\s*—\s*(?P<value>\d+(?:[.,]\d+)?)\s*мм"),
        _entity_thickness("IfcFooting", "Pset_FootingCommon", pattern_hint="footing"),
    ),
    (
        re.compile(r"(?i)окна\s+фасадные.*?огнестойкость\s+стекла\s+(?P<rating>E\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcWindow", property_set="Pset_WindowCommon"
        ),
    ),
    (
        re.compile(r"(?i)толщина\s+стеклопакета\s*—\s*(?P<value>\d+(?:[.,]\d+)?)\s*мм"),
        _entity_thickness("IfcWindow", "Pset_WindowCommon", pattern_hint="window"),
    ),
    (
        re.compile(
            r"(?i)сопротивлени[ея]\s+теплопередаче\s+остекления\s+не\s+менее\s+R\s*=\s*(?P<value>\d+(?:[.,]\d+)?)"
        ),
        _entity_thermal_transmittance("IfcWindow", "Pset_WindowCommon"),
    ),
    (
        re.compile(r"(?i)двери\s+эвакуационные\s*—\s*(?P<rating>EI\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcDoor", property_set="Pset_DoorCommon"
        ),
    ),
    (
        re.compile(r"(?i)ширина\s+марша\s+лестницы\s+не\s+менее\s+(?P<value>\d+(?:[.,]\d+)?)\s*мм"),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-stair-width-{n:03d}",
            ifc_entity="IfcStair",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_StairCommon",
            property_name="Width",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="mm",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(r"(?i)класс\s+бетона\s+лестничных\s+маршей\s*—\s*(?P<value>[СC]\d+/\d+)"),
        _entity_concrete_class("IfcStair", "Pset_ConcreteElementGeneral"),
    ),
    (
        re.compile(
            r"(?i)лестничн[а-я]+.*?защитный\s+слой\s+бетона.*?—\s*(?P<value>\d+(?:[.,]\d+)?)\s*мм"
        ),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-stair-cover-{n:03d}",
            ifc_entity="IfcStair",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_CoveringCommon",
            property_name="CoveringThickness",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="mm",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(r"(?i)площадь\s+не\s+менее\s+(?P<value>\d+(?:[.,]\d+)?)\s*м²"),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-space-area-{n:03d}",
            ifc_entity="IfcSpace",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_SpaceCommon",
            property_name="GrossFloorArea",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="m2",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(r"(?i)потолки\s+помещения.*?огнестойкость\s+не\s+менее\s+(?P<rating>REI\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcSpace", property_set="Pset_SpaceCommon"
        ),
    ),
    (
        re.compile(r"(?i)минимальная\s+высота\s+помещения\s*—\s*(?P<value>\d+(?:[.,]\d+)?)\s*мм"),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-space-height-{n:03d}",
            ifc_entity="IfcSpace",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_SpaceCommon",
            property_name="Height",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="mm",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(
            r"(?i)сопротивлени[ея]\s+теплопередаче\s+ограждающих\s+конструкций\s+не\s+менее\s+R\s*=\s*(?P<value>\d+(?:[.,]\d+)?)"
        ),
        _entity_thermal_transmittance("IfcSpace", "Pset_SpaceCommon"),
    ),
    (
        re.compile(r"(?i)класс\s+прочности\s+стали\s+(?P<value>[СC]\d+)"),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-beam-steel-{n:03d}",
            ifc_entity="IfcBeam",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_BeamCommon",
            property_name="SteelGrade",
            operator=ComparisonOperator.EQUALS,
            expected_value=m.group("value").upper().replace("С", "C"),
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(r"(?i)высота\s+балки\s*—\s*(?P<value>\d+(?:[.,]\d+)?)\s*мм"),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-beam-height-{n:03d}",
            ifc_entity="IfcBeam",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_BeamCommon",
            property_name="Height",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="mm",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(r"(?i)огнестойкость\s+балки\s*—\s*(?P<rating>REI\s*\d+)"),
        lambda m, s, n, line: _fire_rating_entity(
            m, s, n, line, ifc_entity="IfcBeam", property_set="Pset_BeamCommon"
        ),
    ),
    (
        re.compile(r"(?i)толщина\s+(?P<value>\d+(?:[.,]\d+)?)\s*мкм"),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-beam-coating-{n:03d}",
            ifc_entity="IfcBeam",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_BeamCommon",
            property_name="CoatingThickness",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="um",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
    (
        re.compile(r"(?i)нагрузка\s+не\s+менее\s+(?P<value>\d+(?:[.,]\d+)?)\s*кН/м(?!\s*²)"),
        lambda m, s, n, line: ParsedRequirement(
            rule_id=f"ru-beam-load-{n:03d}",
            ifc_entity="IfcBeam",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set="Pset_BeamCommon",
            property_name="LoadBearing",
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            expected_value=_normalize_number(m.group("value")),
            unit="kN/m",
            source=str(s.path) if s.path else s.source_kind.value,
            source_kind=s.source_kind,
            evidence_text=line,
        ),
    ),
]


def extract_russian_aec_requirements(
    source: RequirementSource,
    raw_text: str,
) -> list[ParsedRequirement]:
    requirements: list[ParsedRequirement] = []
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        normalized = line.strip()
        if not normalized or normalized.startswith("="):
            continue
        for pattern, factory in RUSSIAN_AEC_NARRATIVE_PATTERNS:
            match = pattern.search(normalized)
            if match is None:
                continue
            requirement = factory(match, source, line_number, normalized)
            if requirement is not None:
                requirements.append(requirement)
                break
    return requirements


def _normalize_number(raw: str) -> str:
    return raw.replace(",", ".").strip()
