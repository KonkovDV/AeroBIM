"""Helpers for DWG-derived substitute provenance (PDF/IFC/DXF).

Declared provenance is never trusted as-is (in-toto/SLSA posture, mirroring the
BCF T2 hash-binding wave): ``verify_derived_cad_provenance`` re-hashes both the
source DWG and the derived substitute and compares against the declared pair.
A verified pair still never makes ``dwg_dxf`` OK — it only documents that the
analysis refers to a specific derived file (W3C PROV ``wasDerivedFrom``).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from aerobim.domain.cad_conversion_qa import (
    ConversionQaReport,
    evaluate_conversion_qa_section,
)
from aerobim.domain.cad_ingest import (
    DerivedCadProvenance,
    default_dwg_loss_notes,
)

DERIVED_NOT_NATIVE_CLAIM = (
    "analysis refers to the derived file; native DWG is not parsed - dwg_dxf never OK"
)

_SIDECAR_SUFFIX = ".derived-provenance.json"
_ALLOWED_DERIVED_FORMATS = {"pdf", "ifc", "dxf"}


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
    if fmt not in _ALLOWED_DERIVED_FORMATS:
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


@dataclass(frozen=True)
class DerivedProvenanceVerification:
    """Outcome of hash re-verification — declared provenance is evidence only when it recomputes."""

    verified: bool
    mismatches: tuple[str, ...] = ()
    provenance: DerivedCadProvenance | None = None
    conversion_qa: ConversionQaReport | None = None
    """Recomputed loss-QA verdict when the sidecar declares a ``conversion_qa`` section."""


def find_derived_provenance_sidecar(artifact: Path) -> Path | None:
    """Locate ``<name>.derived-provenance.json`` next to a DWG or derived artifact."""

    candidate = artifact.with_name(artifact.name + _SIDECAR_SUFFIX)
    return candidate if candidate.is_file() else None


def derived_provenance_sidecar_payload(provenance: DerivedCadProvenance) -> dict[str, object]:
    """Serializable sidecar payload; keys mirror ``load_derived_provenance_sidecar``."""

    return {
        "artifact_type": "aerobim_derived_cad_provenance",
        "schema_version": "1.0.0",
        "source_dwg_path": provenance.source_dwg_path,
        "source_dwg_sha256": provenance.source_dwg_sha256,
        "derived_path": provenance.derived_path,
        "derived_sha256": provenance.derived_sha256,
        "derived_format": provenance.derived_format,
        "conversion_tool": provenance.conversion_tool,
        "conversion_tool_version": provenance.conversion_tool_version,
        "loss_notes": list(provenance.loss_notes),
        "claim_boundary": DERIVED_NOT_NATIVE_CLAIM,
    }


def write_derived_provenance_sidecar(provenance: DerivedCadProvenance, artifact: Path) -> Path:
    """Write ``<artifact>.derived-provenance.json`` (conversion registration step)."""

    sidecar = artifact.with_name(artifact.name + _SIDECAR_SUFFIX)
    payload = derived_provenance_sidecar_payload(provenance)
    sidecar.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return sidecar


def _resolve_jailed(raw: str, base_dir: Path | None) -> tuple[Path | None, str | None]:
    """Resolve a declared path; when ``base_dir`` is set, jail it to that directory."""

    path = Path(raw)
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    resolved = path.resolve()
    if base_dir is not None:
        try:
            resolved.relative_to(base_dir.resolve())
        except ValueError:
            return None, "escapes the package directory (path jail)"
    return resolved, None


def verify_derived_cad_provenance(
    provenance: DerivedCadProvenance,
    *,
    base_dir: Path | None = None,
) -> DerivedProvenanceVerification:
    """Recompute both hashes of the declared pair; any gap fails closed.

    Mandatory for a verified pair: source path+sha256, derived path+sha256 and a
    known derived format. Files must exist (inside ``base_dir`` when given) and
    recomputed SHA-256 must equal the declared value. A stale, foreign or
    tampered sidecar can never register a derived substitute.
    """

    mismatches: list[str] = []
    fmt = (provenance.derived_format or "").strip().lower()
    if fmt not in _ALLOWED_DERIVED_FORMATS:
        mismatches.append(f"derived_format must be pdf|ifc|dxf, got {provenance.derived_format!r}")
    checks = (
        ("source DWG", provenance.source_dwg_path, provenance.source_dwg_sha256),
        ("derived artifact", provenance.derived_path, provenance.derived_sha256),
    )
    for label, raw_path, declared in checks:
        if not raw_path or not declared:
            mismatches.append(f"{label}: path and sha256 are mandatory for verification")
            continue
        resolved, jail_error = _resolve_jailed(raw_path, base_dir)
        if resolved is None:
            mismatches.append(f"{label}: {raw_path}: {jail_error}")
            continue
        if not resolved.is_file():
            mismatches.append(f"{label}: file is absent: {raw_path}")
            continue
        if sha256_file(resolved) != declared.strip().lower():
            mismatches.append(f"{label}: recomputed sha256 differs from declared")
    return DerivedProvenanceVerification(
        verified=not mismatches,
        mismatches=tuple(mismatches),
        provenance=provenance,
    )


def verify_derived_provenance_sidecar(sidecar: Path) -> DerivedProvenanceVerification:
    """Load and verify a sidecar; unreadable sidecars fail closed (never a clean skip).

    When the sidecar declares a ``conversion_qa`` section, the loss verdict is
    **recomputed** from the declared inventories (a hand-written status cannot
    whitewash a lossy conversion) and a failed QA rejects the pair.
    """

    try:
        raw_payload = json.loads(sidecar.read_text(encoding="utf-8"))
        if not isinstance(raw_payload, dict):
            raise ValueError("derived provenance sidecar must be a JSON object")
        provenance = load_derived_provenance_sidecar(sidecar)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return DerivedProvenanceVerification(
            verified=False,
            mismatches=(f"sidecar unreadable: {exc}",),
            provenance=None,
        )
    verification = verify_derived_cad_provenance(provenance, base_dir=sidecar.parent)
    qa_report = evaluate_conversion_qa_section(raw_payload)
    if qa_report is not None and qa_report.status == "failed":
        return DerivedProvenanceVerification(
            verified=False,
            mismatches=verification.mismatches
            + tuple(f"conversion QA failed: {reason}" for reason in qa_report.reasons),
            provenance=provenance,
            conversion_qa=qa_report,
        )
    return DerivedProvenanceVerification(
        verified=verification.verified,
        mismatches=verification.mismatches,
        provenance=provenance,
        conversion_qa=qa_report,
    )


__all__ = [
    "DERIVED_NOT_NATIVE_CLAIM",
    "DerivedProvenanceVerification",
    "build_derived_cad_provenance",
    "derived_provenance_sidecar_payload",
    "find_derived_provenance_sidecar",
    "load_derived_provenance_sidecar",
    "sha256_file",
    "verify_derived_cad_provenance",
    "verify_derived_provenance_sidecar",
    "write_derived_provenance_sidecar",
]
