from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.domain.models import Severity, ValidationReport, ValidationRequest, ValidationSummary
from aerobim.domain.ports import AuditReportStore, IdsValidator, IfcValidator, RequirementExtractor


class ValidateIfcAgainstIdsUseCase:
    def __init__(
        self,
        requirement_extractor: RequirementExtractor,
        ifc_validator: IfcValidator,
        audit_report_store: AuditReportStore,
        ids_validator: IdsValidator | None = None,
    ) -> None:
        self._requirement_extractor = requirement_extractor
        self._ifc_validator = ifc_validator
        self._audit_report_store = audit_report_store
        self._ids_validator = ids_validator

    def execute(self, request: ValidationRequest) -> ValidationReport:
        requirements = tuple(self._requirement_extractor.extract(request.requirement_source))
        if not requirements and not getattr(request, "ids_path", None):
            raise ValueError("No requirements were extracted from the provided source")

        issues_list = (
            list(self._ifc_validator.validate(request.ifc_path, requirements))
            if requirements
            else []
        )

        ids_path: Path | None = getattr(request, "ids_path", None)
        if ids_path is not None and self._ids_validator is not None:
            ids_issues = self._ids_validator.validate(ids_path, request.ifc_path)
            issues_list.extend(ids_issues)

        issues = tuple(issues_list)
        severity_counts = Counter(issue.severity for issue in issues)
        error_count = severity_counts[Severity.ERROR]
        warning_count = severity_counts[Severity.WARNING]

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
                passed=error_count == 0,
            ),
        )
        self._audit_report_store.save(report)
        return report
