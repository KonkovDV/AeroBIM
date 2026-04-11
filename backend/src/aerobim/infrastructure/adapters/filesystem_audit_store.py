from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from aerobim.domain.models import (
    ComparisonOperator,
    DrawingAnnotation,
    FindingCategory,
    GeneratedRemark,
    ParsedRequirement,
    ProblemZone,
    ReportSummaryEntry,
    RuleScope,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)


class FilesystemAuditStore:
    """Persists validation reports as JSON files with atomic writes."""

    def __init__(self, storage_dir: Path) -> None:
        self._reports_dir = storage_dir / "reports"
        self._reports_dir.mkdir(parents=True, exist_ok=True)

    def save(self, report: ValidationReport) -> str:
        data = asdict(report)
        data["ifc_path"] = str(report.ifc_path)
        target = self._reports_dir / f"{report.report_id}.json"
        tmp = self._reports_dir / f"{report.report_id}.tmp"
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(str(tmp), str(target))
        return report.report_id

    def get(self, report_id: str) -> ValidationReport | None:
        target = self._reports_dir / f"{report_id}.json"
        if not target.exists():
            return None
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            return self._reconstruct_report(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def list_reports(self) -> list[ReportSummaryEntry]:
        entries: list[ReportSummaryEntry] = []
        for path in sorted(self._reports_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                summary = data.get("summary", {})
                entries.append(
                    ReportSummaryEntry(
                        report_id=data["report_id"],
                        request_id=data["request_id"],
                        created_at=data["created_at"],
                        passed=summary.get("passed", False),
                        issue_count=summary.get("issue_count", 0),
                    )
                )
            except (json.JSONDecodeError, KeyError):
                continue
        return entries

    def _reconstruct_report(self, data: dict) -> ValidationReport:
        return ValidationReport(
            report_id=data["report_id"],
            request_id=data["request_id"],
            ifc_path=Path(data["ifc_path"]),
            created_at=data["created_at"],
            requirements=tuple(self._reconstruct_requirement(r) for r in data.get("requirements", [])),
            issues=tuple(self._reconstruct_issue(i) for i in data.get("issues", [])),
            summary=self._reconstruct_summary(data.get("summary", {})),
            drawing_annotations=tuple(
                self._reconstruct_annotation(a) for a in data.get("drawing_annotations", [])
            ),
        )

    def _reconstruct_requirement(self, data: dict) -> ParsedRequirement:
        return ParsedRequirement(
            rule_id=data["rule_id"],
            ifc_entity=data.get("ifc_entity"),
            rule_scope=RuleScope(data["rule_scope"]) if data.get("rule_scope") else RuleScope.IFC_PROPERTY,
            target_ref=data.get("target_ref"),
            property_set=data.get("property_set"),
            property_name=data.get("property_name"),
            operator=ComparisonOperator(data["operator"]) if data.get("operator") else ComparisonOperator.EQUALS,
            expected_value=data.get("expected_value"),
            unit=data.get("unit"),
            source=data.get("source", ""),
            source_kind=SourceKind(data["source_kind"]) if data.get("source_kind") else SourceKind.STRUCTURED_TEXT,
            evidence_text=data.get("evidence_text"),
            instructions=data.get("instructions"),
            evidence_modality=data.get("evidence_modality"),
        )

    def _reconstruct_issue(self, data: dict) -> ValidationIssue:
        problem_zone_data = data.get("problem_zone")
        remark_data = data.get("remark")
        return ValidationIssue(
            rule_id=data["rule_id"],
            severity=Severity(data["severity"]),
            message=data["message"],
            ifc_entity=data.get("ifc_entity"),
            category=FindingCategory(data["category"]) if data.get("category") else FindingCategory.IFC_VALIDATION,
            target_ref=data.get("target_ref"),
            property_set=data.get("property_set"),
            property_name=data.get("property_name"),
            operator=ComparisonOperator(data["operator"]) if data.get("operator") else None,
            expected_value=data.get("expected_value"),
            observed_value=data.get("observed_value"),
            unit=data.get("unit"),
            element_guid=data.get("element_guid"),
            problem_zone=ProblemZone(**problem_zone_data) if problem_zone_data else None,
            remark=GeneratedRemark(**remark_data) if remark_data else None,
        )

    def _reconstruct_summary(self, data: dict) -> ValidationSummary:
        return ValidationSummary(
            requirement_count=data.get("requirement_count", 0),
            issue_count=data.get("issue_count", 0),
            error_count=data.get("error_count", 0),
            warning_count=data.get("warning_count", 0),
            passed=data.get("passed", False),
            drawing_annotation_count=data.get("drawing_annotation_count", 0),
            generated_remark_count=data.get("generated_remark_count", 0),
        )

    def _reconstruct_annotation(self, data: dict) -> DrawingAnnotation:
        problem_zone_data = data.get("problem_zone")
        return DrawingAnnotation(
            annotation_id=data["annotation_id"],
            sheet_id=data["sheet_id"],
            target_ref=data["target_ref"],
            measure_name=data["measure_name"],
            observed_value=data["observed_value"],
            unit=data.get("unit"),
            problem_zone=ProblemZone(**problem_zone_data) if problem_zone_data else None,
            source=data.get("source", "drawing-text"),
        )
