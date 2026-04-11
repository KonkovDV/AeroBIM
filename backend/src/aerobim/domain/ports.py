from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from aerobim.domain.models import (
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


class VisionDrawingAnalyzer(Protocol):
    """Domain port for VLM-based (Vision Language Model) drawing analysis.

    Unlike the text-based ``DrawingAnalyzer`` which parses structured
    pipe-delimited or JSON annotations, this port accepts raster/PDF
    drawing images and returns semantic annotations extracted via a
    vision model (e.g. Qwen-VL, Florence-2, PaddleOCR + layout).

    Adapters may run inference locally (ONNX int8) or delegate to an
    external vision service.  The port intentionally mirrors the
    ``DrawingAnnotation`` return type so that downstream use cases
    can merge text-based and vision-based annotations transparently.
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


class ClashDetector(Protocol):
    """Domain port for BIM clash/collision detection."""

    def detect(self, ifc_path: Path) -> list[ClashResult]: ...
