"""Run drawing text-layer length vs IFC wall Width (deterministic contour)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Protocol, runtime_checkable

from aerobim.domain.drawing_ifc_consistency import (
    RULE_PARSER,
    DrawingIfcConsistencyResult,
    IfcQuantityObservation,
    compare_drawing_length_to_ifc,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    DrawingAnnotation,
    DrawingSource,
    FindingCategory,
    Severity,
    ValidationIssue,
)


@runtime_checkable
class IfcWallWidthExtractorPort(Protocol):
    """Read IfcWall Qto Width; adapter lives in infrastructure."""

    def extract(
        self,
        ifc_path: Path,
        *,
        ifc_revision: str | None = None,
    ) -> list[IfcQuantityObservation]: ...


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _with_drawing_hashes(sources: Sequence[DrawingSource]) -> tuple[DrawingSource, ...]:
    stamped: list[DrawingSource] = []
    for source in sources:
        if source.path is None or not source.path.is_file() or source.sha256:
            stamped.append(source)
            continue
        stamped.append(replace(source, sha256=_sha256_file(source.path)))
    return tuple(stamped)


def merge_quantity_capability(
    existing: CapabilityStatus | None,
    incoming: CapabilityStatus | None,
) -> CapabilityStatus | None:
    if incoming is None:
        return existing
    if existing is None:
        return incoming
    rank = {
        CapabilityState.FAILED: 5,
        CapabilityState.NOT_VERIFIED: 4,
        CapabilityState.MISSING: 3,
        CapabilityState.NOT_IMPLEMENTED: 3,
        CapabilityState.OK: 2,
        CapabilityState.SKIPPED: 1,
    }
    if rank.get(incoming.status, 0) >= rank.get(existing.status, 0):
        return incoming
    return existing


class DrawingIfcConsistencyService:
    def __init__(self, extractor: IfcWallWidthExtractorPort | None = None) -> None:
        self._extractor = extractor

    def evaluate(
        self,
        *,
        ifc_path: Path | None,
        annotations: Sequence[DrawingAnnotation],
        drawing_sources: Sequence[DrawingSource],
        ifc_revision: str | None,
    ) -> tuple[list[ValidationIssue], CapabilityStatus | None]:
        if ifc_path is None or self._extractor is None:
            return [], None
        hashed_drawings = _with_drawing_hashes(drawing_sources)
        try:
            observations: Sequence[IfcQuantityObservation] = self._extractor.extract(
                ifc_path, ifc_revision=ifc_revision
            )
        except FileNotFoundError as exc:
            missing = compare_drawing_length_to_ifc(
                annotations=annotations,
                observations=(),
                drawing_sources=hashed_drawings,
                ifc_revision=ifc_revision,
                ifc_path=ifc_path,
            )
            missing_cap = CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                f"IFC missing for drawing↔width compare: {exc}",
            )
            return list(missing.issues), missing_cap
        except Exception as exc:
            return [
                ValidationIssue(
                    rule_id=RULE_PARSER,
                    severity=Severity.WARNING,
                    message=(
                        "Невозможно проверить IFC для сверки с листом: "
                        f"{type(exc).__name__}: {exc}. "
                        "Не утверждение, что проект содержит нарушение."
                    ),
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="pd-rd-wall-width",
                    origin="deterministic",
                    evidence_refs=("cannot_verify:ifc_parse_error",),
                )
            ], CapabilityStatus(CapabilityState.NOT_VERIFIED, str(exc))

        digest = _sha256_file(ifc_path) if ifc_path.is_file() else None
        result: DrawingIfcConsistencyResult = compare_drawing_length_to_ifc(
            annotations=annotations,
            observations=observations,
            drawing_sources=hashed_drawings,
            ifc_revision=ifc_revision,
            ifc_path=ifc_path,
            ifc_sha256=digest,
        )
        return list(result.issues), result.capability
