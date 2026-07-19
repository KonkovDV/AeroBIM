from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol

from aerobim.domain.bcf_api import BcfApiPushResult
from aerobim.domain.cad_ingest import CadIngestResult
from aerobim.domain.consistency import (
    MultimodalDrawingResult,
    PackageManifest,
    QuantityClaim,
)

# Re-export MEP port for contour/DI discovery (implementation stays in domain.mep).
from aerobim.domain.mep import MepSystemGraphProvider as MepSystemGraphProvider
from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    ClashResult,
    DrawingAnnotation,
    DrawingRegionRef,
    DrawingSource,
    GeneratedRemark,
    NormPackVersionInfo,
    NormRulePack,
    ParsedRequirement,
    ReportListFilters,
    ReportSummaryEntry,
    RequirementSource,
    ReviewEvent,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
)
from aerobim.domain.norm_assist import IdsCompileDraft, NormPassage
from aerobim.domain.section_pairing import SectionPairingReport


class RequirementExtractor(Protocol):
    def extract(self, source: RequirementSource) -> list[ParsedRequirement]: ...


class NarrativeRuleSynthesizer(Protocol):
    def synthesize(self, source: RequirementSource) -> list[ParsedRequirement]: ...


class NormRulePackLoader(Protocol):
    """Load and validate an agreed or explicitly non-approved rule pack."""

    def load(self, pack_path: Path) -> NormRulePack: ...


class SectionDiffAnalyzer(Protocol):
    """Deterministically compare one paired PD/RD discipline section."""

    def compare(self, pd_section_path: Path, rd_section_path: Path) -> list[ValidationIssue]: ...

    def analyze(self, pd_section_path: Path, rd_section_path: Path) -> SectionPairingReport:
        """Compare a PD/RD pair and return findings plus coverage metadata.

        ``compare`` remains the minimal findings-only contract; ``analyze``
        additionally surfaces the resolved canonical discipline and canonical-key
        coverage so the capability status can stay honest about what was mapped.
        """
        ...


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

    def list_reports(
        self,
        filters: ReportListFilters | None = None,
    ) -> list[ReportSummaryEntry]: ...


class ReviewEventStore(Protocol):
    def append(self, event: ReviewEvent) -> str: ...

    def list_for_report(self, report_id: str) -> list[ReviewEvent]: ...


class NormRulePackVersionStore(Protocol):
    """Immutable norm-pack version history (P0.3 HITL). Never overwrites prior versions."""

    def save_version(
        self,
        *,
        pack_id: str,
        version: str,
        payload: bytes,
        created_by: str | None,
        parent_version: str | None,
        approval_status: str | None,
        approval_ref: str | None,
    ) -> NormPackVersionInfo: ...

    def list_versions(self, pack_id: str) -> list[NormPackVersionInfo]: ...

    def get_version_bytes(self, pack_id: str, version: str) -> bytes | None: ...


class BsiValidationService(Protocol):
    """Optional remote IFC schema conformity submission (bSI Validation Service)."""

    def submit(self, ifc_path: Path) -> str:
        """Return external validation request id (``public_id``)."""
        ...


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

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        tenant_id: str | None = None,
    ) -> AnalyzeProjectPackageJob | None: ...

    def count_active_for_tenant(self, tenant_id: str) -> int: ...

    def mark_running(self, job_id: str) -> AnalyzeProjectPackageJob | None: ...

    def mark_succeeded(self, job_id: str, report_id: str) -> AnalyzeProjectPackageJob | None: ...

    def mark_failed(self, job_id: str, error_message: str) -> AnalyzeProjectPackageJob | None: ...

    def heartbeat(
        self, job_id: str, *, lease_seconds: int = 120
    ) -> AnalyzeProjectPackageJob | None: ...

    def request_cancel(self, job_id: str) -> AnalyzeProjectPackageJob | None: ...

    def mark_cancelled(
        self, job_id: str, reason: str | None = None
    ) -> AnalyzeProjectPackageJob | None: ...

    def reclaim_stale_running(
        self, *, now_iso: str | None = None
    ) -> list[AnalyzeProjectPackageJob]: ...


class ExternalEvidenceVerifier(Protocol):
    """Port for third-party calculation / reinforcement evidence verification."""

    def verify(self, request: ValidationRequest) -> list[ValidationIssue]: ...


class ClashDetector(Protocol):
    """Domain port for BIM clash/collision detection."""

    def detect(self, ifc_path: Path) -> list[ClashResult]: ...


class IfcSchemaValidator(Protocol):
    """Pre-gate: SPF / schema / implementer-agreement checks before project rules."""

    def validate_schema(self, ifc_path: Path) -> list[ValidationIssue]: ...


class IdsDocumentAuditor(Protocol):
    """Pre-gate: validate an IDS document before model checking."""

    def audit(self, ids_path: Path) -> list[ValidationIssue]: ...


class BcfApiClient(Protocol):
    """OpenCDE BCF API 3.0 client — push coordination topics to a remote hub."""

    def push_report_topics(
        self,
        report: ValidationReport,
        *,
        project_id: str,
    ) -> BcfApiPushResult: ...


class CadModelIngestor(Protocol):
    """DWG/DXF → drawing annotations.

    Honesty: never claim OK for native DWG without ODA evidence.
    """

    def ingest(self, path: Path, *, sheet_id: str | None = None) -> CadIngestResult: ...


class OfficeDocumentIngestor(Protocol):
    """MS Office / rich docs → RequirementSource with extracted text."""

    def ingest(self, path: Path) -> RequirementSource: ...


class QuantityConsistencyChecker(Protocol):
    """IFC quantity сверка vs declared claims (areas/space). Not solver correctness."""

    def check(
        self,
        ifc_path: Path,
        declared: Sequence[QuantityClaim],
    ) -> list[ValidationIssue]: ...


class LoadEvidenceVerifier(Protocol):
    """Load-table / calc-sheet numeric match. Not independent correctness."""

    def verify(self, request: ValidationRequest) -> list[ValidationIssue]: ...


class LogicConsistencyAnalyzer(Protocol):
    """Cross-section / package logical gaps (orphan sheets, unpaired PD/RD, etc.)."""

    def analyze(self, manifest: PackageManifest) -> list[ValidationIssue]: ...


class DrawingRegionDetector(Protocol):
    """Layout region priors / detector (Blueprint-style); never implies cv_human_level OK."""

    def detect(self, path: Path, *, sheet_id: str | None = None) -> list[DrawingRegionRef]: ...


class MultimodalDrawingPipeline(Protocol):
    """Detector+VLM with mandatory OCR degrade when extras absent."""

    def analyze(
        self,
        source: DrawingSource,
        *,
        mode: Literal["auto", "ocr_only", "detector_vlm"] = "auto",
    ) -> MultimodalDrawingResult: ...


class RequirementToIdsCompiler(Protocol):
    """TZ/requirements → draft IDS 1.0 XML (advisory; never auto sign-off)."""

    def compile(self, source: RequirementSource) -> IdsCompileDraft: ...

    def compile_requirements(
        self,
        requirements: Sequence[ParsedRequirement],
    ) -> IdsCompileDraft: ...


class NormCorpusRetriever(Protocol):
    """Keyword/RAG-style retrieve over local norm corpus; citations required."""

    def retrieve(self, query: str, *, top_k: int = 8) -> list[NormPassage]: ...
