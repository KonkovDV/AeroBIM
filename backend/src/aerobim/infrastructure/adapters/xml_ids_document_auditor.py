"""IDS document self-audit before model validation (IDS Audit Tool class).

Phase 7: reject unsupported facets and empty applicability — no silent skip.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

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
        "description",
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


class XmlIdsDocumentAuditor:
    """Validates IDS XML structure and fails closed on unsupported facets."""

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
            tree = ET.parse(ids_path)
            root = tree.getroot()
        except ET.ParseError as exc:
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
