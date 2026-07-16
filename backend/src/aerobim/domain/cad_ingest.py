"""CAD ingest result types (domain-pure; no CAD SDK)."""

from __future__ import annotations

from dataclasses import dataclass

from aerobim.domain.models import DrawingAnnotation


@dataclass(frozen=True)
class CadIngestResult:
    """Outcome of CadModelIngestor.ingest — DXF partial vs DWG blocked."""

    annotations: tuple[DrawingAnnotation, ...] = ()
    format_resolved: str = "unknown"
    entity_count: int = 0
    degraded: bool = False
    reason: str | None = None
    supported: bool = False
    """True when the adapter produced a usable vector parse (typically DXF)."""
