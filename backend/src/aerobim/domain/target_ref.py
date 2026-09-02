"""target_ref matching: named element vs unrestricted (all instances of the type).

Pipe-format packs (``samples/requirements/samolet-*.txt``, techlab demo rules)
put ``ALL`` in the target_ref column to mean every entity of ``ifc_entity``.
The IFC validator historically treated that token as a Name/GlobalId filter,
so rules fired ``No elements found for entity IFCWALL`` on models that had
tens of thousands of walls. That is an engine artifact, not a customer defect.

Empty / None target_ref is the same unrestricted ALL-rule (column omitted).
IfcRoot.GlobalId is ISO 10303-21 compressed GUID: 22 characters, case-sensitive.
Name / Tag / ObjectType / LongName / Description use ``str.casefold``.
"""

from __future__ import annotations

from typing import Final

from aerobim.domain.ifc_globalid import is_valid_ifc_global_id

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

# IfcRoot identity attributes considered for *named* target_ref.
# GlobalId is exact; the rest are casefolded (see element_matches_named_target_ref).
ELEMENT_TARGET_REF_ATTRIBUTES: Final[tuple[str, ...]] = (
    "GlobalId",
    "Name",
    "LongName",
    "Tag",
    "ObjectType",
    "Description",
)

ELEMENT_TARGET_REF_FOLD_ATTRIBUTES: Final[tuple[str, ...]] = (
    "Name",
    "LongName",
    "Tag",
    "ObjectType",
    "Description",
)


def is_unrestricted_target_ref(target_ref: str | None) -> bool:
    """True when the requirement applies to every instance of its ifc_entity.

    ``None``, empty / whitespace, ``ALL``, ``*``, and ``ANY`` are unrestricted.
    Callers must treat that as an ALL-rule, not as a named-ref miss.
    """

    if target_ref is None:
        return True
    return target_ref.strip().casefold() in UNRESTRICTED_TARGET_REF_TOKENS


def target_ref_matches(requirement_ref: str | None, observed_ref: str) -> bool:
    """Match a requirement target_ref to an observed Name/annotation ref.

    Empty / ALL requirement_ref is unrestricted (matches any observed ref).
    Named annotation refs use ``str.casefold`` (not IFC GlobalId).
    """

    if is_unrestricted_target_ref(requirement_ref):
        return True
    return (requirement_ref or "").strip().casefold() == observed_ref.strip().casefold()


def named_target_ref_cache_key(target_ref: str) -> str:
    """Cache key for a named target_ref: exact GUID, casefold otherwise."""

    stripped = target_ref.strip()
    if is_valid_ifc_global_id(stripped):
        return stripped
    return stripped.casefold()


def element_matches_named_target_ref(element: object, target_ref: str | None) -> bool:
    """True when *element* is in scope for *target_ref*.

    Empty / None / ALL / * / ANY is unrestricted: every instance of the type
    (same as ``is_unrestricted_target_ref``). A named ref that is a valid IFC
    GlobalId matches only ``element.GlobalId`` with exact equality after strip —
    the token is case-sensitive (ISO 10303-21). Other IfcRoot identity attributes
    (Name, LongName, Tag, ObjectType, Description) use ``str.casefold``
    exact-token match, not a substring.
    """

    if is_unrestricted_target_ref(target_ref):
        return True
    raw = (target_ref or "").strip()
    if not raw:
        # Empty needle is already unrestricted; keep ALL semantics explicit.
        return True

    guid = getattr(element, "GlobalId", None)
    if guid is not None and str(guid).strip() == raw:
        return True
    if is_valid_ifc_global_id(raw):
        return False

    needle = raw.casefold()
    for attribute_name in ELEMENT_TARGET_REF_FOLD_ATTRIBUTES:
        value = getattr(element, attribute_name, None)
        if value is not None and str(value).strip().casefold() == needle:
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
    "ELEMENT_TARGET_REF_FOLD_ATTRIBUTES",
    "UNRESTRICTED_ELEMENT_MISMATCH_CAP",
    "UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER",
    "UNRESTRICTED_TARGET_REF_TOKENS",
    "element_matches_named_target_ref",
    "is_unrestricted_target_ref",
    "named_target_ref_cache_key",
    "target_ref_matches",
    "unrestricted_mismatch_suppressor_message",
]
