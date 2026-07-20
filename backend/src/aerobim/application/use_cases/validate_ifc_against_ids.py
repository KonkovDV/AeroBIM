from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.application.services.package_outcome import compute_package_outcome
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ReportCapabilities,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
    ValidationSummary,
)
from aerobim.domain.package_outcome import summary_passed_from_outcome
from aerobim.domain.ports import (
    AuditReportStore,
    IdsDocumentAuditor,
    IdsValidator,
    IfcSchemaValidator,
    IfcValidator,
    RequirementExtractor,
)


class ValidateIfcAgainstIdsUseCase:
    def __init__(
        self,
        requirement_extractor: RequirementExtractor,
        ifc_validator: IfcValidator,
        audit_report_store: AuditReportStore,
        ids_validator: IdsValidator | None = None,
        ifc_schema_validator: IfcSchemaValidator | None = None,
        ids_document_auditor: IdsDocumentAuditor | None = None,
        signoff_profile: str = "development",
        require_clash: bool = False,
        clash_affects_pass: bool = False,
        require_bsi_schema: bool = False,
        require_mep_system_clash: bool = False,
    ) -> None:
        self._requirement_extractor = requirement_extractor
        self._ifc_validator = ifc_validator
        self._audit_report_store = audit_report_store
        self._ids_validator = ids_validator
        self._ifc_schema_validator = ifc_schema_validator
        self._ids_document_auditor = ids_document_auditor
        self._signoff_policy = build_signoff_policy(
            profile=signoff_profile,
            require_clash=require_clash,
            clash_affects_pass=clash_affects_pass,
            require_bsi_schema=require_bsi_schema,
            require_mep_system_clash=require_mep_system_clash,
        )

    def execute(self, request: ValidationRequest) -> ValidationReport:
        requirements = tuple(self._requirement_extractor.extract(request.requirement_source))
        if not requirements and not getattr(request, "ids_path", None):
            raise ValueError("No requirements were extracted from the provided source")

        schema_issues = (
            list(self._ifc_schema_validator.validate_schema(request.ifc_path))
            if self._ifc_schema_validator is not None
            else []
        )
        ids_audit_issues: list[ValidationIssue] = []
        ids_path: Path | None = getattr(request, "ids_path", None)
        if ids_path is not None:
            if self._ids_document_auditor is None:
                # RT D01/D04: never silent-skip a requested IDS audit capability.
                ids_audit_issues = [
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
            else:
                ids_audit_issues = list(self._ids_document_auditor.audit(ids_path))

        issues_list = list(schema_issues)
        issues_list.extend(ids_audit_issues)
        if requirements:
            issues_list.extend(self._ifc_validator.validate(request.ifc_path, requirements))

        if ids_path is not None and self._ids_validator is not None and not ids_audit_issues:
            ids_issues = self._ids_validator.validate(ids_path, request.ifc_path)
            issues_list.extend(ids_issues)

        issues = tuple(issues_list)
        severity_counts = Counter(issue.severity for issue in issues)
        error_count = severity_counts[Severity.ERROR]
        warning_count = severity_counts[Severity.WARNING]

        if self._ifc_schema_validator is None:
            schema_cap = CapabilityStatus(
                CapabilityState.SKIPPED, "IFC schema pre-gate not configured"
            )
        elif schema_issues:
            schema_cap = CapabilityStatus(CapabilityState.FAILED, schema_issues[0].message)
        else:
            schema_cap = CapabilityStatus(CapabilityState.OK)

        if ids_path is None:
            ids_cap = CapabilityStatus(CapabilityState.SKIPPED, "IDS validation not requested")
        elif ids_audit_issues:
            ids_cap = CapabilityStatus(CapabilityState.FAILED, ids_audit_issues[0].message)
        elif self._ids_validator is None:
            ids_cap = CapabilityStatus(CapabilityState.FAILED, "IDS validator not configured")
        else:
            ids_cap = CapabilityStatus(CapabilityState.OK)

        capabilities = ReportCapabilities(
            ifc_schema=schema_cap,
            ids=ids_cap,
            ifc_validation=(
                CapabilityStatus(CapabilityState.OK)
                if requirements
                else CapabilityStatus(CapabilityState.SKIPPED, "no IFC property requirements")
            ),
        )
        outcome = compute_package_outcome(
            error_count=error_count,
            warning_count=warning_count,
            capabilities=capabilities,
            intake_blocked=False,
            policy=self._signoff_policy,
        )
        passed = summary_passed_from_outcome(outcome)
        soft_profile = self._signoff_policy.profile in {"development", "fixture"}
        report = ValidationReport(
            report_id=uuid4().hex,
            request_id=request.request_id,
            ifc_path=request.ifc_path,
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=requirements,
            issues=issues,
            summary=ValidationSummary(
                requirement_count=len(requirements),
                issue_count=len(issues),
                error_count=error_count,
                warning_count=warning_count,
                passed=passed,
                authoritative=not (soft_profile and passed),
                outcome=outcome,
            ),
            capabilities=capabilities,
            project_name=request.project_name,
            discipline=request.discipline,
            stage=request.stage,
            information_container_id=request.information_container_id,
            revision=request.revision,
            doc_status=request.doc_status,
            tenant_id=request.tenant_id,
            project_id=request.project_id,
        )
        self._audit_report_store.save(report)
        return report
