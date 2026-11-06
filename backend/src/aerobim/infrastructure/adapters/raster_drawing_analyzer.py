"""Deterministic drawing analyzer baseline for raster and PDF inputs.

Implements the ``RasterDrawingAnalyzer`` port using OCR and layout heuristics only
(non-deterministic adapters are outside the pilot sign-off path).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aerobim.domain.models import DrawingAnnotation, ProblemZone
from aerobim.domain.paired_dimension import is_paired_dimension
from aerobim.domain.pdf_page_frame import upright_char_box, upright_page_size
from aerobim.domain.stamp_caption_above import (
    STAMP_CAPTION_SOURCE,
    PlacedLine,
    line_center_in_title_block,
    pair_captions_above_values,
    value_is_standard_citation,
)
from aerobim.infrastructure.adapters.drawing_annotation_identity import (
    canonical_coord,
    drawing_annotation_digest,
    drawing_annotation_id,
)
from aerobim.infrastructure.adapters.pdf_page_orientation import viewed_pdfium_page
from aerobim.infrastructure.adapters.pdfminer_extract_isolate import (
    run_pdfminer_extract_isolated,
)

_PDF_OPEN_TIMEOUT_S = 30.0
_MEASURE_ALIASES = {
    "thickness": "thickness",
    "толщина": "thickness",
    "width": "width",
    "ширина": "width",
    "height": "height",
    "высота": "height",
    "length": "length",
    "длина": "length",
    "area": "area",
    "площадь": "area",
}
_UNITS_PATTERN = r"mm|мм|cm|см|m|м|m2|м2|m²|м²"
_TARGET_PATTERN = r"[A-ZА-Я][A-ZА-Я0-9_-]{1,}"
_TEXT_PATTERNS = (
    re.compile(
        rf"(?P<target>{_TARGET_PATTERN})\s+(?P<measure>thickness|width|height|length|area)"
        rf"\s*(?:[:=]|>=|<=|≥|≤|is)?\s*(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>{_UNITS_PATTERN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<target>{_TARGET_PATTERN})\s+(?P<measure>толщина|ширина|высота|длина|площадь)"
        rf"\s*(?:[:=]|>=|<=|≥|≤|не\s+менее|не\s+более)?\s*(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>{_UNITS_PATTERN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<measure>толщина|ширина|высота|длина|площадь)\s+(?P<target>{_TARGET_PATTERN})"
        rf"\s*(?:[:=]|>=|<=|≥|≤|не\s+менее|не\s+более)?\s*(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>{_UNITS_PATTERN})\b",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class _TextRegion:
    text: str
    page_number: int
    x: float
    y: float
    width: float
    height: float


# A hyphen's box sits inside the letter band, but its bottom is not the
# letter bottom. Expand the open line by this slack before the overlap test.
_PDF_LINE_OVERLAP_SLACK_PT = 1.0


def _char_continues_line(
    bottom: float,
    top: float,
    line_bottom: float,
    line_top: float,
) -> bool:
    """Whether a character box belongs to the open line.

    Boxes are closed intervals in PDF points, origin at the bottom-left.
    The open line is expanded by ``_PDF_LINE_OVERLAP_SLACK_PT`` on both
    sides. A hyphen whose bottom sits above the letter baseline still
    overlaps the letter band and stays on the line. A box that clears
    the band starts the next line. Stream order is the only order.
    """

    slack = _PDF_LINE_OVERLAP_SLACK_PT
    return bottom <= line_top + slack and top >= line_bottom - slack


def _extend_line_band(
    line_bottom: float,
    line_top: float,
    bottom: float,
    top: float,
) -> tuple[float, float]:
    """Grow the open line by at most the slack.

    A glyph that merely overlaps the band must not drag the band down to its
    own full height. Otherwise one tall box joins every later line on the page.
    """

    slack = _PDF_LINE_OVERLAP_SLACK_PT
    low = max(bottom, line_bottom - slack)
    high = min(top, line_top + slack)
    if high < low:
        return line_bottom, line_top
    return min(line_bottom, low), max(line_top, high)


def _pdfium_text_lines(
    textpage: Any,
    *,
    rotation: int,
    media_box: tuple[float, float, float, float],
) -> list[tuple[str, float, float, float, float]]:
    """Group PDFium character boxes into lines on the upright page.

    Returns ``(text, x, y, width, height)`` in top-left page space, the same
    frame the pdfminer path uses. Stored boxes are turned by ``/Rotate``
    before the line test: the page size is already the viewed sheet.
    """

    media_x0, media_y0, media_x1, media_y1 = media_box
    _page_w, page_h = upright_page_size(rotation, media_x0, media_y0, media_x1, media_y1)
    count = int(textpage.count_chars())
    lines: list[tuple[str, float, float, float, float]] = []
    buffer: list[tuple[str, float, float, float, float]] = []
    line_bottom: float | None = None
    line_top: float | None = None

    def flush() -> None:
        nonlocal buffer, line_bottom, line_top
        if not buffer:
            return
        text = "".join(item[0] for item in buffer).strip()
        if text:
            x0 = min(item[1] for item in buffer)
            y0 = min(item[2] for item in buffer)
            x1 = max(item[3] for item in buffer)
            y1 = max(item[4] for item in buffer)
            lines.append(
                (
                    text,
                    x0,
                    page_h - y1,
                    max(x1 - x0, 0.0),
                    max(y1 - y0, 0.0),
                )
            )
        buffer = []
        line_bottom = None
        line_top = None

    for index in range(count):
        char = textpage.get_text_range(index, 1) or ""
        if char == "\r":
            continue
        if char == "\n":
            flush()
            continue
        raw_left, raw_bottom, raw_right, raw_top = textpage.get_charbox(index)
        if float(raw_top) < float(raw_bottom):
            continue
        left, bottom, right, top = upright_char_box(
            float(raw_left),
            float(raw_bottom),
            float(raw_right),
            float(raw_top),
            rotation=rotation,
            media_x0=media_x0,
            media_y0=media_y0,
            media_x1=media_x1,
            media_y1=media_y1,
        )
        bottom_f = float(bottom)
        top_f = float(top)
        if (
            line_bottom is not None
            and line_top is not None
            and not _char_continues_line(bottom_f, top_f, line_bottom, line_top)
        ):
            flush()
        buffer.append((char, float(left), bottom_f, float(right), top_f))
        if line_bottom is None or line_top is None:
            line_bottom = bottom_f
            line_top = top_f
        else:
            line_bottom, line_top = _extend_line_band(line_bottom, line_top, bottom_f, top_f)
    flush()
    return lines


class RasterDrawingAnalyzer:
    """Infrastructure adapter implementing ``RasterDrawingAnalyzer`` port."""

    def __init__(
        self,
        ocr_engine_factory: Callable[[], Any] | None = None,
        text_score: float = 0.5,
    ) -> None:
        self._ocr_engine_factory = ocr_engine_factory
        self._ocr_engine: Any | None = None
        self._text_score = text_score

    def analyze_image(
        self,
        image_path: Path,
        sheet_id: str | None = None,
    ) -> list[DrawingAnnotation]:
        if not image_path.exists():
            raise FileNotFoundError(f"Drawing image not found: {image_path}")

        resolved_sheet_id = sheet_id or image_path.stem.upper()
        if image_path.suffix.lower() == ".pdf":
            return self._analyze_pdf(image_path, resolved_sheet_id)
        return self._analyze_raster(image_path, resolved_sheet_id)

    def _analyze_pdf(
        self,
        pdf_path: Path,
        sheet_id: str,
    ) -> list[DrawingAnnotation]:
        try:
            payloads = run_pdfminer_extract_isolated(
                pdf_path,
                sheet_id,
                timeout_s=_PDF_OPEN_TIMEOUT_S,
            )
        except TimeoutError:
            raise TimeoutError(f"PDF analysis timed out after {_PDF_OPEN_TIMEOUT_S:.0f}s") from None
        annotations = [self._annotation_from_payload(item) for item in payloads]
        return self._deduplicate_annotations(annotations)

    def extract_pdf_in_process(
        self,
        pdf_path: Path,
        sheet_id: str,
        *,
        max_pages: int | None = None,
    ) -> list[DrawingAnnotation]:
        """Parse PDF text in the calling process. Used only by the isolate worker.

        PDFium reads the text layer. pdfminer remains the fallback when PDFium
        cannot open the file. The parent process still does not parse the PDF.
        """

        try:
            return self._extract_pdf_pdfium(pdf_path, sheet_id, max_pages=max_pages)
        except RuntimeError:
            raise
        except Exception:
            return self._extract_pdf_pdfminer(pdf_path, sheet_id, max_pages=max_pages)

    def _extract_pdf_pdfium(
        self,
        pdf_path: Path,
        sheet_id: str,
        *,
        max_pages: int | None,
    ) -> list[DrawingAnnotation]:
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(str(pdf_path))
        try:
            page_total = len(document)
            if max_pages is not None and page_total > max_pages:
                raise RuntimeError("PDF drawing rejected: too many pages")
            extracted: list[DrawingAnnotation] = []
            for index in range(page_total):
                page = document[index]
                try:
                    rotation, media_box, page_w, page_h = viewed_pdfium_page(page)
                    textpage = page.get_textpage()
                    try:
                        page_lines: list[PlacedLine] = []
                        for text, x, y, width, height in _pdfium_text_lines(
                            textpage,
                            rotation=rotation,
                            media_box=media_box,
                        ):
                            region = _TextRegion(
                                text=text,
                                page_number=index + 1,
                                x=x,
                                y=y,
                                width=width,
                                height=height,
                            )
                            extracted.extend(
                                self._extract_annotations_from_region(region, sheet_id)
                            )
                            page_lines.append(
                                PlacedLine(text=text, x=x, y=y, width=width, height=height)
                            )
                        extracted.extend(
                            self._stamp_annotations(
                                page_lines,
                                sheet_id=sheet_id,
                                page_number=index + 1,
                                page_width=float(page_w),
                                page_height=float(page_h),
                            )
                        )
                    finally:
                        textpage.close()
                finally:
                    page.close()
        finally:
            document.close()
        return self._deduplicate_annotations(extracted)

    def _extract_pdf_pdfminer(
        self,
        pdf_path: Path,
        sheet_id: str,
        *,
        max_pages: int | None,
    ) -> list[DrawingAnnotation]:
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTPage
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "PDF drawing analysis requires pdfminer.six (core PDF backend)."
            ) from exc

        extracted: list[DrawingAnnotation] = []
        for page_number, page in enumerate(extract_pages(str(pdf_path)), start=1):
            if max_pages is not None and page_number > max_pages:
                raise RuntimeError("PDF drawing rejected: too many pages")
            if not isinstance(page, LTPage):
                continue
            page_h = float(page.bbox[3] - page.bbox[1])
            page_w = float(page.bbox[2] - page.bbox[0])
            extracted.extend(
                self._annotations_from_pdfminer_page(
                    page,
                    sheet_id=sheet_id,
                    page_number=page_number,
                    page_h=page_h,
                    page_w=page_w,
                )
            )
        return extracted

    def _annotation_from_payload(self, payload: dict[str, Any]) -> DrawingAnnotation:
        zone_payload = payload.get("problem_zone")
        zone = None
        if isinstance(zone_payload, dict):
            zone = ProblemZone(
                sheet_id=zone_payload.get("sheet_id"),
                page_number=zone_payload.get("page_number"),
                x=zone_payload.get("x"),
                y=zone_payload.get("y"),
                width=zone_payload.get("width"),
                height=zone_payload.get("height"),
            )
        return DrawingAnnotation(
            annotation_id=str(payload["annotation_id"]),
            sheet_id=str(payload["sheet_id"]),
            target_ref=str(payload["target_ref"]),
            measure_name=str(payload["measure_name"]),
            observed_value=str(payload["observed_value"]),
            unit=payload.get("unit"),
            problem_zone=zone,
            source=str(payload.get("source") or "raster-drawing-analyzer"),
        )

    def _annotations_from_pdfminer_page(
        self,
        page: object,
        *,
        sheet_id: str,
        page_number: int,
        page_h: float,
        page_w: float = 0.0,
    ) -> list[DrawingAnnotation]:
        from pdfminer.layout import LTTextContainer

        extracted: list[DrawingAnnotation] = []
        page_lines: list[PlacedLine] = []

        def _walk(obj: object) -> None:
            if isinstance(obj, LTTextContainer):
                text = (obj.get_text() or "").strip()
                if text:
                    x0, y0, x1, y1 = obj.bbox
                    # pdfminer y origin is bottom-left; convert to top-left
                    # page-point space to match historical PyMuPDF annotations.
                    top = page_h - float(y1)
                    region = _TextRegion(
                        text=text,
                        page_number=page_number,
                        x=float(x0),
                        y=top,
                        width=max(float(x1) - float(x0), 0.0),
                        height=max(float(y1) - float(y0), 0.0),
                    )
                    extracted.extend(self._extract_annotations_from_region(region, sheet_id))
                    page_lines.append(
                        PlacedLine(
                            text=text,
                            x=float(x0),
                            y=top,
                            width=max(float(x1) - float(x0), 0.0),
                            height=max(float(y1) - float(y0), 0.0),
                        )
                    )
                return
            if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
                try:
                    for child in obj:
                        _walk(child)
                except TypeError:
                    return

        _walk(page)
        extracted.extend(
            self._stamp_annotations(
                page_lines,
                sheet_id=sheet_id,
                page_number=page_number,
                page_width=page_w,
                page_height=page_h,
            )
        )
        return extracted

    def _analyze_raster(
        self,
        image_path: Path,
        sheet_id: str,
    ) -> list[DrawingAnnotation]:
        engine = self._get_ocr_engine()
        # RapidOCR accepts filesystem paths; keep Path for callers but coerce for engines.
        ocr_result = engine(str(image_path))

        # RapidOCR returns numpy ndarrays for boxes; `x or []` is ambiguous on arrays.
        boxes = self._ocr_sequence(getattr(ocr_result, "boxes", None), default=())
        texts = self._ocr_sequence(getattr(ocr_result, "txts", None), default=())
        scores = self._ocr_sequence(getattr(ocr_result, "scores", None), default=())
        annotations: list[DrawingAnnotation] = []

        for index, (box, text) in enumerate(zip(boxes, texts, strict=False)):
            score = float(scores[index]) if index < len(scores) else 1.0
            if score < self._text_score:
                continue
            normalized_text = str(text).strip()
            if not normalized_text:
                continue
            x, y, width, height = self._quad_to_bbox(box)
            region = _TextRegion(
                text=normalized_text,
                page_number=1,
                x=x,
                y=y,
                width=width,
                height=height,
            )
            annotations.extend(
                self._extract_annotations_from_region(
                    region,
                    sheet_id,
                    source="raster-drawing-analyzer-ocr",
                )
            )

        return self._deduplicate_annotations(annotations)

    @staticmethod
    def _ocr_sequence(value: Any, *, default: Any) -> Any:
        """Normalize OCR sequence fields without truth-testing numpy arrays."""
        if value is None:
            return default
        size = getattr(value, "size", None)
        if isinstance(size, int):
            return value if size > 0 else default
        return value

    def _get_ocr_engine(self) -> Any:
        if self._ocr_engine is not None:
            return self._ocr_engine
        if self._ocr_engine_factory is not None:
            self._ocr_engine = self._ocr_engine_factory()
            return self._ocr_engine
        try:
            from rapidocr import RapidOCR
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Raster drawing OCR requires rapidocr and onnxruntime. Install the 'raster' extra."
            ) from exc
        self._ocr_engine = RapidOCR()
        return self._ocr_engine

    def _stamp_annotations(
        self,
        lines: list[PlacedLine],
        *,
        sheet_id: str,
        page_number: int,
        page_width: float = 0.0,
        page_height: float = 0.0,
    ) -> list[DrawingAnnotation]:
        """Read a caption that sits above its cell inside the title block.

        Not a rule measurement. A citation of a standard is not a cipher.
        """

        visible = lines
        if page_width > 0.0 and page_height > 0.0:
            visible = [
                line
                for line in lines
                if line_center_in_title_block(line, page_width=page_width, page_height=page_height)
            ]
        annotations: list[DrawingAnnotation] = []
        for pair in pair_captions_above_values(visible):
            if pair.code == "cipher" and value_is_standard_citation(pair.value):
                continue
            target_ref = f"STAMP-{pair.code.upper()}"
            annotations.append(
                DrawingAnnotation(
                    annotation_id=drawing_annotation_id(
                        sheet_id=sheet_id,
                        page_number=page_number,
                        target_ref=target_ref,
                        measure_name=pair.code,
                        observed_value=pair.value,
                        unit=None,
                        x=pair.x,
                        y=pair.y,
                        width=pair.width,
                        height=pair.height,
                    ),
                    sheet_id=sheet_id,
                    target_ref=target_ref,
                    measure_name=pair.code,
                    observed_value=pair.value,
                    unit=None,
                    problem_zone=ProblemZone(
                        sheet_id=sheet_id,
                        page_number=page_number,
                        x=canonical_coord(pair.x),
                        y=canonical_coord(pair.y),
                        width=canonical_coord(pair.width),
                        height=canonical_coord(pair.height),
                    ),
                    source=STAMP_CAPTION_SOURCE,
                )
            )
        return annotations

    def _extract_annotations_from_region(
        self,
        region: _TextRegion,
        sheet_id: str,
        *,
        source: str = "raster-drawing-analyzer",
    ) -> list[DrawingAnnotation]:
        annotations: list[DrawingAnnotation] = []
        for line in self._candidate_lines(region.text):
            structured = self._parse_pipe_line(line, sheet_id, region, source=source)
            if structured is not None:
                annotations.append(structured)
                continue
            regex_match = self._parse_regex_line(line, sheet_id, region, source=source)
            if regex_match is not None:
                annotations.append(regex_match)
        return annotations

    def _candidate_lines(self, raw_text: str) -> list[str]:
        return [line.strip() for line in raw_text.splitlines() if line.strip()]

    def _parse_pipe_line(
        self,
        line: str,
        sheet_id: str,
        region: _TextRegion,
        *,
        source: str = "raster-drawing-analyzer",
    ) -> DrawingAnnotation | None:
        if "|" not in line:
            return None
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 6:
            return None
        annotation_id, parsed_sheet_id, target_ref, measure_name, observed_value, unit = parts[:6]
        resolved_annotation_id = annotation_id or self._make_annotation_id(
            region,
            sheet_id=parsed_sheet_id or sheet_id,
            target_ref=target_ref,
            measure_name=measure_name,
            observed_value=observed_value,
            unit=unit or None,
        )
        return DrawingAnnotation(
            annotation_id=resolved_annotation_id,
            sheet_id=parsed_sheet_id or sheet_id,
            target_ref=target_ref,
            measure_name=self._normalize_measure_name(measure_name),
            observed_value=observed_value,
            unit=unit or None,
            problem_zone=self._make_problem_zone(sheet_id, region),
            source=source,
        )

    def _parse_regex_line(
        self,
        line: str,
        sheet_id: str,
        region: _TextRegion,
        *,
        source: str = "raster-drawing-analyzer",
    ) -> DrawingAnnotation | None:
        if is_paired_dimension(line):
            return None
        for pattern in _TEXT_PATTERNS:
            match = pattern.search(line)
            if match is None:
                continue
            measure_name = self._normalize_measure_name(match.group("measure"))
            target_ref = match.group("target").upper()
            observed_value = match.group("value").replace(",", ".")
            unit = match.group("unit")
            return DrawingAnnotation(
                annotation_id=self._make_annotation_id(
                    region,
                    sheet_id=sheet_id,
                    target_ref=target_ref,
                    measure_name=measure_name,
                    observed_value=observed_value,
                    unit=unit,
                ),
                sheet_id=sheet_id,
                target_ref=target_ref,
                measure_name=measure_name,
                observed_value=observed_value,
                unit=unit,
                problem_zone=self._make_problem_zone(sheet_id, region),
                source=source,
            )
        return None

    def _normalize_measure_name(self, value: str) -> str:
        return _MEASURE_ALIASES.get(value.strip().lower(), value.strip().lower())

    def _make_annotation_id(
        self,
        region: _TextRegion,
        *,
        sheet_id: str,
        target_ref: str,
        measure_name: str,
        observed_value: str,
        unit: str | None,
    ) -> str:
        return drawing_annotation_id(
            sheet_id=sheet_id,
            page_number=region.page_number,
            target_ref=target_ref,
            measure_name=measure_name,
            observed_value=observed_value,
            unit=unit,
            x=region.x,
            y=region.y,
            width=region.width,
            height=region.height,
        )

    def _make_problem_zone(self, sheet_id: str, region: _TextRegion) -> ProblemZone:
        return ProblemZone(
            sheet_id=sheet_id,
            page_number=region.page_number,
            x=canonical_coord(region.x),
            y=canonical_coord(region.y),
            width=canonical_coord(region.width),
            height=canonical_coord(region.height),
        )

    def _quad_to_bbox(self, quad: Any) -> tuple[float, float, float, float]:
        points = [tuple(point) for point in quad]
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        x = min(xs)
        y = min(ys)
        width = max(xs) - x
        height = max(ys) - y
        return x, y, width, height

    def _deduplicate_annotations(
        self,
        annotations: list[DrawingAnnotation],
    ) -> list[DrawingAnnotation]:
        deduplicated: dict[str, DrawingAnnotation] = {}
        for annotation in annotations:
            zone = annotation.problem_zone
            key = drawing_annotation_digest(
                sheet_id=annotation.sheet_id,
                page_number=int(zone.page_number or 0) if zone is not None else 0,
                target_ref=annotation.target_ref,
                measure_name=annotation.measure_name,
                observed_value=annotation.observed_value,
                unit=annotation.unit,
                x=float(zone.x or 0.0) if zone is not None else 0.0,
                y=float(zone.y or 0.0) if zone is not None else 0.0,
                width=float(zone.width or 0.0) if zone is not None else 0.0,
                height=float(zone.height or 0.0) if zone is not None else 0.0,
            )
            deduplicated[key] = annotation
        return list(deduplicated.values())
