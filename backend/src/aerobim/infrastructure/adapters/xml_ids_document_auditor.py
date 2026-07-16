"""IDS document self-audit before model validation (IDS Audit Tool class)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from aerobim.domain.models import FindingCategory, Severity, ValidationIssue


class XmlIdsDocumentAuditor:
    """Validates that an IDS file is well-formed XML with an IDS root element."""

    def audit(self, ids_path: Path) -> list[ValidationIssue]:
        if not ids_path.exists() or not ids_path.is_file():
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-AUDIT",
                    severity=Severity.ERROR,
                    message=f"IDS document not found: {ids_path}",
                    category=FindingCategory.IDS_VALIDATION,
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
                )
            ]
        except OSError as exc:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-AUDIT",
                    severity=Severity.ERROR,
                    message=f"Unable to read IDS document: {exc}",
                    category=FindingCategory.IDS_VALIDATION,
                )
            ]

        local_name = root.tag.rsplit("}", 1)[-1]
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
                )
            ]
        return []
