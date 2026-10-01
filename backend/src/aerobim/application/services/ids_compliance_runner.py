"""IDS, schema, BSI and OpenRebar policy extracted from AnalyzeProjectPackageUseCase."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationRequest,
)
from aerobim.domain.ports import (
    BsiValidationService,
    IdsDocumentAuditor,
    IdsValidator,
    IfcSchemaValidator,
    SectionDiffAnalyzer,
)

_logger = logging.getLogger("aerobim.analyze")

OPENREBAR_WARNING_SEVERITY_CLASS: dict[str, str] = {
    "OPENREBAR-CONTRACT": "critical",
    "OPENREBAR-PROVENANCE-DIGEST": "critical",
    "OPENREBAR-PROVENANCE-REFERENCE-MISSING": "critical",
    "OPENREBAR-OPT-FALLBACK": "major",
    "OPENREBAR-OPT-STRATEGY": "major",
    "OPENREBAR-WASTE-METRIC-MISSING": "major",
    "OPENREBAR-WASTE-THRESHOLD": "major",
    "OPENREBAR-PROJECT-CODE": "minor",
}
OPENREBAR_ENFORCED_ESCALATION_CLASSES = {"critical", "major"}


class IdsComplianceRunner:
    def __init__(
        self,
        *,
        ids_validator: IdsValidator | None,
        ids_document_auditor: IdsDocumentAuditor | None,
        ifc_schema_validator: IfcSchemaValidator | None,
        bsi_validation_service: BsiValidationService | None,
        section_diff_analyzer: SectionDiffAnalyzer | None,
        require_bsi_schema: bool,
    ) -> None:
        self._ids_validator = ids_validator
        self._ids_document_auditor = ids_document_auditor
        self._ifc_schema_validator = ifc_schema_validator
        self._bsi_validation_service = bsi_validation_service
        self._section_diff_analyzer = section_diff_analyzer
        self._require_bsi_schema = require_bsi_schema

    def submit_bsi_validation(self, ifc_path: Path) -> tuple[str | None, list[ValidationIssue]]:
        if self._bsi_validation_service is None:
            return None, []
        try:
            request_id = self._bsi_validation_service.submit(ifc_path)
            return request_id, []
        except Exception as exc:
            severity = Severity.ERROR if self._require_bsi_schema else Severity.WARNING
            return None, [
                ValidationIssue(
                    rule_id="AEROBIM-BSI-VALIDATION",
                    severity=severity,
                    message=f"bSI Validation Service / schema certificate submit failed: {exc}",
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="bsi-schema",
                )
            ]

    def collect_schema_issues(self, ifc_path: Path) -> list[ValidationIssue]:
        if self._ifc_schema_validator is None:
            return []
        return list(self._ifc_schema_validator.validate_schema(ifc_path))

    def collect_ids_audit_issues(self, request: ValidationRequest) -> list[ValidationIssue]:
        if request.ids_path is None:
            return []
        if self._ids_document_auditor is None:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-AUDIT-CAPABILITY",
                    severity=Severity.ERROR,
                    message=(
                        "IDS document audit requested but no ids document auditor is configured"
                    ),
                    category=FindingCategory.IDS_VALIDATION,
                    source_id="ids",
                )
            ]
        return list(self._ids_document_auditor.audit(request.ids_path))

    def collect_ids_issues(self, request: ValidationRequest) -> list[ValidationIssue]:
        if request.ids_path is None:
            return []
        if self._ids_validator is None:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-CAPABILITY",
                    severity=Severity.ERROR,
                    message="IDS validation requested but no ids validator is configured",
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="ids",
                )
            ]
        if request.ifc_path is None:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-CAPABILITY",
                    severity=Severity.ERROR,
                    message="IDS validation requested but ifc_path was omitted",
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="ids",
                )
            ]
        try:
            return list(self._ids_validator.validate(request.ids_path, request.ifc_path))
        except Exception as exc:
            _logger.exception("IDS validation failed for %s", request.ids_path)
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-ERROR",
                    severity=Severity.ERROR,
                    message=f"IDS validation infrastructure failure: {exc}",
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="ids",
                )
            ]

    def apply_openrebar_provenance_policy(
        self,
        issues: Sequence[ValidationIssue],
        mode: str,
    ) -> list[ValidationIssue]:
        if mode != "enforced":
            return list(issues)

        escalated: list[ValidationIssue] = []
        for issue in issues:
            if issue.severity != Severity.WARNING:
                escalated.append(issue)
                continue
            severity_class = OPENREBAR_WARNING_SEVERITY_CLASS.get(issue.rule_id, "major")
            if severity_class not in OPENREBAR_ENFORCED_ESCALATION_CLASSES:
                escalated.append(issue)
                continue
            escalated.append(
                ValidationIssue(
                    rule_id=issue.rule_id,
                    severity=Severity.ERROR,
                    message=issue.message,
                    ifc_entity=issue.ifc_entity,
                    category=issue.category,
                    target_ref=issue.target_ref,
                    property_set=issue.property_set,
                    property_name=issue.property_name,
                    operator=issue.operator,
                    expected_value=issue.expected_value,
                    observed_value=issue.observed_value,
                    unit=issue.unit,
                    element_guid=issue.element_guid,
                    problem_zone=issue.problem_zone,
                    remark=issue.remark,
                )
            )
        return escalated

    def collect_section_pairing_issues(
        self,
        request: ValidationRequest,
    ) -> tuple[tuple[ValidationIssue, ...], CapabilityStatus]:
        pd_path = request.pd_section_path
        rd_path = request.rd_section_path
        if pd_path is None and rd_path is None:
            return (), CapabilityStatus(
                CapabilityState.SKIPPED, "PD/RD section pairing not requested"
            )
        if pd_path is None or rd_path is None:
            raise ValueError(
                "PD/RD section pairing requires both pd_section_path and rd_section_path"
            )
        if self._section_diff_analyzer is None:
            raise RuntimeError("PD/RD section pairing requested but no analyzer is configured")
        report = self._section_diff_analyzer.analyze(pd_path, rd_path)
        reason = report.capability_reason(pd_path.name, rd_path.name)
        if (
            (not report.discipline.recognized)
            or (report.pd_key_count > 0 and report.recognized_key_count == 0)
            or bool(report.unrecognized_keys)
        ):
            return report.issues, CapabilityStatus(CapabilityState.FAILED, reason)
        return report.issues, CapabilityStatus(CapabilityState.OK, reason)
