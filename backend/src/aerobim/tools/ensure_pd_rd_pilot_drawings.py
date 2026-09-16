"""Ensure synthetic PD-RD pilot PDF/text fixtures exist (text-layer only)."""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.simple_text_pdf import write_simple_text_pdf

_ROOT = Path(__file__).resolve().parents[4]
_DIR = _ROOT / "samples" / "demo" / "pd-rd-consistency-pilot-2026-09"


def ensure_pilot_drawings(directory: Path | None = None) -> dict[str, Path]:
    target = directory or _DIR
    target.mkdir(parents=True, exist_ok=True)
    written = {
        "clean": write_simple_text_pdf(
            target / "a-101-thickness-200mm.pdf",
            "A-101  WALL-01 thickness 200 mm",
        ),
        "defect": write_simple_text_pdf(
            target / "a-101-thickness-150mm.pdf",
            "A-101  WALL-01 thickness 150 mm",
        ),
        "unit": write_simple_text_pdf(
            target / "a-101-thickness-0.20m.pdf",
            "A-101  WALL-01 thickness 0.20 m",
        ),
        "missing": write_simple_text_pdf(
            target / "a-101-no-thickness.pdf",
            "A-101 plan view WALL-01 note without a measure",
        ),
    }
    corrupt = target / "corrupt-not-a-pdf.pdf"
    corrupt.write_bytes(b"%PDF-1.4\nthis is not a valid PDF body")
    written["parser_error"] = corrupt
    unsupported = target / "sheet.xyz"
    unsupported.write_text("not a drawing format", encoding="utf-8")
    written["unsupported"] = unsupported
    return written


if __name__ == "__main__":
    paths = ensure_pilot_drawings()
    for name, path in paths.items():
        print(f"{name}\t{path}\t{path.stat().st_size}")
