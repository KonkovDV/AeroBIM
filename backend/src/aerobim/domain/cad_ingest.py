"""CAD ingest result types (domain-pure; no CAD SDK)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aerobim.domain.models import DrawingAnnotation

NATIVE_DWG_MISSING_REASON = "native DWG parser is not implemented"
NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON = (
    "AEROBIM_ODA_CAD_ENABLED=true but ODA/Teigha SDK is not shipped "
    "(STUB-ODA-CAD-001; legal gate open ≠ native DWG product)"
)
NATIVE_AUTODESK_CLOSED_REASON = (
    "native RVT/NWD parser is not implemented; closed Autodesk format without a free reader"
)
AUTODESK_NATIVE_SUFFIXES = frozenset({".rvt", ".rte", ".nwd", ".nwc"})
AUTODESK_NATIVE_FORMATS = frozenset({"rvt", "rte", "nwd", "nwc"})
REVIT_CONTAINER_ZIP_BASENAMES = frozenset({"basicfileinfo"})


def zip_names_indicate_autodesk(names: tuple[str, ...] | list[str]) -> bool:
    """True when a ZIP central directory names Revit/Navisworks members.

    Covers (1) ``*.rvt``/``*.nwd`` members inside an archive and (2) a Revit
    container renamed to ``.zip`` (member ``BasicFileInfo``). Domain-pure: no
    zipfile I/O.
    """

    for raw in names:
        base = raw.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].lower()
        if Path(base).suffix in AUTODESK_NATIVE_SUFFIXES:
            return True
        if base in REVIT_CONTAINER_ZIP_BASENAMES:
            return True
    return False


def is_autodesk_native_cad(path: Path, format_hint: str | None = None) -> bool:
    """True when the path or declared format is native Revit/Navisworks."""

    if path.suffix.lower() in AUTODESK_NATIVE_SUFFIXES:
        return True
    fmt = (format_hint or "").strip().lower().lstrip(".")
    return fmt in AUTODESK_NATIVE_FORMATS


def autodesk_format_resolved(path: Path) -> str:
    """Collapse RTE→rvt and NWC→nwd for honesty reporting."""

    suffix = path.suffix.lower()
    if suffix in {".nwd", ".nwc"}:
        return "nwd"
    return "rvt"


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
    "AUTODESK_NATIVE_FORMATS",
    "AUTODESK_NATIVE_SUFFIXES",
    "CadIngestResult",
    "DerivedCadProvenance",
    "NATIVE_AUTODESK_CLOSED_REASON",
    "NATIVE_DWG_MISSING_REASON",
    "NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON",
    "REVIT_CONTAINER_ZIP_BASENAMES",
    "autodesk_format_resolved",
    "default_dwg_loss_notes",
    "is_autodesk_native_cad",
    "zip_names_indicate_autodesk",
]
