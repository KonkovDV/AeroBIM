"""PDF backend selection (LIC-001 Option B — permissive default)."""

from __future__ import annotations

from typing import Literal

PdfBackendKind = Literal["pdfium", "pymupdf", "none"]


def resolve_pdf_backend(raw: str | None) -> PdfBackendKind:
    """Map config/env to a backend kind.

    Default is ``pdfium`` (pypdfium2 + pdfminer.six). ``pymupdf`` remains only
    when the optional ``pdf-agpl`` extra is installed. Unknown values fall back
    to ``pdfium``.
    """

    value = (raw or "pdfium").strip().lower()
    if value in {"none", "off", "disabled"}:
        return "none"
    if value in {"pymupdf", "fitz", "agpl"}:
        return "pymupdf"
    if value in {"pdfium", "pypdfium2", "pdfminer", "permissive"}:
        return "pdfium"
    return "pdfium"


__all__ = ["PdfBackendKind", "resolve_pdf_backend"]
