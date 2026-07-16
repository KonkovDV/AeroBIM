"""Architecture seams for Task 07: contours, claims, corpus provenance (additive).

These types close red-team risks R1–R5 at the type/runtime boundary without
splitting the modular monolith into microservices.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

CorpusKind = Literal["synthetic", "fixture", "customer"]
AuthorRelationship = Literal["self", "external"]
ContourName = Literal["ingestion", "deterministic_validation", "ai_advisory", "evidence_reporting"]


class Contour(StrEnum):
    INGESTION = "ingestion"
    DETERMINISTIC_VALIDATION = "deterministic_validation"
    AI_ADVISORY = "ai_advisory"
    EVIDENCE_REPORTING = "evidence_reporting"


@dataclass(frozen=True)
class DocumentIdentity:
    """INGESTION contour: version-aware document identity (no silent revision merge)."""

    source_id: str
    doc_type: str
    revision: str | None = None
    status: str | None = None
    stage: str | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class EvidenceProvenance:
    """Who produced an evaluation/audit artifact (R2)."""

    author_relationship: AuthorRelationship
    label: str
    """Human label; must not claim external/independent when relationship is self."""

    def display_label(self) -> str:
        if self.author_relationship == "self":
            # Hard rule: self assessments cannot be branded external/independent.
            banned = ("external", "independent", "third-party", "3rd-party")
            lowered = self.label.casefold()
            if any(token in lowered for token in banned):
                return "internal self-audit"
            return self.label
        return self.label


@dataclass(frozen=True)
class PrecisionClaim:
    """Typed precision claim (R1/R4). Unpublishable without customer corpus + ≥2 adjudicators."""

    metric: str
    value: float
    corpus_id: str
    corpus_kind: CorpusKind
    adjudicators: int
    date: str
    finding_class: str | None = None

    @property
    def publishable(self) -> bool:
        return self.corpus_kind == "customer" and self.adjudicators >= 2

    def render_value(self) -> str:
        """Return display text; blocks raw percentage for non-publishable claims."""
        if not self.publishable:
            return (
                f"{self.metric}=withheld "
                f"(corpus_kind={self.corpus_kind}, adjudicators={self.adjudicators}; "
                "not publishable as product accuracy)"
            )
        return f"{self.metric}={self.value:.4f}"


@dataclass(frozen=True)
class EvidenceRef:
    """Immutable evidence pointer required for a valid finding (EVIDENCE contour)."""

    source_id: str
    revision: str | None = None
    page_or_sheet: str | None = None
    coordinates: str | None = None
    ifc_guid: str | None = None
    rule_version: str | None = None
    extractor_version: str | None = None
    corpus_kind: CorpusKind | None = None


@dataclass(frozen=True)
class StageBudget:
    """Per-contour wall-time budgets for package SLA (default sum = 30 min)."""

    ingestion_minutes: float = 5.0
    deterministic_validation_minutes: float = 18.0
    ai_advisory_minutes: float = 2.0
    evidence_reporting_minutes: float = 5.0

    @property
    def total_minutes(self) -> float:
        return (
            self.ingestion_minutes
            + self.deterministic_validation_minutes
            + self.ai_advisory_minutes
            + self.evidence_reporting_minutes
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "ingestion_minutes": self.ingestion_minutes,
            "deterministic_validation_minutes": self.deterministic_validation_minutes,
            "ai_advisory_minutes": self.ai_advisory_minutes,
            "evidence_reporting_minutes": self.evidence_reporting_minutes,
            "total_minutes": self.total_minutes,
        }


DEFAULT_PACKAGE_STAGE_BUDGET = StageBudget()


# Contour ownership of existing ports (documentation + test anchors).
CONTOUR_PORTS: dict[Contour, tuple[str, ...]] = {
    Contour.INGESTION: (
        "RequirementExtractor",
        "RasterDrawingAnalyzer",
        "DrawingAnalyzer",
        "DocumentIdentity",
        "CadModelIngestor",
        "OfficeDocumentIngestor",
        "MultimodalDrawingPipeline",
    ),
    Contour.DETERMINISTIC_VALIDATION: (
        "IfcValidator",
        "IdsValidator",
        "ClashDetector",
        "NormRulePackLoader",
        "SectionDiffAnalyzer",
        "ExternalEvidenceVerifier",
        "MepSystemGraphProvider",
        "QuantityConsistencyChecker",
        "LoadEvidenceVerifier",
        "LogicConsistencyAnalyzer",
    ),
    Contour.AI_ADVISORY: (
        "IdsAssistDraftPort",
        "AdvisoryTextAssist",  # reserved; LLM assist never writes summary.passed
        "RequirementToIdsCompiler",
        "NormCorpusRetriever",
        "ComplianceAgentOrchestrator",
    ),
    Contour.EVIDENCE_REPORTING: (
        "AuditReportStore",
        "ReviewEventStore",
        "NormRulePackVersionStore",
        "BcfApiClient",
        "RemarkGenerator",
    ),
}


def assert_precision_publishable(claim: PrecisionClaim) -> None:
    if not claim.publishable:
        raise ValueError(
            "PrecisionClaim is not publishable without corpus_kind=customer "
            "and adjudicators>=2 (red-team R1/R4)"
        )
