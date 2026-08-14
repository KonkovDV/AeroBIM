"""ECPE/EGRZ XML *intake* pre-check. Not expertise. Not RT-001 CLOSED.

Adjacent to RT-001: EGRZ/ECPE returns packages in minutes for XML/format
failures *before* an expert writes remarks. That is not a dual-adjudicated
remark corpus (PP RF 878 of 24.07.2017 §23 remains metadata).

Vendored MinStroy XSD 1.1 files. Catalog subsections p9_4 / p12_2 (retrieved
2026-08-14) include PZ **01.07** and ZnP **01.01**, matching ECPE in-force
versions from 2026-06-11. Zip member folders still contain ``dev_``; the XSD
``SchemaVersion`` attributes are fixed 01.07 / 01.01. XMLSchema11 cannot load
PZ/ZnP *as published* (duplicate xml:id='Name' on xs:documentation). Load-time
strip of those attributes is a parser workaround, not a modified official
file in git. Do not treat XMLSchema10 empty-elements as a validator. No new
port.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Final, Literal

from aerobim.domain.models import FindingCategory, Severity, ValidationIssue

SchemaKind = Literal["conclusion", "explanatory_note", "design_assignment"]

AS_OF: Final = "2026-08-14"
CATALOG_PAGE: Final = "https://minstroyrf.gov.ru/tim/xml-skhemy/"
ECPE_IN_FORCE_SINCE: Final = "2026-06-11"
ECPE_CITATION: Final = "https://www.xn--13-6kclkmgo9almibr3n.xn--p1ai/useful-information/769/"

RULE_MISSING = "AEROBIM-EGRZ-XML-MISSING"
RULE_WELLFORMED = "AEROBIM-EGRZ-XML-WELLFORMED"
RULE_ROOT = "AEROBIM-EGRZ-XML-ROOT"
RULE_STALE = "AEROBIM-EGRZ-XML-SCHEMA-STALE"
RULE_PARSER = "AEROBIM-EGRZ-XML-PARSER-BLOCKED"
RULE_XSD = "AEROBIM-EGRZ-XML-XSD"

_XML_ID_ATTR = re.compile(r'\s+xml:id="[^"]*"')

CLAIM_BOUNDARY = (
    "EGRZ/ECPE XML intake pre-check on published MinStroy XSD. Not GrK art. 49 "
    "expertise, not a remark corpus, not УКЭП, not 783/пр compliance of a "
    "customer package. PZ 01.07 / ZnP 01.01 match ECPE in-force versions; "
    "XMLSchema11 still needs a documentation xml:id strip to load those two "
    "files. Official zip folders contain 'dev_'. Checkpoint NO_GO. "
    "closes_rt001=false."
)

SCHEMA_CATALOG: Final[tuple[dict[str, Any], ...]] = (
    {
        "kind": "conclusion",
        "instrument_id": "MINSTROY-CONCLUSION-XSD-01-03",
        "rel": "samples/xsd/minstroy/conclusion-01-03.xsd",
        "listed_version": "01.03",
        "ecpe_in_force_version": "01.03",
        "stale_vs_ecpe": False,
        "root_localname": "Conclusion",
        "xsd_processor": "XMLSchema11",
        "loadable_xmlschema11": True,
        "loadable_xmlschema11_after_doc_id_sanitize": True,
        "load_blocker": None,
        "catalog_zip_url": (
            "https://minstroyrf.gov.ru/upload/iblock/02a/"
            "m2h9oxr3th3jv94m2cmc27hifv7lnn5n/"
            "1_XML_skhema_zaklyucheniya_ekspertizy_V1_03.zip"
        ),
        "zip_member": "conclusion-01-03.xsd",
    },
    {
        "kind": "explanatory_note",
        "instrument_id": "MINSTROY-PZ-XSD-01-07",
        "rel": "samples/xsd/minstroy/explanatorynote-01-07.xsd",
        "listed_version": "01.07",
        "ecpe_in_force_version": "01.07",
        "stale_vs_ecpe": False,
        "root_localname": "ExplanatoryNote",
        "xsd_processor": "XMLSchema11",
        "loadable_xmlschema11": False,
        "loadable_xmlschema11_after_doc_id_sanitize": True,
        "load_blocker": "duplicate_xml_id_Name",
        "ecpe_in_force_since": ECPE_IN_FORCE_SINCE,
        "ecpe_citation": ECPE_CITATION,
        "catalog_subsection": (
            "https://minstroyrf.gov.ru/tim/xml-skhemy/"
            "razdel-1-proektnoy-dokumentatsii-poyasnitelnaya-zapiska/p9_4/"
        ),
        "catalog_zip_url": (
            "https://minstroyrf.gov.ru/upload/iblock/155/"
            "iezb8pgqdluz2c6r8y0n9g7nwcogynf2/"
            "%D0%A0%D0%B0%D0%B7%D0%B4%D0%B5%D0%BB%20%E2%84%961%20"
            "%D0%BF%D1%80%D0%BE%D0%B5%D0%BA%D1%82%D0%BD%D0%BE%D0%B9%20"
            "%D0%B4%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D0%B0%D1%86%D0%B8%D0%B8%20"
            "%C2%AB%D0%9F%D0%BE%D1%8F%D1%81%D0%BD%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%B0%D1%8F%20"
            "%D0%B7%D0%B0%D0%BF%D0%B8%D1%81%D0%BA%D0%B0%C2%BB.zip"
        ),
        "zip_member": (
            "explanatorynote-dev_explanatorynote_v_1_07/explanatorynote-01-07.xsd"
        ),
        "zip_member_folder_note": (
            "official zip folder name contains 'dev_'; SchemaVersion is fixed 01.07"
        ),
    },
    {
        "kind": "design_assignment",
        "instrument_id": "MINSTROY-ZNP-XSD-01-01",
        "rel": "samples/xsd/minstroy/DesignAssignment-01-01.xsd",
        "listed_version": "01.01",
        "ecpe_in_force_version": "01.01",
        "stale_vs_ecpe": False,
        "root_localname": "Document",
        "xsd_processor": "XMLSchema11",
        "loadable_xmlschema11": False,
        "loadable_xmlschema11_after_doc_id_sanitize": True,
        "load_blocker": "duplicate_xml_id_Name",
        "ecpe_in_force_since": ECPE_IN_FORCE_SINCE,
        "ecpe_citation": ECPE_CITATION,
        "catalog_subsection": (
            "https://minstroyrf.gov.ru/tim/xml-skhemy/zadanie-na-proektirovanie/p12_2/"
        ),
        "catalog_zip_url": (
            "https://minstroyrf.gov.ru/upload/iblock/91a/"
            "3w3v4ujw8ykwyrjymu2oqtehhmr1wza9/"
            "%D0%97%D0%B0%D0%B4%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%BD%D0%B0%20"
            "%D0%BF%D1%80%D0%BE%D0%B5%D0%BA%D1%82%D0%B8%D1%80%D0%BE%D0%B2%D0%B0"
            "%D0%BD%D0%B8%D0%B5.zip"
        ),
        "zip_member": (
            "DesignAssignment-dev_DesignAssignment_v_1_01/DesignAssignment-01-01.xsd"
        ),
        "zip_member_folder_note": (
            "official zip folder name contains 'dev_'; SchemaVersion is fixed 01.01"
        ),
    },
)

_SCHEMA_CACHE: dict[str, Any] = {}


def minstroy_xml_schema_catalog() -> tuple[dict[str, Any], ...]:
    return SCHEMA_CATALOG


def schema_by_kind(kind: SchemaKind) -> dict[str, Any]:
    for row in SCHEMA_CATALOG:
        if row["kind"] == kind:
            return row
    raise KeyError(f"unknown MinStroy XML schema kind {kind!r}")


def strip_documentation_xml_ids(xsd_text: str) -> str:
    """Drop xml:id on XSD text. Official PZ/ZnP files duplicate xml:id='Name'."""

    return _XML_ID_ATTR.sub("", xsd_text)


def egrz_intake_catalog_snapshot() -> dict[str, Any]:
    """JSON-safe catalog for rehearsal payloads. Does not load XSD."""

    rows = list(SCHEMA_CATALOG)
    return {
        "as_of": AS_OF,
        "catalog_page": CATALOG_PAGE,
        "ecpe_in_force_since": ECPE_IN_FORCE_SINCE,
        "ecpe_citation": ECPE_CITATION,
        "closes_rt001": False,
        "no_pass_fixture": True,
        "loadable_kinds": [row["kind"] for row in rows if row["loadable_xmlschema11"]],
        "sanitize_loadable_kinds": [
            row["kind"] for row in rows if row["loadable_xmlschema11_after_doc_id_sanitize"]
        ],
        "stale_kinds": [row["kind"] for row in rows if row["stale_vs_ecpe"]],
        "schemas": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def collect_egrz_xml_validate_issues(
    *,
    kind: SchemaKind,
    xml_path: Path | None,
    xsd_path: Path,
) -> tuple[ValidationIssue, ...]:
    """Fail-closed intake checks. Never reports schema-valid as RT-001 CLOSED."""

    row = schema_by_kind(kind)
    expected_root = str(row["root_localname"])
    issues: list[ValidationIssue] = []

    if bool(row["stale_vs_ecpe"]):
        issues.append(
            _issue(
                RULE_STALE,
                Severity.ERROR,
                (
                    f"Vendored {kind} XSD {row['listed_version']} is SCHEMA_STALE vs "
                    f"ECPE in-force {row['ecpe_in_force_version']} since "
                    f"{ECPE_IN_FORCE_SINCE}; {CLAIM_BOUNDARY}"
                ),
                expected=str(row["ecpe_in_force_version"]),
                observed=str(row["listed_version"]),
            )
        )

    if xml_path is None or not xml_path.is_file():
        issues.append(
            _issue(
                RULE_MISSING,
                Severity.ERROR,
                f"{kind} XML instance missing; {CLAIM_BOUNDARY}",
                expected=f"{expected_root} XML",
                observed="missing",
            )
        )
        return tuple(issues)

    parsed = _parse_root(xml_path)
    if parsed is None:
        issues.append(
            _issue(
                RULE_WELLFORMED,
                Severity.ERROR,
                f"{xml_path.name} is not well-formed XML; {CLAIM_BOUNDARY}",
                expected="well-formed XML",
                observed=xml_path.name,
            )
        )
        return tuple(issues)

    observed_root = _local_tag(parsed)
    if observed_root != expected_root:
        issues.append(
            _issue(
                RULE_ROOT,
                Severity.ERROR,
                (
                    f"XML root {observed_root!r} is not {expected_root!r} for {kind}; "
                    f"{CLAIM_BOUNDARY}"
                ),
                expected=expected_root,
                observed=observed_root,
            )
        )
        return tuple(issues)

    if not xsd_path.is_file():
        issues.append(
            _issue(
                RULE_MISSING,
                Severity.ERROR,
                f"MinStroy XSD missing at {xsd_path.name}; {CLAIM_BOUNDARY}",
                expected=str(row["rel"]),
                observed="missing-xsd",
            )
        )
        return tuple(issues)

    try:
        import xmlschema
    except ImportError as exc:
        issues.append(
            _issue(
                RULE_XSD,
                Severity.ERROR,
                f"xmlschema not installed ({exc}); {CLAIM_BOUNDARY}",
                expected="xmlschema XMLSchema11",
                observed="unavailable",
            )
        )
        return tuple(issues)

    try:
        _load_xmlschema11(xmlschema, xsd_path)
    except Exception as exc:  # noqa: BLE001 — official XSD quality
        issues.append(
            _issue(
                RULE_PARSER,
                Severity.ERROR,
                (
                    f"XMLSchema11 cannot load {kind} XSD "
                    f"({row['load_blocker'] or type(exc).__name__}); do not treat "
                    f"XMLSchema10 empty elements as a validator; {CLAIM_BOUNDARY}"
                ),
                expected="XMLSchema11 loadable schema",
                observed=str(row["load_blocker"] or type(exc).__name__),
            )
        )
        return tuple(issues)

    issues.extend(_xsd11_errors(xsd_path, xml_path))
    return tuple(issues)


def _parse_root(xml_path: Path) -> str | None:
    try:
        from defusedxml import ElementTree

        root = ElementTree.parse(xml_path).getroot()
    except Exception:  # noqa: BLE001 — fixture parse path
        return None
    if root is None:
        return None
    return str(root.tag)


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _xsd11_errors(xsd_path: Path, xml_path: Path) -> tuple[ValidationIssue, ...]:
    try:
        import xmlschema
    except ImportError as exc:
        return (
            _issue(
                RULE_XSD,
                Severity.ERROR,
                f"xmlschema not installed ({exc}); {CLAIM_BOUNDARY}",
                expected="xmlschema XMLSchema11",
                observed="unavailable",
            ),
        )
    try:
        schema = _load_xmlschema11(xmlschema, xsd_path)
        errors = list(schema.iter_errors(str(xml_path)))
    except Exception as exc:  # noqa: BLE001 — official XSD quality
        return (
            _issue(
                RULE_XSD,
                Severity.ERROR,
                f"XSD 1.1 validation could not run ({exc}); {CLAIM_BOUNDARY}",
                expected="schema load + validate",
                observed=type(exc).__name__,
            ),
        )
    if not errors:
        return ()
    first = errors[0]
    return (
        _issue(
            RULE_XSD,
            Severity.ERROR,
            f"XML fails MinStroy XSD 1.1 ({first}); {CLAIM_BOUNDARY}",
            expected="valid against loadable XSD 1.1",
            observed=xml_path.name,
        ),
    )


def _load_xmlschema11(xmlschema: Any, xsd_path: Path) -> Any:
    key = str(xsd_path.resolve())
    cached = _SCHEMA_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        schema = xmlschema.XMLSchema11(str(xsd_path))
    except Exception:
        raw = xsd_path.read_text(encoding="utf-8")
        sanitized = strip_documentation_xml_ids(raw)
        if sanitized == raw:
            raise
        schema = xmlschema.XMLSchema11(sanitized)
    _SCHEMA_CACHE[key] = schema
    return schema


def _issue(
    rule_id: str,
    severity: Severity,
    message: str,
    *,
    expected: str | None,
    observed: str | None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        severity=severity,
        message=message,
        category=FindingCategory.CROSS_DOCUMENT,
        origin="deterministic",
        expected_value=expected,
        observed_value=observed,
        evidence_refs=("claim_boundary:egrz_intake_precheck",),
        source_id="egrz-intake-xml",
    )
