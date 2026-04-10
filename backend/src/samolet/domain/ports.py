from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from samolet.domain.models import (
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


@dataclass(frozen=True)
class ClashResult:
    """A single spatial clash between two IFC elements."""

    element_a_guid: str
    element_b_guid: str
    clash_type: str  # "hard" | "clearance"
    distance: float  # penetration depth or clearance gap (metres)
    description: str


class ClashDetector(Protocol):
    """Domain port for BIM clash/collision detection."""

    def detect(self, ifc_path: Path) -> list[ClashResult]: ...
