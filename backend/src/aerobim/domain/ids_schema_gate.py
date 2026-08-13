"""Fail-closed IDS ``ifcVersion`` vs IFC ``FILE_SCHEMA`` gate.

IfcTester 0.8.x records ``is_ifc_version`` but still executes the spec
(``should_filter_version`` defaults to False). Official buildingSMART case
0101 states that specification version is purely metadata. AeroBIM does not
accept that as a silent pass: a spec that names IFC2X3 must not look clean
on an IFC4 model. Domain-pure — no IfcTester import.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

RULE_IFC_VERSION = "AEROBIM-IDS-IFC-VERSION"
RULE_SKIPPED = "AEROBIM-IDS-SKIPPED"

# Same default list IfcTester uses when the attribute is omitted.
DEFAULT_IDS_IFC_VERSIONS: frozenset[str] = frozenset({"IFC2X3", "IFC4", "IFC4X3_ADD2"})

_FILE_SCHEMA_RE = re.compile(
    r"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'",
    re.IGNORECASE | re.DOTALL,
)
_FILE_DESCRIPTION_RE = re.compile(
    r"FILE_DESCRIPTION\s*\(\s*\(\s*'([^']+)'",
    re.IGNORECASE | re.DOTALL,
)
_VIEW_DEFINITION_RE = re.compile(
    r"ViewDefinition\[([^\]]+)\]",
    re.IGNORECASE,
)
_SPEC_OPEN_RE = re.compile(r"<specification\b([^>]*)>", re.IGNORECASE)
_NAME_ATTR_RE = re.compile(r"""\bname\s*=\s*(['"])(.*?)\1""", re.IGNORECASE | re.DOTALL)
_VERSION_ATTR_RE = re.compile(
    r"""\bifcVersion\s*=\s*(['"])(.*?)\1""",
    re.IGNORECASE | re.DOTALL,
)


def normalize_ifc_schema_token(raw: str) -> str:
    return raw.strip().upper().replace(" ", "").replace(".", "")


def parse_ifc_file_schema(header_text: str) -> str | None:
    match = _FILE_SCHEMA_RE.search(header_text)
    if match is None:
        return None
    token = normalize_ifc_schema_token(match.group(1))
    return token or None


def parse_ifc_view_definition(header_text: str) -> str | None:
    """Return the ViewDefinition token from FILE_DESCRIPTION, if present."""
    match = _FILE_DESCRIPTION_RE.search(header_text)
    if match is None:
        return None
    inner = _VIEW_DEFINITION_RE.search(match.group(1))
    token = (inner.group(1) if inner else match.group(1)).strip()
    return token or None


def parse_ids_ifc_version_tokens(raw: str | None) -> frozenset[str]:
    if raw is None:
        return DEFAULT_IDS_IFC_VERSIONS
    tokens = [normalize_ifc_schema_token(part) for part in raw.split()]
    normalized = frozenset(token for token in tokens if token)
    return normalized or DEFAULT_IDS_IFC_VERSIONS


@dataclass(frozen=True)
class IdsSpecificationVersions:
    name: str
    versions: frozenset[str]


def parse_ids_specification_versions(ids_xml: str) -> tuple[IdsSpecificationVersions, ...]:
    specs: list[IdsSpecificationVersions] = []
    for index, match in enumerate(_SPEC_OPEN_RE.finditer(ids_xml), start=1):
        attrs = match.group(1)
        name_match = _NAME_ATTR_RE.search(attrs)
        version_match = _VERSION_ATTR_RE.search(attrs)
        name = (name_match.group(2).strip() if name_match else "") or f"specification-{index}"
        versions = parse_ids_ifc_version_tokens(
            version_match.group(2) if version_match else None
        )
        specs.append(IdsSpecificationVersions(name=name, versions=versions))
    return tuple(specs)


def model_schema_allowed(model_schema: str, ids_versions: frozenset[str]) -> bool:
    token = normalize_ifc_schema_token(model_schema)
    allowed = {normalize_ifc_schema_token(item) for item in ids_versions}
    return bool(token) and token in allowed


@dataclass(frozen=True)
class IdsSchemaMismatch:
    spec_name: str
    model_schema: str
    ids_versions: tuple[str, ...]


def collect_schema_mismatches(
    *,
    model_schema: str | None,
    specs: tuple[IdsSpecificationVersions, ...],
) -> tuple[IdsSchemaMismatch, ...]:
    if not model_schema:
        return tuple(
            IdsSchemaMismatch(
                spec_name=spec.name,
                model_schema="",
                ids_versions=tuple(sorted(spec.versions)),
            )
            for spec in specs
        )
    mismatches: list[IdsSchemaMismatch] = []
    for spec in specs:
        if not model_schema_allowed(model_schema, spec.versions):
            mismatches.append(
                IdsSchemaMismatch(
                    spec_name=spec.name,
                    model_schema=normalize_ifc_schema_token(model_schema),
                    ids_versions=tuple(sorted(spec.versions)),
                )
            )
    return tuple(mismatches)


def skipped_spec_fail_closed_rule_id(
    *,
    is_skipped: object = None,
    status: object = None,
    is_ifc_version: object = None,
) -> str | None:
    """Return the fail-closed rule id, or None if IfcTester's pass may stand.

    ``is_ifc_version is False`` is the silent metadata pass (BSI 0101).
    ``status is None`` means the spec never ran.
    ``is_skipped is True`` is optional/zero-check skip in the Json reporter.
    """

    if is_ifc_version is False:
        return RULE_IFC_VERSION
    if status is None:
        return RULE_SKIPPED
    if is_skipped is True:
        return RULE_SKIPPED
    return None
