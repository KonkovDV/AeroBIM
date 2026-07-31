"""PDF backend selection (LIC-001 Phase 1 — isolation seam, not AGPL clearance)."""

from __future__ import annotations

from typing import Literal

PdfBackendKind = Literal["pymupdf", "none"]


def resolve_pdf_backend(raw: str | None) -> PdfBackendKind:
    """Map config/env to a backend kind. Unknown → pymupdf (current production default)."""

    value = (raw or "pymupdf").strip().lower()
    if value in {"none", "off", "disabled"}:
        return "none"
    return "pymupdf"


__all__ = ["PdfBackendKind", "resolve_pdf_backend"]
