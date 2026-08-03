"""Optional OCR-vs-text-layer enrichment for extraction-integrity (LIC-001 / P-003).

Renders PDF pages via pypdfium2 and, when RapidOCR is installed (``raster`` extra),
fills ``ocr_char_count`` and ``ocr_digit_runs`` so the domain assessor can collide
text-layer vs OCR (char-volume WARNING; digit-run mismatch FAILED).

Honest scope:
- Engineering signal — catches same-length numeric spoof (visual «3000» / text «3300»).
- NOT a full product-grade render-vs-extract claim (OCR noise, limited pages).
- If RapidOCR is missing, returns the base text-layer signals unchanged
  (``ocr_char_count=None``, ``ocr_digit_runs=None``).
"""

from __future__ import annotations

import io
from dataclasses import replace
from pathlib import Path
from typing import Any

from aerobim.domain.extraction_integrity import (
    ExtractionIntegritySignals,
    extract_digit_runs,
)
from aerobim.infrastructure.adapters.pdfminer_extraction_integrity_producer import (
    PdfMinerExtractionIntegrityProducer,
)


class OcrAwareExtractionIntegrityProducer:
    """Compose pdfminer text-layer signals with optional OCR on rendered pages."""

    def __init__(
        self,
        *,
        text_producer: PdfMinerExtractionIntegrityProducer | None = None,
        ocr_engine_factory: Any | None = None,
        max_pages: int = 3,
        render_scale: float = 150 / 72.0,
    ) -> None:
        self._text = text_producer or PdfMinerExtractionIntegrityProducer()
        self._ocr_engine_factory = ocr_engine_factory
        self._ocr_engine: Any | None = None
        self._max_pages = max(1, max_pages)
        self._render_scale = render_scale

    def produce(self, path: Path) -> ExtractionIntegritySignals:
        base = self._text.produce(path)
        ocr = self._try_ocr(path)
        if ocr is None:
            return base
        ocr_chars, ocr_text = ocr
        rendered = base.rendered_text_present
        if ocr_chars > 0:
            rendered = True
        return replace(
            base,
            ocr_char_count=ocr_chars,
            rendered_text_present=rendered,
            ocr_digit_runs=extract_digit_runs(ocr_text),
        )

    def _try_ocr(self, path: Path) -> tuple[int, str] | None:
        engine = self._resolve_ocr_engine()
        if engine is None:
            return None
        try:
            import pypdfium2 as pdfium
        except ModuleNotFoundError:
            return None
        try:
            from PIL import Image
        except ModuleNotFoundError:
            return None

        parts: list[str] = []
        document = pdfium.PdfDocument(str(path))
        try:
            page_count = min(len(document), self._max_pages)
            for index in range(page_count):
                page = document[index]
                bitmap = page.render(scale=self._render_scale)
                image = bitmap.to_pil()
                if not isinstance(image, Image.Image):
                    continue
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                parts.append(self._ocr_png_bytes(engine, buffer.getvalue()))
        finally:
            document.close()
        text = "\n".join(parts)
        return len(text.strip()), text

    def _ocr_png_bytes(self, engine: Any, png: bytes) -> str:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            handle.write(png)
            temp_path = Path(handle.name)
        try:
            result = engine(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
        texts = getattr(result, "txts", None) or ()
        return " ".join(str(text).strip() for text in texts if str(text).strip())

    def _resolve_ocr_engine(self) -> Any | None:
        if self._ocr_engine is not None:
            return self._ocr_engine
        if self._ocr_engine_factory is not None:
            self._ocr_engine = self._ocr_engine_factory()
            return self._ocr_engine
        try:
            from rapidocr import RapidOCR
        except ModuleNotFoundError:
            return None
        self._ocr_engine = RapidOCR()
        return self._ocr_engine


__all__ = ["OcrAwareExtractionIntegrityProducer"]
