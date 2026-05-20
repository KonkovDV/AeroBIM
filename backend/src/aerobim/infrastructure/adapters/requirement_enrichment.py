"""Post-extraction enrichment: typed quantities and bSDD URIs."""

from __future__ import annotations

from dataclasses import replace

from aerobim.domain.models import ParsedRequirement
from aerobim.domain.quantity import parse_quantity
from aerobim.infrastructure.adapters.bsdd_term_mapper import BsddTermMapper


def _attach_quantity(requirement: ParsedRequirement) -> ParsedRequirement:
    if requirement.unit is None or requirement.expected_value is None:
        return requirement
    try:
        numeric = float(str(requirement.expected_value).replace(",", "."))
    except ValueError:
        return requirement
    quantity = parse_quantity(numeric, requirement.unit)
    return replace(requirement, quantity=quantity)


def enrich_requirements(
    requirements: list[ParsedRequirement],
    *,
    bsdd_mapper: BsddTermMapper | None = None,
) -> list[ParsedRequirement]:
    mapper = bsdd_mapper or BsddTermMapper()
    enriched: list[ParsedRequirement] = []
    for requirement in requirements:
        with_quantity = _attach_quantity(requirement)
        enriched.append(mapper.enrich(with_quantity))
    return enriched
