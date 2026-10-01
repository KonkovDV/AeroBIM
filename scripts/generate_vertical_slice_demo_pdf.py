#!/usr/bin/env python3
"""Generate the fixed vertical-slice demo PDF (fixture, vector text only).

Claim boundary: deterministic text-layer input for a demo slice — not scanned
OCR evidence and not engineering CV.
"""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_OUT = _REPO / "samples" / "demo" / "vertical-slice-2026-08-11" / "techlab-a101-wall-thickness.pdf"


def _wrap_single_page(content: bytes, page_w: float = 612, page_h: float = 792) -> bytes:
    stream = content
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        + (
            f"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 {page_w} {page_h}]/"
            f"Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
            f"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            f"5 0 obj<</Length {len(stream)}>>stream\n"
        ).encode("latin-1")
        + stream
        + b"endstream\nendobj\nxref\n0 6\n"
        b"0000000000 65535 f \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n0\n%%EOF\n"
    )


def main() -> None:
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    text = "WALL-01 thickness 150 mm"
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET\n".encode("latin-1", errors="replace")
    _OUT.write_bytes(_wrap_single_page(content))
    print(f"wrote {_OUT} bytes={_OUT.stat().st_size}")


if __name__ == "__main__":
    main()
