"""IDS document self-audit before model validation (IDS Audit Tool class).

Phase 7: reject unsupported facets and empty applicability — no silent skip.
Wave F (2026-07-25): official IDS 1.0 XSD validation against the vendored
buildingSMART schema (``samples/ids-xsd/ids.xsd``), following the
IDS-Audit-tool practice (schema audit before semantic audit). Fail-honest:
missing validator/schema is reported as an explicit WARNING, never silent OK.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import ParseError

from aerobim.core.security.xml_limits import XmlBombError, safe_parse
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue

# IDS 1.0 facet local-names (case-insensitive) accepted by AeroBIM / IfcTester path.
_ALLOWED_FACET_NAMES = frozenset(
    {
        "entity",
        "attribute",
        "property",
        "classification",
        "material",
        "partof",
        "restrictions",
        "restriction",
        "enumeration",
        "pattern",
        "bounds",
        "length",
        "value",
        "baseNames",  # rare
        "basenames",
    }
)

# Structural IDS containers — not facets.
_STRUCTURAL_NAMES = frozenset(
    {
        "ids",
        "informationsdeliveryspecification",
        "info",
        "title",
        "copyright",
        "version",
        "description",
        "author",
        "date",
        "purpose",
        "milestone",
        "specifications",
        "specification",
        "applicability",
        "requirements",
        "requirement",
        "name",
        "instructions",
        "ifcversion",
        "identifier",
        "simplevalue",
        "uri",
        "system",
        "value",
        "cardinality",
        "datatype",
        "minoccurs",
        "maxoccurs",
        "relation",
    }
)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def default_ids_xsd_path() -> Path | None:
    """Vendored official IDS 1.0 schema, if present in the repo."""

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "samples" / "ids-xsd" / "ids.xsd"
        if candidate.is_file():
            return candidate
    return None


@lru_cache(maxsize=2)
def _load_ids_schema(xsd_path: str) -> Any:
    """Build the XSD once per path; raises if xmlschema/schema are unusable.

    The official ids.xsd imports W3C base schemas by http URL; we remap those
    URLs to the copies bundled inside the ``xmlschema`` package so the build
    stays offline (SSRF guard: no outbound fetch from a validator).
    """

    import xmlschema

    bundled = Path(xmlschema.__file__).resolve().parent / "schemas"
    w3c_local = {
        "http://www.w3.org/2001/xml.xsd": (bundled / "XML" / "xml.xsd").as_uri(),
        "http://www.w3.org/2001/XMLSchema.xsd": (bundled / "XSD_1.0" / "XMLSchema.xsd").as_uri(),
        "http://www.w3.org/2001/XMLSchema-instance": (
            bundled / "XSI" / "XMLSchema-instance.xsd"
        ).as_uri(),
    }

    def _uri_mapper(uri: str) -> str:
        return w3c_local.get(uri, uri)

    return xmlschema.XMLSchema10(xsd_path, uri_mapper=_uri_mapper)


def _xsd_audit_issues(ids_path: Path, xsd_path: Path | None) -> list[ValidationIssue]:
    """Official-schema audit. Explicit WARNING when validation cannot run."""

    if xsd_path is None:
        return [
            ValidationIssue(
                rule_id="AEROBIM-IDS-XSD-CAPABILITY",
                severity=Severity.WARNING,
                message=(
                    "Official IDS 1.0 XSD not available (samples/ids-xsd/ids.xsd); "
                    "schema validation skipped — structural audit only"
                ),
                category=FindingCategory.IDS_VALIDATION,
                origin="deterministic",
                source_id=str(ids_path.name),
            )
        ]
    try:
        schema = _load_ids_schema(str(xsd_path))
    except Exception as exc:  # noqa: BLE001 — validator absence must be visible
        return [
            ValidationIssue(
                rule_id="AEROBIM-IDS-XSD-CAPABILITY",
                severity=Severity.WARNING,
                message=f"IDS XSD validator unavailable ({exc}); schema validation skipped",
                category=FindingCategory.IDS_VALIDATION,
                origin="deterministic",
                source_id=str(ids_path.name),
            )
        ]
    issues: list[ValidationIssue] = []
    try:
        errors = list(schema.iter_errors(str(ids_path)))
    except Exception as exc:  # noqa: BLE001 — malformed input handled upstream too
        errors = []
        issues.append(
            ValidationIssue(
                rule_id="AEROBIM-IDS-XSD-INVALID",
                severity=Severity.ERROR,
                message=f"IDS document failed official XSD validation: {exc}",
                category=FindingCategory.IDS_VALIDATION,
                origin="deterministic",
                source_id=str(ids_path.name),
            )
        )
    for error in errors[:20]:
        reason = str(getattr(error, "reason", None) or error).strip().splitlines()[0]
        path_hint = getattr(error, "path", None)
        issues.append(
            ValidationIssue(
                rule_id="AEROBIM-IDS-XSD-INVALID",
                severity=Severity.ERROR,
                message=(
                    f"IDS document violates official IDS 1.0 XSD at "
                    f"{path_hint or '<document>'}: {reason}"
                ),
                category=FindingCategory.IDS_VALIDATION,
                origin="deterministic",
                source_id=str(ids_path.name),
                target_ref=str(path_hint) if path_hint else None,
            )
        )
    return issues


class XmlIdsDocumentAuditor:
    """Validates IDS XML structure and fails closed on unsupported facets.

    Audit layers (IDS-Audit-tool alignment):
    1. well-formedness + root sanity (fail-closed ERROR);
    2. official IDS 1.0 XSD validation (ERROR per finding; WARNING when the
       validator/schema is unavailable — never silent);
    3. AeroBIM structural rules (unsupported facets, empty applicability).
    """

    def __init__(self, *, xsd_path: Path | None = None) -> None:
        self._xsd_path = xsd_path if xsd_path is not None else default_ids_xsd_path()

    def audit(self, ids_path: Path) -> list[ValidationIssue]:
        if not ids_path.exists() or not ids_path.is_file():
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-AUDIT",
                    severity=Severity.ERROR,
                    message=f"IDS document not found: {ids_path}",
                    category=FindingCategory.IDS_VALIDATION,
                    origin="deterministic",
                )
            ]

        try:
            tree = safe_parse(ids_path)
            root = tree.getroot()
        except (ParseError, XmlBombError) as exc:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-AUDIT",
                    severity=Severity.ERROR,
                    message=f"IDS document is not well-formed XML: {exc}",
                    category=FindingCategory.IDS_VALIDATION,
                    origin="deterministic",
                )
            ]
        except OSError as exc:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-AUDIT",
                    severity=Severity.ERROR,
                    message=f"Unable to read IDS document: {exc}",
                    category=FindingCategory.IDS_VALIDATION,
                    origin="deterministic",
                )
            ]

        if root is None:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-AUDIT",
                    severity=Severity.ERROR,
                    message="IDS document has no root element",
                    category=FindingCategory.IDS_VALIDATION,
                    origin="deterministic",
                )
            ]

        local_name = _local(root.tag)
        if local_name.lower() not in {"ids", "informationsdeliveryspecification"}:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-AUDIT",
                    severity=Severity.ERROR,
                    message=(
                        f"IDS document root element '{local_name}' is not an IDS root "
                        "(expected ids / informationsDeliverySpecification)"
                    ),
                    category=FindingCategory.IDS_VALIDATION,
                    origin="deterministic",
                )
            ]

        issues: list[ValidationIssue] = []
        issues.extend(_xsd_audit_issues(ids_path, self._xsd_path))
        for node in root.iter():
            name = _local(node.tag).lower()
            if name in {"applicability", "requirements"}:
                facet_children = [
                    child
                    for child in list(node)
                    if _local(child.tag).lower()
                    not in {
                        "instructions",
                        "description",
                        "name",
                        "identifier",
                    }
                ]
                if name == "applicability" and not facet_children:
                    issues.append(
                        ValidationIssue(
                            rule_id="AEROBIM-IDS-EMPTY-APPLICABILITY",
                            severity=Severity.ERROR,
                            message="IDS specification has empty applicability (no facets)",
                            category=FindingCategory.IDS_VALIDATION,
                            origin="deterministic",
                            source_id=str(ids_path.name),
                        )
                    )
                for child in facet_children:
                    child_name = _local(child.tag).lower()
                    if child_name in _STRUCTURAL_NAMES:
                        continue
                    if child_name not in _ALLOWED_FACET_NAMES:
                        issues.append(
                            ValidationIssue(
                                rule_id="AEROBIM-IDS-UNSUPPORTED-FACET",
                                severity=Severity.ERROR,
                                message=(
                                    f"Unsupported IDS facet '{_local(child.tag)}' under "
                                    f"{name}; silent skip is forbidden"
                                ),
                                category=FindingCategory.IDS_VALIDATION,
                                origin="deterministic",
                                source_id=str(ids_path.name),
                                observed_value=_local(child.tag),
                            )
                        )
        return issues
