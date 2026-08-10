"""CAD ingest result types (domain-pure; no CAD SDK)."""

from __future__ import annotations

from dataclasses import dataclass

from aerobim.domain.models import DrawingAnnotation

NATIVE_DWG_MISSING_REASON = "native DWG parser is not implemented"
NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON = (
    "AEROBIM_ODA_CAD_ENABLED=true but ODA/Teigha SDK is not shipped "
    "(STUB-ODA-CAD-001; legal gate open ≠ native DWG product)"
)


@dataclass(frozen=True)
class DerivedCadProvenance:
    """Provenance when analysis runs on a file derived from DWG (never = native DWG)."""

    source_dwg_path: str | None = None
    source_dwg_sha256: str | None = None
    derived_path: str | None = None
    derived_sha256: str | None = None
    derived_format: str | None = None
    """pdf | ifc | dxf — derived input, not native DWG support."""
    conversion_tool: str | None = None
    conversion_tool_version: str | None = None
    loss_notes: tuple[str, ...] = ()
    """Known losses: layers, blocks, XREF, attributes, coordinates."""


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
    derived_provenance: DerivedCadProvenance | None = None
    """Set only when ingesting an explicitly declared derived substitute."""


def default_dwg_loss_notes() -> tuple[str, ...]:
    return (
        "layers may be flattened or renamed",
        "blocks/XREF may be unresolved or exploded",
        "attributes and custom properties may be dropped",
        "coordinate systems / UCS may differ from source DWG",
    )


__all__ = [
    "CadIngestResult",
    "DerivedCadProvenance",
    "NATIVE_DWG_MISSING_REASON",
    "NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON",
    "default_dwg_loss_notes",
]
