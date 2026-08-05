"""Select GOST R 21.101 edition label for a documentation check run.

Rules live in ``samples/config/documentation-standard-edition.json``.
This module only applies an already-loaded rule mapping — no hard-coded
statutory interpretation beyond date comparison.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

DEFAULT_CONFIG_RELATIVE = "samples/config/documentation-standard-edition.json"


def select_documentation_standard_edition(
    *,
    package_developed_on: str | None = None,
    explicit_edition: str | None = None,
    rule: Mapping[str, Any] | None = None,
) -> tuple[str | None, str]:
    """Return ``(edition_id, selection_source)``.

    ``rule`` expects the ``selection_rule`` object from the config JSON
    (or a compatible mapping). If ``explicit_edition`` is set, it wins.
    """

    explicit = (explicit_edition or "").strip() or None
    if explicit:
        return explicit, "explicit_inventory_field"

    if rule is None:
        return None, "no_rule"

    cutoff = str(rule.get("cutoff_exclusive") or "").strip()
    before = str(rule.get("before_cutoff") or "").strip() or None
    after = str(rule.get("on_or_after_cutoff") or "").strip() or None
    developed = (package_developed_on or "").strip() or None
    if not developed or not cutoff:
        return None, "missing_package_developed_on_or_cutoff"
    # ISO date lexicographic compare is valid for YYYY-MM-DD.
    if developed < cutoff:
        return before, "config_date_cutoff_before"
    return after, "config_date_cutoff_on_or_after"


def load_selection_rule(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Extract ``selection_rule`` from a full config document."""

    raw = payload.get("selection_rule")
    return raw if isinstance(raw, Mapping) else None
