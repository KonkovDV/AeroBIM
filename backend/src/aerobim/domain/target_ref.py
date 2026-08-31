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
# Tokens that mean "do not filter by Name/Tag/GlobalId/Description".
# An element whose Name is literally "ALL" cannot be selected via target_ref;
# address it by GlobalId. Empty / None is the same as ALL (column omitted).
UNRESTRICTED_TARGET_REF_TOKENS: Final[frozenset[str]] = frozenset(
    {"", "all", "*", "any"}
)

# Per-element value mismatches on unrestricted rules. Full-set EXISTS/EQ
# gaps are one coverage row, not N issues. Cap prevents a 20k-row flood from
# an unsigned ALL+eq pack; suppressed rows are not a customer defect list.
UNRESTRICTED_ELEMENT_MISMATCH_CAP: Final = 50


def is_unrestricted_target_ref(target_ref: str | None) -> bool:
    """True when the requirement applies to every instance of its ifc_entity."""

    if target_ref is None:
        return True
    return target_ref.strip().casefold() in UNRESTRICTED_TARGET_REF_TOKENS


def target_ref_matches(requirement_ref: str | None, observed_ref: str) -> bool:
    """Match a requirement target_ref to an observed Name/annotation ref."""

    if is_unrestricted_target_ref(requirement_ref):
        return True
    assert requirement_ref is not None
    return requirement_ref.strip().lower() == observed_ref.strip().lower()


__all__ = [
    "UNRESTRICTED_ELEMENT_MISMATCH_CAP",
    "UNRESTRICTED_TARGET_REF_TOKENS",
    "is_unrestricted_target_ref",
    "target_ref_matches",
]
