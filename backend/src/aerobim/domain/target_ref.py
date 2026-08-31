"""target_ref matching: named element vs unrestricted (all instances of the type).

Pipe-format packs (``samples/requirements/samolet-*.txt``, techlab demo rules)
put ``ALL`` in the target_ref column to mean every entity of ``ifc_entity``.
The IFC validator historically treated that token as a Name/GlobalId filter,
so rules fired ``No elements found for entity IFCWALL`` on models that had
tens of thousands of walls. That is an engine artifact, not a customer defect.
"""

from __future__ import annotations

from typing import Final

# Tokens that mean "do not filter by Name/Tag/GlobalId/Description".
# An element whose Name is literally "ALL" cannot be selected via target_ref;
# address it by GlobalId. Empty / None is the same as ALL (column omitted).
UNRESTRICTED_TARGET_REF_TOKENS: Final[frozenset[str]] = frozenset({"", "all", "*", "any"})

# Per-element value mismatches on unrestricted rules. Full-set EXISTS/EQ
# gaps are one coverage row, not N issues. Cap prevents a 20k-row flood from
# an unsigned ALL+eq pack; suppressed rows are not a customer defect list.
UNRESTRICTED_ELEMENT_MISMATCH_CAP: Final = 50

# Stable fragment for finding-volume taxonomy (coverage_unsigned, not defects).
UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER: Final = "suppressed (unrestricted target_ref cap"

# IfcRoot identity attributes used for *named* target_ref (case-insensitive).
ELEMENT_TARGET_REF_ATTRIBUTES: Final[tuple[str, ...]] = (
    "GlobalId",
    "Name",
    "LongName",
    "Tag",
    "ObjectType",
    "Description",
)


def is_unrestricted_target_ref(target_ref: str | None) -> bool:
    """True when the requirement applies to every instance of its ifc_entity."""

    if target_ref is None:
        return True
    return target_ref.strip().casefold() in UNRESTRICTED_TARGET_REF_TOKENS


def target_ref_matches(requirement_ref: str | None, observed_ref: str) -> bool:
    """Match a requirement target_ref to an observed Name/annotation ref."""

    if is_unrestricted_target_ref(requirement_ref):
        return True
    return (requirement_ref or "").strip().lower() == observed_ref.strip().lower()


def element_matches_named_target_ref(element: object, target_ref: str | None) -> bool:
    """True when *element* is in scope for *target_ref*.

    Unrestricted tokens match every instance. Named refs compare case-insensitively
    against IfcRoot identity attributes — exact token, not a substring.
    """

    if is_unrestricted_target_ref(target_ref):
        return True
    needle = (target_ref or "").strip().lower()
    if not needle:
        return True
    for attribute_name in ELEMENT_TARGET_REF_ATTRIBUTES:
        value = getattr(element, attribute_name, None)
        if value is not None and str(value).strip().lower() == needle:
            return True
    return False


def unrestricted_mismatch_suppressor_message(
    *,
    ifc_entity: str | None,
    suppressed: int,
    cap: int = UNRESTRICTED_ELEMENT_MISMATCH_CAP,
) -> str:
    """One coverage row after the per-element mismatch cap (not a defect list)."""

    entity = ifc_entity or "element"
    return (
        f"{suppressed} further {entity} property mismatches "
        f"{UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER} {cap}; "
        "not a customer defect list)"
    )


__all__ = [
    "ELEMENT_TARGET_REF_ATTRIBUTES",
    "UNRESTRICTED_ELEMENT_MISMATCH_CAP",
    "UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER",
    "UNRESTRICTED_TARGET_REF_TOKENS",
    "element_matches_named_target_ref",
    "is_unrestricted_target_ref",
    "target_ref_matches",
    "unrestricted_mismatch_suppressor_message",
]
