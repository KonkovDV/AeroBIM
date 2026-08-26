"""AGR exchange-shape checks (class 1). No new port.

Moscow CIM AGR wording (TechLab brief 0.5, 14.08.2026): IFC4 ReferenceView,
IFC SPF, no IfcBuildingElementProxy, five-field filename, file ≤500 MB.

This is NOT the moscow_agr profile: no УКЭП, no CRS, no MSSK.
TEP XML sidecar presence is class-1 well-formed XML. Official ДГП example
``AGR_TEO.xml`` (root ``ArchitecturalUrbanPlanningSolution``) and official
``Vedomost_AGR_VED_NEW.xsd`` are public city files, not a Samolet pack.
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.ids_schema_gate import (
    normalize_ifc_schema_token,
    parse_ifc_file_schema,
    parse_ifc_view_definition,
)
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue

RULE_SCHEMA = "AEROBIM-AGR-IFC-SCHEMA"
RULE_VIEW = "AEROBIM-AGR-REFERENCE-VIEW"
RULE_PROXY = "AEROBIM-AGR-PROXY-BANNED"
RULE_SIZE = "AEROBIM-AGR-FILE-SIZE"
RULE_FILENAME = "AEROBIM-AGR-FILENAME"
RULE_TEP_XML = "AEROBIM-AGR-TEP-XML"
RULE_TEP_ROOT = "AEROBIM-AGR-TEP-ROOT"
RULE_VEDOMOST_XSD = "AEROBIM-AGR-VEDOMOST-XSD"
OFFICIAL_TEP_ROOT = "ArchitecturalUrbanPlanningSolution"

CLAIM_BOUNDARY = (
    "AGR exchange-shape checks on a fixture (class 1). Not moscow_agr profile. "
    "Not УКЭП. Not CRS. Not MSSK. Official ДГП TEP example + Vedomost XSD "
    "are public city files, not a Samolet-signed acceptance pack. "
    "Not customer CIM acceptance. Cited NPA is territorial (Moscow 17-PP + "
    "DGP-R-1/26); the stroimprosto IDS zip is not itself an NPA. Does not "
    "substitute GrK art. 49 expertise, PP 614 IM obligation, or an AGR certificate."
)
REQUIRED_SCHEMA = "IFC4"
MAX_IFC_BYTES = 500 * 1024 * 1024
FILENAME_FIELD_COUNT = 5
# Windows-incompatible + whitespace. Official Moscow forbidden set is not vendored.
FORBIDDEN_FILENAME_CHARS = frozenset('<>:"/\\|?* \t\n\r')
IFC_PROXY_ENTITY = "IFCBUILDINGELEMENTPROXY"


def split_five_field_filename(filename: str) -> tuple[str, ...] | None:
    stem = Path(filename).name
    if stem.lower().endswith(".ifc"):
        stem = stem[:-4]
    parts = stem.split("_")
    if len(parts) != FILENAME_FIELD_COUNT:
        return None
    if any(not part.strip() for part in parts):
        return None
    return tuple(parts)


def filename_forbidden_chars(filename: str) -> tuple[str, ...]:
    found = {char for char in filename if char in FORBIDDEN_FILENAME_CHARS}
    return tuple(sorted(found))


def collect_agr_exchange_issues(
    *,
    filename: str,
    header_text: str,
    body_text: str,
    size_bytes: int,
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    schema = parse_ifc_file_schema(header_text)
    view = parse_ifc_view_definition(header_text)

    if normalize_ifc_schema_token(schema or "") != REQUIRED_SCHEMA:
        issues.append(
            _issue(
                RULE_SCHEMA,
                (
                    f"FILE_SCHEMA {schema or '(missing)'} is not {REQUIRED_SCHEMA}; "
                    f"Moscow AGR CIM exchange is IFC4 ReferenceView; {CLAIM_BOUNDARY}"
                ),
                expected=REQUIRED_SCHEMA,
                observed=schema,
            )
        )

    view_folded = (view or "").casefold()
    if "referenceview" not in view_folded:
        issues.append(
            _issue(
                RULE_VIEW,
                (
                    f"FILE_DESCRIPTION view {view or '(missing)'} is not ReferenceView; "
                    f"{CLAIM_BOUNDARY}"
                ),
                expected="ReferenceView",
                observed=view,
            )
        )

    if IFC_PROXY_ENTITY in body_text.upper():
        issues.append(
            _issue(
                RULE_PROXY,
                (
                    "IfcBuildingElementProxy occurrence is forbidden for Moscow AGR CIM "
                    f"except documented exceptions (none declared on this fixture); "
                    f"{CLAIM_BOUNDARY}"
                ),
                expected="no IfcBuildingElementProxy",
                observed="IFCBUILDINGELEMENTPROXY",
            )
        )

    if size_bytes > MAX_IFC_BYTES:
        issues.append(
            _issue(
                RULE_SIZE,
                (f"IFC size {size_bytes} bytes exceeds {MAX_IFC_BYTES} (500 MB); {CLAIM_BOUNDARY}"),
                expected=str(MAX_IFC_BYTES),
                observed=str(size_bytes),
            )
        )

    parts = split_five_field_filename(filename)
    forbidden = filename_forbidden_chars(Path(filename).name)
    if parts is None or forbidden:
        detail = []
        if parts is None:
            detail.append(f"need exactly {FILENAME_FIELD_COUNT} '_' fields")
        if forbidden:
            shown = " ".join(repr(char) for char in forbidden)
            detail.append(f"forbidden characters {shown}")
        issues.append(
            _issue(
                RULE_FILENAME,
                (
                    f"filename {filename!r} fails AGR exchange shape ({'; '.join(detail)}); "
                    f"{CLAIM_BOUNDARY}"
                ),
                expected="5 underscore fields, no forbidden charset",
                observed=filename,
            )
        )
    return tuple(issues)


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def collect_agr_tep_xml_issues(
    *,
    xml_path: Path | None,
    expected_root: str | None = None,
) -> tuple[ValidationIssue, ...]:
    """Sidecar presence + well-formed XML; optional official TEP root local-name."""
    if xml_path is None or not xml_path.is_file():
        return (
            _issue(
                RULE_TEP_XML,
                (
                    "AGR exchange requires a TEP XML sidecar with the IFC (ДГП-Р-1/26); "
                    f"sidecar missing; {CLAIM_BOUNDARY}"
                ),
                expected="well-formed XML sidecar",
                observed="missing",
            ),
        )
    try:
        from defusedxml import ElementTree

        root = ElementTree.parse(xml_path).getroot()
    except Exception as exc:
        return (
            _issue(
                RULE_TEP_XML,
                f"TEP XML sidecar is not well-formed XML ({exc}); {CLAIM_BOUNDARY}",
                expected="well-formed XML sidecar",
                observed=xml_path.name,
            ),
        )
    if root is None:
        return (
            _issue(
                RULE_TEP_XML,
                f"TEP XML sidecar has no root element; {CLAIM_BOUNDARY}",
                expected="well-formed XML sidecar",
                observed=xml_path.name,
            ),
        )
    if expected_root:
        observed = _local_tag(str(root.tag))
        if observed != expected_root:
            return (
                _issue(
                    RULE_TEP_ROOT,
                    (
                        f"TEP XML root {observed!r} is not official ДГП example "
                        f"root {expected_root!r}; {CLAIM_BOUNDARY}"
                    ),
                    expected=expected_root,
                    observed=observed,
                ),
            )
    return ()


def collect_agr_vedomost_xsd_issues(
    *,
    xml_path: Path | None,
    xsd_path: Path,
) -> tuple[ValidationIssue, ...]:
    """Official ДГП Vedomost_AGR XSD. Not TEP AGR_TEO.xml. Not Samolet pack."""
    if xml_path is None or not xml_path.is_file():
        return (
            _issue(
                RULE_VEDOMOST_XSD,
                f"AGR CIM inventory XML sidecar missing; {CLAIM_BOUNDARY}",
                expected="Vedomost XML valid against official XSD",
                observed="missing",
            ),
        )
    if not xsd_path.is_file():
        return (
            _issue(
                RULE_VEDOMOST_XSD,
                f"Official Vedomost XSD missing at {xsd_path.name}; {CLAIM_BOUNDARY}",
                expected="Vedomost_AGR_VED_NEW.xsd",
                observed="missing-xsd",
            ),
        )
    try:
        import xmlschema
    except ImportError as exc:
        return (
            _issue(
                RULE_VEDOMOST_XSD,
                f"xmlschema not installed ({exc}); {CLAIM_BOUNDARY}",
                expected="xmlschema XMLSchema10",
                observed="unavailable",
            ),
        )
    try:
        schema = xmlschema.XMLSchema10(str(xsd_path))
        errors = list(schema.iter_errors(str(xml_path)))
    except Exception as exc:
        return (
            _issue(
                RULE_VEDOMOST_XSD,
                f"Vedomost XSD validation could not run ({exc}); {CLAIM_BOUNDARY}",
                expected="schema load + validate",
                observed=type(exc).__name__,
            ),
        )
    if errors:
        first = errors[0]
        return (
            _issue(
                RULE_VEDOMOST_XSD,
                (f"Vedomost XML fails official ДГП XSD ({first}); {CLAIM_BOUNDARY}"),
                expected="valid against Vedomost_AGR_VED_NEW.xsd",
                observed=xml_path.name,
            ),
        )
    return ()


def _issue(
    rule_id: str,
    message: str,
    *,
    expected: str | None,
    observed: str | None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        message=message,
        category=FindingCategory.IFC_VALIDATION,
        origin="deterministic",
        expected_value=expected,
        observed_value=observed,
        evidence_refs=("claim_boundary:agr_exchange_shape",),
        source_id="agr-exchange-fixture",
    )
