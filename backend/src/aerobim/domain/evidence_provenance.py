"""
P0-G: Evidence-First Architecture.

Every finding must be provable. Answers the question:
  "Why did AeroBIM generate this remark?"
  → machine-reproducible answer via stable hashes.

Evidence chain:
  Package → File → Revision → Extraction → Rule → Evidence → Finding → Remark → BCF

Each EvidenceRecord stores:
  source, locator, object_guid, document_page, coordinates,
  actual_value, expected_value, extraction_method, source_hash,
  rule_version, norm_pack_version, timestamp, provenance.

Reduces: auditability risk, customer deployment risk.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ExtractionMethod(StrEnum):
    """How a value was extracted. AI outputs must be marked AI_ADVISORY."""

    DETERMINISTIC_PARSER = "deterministic_parser"  # IFC property reader
    DETERMINISTIC_GEOMETRY = "deterministic_geometry"  # Geometric computation
    IDS_VALIDATOR = "ids_validator"  # ifctester / buildingSMART
    AI_ADVISORY = "ai_advisory"  # LLM/NLP; never deterministic verdict
    OCR_EXTRACTED = "ocr_extracted"  # PDF/raster; advisory
    MANUAL_ANNOTATED = "manual_annotated"  # Human-entered
    CROSS_DOC_MATCH = "cross_doc_match"  # IFC ↔ drawing consistency


class EvidenceLocatorType(StrEnum):
    IFC_PROPERTY = "ifc_property"  # PropSet.PropName on GUID
    IFC_ELEMENT = "ifc_element"  # Element by GUID
    IFC_RELATIONSHIP = "ifc_relationship"
    DOCUMENT_PAGE = "document_page"  # Page N, region coords
    DOCUMENT_TABLE = "document_table"  # Sheet/row/col
    GEOMETRIC_REGION = "geometric_region"  # XYZ bounding box
    CROSS_DOC_PAIR = "cross_doc_pair"  # (ifc_guid, doc_page) pair


@dataclass
class EvidenceLocator:
    """Precise machine-addressable location of the evidence source."""

    locator_type: EvidenceLocatorType
    ifc_guid: str | None = None
    ifc_entity_type: str | None = None
    ifc_property_set: str | None = None
    ifc_property_name: str | None = None
    document_page: int | None = None
    document_sheet: str | None = None
    region_x1: float | None = None
    region_y1: float | None = None
    region_x2: float | None = None
    region_y2: float | None = None
    table_row: int | None = None
    table_col: int | None = None
    custom: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "locator_type": self.locator_type.value,
            "ifc_guid": self.ifc_guid,
            "ifc_entity_type": self.ifc_entity_type,
            "ifc_property_set": self.ifc_property_set,
            "ifc_property_name": self.ifc_property_name,
            "document_page": self.document_page,
            "document_sheet": self.document_sheet,
            "region": [self.region_x1, self.region_y1, self.region_x2, self.region_y2]
            if any(v is not None for v in [self.region_x1, self.region_y1])
            else None,
            "table_row": self.table_row,
            "table_col": self.table_col,
            "custom": self.custom,
        }


@dataclass
class EvidenceRecord:
    """
    Single unit of evidence supporting a finding.

    All fields needed for reproducibility:
      source_hash + rule_version + norm_pack_version + engine_version
      → deterministic replay.

    extraction_method MUST be AI_ADVISORY if any AI step contributed.
    AI_ADVISORY evidence cannot set deterministic verdict.
    """

    evidence_id: str
    finding_id: str  # Parent finding
    package_id: str
    file_logical_path: str  # Which file
    source_hash: str  # sha256 of source file bytes (from manifest)
    locator: EvidenceLocator
    actual_value: Any  # What was found
    expected_value: Any  # What was required by rule
    extraction_method: ExtractionMethod
    rule_id: str
    rule_version: str  # stable_version of ComplianceRule
    norm_pack_id: str
    norm_pack_version: str
    norm_pack_hash: str
    engine_version: str  # AeroBIM semver
    configuration_hash: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    confidence: float | None = None  # 0-1; required for AI_ADVISORY
    is_ai_advisory: bool = False
    supplementary: dict[str, Any] | None = None  # Free-form extra context

    def __post_init__(self) -> None:
        if self.extraction_method == ExtractionMethod.AI_ADVISORY:
            self.is_ai_advisory = True

    @property
    def provenance_id(self) -> str:
        """Stable hash covering all reproducibility fields."""
        payload = json.dumps(
            {
                "package_id": self.package_id,
                "file": self.file_logical_path,
                "source_hash": self.source_hash,
                "rule_id": self.rule_id,
                "rule_version": self.rule_version,
                "norm_pack_hash": self.norm_pack_hash,
                "engine_version": self.engine_version,
                "configuration_hash": self.configuration_hash,
                "locator": self.locator.to_dict(),
                "actual_value": str(self.actual_value),
                "expected_value": str(self.expected_value),
            },
            sort_keys=True,
        ).encode()
        return hashlib.sha256(payload).hexdigest()[:24]

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "finding_id": self.finding_id,
            "package_id": self.package_id,
            "file_logical_path": self.file_logical_path,
            "source_hash": self.source_hash,
            "locator": self.locator.to_dict(),
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "extraction_method": self.extraction_method.value,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "norm_pack_id": self.norm_pack_id,
            "norm_pack_version": self.norm_pack_version,
            "norm_pack_hash": self.norm_pack_hash,
            "engine_version": self.engine_version,
            "configuration_hash": self.configuration_hash,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "is_ai_advisory": self.is_ai_advisory,
            "provenance_id": self.provenance_id,
            "supplementary": self.supplementary,
        }


@dataclass
class FindingProvenance:
    """
    Complete provenance for a single finding.
    Answers all 15 checklist questions from the Definition of Done.

    Principle: unknown != pass. Missing evidence → NOT_VERIFIED.
    """

    finding_id: str
    rule_id: str
    rule_version: str
    norm_pack_id: str
    norm_pack_version: str
    norm_pack_hash: str
    package_id: str
    revision_id: str
    tenant_id: str
    project_id: str
    engine_version: str
    configuration_hash: str
    evidence_refs: list[str]  # evidence_id list; must not be empty for FAIL/PASS
    is_ai_advisory: bool  # True if any evidence is AI_ADVISORY
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    @property
    def is_reproducible(self) -> bool:
        """True if all reproducibility fields are present."""
        return bool(
            self.norm_pack_hash
            and self.rule_version
            and self.engine_version
            and self.configuration_hash
            and self.evidence_refs
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "norm_pack_id": self.norm_pack_id,
            "norm_pack_version": self.norm_pack_version,
            "norm_pack_hash": self.norm_pack_hash,
            "package_id": self.package_id,
            "revision_id": self.revision_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "engine_version": self.engine_version,
            "configuration_hash": self.configuration_hash,
            "evidence_refs": self.evidence_refs,
            "is_ai_advisory": self.is_ai_advisory,
            "is_reproducible": self.is_reproducible,
            "created_at": self.created_at.isoformat(),
        }
