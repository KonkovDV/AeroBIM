"""PyMuPDF signal producer for extraction-integrity (P-003 producer wire).

Honest scope: inspects the PDF *text layer* for hidden / off-page / zero-size
spans. This is NOT a full render-vs-extract product (no raster OCR comparison).
Domain assessor remains in ``domain/extraction_integrity.py``.
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.extraction_integrity import ExtractionIntegritySignals


class PyMuPDFExtractionIntegrityProducer:
    """Infrastructure adapter — stays behind the LIC-001 seam (pymupdf only here)."""

    def produce(self, path: Path) -> ExtractionIntegritySignals:
        try:
            import pymupdf
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Extraction-integrity PDF probe requires PyMuPDF (core dependency)"
            ) from exc

        extracted = 0
        hidden = 0
        offpage = 0
        visible_glyphs = False

        with pymupdf.open(path) as document:
            for page in document:
                page_rect = page.rect
                # Visible extract path (same family as RasterDrawingAnalyzer).
                plain = page.get_text("text") or ""
                extracted += len(plain.strip())

                raw = page.get_text("dict") or {}
                for block in raw.get("blocks") or ():
                    if not isinstance(block, dict) or block.get("type", 0) != 0:
                        continue
                    for line in block.get("lines") or ():
                        if not isinstance(line, dict):
                            continue
                        for span in line.get("spans") or ():
                            if not isinstance(span, dict):
                                continue
                            text = span.get("text") or ""
                            if not isinstance(text, str) or not text.strip():
                                continue
                            size = float(span.get("size") or 0.0)
                            bbox = span.get("bbox")
                            color = span.get("color")
                            # Zero / near-zero font size → hidden/invisible layer signal.
                            if size <= 0.05:
                                hidden += len(text)
                                continue
                            # White-ish text (RGB packed int near white) → hidden signal.
                            if isinstance(color, int) and color >= 0xF0F0F0:
                                hidden += len(text)
                                continue
                            if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                                x0 = float(bbox[0])
                                y0 = float(bbox[1])
                                x1 = float(bbox[2])
                                y1 = float(bbox[3])
                                outside = (
                                    x1 < page_rect.x0
                                    or x0 > page_rect.x1
                                    or y1 < page_rect.y0
                                    or y0 > page_rect.y1
                                )
                                if outside:
                                    offpage += len(text)
                                    continue
                            visible_glyphs = True

        return ExtractionIntegritySignals(
            extracted_char_count=extracted,
            rendered_text_present=visible_glyphs if (extracted > 0 or visible_glyphs) else None,
            hidden_text_char_count=hidden,
            offpage_text_char_count=offpage,
            duplicated_layer_count=0,
            ocr_char_count=None,
        )


__all__ = ["PyMuPDFExtractionIntegrityProducer"]
