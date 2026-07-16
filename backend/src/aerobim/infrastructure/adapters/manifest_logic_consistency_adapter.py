"""Package-level logical consistency (orphan sheets, unpaired PD/RD, sparse ingest)."""

from __future__ import annotations

from aerobim.domain.consistency import PackageManifest
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue


class ManifestLogicConsistencyAdapter:
    def analyze(self, manifest: PackageManifest) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if manifest.pd_section_path is not None and manifest.rd_section_path is None:
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-LOGIC-PD-WITHOUT-RD",
                    severity=Severity.WARNING,
                    message="PD section provided without RD pair — section pairing incomplete",
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id="logic-consistency",
                )
            )
        if manifest.rd_section_path is not None and manifest.pd_section_path is None:
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-LOGIC-RD-WITHOUT-PD",
                    severity=Severity.WARNING,
                    message="RD section provided without PD pair — section pairing incomplete",
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id="logic-consistency",
                )
            )

        if manifest.drawing_count > 0:
            missing_sheets = sum(1 for sheet in manifest.drawing_sheet_ids if not sheet.strip())
            if missing_sheets:
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-LOGIC-ORPHAN-SHEET",
                        severity=Severity.INFO,
                        message=(
                            f"{missing_sheets} drawing source(s) lack sheet_id — "
                            "expert review may miss spatial highlight targets"
                        ),
                        category=FindingCategory.DRAWING_VALIDATION,
                        source_id="logic-consistency",
                    )
                )

        if (
            not manifest.has_requirement_source
            and not manifest.has_ids
            and not manifest.has_technical_spec
        ):
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-LOGIC-SPARSE-PACKAGE",
                    severity=Severity.WARNING,
                    message=(
                        "Package has neither structured requirements, IDS, "
                        "nor technical specification"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id="logic-consistency",
                )
            )

        if manifest.has_calculation_source and not manifest.has_requirement_source:
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-LOGIC-CALC-WITHOUT-REQ",
                    severity=Severity.INFO,
                    message=(
                        "Calculation source present without structured requirements — "
                        "load сверка is advisory-only relative to IFC rules"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id="logic-consistency",
                )
            )

        return issues
