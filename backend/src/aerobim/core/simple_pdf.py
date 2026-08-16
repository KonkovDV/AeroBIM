"""Minimal multi-page PDF writer (Helvetica, no external deps)."""

from __future__ import annotations

from pathlib import Path


def escape_pdf_literal(line: str) -> str:
    """Escape text for a PDF ``(...)`` string (HD5-PDF-01).

    Backslash and parentheses are escaped. CR/LF become spaces so a content
    stream cannot break mid-literal. Non-ASCII is replaced (Helvetica).
    """
    return (
        line.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", " ")
        .replace("\n", " ")
        .encode("ascii", "replace")
        .decode("ascii")
    )


def write_simple_pdf(path: Path, lines: list[str], *, lines_per_page: int = 50) -> None:
    """Write a plain-text PDF with paginated content blocks."""

    pages: list[list[str]] = []
    chunk: list[str] = []
    for line in lines:
        chunk.append(line)
        if len(chunk) >= lines_per_page:
            pages.append(chunk)
            chunk = []
    if chunk:
        pages.append(chunk)
    if not pages:
        pages = [["(empty)"]]

    objects: list[bytes] = []
    page_streams: list[bytes] = []
    for page_lines in pages:
        content_lines = ["BT /F1 9 Tf 40 780 Td 11 TL"]
        for i, line in enumerate(page_lines):
            safe = escape_pdf_literal(line)
            if i == 0:
                content_lines.append(f"({safe}) Tj")
            else:
                content_lines.append(f"T* ({safe}) Tj")
        content_lines.append("ET")
        page_streams.append("\n".join(content_lines).encode("latin-1", "replace"))

    n_pages = len(page_streams)
    page_obj_nums = list(range(3, 3 + n_pages))
    content_obj_nums = list(range(3 + n_pages, 3 + 2 * n_pages))
    font_obj = 3 + 2 * n_pages

    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
    objects.append(
        f"2 0 obj<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>endobj\n".encode("ascii")
    )
    for page_num, content_num in zip(page_obj_nums, content_obj_nums, strict=True):
        objects.append(
            (
                f"{page_num} 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_num} 0 R /Resources<< /Font<< /F1 {font_obj} 0 R >> >> >>"
                f"endobj\n"
            ).encode("ascii")
        )
    for content_num, stream in zip(content_obj_nums, page_streams, strict=True):
        objects.append(
            f"{content_num} 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
            + stream
            + b"\nendstream\nendobj\n"
        )
    objects.append(
        f"{font_obj} 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n".encode(
            "ascii"
        )
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
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "ascii"
        )
    )
    path.write_bytes(bytes(out))
