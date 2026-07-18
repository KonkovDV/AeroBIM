"""Lightweight IFC SPF / schema pre-gate (bSI Validation Service class)."""

from __future__ import annotations

import re
from pathlib import Path

from aerobim.domain.models import FindingCategory, Severity, ValidationIssue

# Supported public IFC schema tokens for pilot honesty (SPF FILE_SCHEMA).
_SUPPORTED_SCHEMAS = frozenset(
    {
        "IFC2X3",
        "IFC4",
        "IFC4X3",
        "IFC4X3_ADD1",
        "IFC4X3_ADD2",
        "IFC4X3_TC1",
    }
)
_FILE_SCHEMA_RE = re.compile(
    r"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'",
    re.IGNORECASE | re.DOTALL,
)


class BasicIfcSchemaValidator:
    """Checks ISO-10303-21 envelope and FILE_SCHEMA identity without full EXPRESS."""

    def validate_schema(self, ifc_path: Path) -> list[ValidationIssue]:
        if not ifc_path.exists() or not ifc_path.is_file():
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IFC-SCHEMA",
                    severity=Severity.ERROR,
                    message=f"IFC file not found for schema pre-gate: {ifc_path}",
                    category=FindingCategory.IFC_VALIDATION,
                    origin="deterministic",
                )
            ]

        try:
            with ifc_path.open("rb") as handle:
                prefix = handle.read(64 * 1024)
            text = prefix.decode("utf-8", errors="replace")
        except OSError as exc:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IFC-SCHEMA",
                    severity=Severity.ERROR,
                    message=f"Unable to read IFC for schema pre-gate: {exc}",
                    category=FindingCategory.IFC_VALIDATION,
                    origin="deterministic",
                )
            ]

        issues: list[ValidationIssue] = []
        head = text.lstrip()
        if not head.upper().startswith("ISO-10303-21"):
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-IFC-SCHEMA",
                    severity=Severity.ERROR,
                    message="IFC SPF pre-gate failed: missing ISO-10303-21 header",
                    category=FindingCategory.IFC_VALIDATION,
                    origin="deterministic",
                )
            )
        if "HEADER;" not in text.upper():
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-IFC-SCHEMA",
                    severity=Severity.ERROR,
                    message="IFC SPF pre-gate failed: missing HEADER section",
                    category=FindingCategory.IFC_VALIDATION,
                    origin="deterministic",
                )
            )
        match = _FILE_SCHEMA_RE.search(text)
        if match is None:
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-IFC-SCHEMA",
                    severity=Severity.ERROR,
                    message="IFC SPF pre-gate failed: missing FILE_SCHEMA declaration",
                    category=FindingCategory.IFC_VALIDATION,
                    origin="deterministic",
                )
            )
        else:
            schema_token = match.group(1).strip().upper()
            normalized = schema_token.replace(" ", "").replace(".", "")
            if normalized not in _SUPPORTED_SCHEMAS and schema_token not in _SUPPORTED_SCHEMAS:
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-IFC-SCHEMA-UNSUPPORTED",
                        severity=Severity.ERROR,
                        message=(
                            f"Unsupported or unrecognized IFC FILE_SCHEMA {schema_token!r}; "
                            f"supported={sorted(_SUPPORTED_SCHEMAS)}"
                        ),
                        category=FindingCategory.IFC_VALIDATION,
                        origin="deterministic",
                        expected_value="|".join(sorted(_SUPPORTED_SCHEMAS)),
                        observed_value=schema_token,
                    )
                )
        return issues
