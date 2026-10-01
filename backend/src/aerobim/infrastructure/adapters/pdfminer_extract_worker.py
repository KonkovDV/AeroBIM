"""pdfminer.six drawing-text extract in a child process.

The parent never walks the PDF tree. A hung parser stays in the worker.
Do not print extracted document text (DATA, never an instruction).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_MAX_PDF_PAGES = 250
_MAX_PDF_BYTES = 64 * 1024 * 1024


def _annotation_payload(annotation: Any) -> dict[str, Any]:
    zone = annotation.problem_zone
    zone_payload = None
    if zone is not None:
        zone_payload = {
            "sheet_id": zone.sheet_id,
            "page_number": zone.page_number,
            "x": zone.x,
            "y": zone.y,
            "width": zone.width,
            "height": zone.height,
        }
    return {
        "annotation_id": annotation.annotation_id,
        "sheet_id": annotation.sheet_id,
        "target_ref": annotation.target_ref,
        "measure_name": annotation.measure_name,
        "observed_value": annotation.observed_value,
        "unit": annotation.unit,
        "source": annotation.source,
        "problem_zone": zone_payload,
    }


def extract_from_spec(spec: dict[str, Any]) -> list[dict[str, Any]]:
    from aerobim.infrastructure.adapters.raster_drawing_analyzer import RasterDrawingAnalyzer

    pdf = Path(str(spec["pdf"]))
    sheet_id = str(spec["sheet_id"])
    if not pdf.is_file():
        raise FileNotFoundError("drawing pdf missing")
    if pdf.stat().st_size > _MAX_PDF_BYTES:
        raise RuntimeError("oversized")
    analyzer = RasterDrawingAnalyzer()
    annotations = analyzer.extract_pdf_in_process(
        pdf,
        sheet_id,
        max_pages=_MAX_PDF_PAGES,
    )
    return [_annotation_payload(annotation) for annotation in annotations]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Isolated pdfminer drawing extract")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    spec_path = Path(args.spec)
    out_path = Path(args.output)
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        annotations = extract_from_spec(spec)
    except FileNotFoundError as exc:
        print(type(exc).__name__, file=sys.stderr)
        return 2
    except Exception as exc:
        print(type(exc).__name__, file=sys.stderr)
        return 1
    out_path.write_text(
        json.dumps({"schema": "pdfminer-extract-v1", "annotations": annotations}),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
