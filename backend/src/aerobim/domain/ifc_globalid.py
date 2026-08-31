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
_SPF_ENTITY_FIRST_STRING = re.compile(
    r"^#\d+\s*=\s*(IFC[A-Z0-9_]+)\s*\(\s*'([^']*)'",
    re.IGNORECASE,
)

# IfcPropertyDefinition subtypes whose first attribute IS GlobalId.
_IFC_ROOT_PROPERTY_FAMILY = frozenset(
    {
        "PROPERTYSET",
        "PROPERTYSETTEMPLATE",
        "QUANTITYSET",
        "COMPLEXPROPERTYTEMPLATE",
        "SIMPLEPROPERTYTEMPLATE",
        "PROPERTYTEMPLATE",
    }
)

# Types that share an allow-prefix but are NOT IfcRoot (first attr is not GlobalId).
_IFC_ROOT_ALLOW_COLLISIONS = frozenset(
    {
        "ACTORROLE",
        "COSTVALUE",
        "ELEMENTARYSURFACE",
        "GRIDAXIS",
        "GRIDPLACEMENT",
        "PRODUCTDEFINITIONSHAPE",
        "VIRTUALGRIDINTERSECTION",
    }
)

# Default-deny: only these prefixes (plus PROPERTYSET family, REL*, *TYPE) are
# scanned as IfcRoot GlobalId. False negatives go to ifcopenshell IfcRoot scan.
_IFC_ROOT_ALLOW_PREFIXES = (
    "REL",
    "PROJECT",
    "SITE",
    "BUILDING",
    "SPACE",
    "SPATIAL",
    "ZONE",
    "GROUP",
    "SYSTEM",
    "ANNOTATION",
    "WALL",
    "SLAB",
    "DOOR",
    "WINDOW",
    "COLUMN",
    "BEAM",
    "MEMBER",
    "PLATE",
    "STAIR",
    "RAILING",
    "RAMP",
    "ROOF",
    "COVERING",
    "CHIMNEY",
    "PILE",
    "FOOTING",
    "CURTAIN",
    "OPENING",
    "FURNISH",
    "TRANSPORT",
    "ELECTRIC",
    "ENERGY",
    "FLOW",
    "DISTRIBUTION",
    "DUCT",
    "PIPE",
    "CABLE",
    "SANITARY",
    "PROXY",
    "TASK",
    "EVENT",
    "PROCEDURE",
    "WORK",
    "CONTROL",
    "PERMIT",
    "ACTION",
    "PERFORMANCE",
    "OCCUPANT",
    "PROCESS",
    "CONSTRUCTION",
    "CREW",
    "LABOR",
    "SUBCONTRACT",
    "BOILER",
    "CHILLER",
    "COIL",
    "FAN",
    "FILTER",
    "PUMP",
    "VALVE",
    "DAMPER",
    "SENSOR",
    "ACTUATOR",
    "ALARM",
    "CONTROLLER",
    "UNITARY",
    "PROTECTIVE",
    "SWITCHING",
    "LAMP",
    "OUTLET",
    "STACK",
    "TANK",
    "BURNER",
    "CONDENSER",
    "EVAPORATOR",
    "HUMIDIFIER",
    "SPACEHEATER",
    "INTERCEPTOR",
    "FIRE",
    "MEDICAL",
    "COMMUNICATION",
    "AUDIOVISUAL",
    "TRANSFORMER",
    "GENERATOR",
    "MOTOR",
    "ENGINE",
    "SOLAR",
    "BATTERY",
)

_IFC_ROOT_ALLOW_EXACT = frozenset(
    {
        "ACTOR",
        "COSTITEM",
        "COSTSCHEDULE",
        "ELEMENTASSEMBLY",
        "ELEMENTQUANTITY",
        "GRID",
        "VIRTUALELEMENT",
        "BUILDINGELEMENTPART",
    }
)


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


def spf_entity_first_attr_is_global_id(entity_type: str) -> bool:
    """True when the first SPF attribute of *entity_type* is IfcRoot.GlobalId.

    Default-deny: unknown types are not scanned. A missed rooted type is still
    covered by ``collect_global_id_integrity_issues`` on ``IfcRoot``. False
    positives (22-character Name on IfcProperty/IfcMaterial) must not happen.
    """

    raw = entity_type.strip().upper()
    name = raw[3:] if raw.startswith("IFC") else raw
    if name in _IFC_ROOT_PROPERTY_FAMILY:
        return True
    if name.startswith("PROPERTY"):
        return False
    if name in _IFC_ROOT_ALLOW_COLLISIONS:
        return False
    if name in _IFC_ROOT_ALLOW_EXACT:
        return True
    if name.endswith("TYPE") and name != "QUANTITYTYPE":
        return True
    return name.startswith(_IFC_ROOT_ALLOW_PREFIXES)


def spf_line_rooted_global_id(line: str) -> str | None:
    """Return a valid IfcRoot GlobalId from one SPF DATA line, or None.

    The schema pre-gate used to treat any 22-character first quoted string as
    a GUID. IfcPropertySingleValue.Name and IfcMaterial.Name are often 22
    characters (``TreadLengthAtInnerSide``, ``Stainless Steel_Weland``) and
    repeat across instances — that is not a duplicate GlobalId.
    """

    match = _SPF_ENTITY_FIRST_STRING.match(line.lstrip("\ufeff").strip())
    if match is None:
        return None
    entity_type, first_attr = match.group(1), match.group(2)
    if not spf_entity_first_attr_is_global_id(entity_type):
        return None
    if not is_valid_ifc_global_id(first_attr):
        return None
    return first_attr


_SPF_ENTITY_START = re.compile(r"^#\d+\s*=\s*IFC[A-Z0-9_]+", re.IGNORECASE)


def iter_spf_entity_heads(lines: Iterable[str]) -> Iterable[str]:
    """Yield entity-start text, joining the next line when the GUID is wrapped."""

    pending: str | None = None
    for raw in lines:
        text = raw.strip()
        if pending is not None:
            pending = f"{pending} {text}"
            if "'" in pending or len(pending) > 8192 or text.endswith(";"):
                yield pending
                pending = None
            continue
        if not text.startswith("#"):
            continue
        if _SPF_ENTITY_FIRST_STRING.match(text):
            yield text
            continue
        if _SPF_ENTITY_START.match(text):
            pending = text
    if pending is not None:
        yield pending


__all__ = [
    "collect_global_id_integrity_issues",
    "is_valid_ifc_global_id",
    "iter_spf_entity_heads",
    "spf_entity_first_attr_is_global_id",
    "spf_line_rooted_global_id",
]
