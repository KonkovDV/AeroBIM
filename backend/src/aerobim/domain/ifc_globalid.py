"""IFC GlobalId integrity helpers (Phase 7).

buildingSMART IFC GlobalIds are 22-character base64-like tokens (IFC compressed GUID).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from typing import Any

from aerobim.domain.models import FindingCategory, Severity, ValidationIssue

# IFC compressed GUID alphabet (IfcGloballyUniqueId).
_GUID_RE = re.compile(r"^[0-9A-Za-z_$]{22}$")


def is_valid_ifc_global_id(value: str | None) -> bool:
    if value is None:
        return False
    text = value.strip()
    if not text:
        return False
    return _GUID_RE.fullmatch(text) is not None


def collect_global_id_integrity_issues(
    elements: Iterable[Any],
    *,
    source_id: str = "ifc-globalid",
) -> list[ValidationIssue]:
    """Emit ERROR findings for invalid or duplicate GlobalIds on IFC elements."""

    issues: list[ValidationIssue] = []
    seen: list[str] = []
    for element in elements:
        raw = getattr(element, "GlobalId", None)
        if raw is None:
            continue
        guid = str(raw).strip()
        ifc_type = type(element).__name__
        if not is_valid_ifc_global_id(guid):
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-IFC-GUID-INVALID",
                    severity=Severity.ERROR,
                    message=f"Invalid IFC GlobalId on {ifc_type}: {guid!r}",
                    category=FindingCategory.IFC_VALIDATION,
                    ifc_entity=ifc_type,
                    element_guid=guid or None,
                    source_id=source_id,
                    origin="deterministic",
                    evidence_refs=(f"{source_id}#guid:{guid or 'empty'}",),
                )
            )
            continue
        seen.append(guid)

    counts = Counter(seen)
    for guid, count in sorted(counts.items()):
        if count < 2:
            continue
        issues.append(
            ValidationIssue(
                rule_id="AEROBIM-IFC-GUID-DUPLICATE",
                severity=Severity.ERROR,
                message=f"Duplicate IFC GlobalId {guid!r} occurs {count} times",
                category=FindingCategory.IFC_VALIDATION,
                element_guid=guid,
                source_id=source_id,
                origin="deterministic",
                evidence_refs=(f"{source_id}#guid:{guid}",),
            )
        )
    return issues


__all__ = [
    "collect_global_id_integrity_issues",
    "is_valid_ifc_global_id",
]
