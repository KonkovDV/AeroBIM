"""pypdfium2 crop/render in a child process (RT-C3PO-002).

The parent never imports pypdfium2. A hung or crashing PDFium build stays
in the worker; this is process isolation, not an extra in-thread timeout.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from typing import Any


def _normalize_bbox(
    bbox: tuple[float, float, float, float],
    width_pt: float,
    height_pt: float,
    coordinate_system: str,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = bbox
    if coordinate_system == "page-point" and max(bbox) <= 1.0 and min(bbox) >= 0.0:
        raise ValueError(
            "bbox looks normalized-0-1 but cropper coordinate_system is page-point; "
            "refuse ambiguous crop (set coordinate_system='normalized-0-1')"
        )
    if coordinate_system == "normalized-0-1":
        x1, x2 = x1 * width_pt, x2 * width_pt
        y1, y2 = y1 * height_pt, y2 * height_pt
    return x1, y1, x2, y2


def _bounded_dpi(width_pt: float, height_pt: float, dpi: int, max_side_px: int) -> int:
    longest_pt = max(width_pt, height_pt)
    if longest_pt <= 0:
        return dpi
    max_dpi_for_budget = int(max_side_px * 72 / longest_pt)
    return max(72, min(dpi, max_dpi_for_budget))


def crop_pdf_region(
    *,
    path: str,
    page_number: int,
    bbox_xyxy: tuple[float, float, float, float],
    dpi: int,
    coordinate_system: str,
    max_side_px: int,
) -> bytes:
    """Open PDF + render crop inside the calling process (the isolated worker)."""

    try:
        import pypdfium2 as pdfium
    except ModuleNotFoundError as exc:  # pragma: no cover - core dep
        raise RuntimeError("Region cropping requires pypdfium2 (core PDF backend)") from exc
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("Region cropping requires Pillow (core dependency)") from exc

    document = pdfium.PdfDocument(path)
    try:
        if not 0 <= page_number < len(document):
            raise ValueError(f"page {page_number} out of range (pages={len(document)})")
        page = document[page_number]
        width_pt = float(page.get_width())
        height_pt = float(page.get_height())
        x1, y1, x2, y2 = _normalize_bbox(bbox_xyxy, width_pt, height_pt, coordinate_system)
        left = max(0.0, min(x1, x2))
        right = min(width_pt, max(x1, x2))
        top_from_top = max(0.0, min(y1, y2))
        bottom_from_top = min(height_pt, max(y1, y2))
        if right - left <= 0 or bottom_from_top - top_from_top <= 0:
            raise ValueError(f"degenerate/out-of-bounds crop rect for bbox={bbox_xyxy}")

        render_dpi = _bounded_dpi(right - left, bottom_from_top - top_from_top, dpi, max_side_px)
        scale = render_dpi / 72.0
        cut_left = left
        cut_right = width_pt - right
        cut_top = top_from_top
        cut_bottom = height_pt - bottom_from_top
        bitmap = page.render(
            scale=scale,
            crop=(cut_left, cut_bottom, cut_right, cut_top),
        )
        image = bitmap.to_pil()
        if not isinstance(image, Image.Image):
            raise RuntimeError("pypdfium2 render did not yield a PIL image")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    finally:
        document.close()


def _crop_from_spec(spec: dict[str, Any]) -> bytes:
    bbox = spec["bbox_xyxy"]
    return crop_pdf_region(
        path=str(spec["path"]),
        page_number=int(spec["page_number"]),
        bbox_xyxy=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
        dpi=int(spec["dpi"]),
        coordinate_system=str(spec["coordinate_system"]),
        max_side_px=int(spec["max_side_px"]),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Isolated pypdfium2 region crop")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    spec_path = Path(args.spec)
    out_path = Path(args.output)
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        png = _crop_from_spec(spec)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    out_path.write_bytes(png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
