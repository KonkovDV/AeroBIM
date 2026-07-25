"""ODA/Teigha native DWG ingest — legal-gated stub (not shipped).

/** @sota-stub */
Enable only after legal review via ``AEROBIM_ODA_CAD_ENABLED=true``.
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.cad_ingest import NATIVE_DWG_MISSING_REASON, CadIngestResult


class OdaCadModelIngestor:
    """Native DWG adapter placeholder.

    /** @sota-stub */
    Tracked as STUB-ODA-CAD-001. Never implies product DWG readiness.
    Never wired into AnalyzeProjectPackageUseCase — analyze uses EzdxfCadModelIngestor.
    """

    def __init__(self, *, enabled: bool = False) -> None:
        self._enabled = enabled

    def ingest(self, path: Path, *, sheet_id: str | None = None) -> CadIngestResult:
        del sheet_id
        if not self._enabled:
            return CadIngestResult(
                annotations=(),
                format_resolved="dwg",
                entity_count=0,
                degraded=True,
                supported=False,
                reason=NATIVE_DWG_MISSING_REASON,
            )
        return CadIngestResult(
            annotations=(),
            format_resolved="dwg",
            entity_count=0,
            degraded=True,
            supported=False,
            reason=NATIVE_DWG_MISSING_REASON,
        )
