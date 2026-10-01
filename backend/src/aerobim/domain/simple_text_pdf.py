"""Minimal one-page PDF-1.4 writer for synthetic text-layer fixtures.

No images, no fonts beyond Helvetica, no network. Used so PDFMiner actually
parses a drawing instead of a pre-baked finding JSON.
"""

from __future__ import annotations

from pathlib import Path


def escape_pdf_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_simple_text_pdf_bytes(text: str) -> bytes:
    """Return a one-page A4 PDF whose text layer contains *text*."""

    escaped = escape_pdf_string(text)
    stream = f"BT /F1 14 Tf 50 720 Td ({escaped}) Tj ET\n".encode("latin-1", errors="replace")
    obj4 = (
        f"4 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1")
        + stream
        + b"endstream\nendobj\n"
    )
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        ),
        obj4,
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = []
    body = bytearray()
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        body.extend(obj)
        cursor += len(obj)
    xref_pos = cursor
    xref = [b"xref\n0 6\n", b"0000000000 65535 f \n"]
    for offset in offsets:
        xref.append(f"{offset:010d} 00000 n \n".encode("latin-1"))
    trailer = (
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        + f"startxref\n{xref_pos}\n".encode("latin-1")
        + b"%%EOF\n"
    )
    return header + bytes(body) + b"".join(xref) + trailer


def write_simple_text_pdf(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_simple_text_pdf_bytes(text))
    return path


__all__ = [
    "build_simple_text_pdf_bytes",
    "escape_pdf_string",
    "write_simple_text_pdf",
]
