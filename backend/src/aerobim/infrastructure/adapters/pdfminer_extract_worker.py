"""Drawing-text extract in a child process.

PDFium reads the text layer. pdfminer.six is the fallback when PDFium cannot
open the file. The parent never walks the PDF tree. A hung parser stays in the
worker.
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
    except Exception as exc:
        print(type(exc).__name__, file=sys.stderr)
        return 1
    files = spec.get("files") if isinstance(spec, dict) else None
    if not isinstance(files, list):
        print("ValueError", file=sys.stderr)
        return 1
    with out_path.open("w", encoding="utf-8") as handle:
        for index, item in enumerate(files):
            record: dict[str, Any] = {"index": index}
            try:
                if not isinstance(item, dict):
                    raise ValueError("bad item")
                record["annotations"] = extract_from_spec(item)
            except Exception as exc:
                record["error"] = type(exc).__name__
            handle.write(json.dumps(record) + "\n")
            handle.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
