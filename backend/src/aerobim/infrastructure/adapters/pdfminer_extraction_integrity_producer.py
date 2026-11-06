"""Text-layer signal producer for extraction-integrity (LIC-001 Option B).

PDFium reads font size and character boxes. pdfminer.six remains the fallback
when PDFium cannot open the file. Honest scope: near-zero font size and
off-page characters in the text layer. This is not a render-vs-extract product.
Digit runs follow the PDFium text layer, so a sheet can show numbers pdfminer
never returned. Hidden-text and off-page counts stay on the same cutoff.
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.extraction_integrity import (
    ExtractionIntegritySignals,
    dominant_letter_script,
    extract_digit_runs,
)
from aerobim.domain.pdf_page_frame import upright_char_box
from aerobim.infrastructure.adapters.pdfium_page_view import viewed_pdfium_page

# pdfminer treats a font size at or below this as invisible. PDFium exposes the
# same size, so the cutoff stays here rather than on the tight glyph box: a
# period in a normal font is short, but it is not hidden text.
_HIDDEN_FONT_SIZE_PT = 0.05
_MAX_PAGES = 200


class PdfMinerExtractionIntegrityProducer:
    """Infrastructure adapter — permissive MIT text-layer probe."""

    def produce(self, path: Path) -> ExtractionIntegritySignals:
        try:
            return self._produce_pdfium(path)
        except Exception:
            return self._produce_pdfminer(path)

    def _produce_pdfium(self, path: Path) -> ExtractionIntegritySignals:
        import pypdfium2 as pdfium
        import pypdfium2.raw as pdfium_c

        extracted = 0
        hidden = 0
        offpage = 0
        visible_glyphs = False
        page_texts: list[str] = []
        document = pdfium.PdfDocument(str(path))
        try:
            page_count = min(len(document), _MAX_PAGES)
            for index in range(page_count):
                page = document[index]
                try:
                    rotation, media_box, page_w, page_h = viewed_pdfium_page(page)
                    textpage = page.get_textpage()
                    try:
                        chars: list[str] = []
                        for char_index in range(int(textpage.count_chars())):
                            char = textpage.get_text_range(char_index, 1) or ""
                            if not char:
                                continue
                            chars.append(char)
                            if not char.strip():
                                continue
                            font_size = float(
                                pdfium_c.FPDFText_GetFontSize(textpage.raw, char_index)
                            )
                            if font_size <= _HIDDEN_FONT_SIZE_PT:
                                hidden += len(char)
                                continue
                            raw_left, raw_bottom, raw_right, raw_top = textpage.get_charbox(
                                char_index
                            )
                            if float(raw_top) < float(raw_bottom):
                                continue
                            left, bottom, right, top = upright_char_box(
                                float(raw_left),
                                float(raw_bottom),
                                float(raw_right),
                                float(raw_top),
                                rotation=rotation,
                                media_x0=media_box[0],
                                media_y0=media_box[1],
                                media_x1=media_box[2],
                                media_y1=media_box[3],
                            )
                            outside = right < 0.0 or left > page_w or top < 0.0 or bottom > page_h
                            if outside:
                                offpage += len(char)
                                continue
                            visible_glyphs = True
                        page_texts.append("".join(chars))
                    finally:
                        textpage.close()
                finally:
                    page.close()
        finally:
            document.close()

        plain = "\n".join(page_texts)
        extracted = len(plain.strip())
        return ExtractionIntegritySignals(
            extracted_char_count=extracted,
            rendered_text_present=visible_glyphs if (extracted > 0 or visible_glyphs) else None,
            hidden_text_char_count=hidden,
            offpage_text_char_count=offpage,
            duplicated_layer_count=0,
            ocr_char_count=None,
            extracted_digit_runs=extract_digit_runs(plain),
            ocr_digit_runs=None,
            dominant_script=dominant_letter_script(plain),
        )

    def _produce_pdfminer(self, path: Path) -> ExtractionIntegritySignals:
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
        all_plain: list[str] = []

        for page_index, page in enumerate(extract_pages(str(path))):
            if page_index >= _MAX_PAGES:
                break
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
                    if size <= _HIDDEN_FONT_SIZE_PT:
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
                        for child in obj:
                            _walk(child, box=box, parts=parts)
                    except TypeError:
                        return

            _walk(page)
            page_text = "".join(plain_parts)
            all_plain.append(page_text)
            extracted += len(page_text.strip())

        plain = "\n".join(all_plain)
        return ExtractionIntegritySignals(
            extracted_char_count=extracted,
            rendered_text_present=visible_glyphs if (extracted > 0 or visible_glyphs) else None,
            hidden_text_char_count=hidden,
            offpage_text_char_count=offpage,
            duplicated_layer_count=0,
            ocr_char_count=None,
            extracted_digit_runs=extract_digit_runs(plain),
            ocr_digit_runs=None,
            dominant_script=dominant_letter_script(plain),
        )


__all__ = ["PdfMinerExtractionIntegrityProducer"]
