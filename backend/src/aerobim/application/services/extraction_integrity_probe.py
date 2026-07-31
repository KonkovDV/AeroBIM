"""Application-layer probe: PDF sources → extraction_integrity CapabilityStatus."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from aerobim.domain.extraction_integrity import (
    assess_extraction_integrity,
    merge_integrity_results,
)
from aerobim.domain.models import CapabilityState, CapabilityStatus, DrawingSource
from aerobim.domain.ports import ExtractionIntegritySignalProducer


def probe_extraction_integrity(
    producer: ExtractionIntegritySignalProducer | None,
    drawing_sources: Sequence[DrawingSource],
) -> CapabilityStatus:
    """Probe PDF drawing sources; leave non-PDF packages as SKIPPED."""

    if producer is None:
        return CapabilityStatus(
            CapabilityState.NOT_VERIFIED,
            "extraction-integrity producer not configured; "
            "extracted text must not be presumed render-consistent",
        )

    pdf_paths: list[Path] = []
    for source in drawing_sources:
        if source.path is None:
            continue
        if source.path.suffix.lower() == ".pdf":
            pdf_paths.append(source.path)

    if not pdf_paths:
        return CapabilityStatus(
            CapabilityState.SKIPPED,
            "no PDF drawing sources for extraction-integrity probe",
        )

    results = []
    for path in pdf_paths:
        try:
            signals = producer.produce(path)
        except Exception as exc:  # noqa: BLE001 — probe must not crash analyze
            return CapabilityStatus(
                CapabilityState.FAILED,
                f"extraction-integrity probe failed for {path.name}: {exc}",
            )
        results.append(assess_extraction_integrity(signals))

    merged = merge_integrity_results(tuple(results))
    return merged.to_capability_status()


__all__ = ["probe_extraction_integrity"]
