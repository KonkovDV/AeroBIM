"""TZ architecture contracts — EntityGraph, SystemClash, IFC KG, interpretation (SOTA 2026)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from aerobim.domain.models import CapabilityStatus, DrawingRegionRef, DrawingSource

SheetType = Literal["plan_ar", "plan_ov", "title_block", "spec", "unknown"]
RaseTag = Literal["R", "A", "S", "E"]


@dataclass(frozen=True)
class DetectedObject:
    object_id: str
    kind: str
    bbox_xyxy: tuple[float, float, float, float] | None = None
    confidence: float = 0.0


@dataclass(frozen=True)
class DetectedDimension:
    dimension_id: str
    value_text: str
    bbox_xyxy: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class DetectedText:
    text_id: str
    text: str
    bbox_xyxy: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class StructuredAnnotations:
    """DrawingAnalyzerPort output — degrades to OCR when CV extras absent."""

    sheet_id: str
    sheet_type: SheetType
    objects: tuple[DetectedObject, ...] = ()
    dimensions: tuple[DetectedDimension, ...] = ()
    texts: tuple[DetectedText, ...] = ()
    regions: tuple[DrawingRegionRef, ...] = ()
    pipeline_mode: str = "none"
    degraded: bool = True
    reason: str | None = None
    confidence_floor: float = 0.0


@dataclass(frozen=True)
class MachineCheckableRule:
    rule_id: str
    ids_fragment_or_dsl: str
    rase_elements: tuple[RaseTag, ...] = ()
    source_span: str | None = None
    locale: Literal["ru", "en"] = "ru"
    confidence: float = 0.0
    advisory_only: bool = True


@dataclass(frozen=True)
class CadEntity:
    entity_id: str
    kind: str
    layer: str | None = None
    geometry_ref: str | None = None
    attributes: Mapping[str, str] | None = None
    bbox: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class EntityGraph:
    source_id: str
    format: Literal["dxf", "dwg", "unknown"]
    entities: tuple[CadEntity, ...] = ()
    capability: CapabilityStatus | None = None


@dataclass(frozen=True)
class SpatialFinding:
    finding_id: str
    system_a: str
    system_b: str
    element_a_guid: str
    element_b_guid: str
    message: str
    clash_kind: Literal["hard", "clearance", "routing"] = "hard"
    clearance_mm: float | None = None


@dataclass(frozen=True)
class IfcKnowledgeQueryResult:
    """Advisory-only NL→IFC query outcome (IfcLLM-style); never drives passed."""

    question: str
    element_guids: tuple[str, ...] = ()
    facts: tuple[str, ...] = ()
    backend: Literal["stub", "relational", "graph", "hybrid"] = "stub"
    degraded: bool = True
    reason: str | None = None


class DrawingAnalyzerPort(Protocol):
    """TZ DrawingAnalyzerPort — detector+VLM with OCR degrade."""

    def analyze(
        self,
        sheet: DrawingSource,
        sheet_type: SheetType = "unknown",
    ) -> StructuredAnnotations: ...


class RequirementInterpreterPort(Protocol):
    """TZ/norm NL → machine-checkable rules (same IDS/DSL family as regex baseline)."""

    def interpret(
        self,
        tz_text: str,
        *,
        locale: Literal["ru", "en"] = "ru",
        mode: Literal["deterministic", "llm_assisted"] = "deterministic",
    ) -> list[MachineCheckableRule]: ...


class CadEntityLoaderPort(Protocol):
    """DWG/DXF → EntityGraph (same conceptual contract as IFC objects for overlays)."""

    def load(self, path: Path) -> EntityGraph: ...


class SystemClashPort(Protocol):
    """MEP system-aware clash / clearance (MEP-CLASH-001)."""

    def detect(
        self,
        model_path: Path,
        *,
        clearance_matrix: Mapping[tuple[str, str], float] | None = None,
    ) -> list[SpatialFinding]: ...


class IfcKnowledgeGraphPort(Protocol):
    """IfcLLM-style NL query over relational/graph backends — advisory only."""

    def query_nl(self, question: str, *, ifc_path: Path) -> IfcKnowledgeQueryResult: ...


class NormRetrieverPort(Protocol):
    """Alias contract for NormCorpusRetriever (RAG-ready)."""

    def retrieve(
        self,
        query: str,
        *,
        corpus: Literal["sp", "snip", "gost", "internal", "all"] = "all",
        top_k: int = 8,
    ) -> Sequence[object]: ...


__all__ = [
    "CadEntity",
    "CadEntityLoaderPort",
    "DetectedDimension",
    "DetectedObject",
    "DetectedText",
    "DrawingAnalyzerPort",
    "EntityGraph",
    "IfcKnowledgeGraphPort",
    "IfcKnowledgeQueryResult",
    "MachineCheckableRule",
    "NormRetrieverPort",
    "RequirementInterpreterPort",
    "SheetType",
    "SpatialFinding",
    "StructuredAnnotations",
    "SystemClashPort",
]
