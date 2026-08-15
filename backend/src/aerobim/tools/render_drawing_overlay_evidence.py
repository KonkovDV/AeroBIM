"""Render honest drawing-overlay evidence PNGs (fixture / smoke path).

Draws known ``problem_zone`` rectangles on a rasterized sheet. Claim boundary:
deterministic overlay of known bboxes — not CV, not stamp product, not >90%.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _rasterize_pdf_page(pdf_path: Path, page_number: int, *, scale: float) -> tuple[Any, str]:
    """Rasterize one PDF page. Core path is pypdfium2 (LIC-001); PyMuPDF is fallback."""

    from PIL import Image

    try:
        import pypdfium2 as pdfium
    except ModuleNotFoundError:
        pdfium = None
    if pdfium is not None:
        document = pdfium.PdfDocument(str(pdf_path))
        try:
            index = page_number - 1
            if not 0 <= index < len(document):
                raise ValueError(f"page {page_number} out of range (pages={len(document)})")
            bitmap = document[index].render(scale=scale)
            image = bitmap.to_pil()
        finally:
            document.close()
        if not isinstance(image, Image.Image):
            raise RuntimeError("pypdfium2 render did not yield a PIL image")
        return image.convert("RGB"), "pypdfium2"

    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    try:
        page = doc.load_page(page_number - 1)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    finally:
        doc.close()
    return image.convert("RGB"), "pymupdf"


def render_overlay(
    *,
    pdf_path: Path,
    out_png: Path,
    zone: dict[str, float],
    page_number: int = 1,
) -> dict[str, object]:
    from PIL import ImageDraw

    scale = 2.0
    img, renderer = _rasterize_pdf_page(pdf_path, page_number, scale=scale)
    x0 = float(zone["x"]) * scale
    y0 = float(zone["y"]) * scale
    x1 = x0 + float(zone["width"]) * scale
    y1 = y0 + float(zone["height"]) * scale
    draw = ImageDraw.Draw(img)
    draw.rectangle([x0, y0, x1, y1], outline=(220, 40, 40), width=4)
    draw.line([(x0, y0), (x1, y1)], fill=(220, 40, 40), width=2)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, format="PNG")
    digest = hashlib.sha256(out_png.read_bytes()).hexdigest()
    return {
        "png": str(out_png.as_posix()),
        "sha256": digest,
        "page_number": page_number,
        "problem_zone": zone,
        "source_pdf": str(pdf_path.as_posix()),
        "rendered_at": datetime.now(tz=UTC).isoformat(),
        "renderer": renderer,
        "claim_boundary": (
            "Deterministic bbox overlay on rasterized PDF page; not CV; "
            "not stamp product detection; illustration evidence for TZ drawing overlay."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    repo = _repo_root()
    pdf = args.pdf or (
        repo / "samples" / "demo" / "vertical-slice-2026-08-11" / "techlab-a101-wall-thickness.pdf"
    )
    out_dir = args.out_dir or (repo / "docs" / "evidence" / "drawing-overlay-smoke-2026-08")
    zones = {
        "wall_thickness": {
            "file": "overlay-wall-thickness.png",
            "zone": {"x": 72.0, "y": 62.0, "width": 150.0, "height": 14.0},
        },
        "sheet_header": {
            "file": "overlay-sheet-header.png",
            "zone": {"x": 36.0, "y": 36.0, "width": 220.0, "height": 28.0},
        },
    }
    overlays: dict[str, object] = {}
    for key, spec in zones.items():
        png = out_dir / str(spec["file"])
        zone = spec["zone"]
        assert isinstance(zone, dict)
        meta = render_overlay(pdf_path=pdf, out_png=png, zone=zone, page_number=1)
        try:
            png_rel = str(png.resolve().relative_to(repo).as_posix())
        except ValueError:
            png_rel = str(png.as_posix())
        overlays[key] = {**meta, "png": png_rel}

    try:
        pdf_rel = str(pdf.resolve().relative_to(repo).as_posix())
    except ValueError:
        pdf_rel = str(pdf.as_posix())

    primary = overlays["wall_thickness"]
    assert isinstance(primary, dict)
    status_payload = {
        "schema_version": "1.1.0",
        "slice_id": "drawing-overlay-smoke-2026-08",
        "date": "2026-08-12",
        "status": "fixture_rendered",
        "claim_level": "fixture_only",
        "source_pdf": pdf_rel,
        "overlays": overlays,
        "png": primary["png"],
        "sha256": primary["sha256"],
        "page_number": primary["page_number"],
        "problem_zone": primary["problem_zone"],
        "rendered_at": primary["rendered_at"],
        "claim_boundary": primary["claim_boundary"],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "STATUS.json").write_text(
        json.dumps(status_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(
        '<!-- claims-lint: allow-file reason="Overlay evidence boundary doc" -->\n'
        "---\n"
        'title: "Drawing overlay smoke evidence"\n'
        'date: "2026-08-12"\n'
        'claim_boundary: "Deterministic bboxes on rasterized PDF — not CV / stamp product."\n'
        "---\n\n"
        "# Drawing overlay smoke (2026-08-12)\n\n"
        f"- Primary PNG: `{Path(str(primary['png'])).name}`\n"
        f"- Primary SHA-256: `{primary['sha256']}`\n"
        f"- Zones: wall thickness + sheet header on page 1 of `{pdf.name}`\n\n"
        "Illustrates TZ «просмотр чертежей с наложением ошибок» with known "
        "`problem_zone`s. Does **not** claim computer-vision stamp detection.\n",
        encoding="utf-8",
    )
    print(json.dumps(status_payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
