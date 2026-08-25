"""Samolet-stated upload caps vs development / analyze / WASM limits.

Answers 1.1.4 (2026-08-25): office documents ≤ 500 MB decimal; model files ≤ 1.5 GB
decimal. Those numbers are customer statements, not the development default and not
the IFC analyze / browser WASM cap.

Do not treat ingest of a 1.5 GB IFC as proof that analyze or the viewer can open it.
"""

from __future__ import annotations

from aerobim.core.security.upload_content import extension_of

# Decimal megabytes / gigabytes as stated by the customer (not 1024-based MiB/GiB).
SAMOLET_STATED_OFFICE_BYTES = 500_000_000
SAMOLET_STATED_MODEL_BYTES = 1_500_000_000

# Development / fixture default and analyze/WASM cap (256 MiB).
# Comparable to buildingSMART Validation Service 256 MB, not the same unit.
DEV_DEFAULT_UPLOAD_BYTES = 256 * 1024 * 1024
WASM_IFC_VIEWER_CAP_BYTES = 256 * 1024 * 1024

_MODEL_EXTENSIONS = frozenset(
    {
        ".ifc",
        ".ifczip",
        ".rvt",
        ".rte",
        ".nwd",
        ".nwc",
        ".dwg",
        ".dxf",
        ".zip",
    }
)


def classify_upload_kind(filename: str) -> str:
    """Return ``model`` or ``office`` from the declared filename extension."""

    ext = extension_of(filename)
    if ext in _MODEL_EXTENSIONS:
        return "model"
    return "office"


def upload_limit_bytes(
    filename: str,
    *,
    max_office_bytes: int,
    max_model_bytes: int,
    envelope_bytes: int,
) -> int:
    """Per-file ingest cap: min(type cap, envelope). Envelope is ``max_upload_bytes``."""

    typed = max_model_bytes if classify_upload_kind(filename) == "model" else max_office_bytes
    return min(max(0, int(typed)), max(0, int(envelope_bytes)))


__all__ = [
    "DEV_DEFAULT_UPLOAD_BYTES",
    "SAMOLET_STATED_MODEL_BYTES",
    "SAMOLET_STATED_OFFICE_BYTES",
    "WASM_IFC_VIEWER_CAP_BYTES",
    "classify_upload_kind",
    "upload_limit_bytes",
]
