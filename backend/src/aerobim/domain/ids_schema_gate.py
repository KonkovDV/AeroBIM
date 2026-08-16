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
RULE_STATUS_TYPE = "AEROBIM-IDS-STATUS-TYPE"

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
    r"ViewDefinition\s*\[([^\]]+)\]",
    re.IGNORECASE,
)
_SPEC_OPEN_RE = re.compile(r"<(?:[\w.-]+:)?specification\b([^>]*)>", re.IGNORECASE)
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


@dataclass(frozen=True)
class IfcFileNameHeader:
    """ISO-10303-21 FILE_NAME fields used to identify the exporting system."""

    name: str
    timestamp: str
    preprocessor_version: str
    originating_system: str
    authorization: str


def _extract_step_call_inner(header_text: str, call_name: str) -> str | None:
    match = re.search(rf"{re.escape(call_name)}\s*\(", header_text, re.IGNORECASE)
    if match is None:
        return None
    start = match.end()
    depth = 1
    in_string = False
    index = start
    while index < len(header_text):
        char = header_text[index]
        if in_string:
            if char == "'" and index + 1 < len(header_text) and header_text[index + 1] == "'":
                index += 2
                continue
            if char == "'":
                in_string = False
            index += 1
            continue
        if char == "'":
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return header_text[start:index]
        index += 1
    return None


def _split_step_args(inner: str) -> tuple[str, ...]:
    args: list[str] = []
    buf: list[str] = []
    depth = 0
    in_string = False
    index = 0
    while index < len(inner):
        char = inner[index]
        if in_string:
            if char == "'" and index + 1 < len(inner) and inner[index + 1] == "'":
                buf.append("''")
                index += 2
                continue
            buf.append(char)
            if char == "'":
                in_string = False
            index += 1
            continue
        if char == "'":
            in_string = True
            buf.append(char)
        elif char == "(":
            depth += 1
            buf.append(char)
        elif char == ")":
            depth -= 1
            buf.append(char)
        elif char == "," and depth == 0:
            args.append("".join(buf).strip())
            buf = []
        else:
            buf.append(char)
        index += 1
    tail = "".join(buf).strip()
    if tail:
        args.append(tail)
    return tuple(args)


def _unquote_step_string(raw: str) -> str:
    text = raw.strip()
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'":
        return text[1:-1].replace("''", "'")
    return text


def parse_ifc_file_name(header_text: str) -> IfcFileNameHeader | None:
    """Parse FILE_NAME preprocessor / originating_system from an IFC header."""
    inner = _extract_step_call_inner(header_text, "FILE_NAME")
    if inner is None:
        return None
    args = _split_step_args(inner)
    if len(args) < 6:
        return None
    return IfcFileNameHeader(
        name=_unquote_step_string(args[0]),
        timestamp=_unquote_step_string(args[1]),
        preprocessor_version=_unquote_step_string(args[4]),
        originating_system=_unquote_step_string(args[5]),
        authorization=_unquote_step_string(args[6]) if len(args) > 6 else "",
    )


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
        versions = parse_ids_ifc_version_tokens(version_match.group(2) if version_match else None)
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


def ids_reporter_status_is_bool(status: object) -> bool:
    """IfcTester Json reporter emits JSON booleans. Any other type is format drift."""

    return isinstance(status, bool)
