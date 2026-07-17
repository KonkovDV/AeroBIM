"""RASE-style provenance tags for advisory ACC findings (I8b).

R/A/S/E never write ``summary.passed``. Tags are advisory transparency only.
"""

from __future__ import annotations

from typing import Literal

from aerobim.domain.models import ParsedRequirement

RaseElement = Literal["R", "A", "S", "E"]


def infer_rase_elements(requirement: ParsedRequirement) -> tuple[RaseElement, ...]:
    """Infer coarse RASE tags from a structured requirement.

    - R: always when a rule_id exists (requirement statement)
    - A: IFC entity / applicability present
    - S: property/quantity selection present
    - E: reserved — only when message/exception markers exist (not auto today)
    """

    tags: list[RaseElement] = []
    if requirement.rule_id:
        tags.append("R")
    if requirement.ifc_entity:
        tags.append("A")
    if requirement.property_set or requirement.property_name or requirement.target_ref:
        tags.append("S")
    return tuple(tags)


def format_rase_summary(elements: tuple[RaseElement, ...]) -> str:
    if not elements:
        return "RASE not inferred"
    return "+".join(elements) + " (advisory; E not auto-inferred)"
