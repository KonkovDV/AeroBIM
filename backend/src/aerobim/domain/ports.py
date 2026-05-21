from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    ClashResult,
    DrawingAnnotation,
    DrawingSource,
    GeneratedRemark,
    ParsedRequirement,
    ReportSummaryEntry,
    RequirementSource,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
)


class RequirementExtractor(Protocol):
    def extract(self, source: RequirementSource) -> list[ParsedRequirement]: ...


class NarrativeRuleSynthesizer(Protocol):
    def synthesize(self, source: RequirementSource) -> list[ParsedRequirement]: ...


class DrawingAnalyzer(Protocol):
    def analyze(self, source: DrawingSource) -> list[DrawingAnnotation]: ...


class RasterDrawingAnalyzer(Protocol):
    """Domain port for optional raster/PDF drawing analysis (OCR + layout).

    Unlike ``DrawingAnalyzer`` (structured text/JSON), this port accepts
    raster or PDF inputs and returns ``DrawingAnnotation`` records via
    deterministic OCR and layout heuristics. Non-deterministic adapters
    may implement the same port but are outside the pilot sign-off path.
    """

    def analyze_image(
        self,
        image_path: Path,
        sheet_id: str | None = None,
    ) -> list[DrawingAnnotation]: ...


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


class ObjectStore(Protocol):
    def put_bytes(
        self,
        key: str,
        payload: bytes,
        *,
        content_type: str | None = None,
    ) -> str: ...

    def get_bytes(self, key: str) -> bytes | None: ...

    def delete(self, key: str) -> None: ...

    def presign_get(self, key: str, *, expires_in_seconds: int = 3600) -> str | None: ...


class AnalyzeProjectPackageJobStore(Protocol):
    def create(self, job: AnalyzeProjectPackageJob) -> str: ...

    def get(self, job_id: str) -> AnalyzeProjectPackageJob | None: ...

    def mark_running(self, job_id: str) -> AnalyzeProjectPackageJob | None: ...

    def mark_succeeded(self, job_id: str, report_id: str) -> AnalyzeProjectPackageJob | None: ...

    def mark_failed(self, job_id: str, error_message: str) -> AnalyzeProjectPackageJob | None: ...


class ExternalEvidenceVerifier(Protocol):
    """Port for third-party calculation / reinforcement evidence verification."""

    def verify(self, request: ValidationRequest) -> list[ValidationIssue]: ...


class ClashDetector(Protocol):
    """Domain port for BIM clash/collision detection."""

    def detect(self, ifc_path: Path) -> list[ClashResult]: ...
