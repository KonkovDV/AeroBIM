"""Render an honest drawing-overlay evidence PNG (fixture / smoke path).

Draws a ``problem_zone`` rectangle on a rasterized sheet. Claim boundary:
deterministic overlay of a known bbox on a drawing page — not CV stamp
detection, not human-level drawing understanding, not product >90%.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def render_overlay(
    *,
    pdf_path: Path,
    out_png: Path,
    zone: dict[str, float],
    page_number: int = 1,
) -> dict[str, object]:
    import pymupdf
    from PIL import Image, ImageDraw

    doc = pymupdf.open(str(pdf_path))
    try:
        page = doc.load_page(page_number - 1)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    finally:
        doc.close()

    # PDF user-space coords → pixmap (2× zoom).
    scale = 2.0
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
        "claim_boundary": (
            "Deterministic bbox overlay on rasterized PDF page; not CV; "
            "not stamp product detection; illustration evidence for TZ drawing overlay."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Source PDF (default: samples/demo vertical-slice sheet)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Evidence dir (default: docs/evidence/drawing-overlay-smoke-2026-08)",
    )
    args = parser.parse_args(argv)
    repo = _repo_root()
    pdf = args.pdf or (
        repo / "samples" / "demo" / "vertical-slice-2026-08-11" / "techlab-a101-wall-thickness.pdf"
    )
    out_dir = args.out_dir or (repo / "docs" / "evidence" / "drawing-overlay-smoke-2026-08")
    # Zone aligned with vertical-slice WALL-01 thickness text band (page user space).
    zone = {"x": 72.0, "y": 62.0, "width": 150.0, "height": 14.0}
    png = out_dir / "overlay-wall-thickness.png"
    meta = render_overlay(pdf_path=pdf, out_png=png, zone=zone, page_number=1)
    try:
        pdf_rel = str(pdf.resolve().relative_to(repo).as_posix())
        png_rel = str(png.resolve().relative_to(repo).as_posix())
    except ValueError:
        pdf_rel = str(pdf.as_posix())
        png_rel = str(png.as_posix())
    status_payload = {
        "schema_version": "1.0.0",
        "slice_id": "drawing-overlay-smoke-2026-08",
        "date": "2026-08-11",
        "status": "fixture_rendered",
        "claim_level": "fixture_only",
        **meta,
        "png": png_rel,
        "source_pdf": pdf_rel,
    }
    (out_dir / "STATUS.json").write_text(
        json.dumps(status_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    readme = out_dir / "README.md"
    readme.write_text(
        "<!-- claims-lint: allow-file reason=\"Overlay evidence boundary doc\" -->\n"
        "---\n"
        'title: "Drawing overlay smoke evidence"\n'
        'date: "2026-08-11"\n'
        'claim_boundary: "Deterministic bbox on rasterized PDF — not CV / stamp product."\n'
        "---\n\n"
        "# Drawing overlay smoke (2026-08-11)\n\n"
        f"- PNG: `{png.name}`\n"
        f"- SHA-256: `{meta['sha256']}`\n"
        f"- Zone: `{zone}` on page 1 of `{pdf.name}`\n\n"
        "This illustrates TZ «просмотр чертежей с наложением ошибок» with a known\n"
        "`problem_zone`. It does **not** claim computer-vision stamp detection.\n",
        encoding="utf-8",
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
