"""IFC analyze cap vs ingest envelope vs bSI vs WASM.

SPF ``ifcopenshell.open`` stays 256 MiB (``AEROBIM_MAX_IFC_BYTES``). Files
above that and up to the Samolet-stated 1.5 GB model envelope are analyzed
via IfcOpenShell RocksDB (streaming convert, then open the key-value store).
That is not an in-memory SPF raise and not a WASM raise.

Checkpoint NO_GO. Does not raise the SPF default cap.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Final

from aerobim.core.security.upload_limits import (
    DEV_DEFAULT_UPLOAD_BYTES,
    SAMOLET_STATED_MODEL_BYTES,
    WASM_IFC_VIEWER_CAP_BYTES,
)

CLAIM_BOUNDARY: Final = (
    "SPF in-memory open stays 256 MiB. Files up to 1.5 GB use RocksDB, "
    "not SPF RAM. WASM viewer stays 256 MiB. bSI is 256 MB decimal. "
    "SPF RAM multiplier is literature, not our RSS. Checkpoint NO_GO."
)

# buildingSMART Validation Service user guide: uncompressed .ifc, 256 MB.
# https://buildingsmart.github.io/validate/user/index.html
BSI_VALIDATE_UNCOMPRESSED_IFC_BYTES: Final = 256_000_000

# Conservative planning multiplier. aothms (IfcOpenShell #7116, 2025-09-11):
# SPF parse of a ~275–300 MB model is "roughly 10x the size on disk when stored
# in RAM"; the published 275 MB Riverside open was 2.19 GiB RSS (~8×).
SPF_RAM_MULTIPLIER_LITERATURE: Final = 10
SPF_RAM_MULTIPLIER_SOURCE: Final = (
    "IfcOpenShell#7116 SPF ~8–10x disk on ~275–300 MB; planning uses 10"
)

BAND_ANALYZE_OK: Final = "analyze_ok"
BAND_ANALYZE_DISK: Final = "analyze_disk"
BAND_ANALYZE_BLOCKED_INGEST_OK: Final = BAND_ANALYZE_DISK  # historical alias
BAND_OVER_INGEST: Final = "over_ingest"

BACKEND_SPF: Final = "spf"
BACKEND_ROCKSDB: Final = "rocksdb"
BACKEND_NONE: Final = "none"

PUBLIC_ANALYZE_CAP_DETAIL: Final = "IFC exceeds analyze size limit"
PUBLIC_ANALYZE_CAP_REASON_CODE: Final = "ifc_over_ingest_cap"
PUBLIC_ANALYZE_CAP_REQUIRED_PROFILE: Final = "samolet_pilot"
PUBLIC_ANALYZE_CAP_SEE: Final = "docs/quality/IFC_ANALYZE_VS_INGEST_CAP_2026_08.md"
PUBLIC_IFC_DISK_BACKEND_DETAIL: Final = "IFC disk backend unavailable"
ROCKSDB_BACKEND_STATUS: Final = "wired_over_spf_cap"


class IfcAnalyzeCapError(RuntimeError):
    """Raised when the file exceeds the 1.5 GB analyze envelope."""

    def __init__(self, decision: IfcSizeDecision) -> None:
        super().__init__(PUBLIC_ANALYZE_CAP_DETAIL)
        self.decision = decision


class IfcDiskBackendError(RuntimeError):
    """Raised when RocksDB convert/open is required and is unavailable."""

    def __init__(self) -> None:
        super().__init__(PUBLIC_IFC_DISK_BACKEND_DETAIL)


@dataclass(frozen=True)
class IfcSizeDecision:
    file_bytes: int
    analyze_cap_bytes: int
    ingest_cap_bytes: int
    bsi_cap_bytes: int
    wasm_cap_bytes: int
    analyze_allowed: bool
    ingest_would_accept: bool
    over_bsi_uncompressed: bool
    band: str
    backend: str
    literature_spf_rss_bytes: int
    raises_default_cap: bool
    claim_boundary: str

    def as_dict(self) -> dict[str, Any]:
        return dict(asdict(self))


def analyze_cap_from_env(*, default: int = DEV_DEFAULT_UPLOAD_BYTES) -> int:
    raw = os.getenv("AEROBIM_MAX_IFC_BYTES")
    if raw is None or not str(raw).strip():
        return default
    return int(raw)


def ingest_cap_from_env(*, default: int = SAMOLET_STATED_MODEL_BYTES) -> int:
    raw = os.getenv("AEROBIM_MAX_MODEL_BYTES")
    if raw is None or not str(raw).strip():
        return default
    return int(raw)


def literature_spf_rss_bytes(file_bytes: int) -> int:
    """Attributed RAM planning figure. Not a measured AeroBIM RSS."""

    return max(0, int(file_bytes)) * SPF_RAM_MULTIPLIER_LITERATURE


def classify_ifc_bytes(
    file_bytes: int,
    *,
    analyze_cap_bytes: int | None = None,
    ingest_cap_bytes: int | None = None,
) -> IfcSizeDecision:
    """Classify a file against SPF / RocksDB / ingest / bSI / WASM. Never opens IFC."""

    size = max(0, int(file_bytes))
    analyze = DEV_DEFAULT_UPLOAD_BYTES if analyze_cap_bytes is None else int(analyze_cap_bytes)
    ingest = SAMOLET_STATED_MODEL_BYTES if ingest_cap_bytes is None else int(ingest_cap_bytes)
    if size <= analyze:
        band = BAND_ANALYZE_OK
        backend = BACKEND_SPF
    elif size <= ingest:
        band = BAND_ANALYZE_DISK
        backend = BACKEND_ROCKSDB
    else:
        band = BAND_OVER_INGEST
        backend = BACKEND_NONE
    return IfcSizeDecision(
        file_bytes=size,
        analyze_cap_bytes=analyze,
        ingest_cap_bytes=ingest,
        bsi_cap_bytes=BSI_VALIDATE_UNCOMPRESSED_IFC_BYTES,
        wasm_cap_bytes=WASM_IFC_VIEWER_CAP_BYTES,
        analyze_allowed=backend != BACKEND_NONE,
        ingest_would_accept=size <= ingest,
        over_bsi_uncompressed=size > BSI_VALIDATE_UNCOMPRESSED_IFC_BYTES,
        band=band,
        backend=backend,
        literature_spf_rss_bytes=literature_spf_rss_bytes(size),
        raises_default_cap=False,
        claim_boundary=CLAIM_BOUNDARY,
    )


def size_policy_snapshot() -> dict[str, object]:
    """Honesty snapshot for capabilities / streaming design consumers."""

    analyze = DEV_DEFAULT_UPLOAD_BYTES
    ingest = SAMOLET_STATED_MODEL_BYTES
    return {
        "artifact_type": "ifc_size_policy",
        "claim_level": "coverage_map_only",
        "checkpoint": "NO_GO",
        "analyze_cap_bytes": analyze,
        "analyze_cap_unit": "256 MiB SPF in-memory",
        "disk_analyze_cap_bytes": ingest,
        "disk_analyze_cap_unit": "1.5 GB decimal via RocksDB",
        "ingest_cap_bytes": ingest,
        "ingest_cap_unit": "1.5 GB decimal (answers 1.1.4)",
        "bsi_validate_uncompressed_ifc_bytes": BSI_VALIDATE_UNCOMPRESSED_IFC_BYTES,
        "bsi_validate_unit": "256 MB decimal",
        "bsi_faq_heading_notes_250_mb": True,
        "bsi_faq_heading_not_used_for_classification": True,
        "wasm_cap_bytes": WASM_IFC_VIEWER_CAP_BYTES,
        "spf_ram_multiplier_literature": SPF_RAM_MULTIPLIER_LITERATURE,
        "spf_ram_multiplier_source": SPF_RAM_MULTIPLIER_SOURCE,
        "literature_rss_at_analyze_cap_bytes": literature_spf_rss_bytes(analyze),
        "literature_rss_at_ingest_cap_bytes": literature_spf_rss_bytes(ingest),
        "revit_exporter_toolkit_limit_note": (
            "Autodesk IFC exporter help: third-party write toolkit practical "
            "limit ~1.5 GB — same order as the customer ingest statement"
        ),
        "raises_default_cap": False,
        "streaming_parser": "designed_not_implemented",
        "rocksdb_backend": ROCKSDB_BACKEND_STATUS,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def public_analyze_cap_detail() -> str:
    """Stable HTTP 413 message. Does not echo file size (RT-ERR-001)."""

    return PUBLIC_ANALYZE_CAP_DETAIL


def public_analyze_cap_body() -> dict[str, object]:
    """Machine-readable 413. No byte oracle. RSS is not a measured figure."""

    return {
        "message": PUBLIC_ANALYZE_CAP_DETAIL,
        "reason_code": PUBLIC_ANALYZE_CAP_REASON_CODE,
        "required_profile": PUBLIC_ANALYZE_CAP_REQUIRED_PROFILE,
        "see": PUBLIC_ANALYZE_CAP_SEE,
        "spf_cap_unraised": True,
        "rss_measured": False,
    }


def public_ifc_disk_backend_detail() -> str:
    """Stable 503 body when RocksDB convert/open cannot run."""

    return PUBLIC_IFC_DISK_BACKEND_DETAIL


def raise_if_over_analyze_cap(
    file_bytes: int,
    *,
    analyze_cap_bytes: int | None = None,
    ingest_cap_bytes: int | None = None,
) -> IfcSizeDecision:
    decision = classify_ifc_bytes(
        file_bytes,
        analyze_cap_bytes=analyze_cap_bytes,
        ingest_cap_bytes=ingest_cap_bytes,
    )
    if not decision.analyze_allowed:
        raise IfcAnalyzeCapError(decision)
    return decision


__all__ = [
    "BACKEND_NONE",
    "BACKEND_ROCKSDB",
    "BACKEND_SPF",
    "BAND_ANALYZE_BLOCKED_INGEST_OK",
    "BAND_ANALYZE_DISK",
    "BAND_ANALYZE_OK",
    "BAND_OVER_INGEST",
    "BSI_VALIDATE_UNCOMPRESSED_IFC_BYTES",
    "CLAIM_BOUNDARY",
    "PUBLIC_ANALYZE_CAP_DETAIL",
    "PUBLIC_ANALYZE_CAP_REASON_CODE",
    "PUBLIC_ANALYZE_CAP_REQUIRED_PROFILE",
    "PUBLIC_ANALYZE_CAP_SEE",
    "PUBLIC_IFC_DISK_BACKEND_DETAIL",
    "ROCKSDB_BACKEND_STATUS",
    "SPF_RAM_MULTIPLIER_LITERATURE",
    "SPF_RAM_MULTIPLIER_SOURCE",
    "IfcAnalyzeCapError",
    "IfcDiskBackendError",
    "IfcSizeDecision",
    "analyze_cap_from_env",
    "classify_ifc_bytes",
    "ingest_cap_from_env",
    "literature_spf_rss_bytes",
    "public_analyze_cap_body",
    "public_analyze_cap_detail",
    "public_ifc_disk_backend_detail",
    "raise_if_over_analyze_cap",
    "size_policy_snapshot",
]
