from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from samolet.domain.models import (
    ClashResult,
    DrawingAnnotation,
    DrawingSource,
    GeneratedRemark,
    ParsedRequirement,
    ReportSummaryEntry,
    RequirementSource,
    ValidationIssue,
    ValidationReport,
)


class RequirementExtractor(Protocol):
    def extract(self, source: RequirementSource) -> list[ParsedRequirement]: ...


class NarrativeRuleSynthesizer(Protocol):
    def synthesize(self, source: RequirementSource) -> list[ParsedRequirement]: ...


class DrawingAnalyzer(Protocol):
    def analyze(self, source: DrawingSource) -> list[DrawingAnnotation]: ...


class IfcValidator(Protocol):
    def validate(
        self,
        ifc_path: Path,
        requirements: Sequence[ParsedRequirement],
    ) -> list[ValidationIssue]: ...


class IdsValidator(Protocol):
    def validate(self, ids_path: Path, ifc_path: Path) -> list[ValidationIssue]: ...


class RemarkGenerator(Protocol):
    def generate(self, issue: ValidationIssue) -> GeneratedRemark: ...


class AuditReportStore(Protocol):
    def save(self, report: ValidationReport) -> str: ...

    def get(self, report_id: str) -> ValidationReport | None: ...

    def list_reports(self) -> list[ReportSummaryEntry]: ...


class ClashDetector(Protocol):
    """Domain port for BIM clash/collision detection."""

    def detect(self, ifc_path: Path) -> list[ClashResult]: ...
