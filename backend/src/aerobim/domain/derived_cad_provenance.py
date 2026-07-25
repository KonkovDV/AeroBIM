"""Helpers for DWG-derived substitute provenance (PDF/IFC/DXF)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aerobim.domain.cad_ingest import (
    DerivedCadProvenance,
    default_dwg_loss_notes,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_derived_cad_provenance(
    *,
    source_dwg: Path | None,
    derived: Path,
    derived_format: str,
    conversion_tool: str | None = None,
    conversion_tool_version: str | None = None,
    loss_notes: tuple[str, ...] | None = None,
) -> DerivedCadProvenance:
    """Register derived substitute with hashes — never claims native DWG support."""

    if not derived.is_file():
        raise FileNotFoundError(derived)
    fmt = derived_format.strip().lower()
    if fmt not in {"pdf", "ifc", "dxf"}:
        raise ValueError(f"derived_format must be pdf|ifc|dxf, got {derived_format!r}")
    source_hash = sha256_file(source_dwg) if source_dwg and source_dwg.is_file() else None
    return DerivedCadProvenance(
        source_dwg_path=str(source_dwg) if source_dwg else None,
        source_dwg_sha256=source_hash,
        derived_path=str(derived),
        derived_sha256=sha256_file(derived),
        derived_format=fmt,
        conversion_tool=conversion_tool,
        conversion_tool_version=conversion_tool_version,
        loss_notes=loss_notes if loss_notes is not None else default_dwg_loss_notes(),
    )


def load_derived_provenance_sidecar(path: Path) -> DerivedCadProvenance:
    """Load ``*.derived-provenance.json`` next to a converted artifact."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("derived provenance sidecar must be a JSON object")
    notes = payload.get("loss_notes") or []
    if not isinstance(notes, list):
        raise ValueError("loss_notes must be an array")
    return DerivedCadProvenance(
        source_dwg_path=_opt_str(payload.get("source_dwg_path")),
        source_dwg_sha256=_opt_str(payload.get("source_dwg_sha256")),
        derived_path=_opt_str(payload.get("derived_path")),
        derived_sha256=_opt_str(payload.get("derived_sha256")),
        derived_format=_opt_str(payload.get("derived_format")),
        conversion_tool=_opt_str(payload.get("conversion_tool")),
        conversion_tool_version=_opt_str(payload.get("conversion_tool_version")),
        loss_notes=tuple(str(item) for item in notes),
    )


def _opt_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "build_derived_cad_provenance",
    "load_derived_provenance_sidecar",
    "sha256_file",
]
