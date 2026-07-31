"""pdfminer.six signal producer for extraction-integrity (LIC-001 Option B).

Honest scope: inspects the PDF *text layer* for near-zero font size and
off-page characters. This is NOT a full render-vs-extract / OCR product.
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.extraction_integrity import ExtractionIntegritySignals


class PdfMinerExtractionIntegrityProducer:
    """Infrastructure adapter — permissive MIT text-layer probe."""

    def produce(self, path: Path) -> ExtractionIntegritySignals:
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTChar, LTPage, LTTextContainer
        except ModuleNotFoundError as exc:  # pragma: no cover - core dep
            raise RuntimeError(
                "Extraction-integrity PDF probe requires pdfminer.six (core PDF backend)"
            ) from exc

        extracted = 0
        hidden = 0
        offpage = 0
        visible_glyphs = False

        for page in extract_pages(str(path)):
            if not isinstance(page, LTPage):
                continue
            page_x0, page_y0, page_x1, page_y1 = page.bbox
            plain_parts: list[str] = []
            page_box = (page_x0, page_y0, page_x1, page_y1)

            def _walk(
                obj: object,
                *,
                box: tuple[float, float, float, float] = page_box,
                parts: list[str] = plain_parts,
            ) -> None:
                nonlocal hidden, offpage, visible_glyphs
                if isinstance(obj, LTChar):
                    text = obj.get_text() or ""
                    if not text.strip():
                        return
                    size = float(getattr(obj, "size", 0.0) or 0.0)
                    x0, y0, x1, y1 = obj.bbox
                    if size <= 0.05:
                        hidden += len(text)
                        return
                    bx0, by0, bx1, by1 = box
                    outside = x1 < bx0 or x0 > bx1 or y1 < by0 or y0 > by1
                    if outside:
                        offpage += len(text)
                        return
                    visible_glyphs = True
                    return
                if isinstance(obj, LTTextContainer):
                    parts.append(obj.get_text() or "")
                    for child in obj:
                        _walk(child, box=box, parts=parts)
                    return
                if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
                    try:
                        for child in obj:  # type: ignore[union-attr]
                            _walk(child, box=box, parts=parts)
                    except TypeError:
                        return

            _walk(page)
            extracted += len("".join(plain_parts).strip())

        return ExtractionIntegritySignals(
            extracted_char_count=extracted,
            rendered_text_present=visible_glyphs if (extracted > 0 or visible_glyphs) else None,
            hidden_text_char_count=hidden,
            offpage_text_char_count=offpage,
            duplicated_layer_count=0,
            ocr_char_count=None,
        )


__all__ = ["PdfMinerExtractionIntegrityProducer"]
