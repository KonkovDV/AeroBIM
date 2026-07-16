"""Lightweight IFC SPF / schema pre-gate (bSI Validation Service class)."""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.models import FindingCategory, Severity, ValidationIssue


class BasicIfcSchemaValidator:
    """Checks ISO-10303-21 envelope and FILE_SCHEMA presence without full EXPRESS."""

    def validate_schema(self, ifc_path: Path) -> list[ValidationIssue]:
        if not ifc_path.exists() or not ifc_path.is_file():
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IFC-SCHEMA",
                    severity=Severity.ERROR,
                    message=f"IFC file not found for schema pre-gate: {ifc_path}",
                    category=FindingCategory.IFC_VALIDATION,
                )
            ]

        try:
            # Read a bounded prefix — enough for HEADER section on typical models.
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
                )
            )
        if "HEADER;" not in text.upper():
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-IFC-SCHEMA",
                    severity=Severity.ERROR,
                    message="IFC SPF pre-gate failed: missing HEADER section",
                    category=FindingCategory.IFC_VALIDATION,
                )
            )
        if "FILE_SCHEMA" not in text.upper():
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-IFC-SCHEMA",
                    severity=Severity.ERROR,
                    message="IFC SPF pre-gate failed: missing FILE_SCHEMA declaration",
                    category=FindingCategory.IFC_VALIDATION,
                )
            )
        return issues
