"""ODA/Teigha native DWG ingest — legal-gated stub (not shipped).

/** @sota-stub */
Enable only after legal review via ``AEROBIM_ODA_CAD_ENABLED=true``.
The flag opens the *legal* gate only — without a licensed ODA/Teigha SDK this
adapter still returns ``supported=False`` (STUB-ODA-CAD-001).
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.cad_ingest import (
    NATIVE_DWG_MISSING_REASON,
    NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON,
    CadIngestResult,
)


class OdaCadModelIngestor:
    """Native DWG adapter placeholder.

    /** @sota-stub */
    Tracked as STUB-ODA-CAD-001. Never implies product DWG readiness.
    Never wired into AnalyzeProjectPackageUseCase — analyze uses EzdxfCadModelIngestor.
    """

    def __init__(self, *, enabled: bool = False) -> None:
        self._enabled = enabled

    def ingest(self, path: Path, *, sheet_id: str | None = None) -> CadIngestResult:
        del path, sheet_id
        reason = (
            NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON if self._enabled else NATIVE_DWG_MISSING_REASON
        )
        return CadIngestResult(
            annotations=(),
            format_resolved="dwg",
            entity_count=0,
            degraded=True,
            supported=False,
            reason=reason,
        )
