"""Permissive PDF fixtures for tests (no PyMuPDF / AGPL).

Writes minimal PDF 1.4 documents with vector content so crop / text probes
work without the optional ``pdf-agpl`` extra.
"""

from __future__ import annotations

from pathlib import Path


def write_box_pdf(path: Path, *, x: float = 50, y_from_top: float = 50) -> Path:
    """One-page PDF with a filled black rectangle (page 612x792 pt).

    ``y_from_top`` matches the former PyMuPDF page-point convention used by
    region crop tests (origin top-left).
    """

    page_h = 792.0
    width = 150.0
    height = 100.0
    pdf_y = page_h - y_from_top - height
    content = f"0 0 0 rg {x:.1f} {pdf_y:.1f} {width:.1f} {height:.1f} re f\n".encode("ascii")
    path.write_bytes(_wrap_single_page(content, page_w=612, page_h=792))
    return path


def write_text_pdf(path: Path, text: str = "WALL-1 thickness 200 mm") -> Path:
    """One-page PDF with a simple text string (Helvetica)."""

    # Escape PDF string delimiters.
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET\n".encode("latin-1", errors="replace")
    path.write_bytes(_wrap_single_page(content, page_w=612, page_h=792, with_font=True))
    return path


def _wrap_single_page(
    content: bytes,
    *,
    page_w: int,
    page_h: int,
    with_font: bool = False,
) -> bytes:
    objects: list[bytes] = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    resources = " /Resources<< /Font<< /F1 5 0 R >> >>" if with_font else ""
    objects.append(
        (
            f"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w} {page_h}]"
            f"{resources} /Contents 4 0 R >>endobj\n"
        ).encode("ascii")
    )
    objects.append(
        b"4 0 obj<< /Length "
        + str(len(content)).encode("ascii")
        + b" >>stream\n"
        + content
        + b"endstream\nendobj\n"
    )
    if with_font:
        objects.append(
            b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
        )

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        (
            f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(out)


__all__ = ["write_box_pdf", "write_text_pdf"]
