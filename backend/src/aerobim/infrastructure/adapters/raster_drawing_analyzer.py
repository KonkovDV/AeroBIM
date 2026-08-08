"""Deterministic drawing analyzer baseline for raster and PDF inputs.

Implements the ``RasterDrawingAnalyzer`` port using OCR and layout heuristics only
(non-deterministic adapters are outside the pilot sign-off path).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aerobim.domain.models import DrawingAnnotation, ProblemZone

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
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTPage
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "PDF drawing analysis requires pdfminer.six (core PDF backend)."
            ) from exc

        annotations: list[DrawingAnnotation] = []

        def _extract() -> list[DrawingAnnotation]:
            extracted: list[DrawingAnnotation] = []
            for page_number, page in enumerate(extract_pages(str(pdf_path)), start=1):
                if not isinstance(page, LTPage):
                    continue
                page_h = float(page.bbox[3] - page.bbox[1])
                extracted.extend(
                    self._annotations_from_pdfminer_page(
                        page,
                        sheet_id=sheet_id,
                        pdf_path=pdf_path,
                        page_number=page_number,
                        page_h=page_h,
                    )
                )
            return extracted

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_extract)
            try:
                annotations = future.result(timeout=_PDF_OPEN_TIMEOUT_S)
            except FuturesTimeout as exc:
                raise TimeoutError(
                    f"PDF analysis timed out after {_PDF_OPEN_TIMEOUT_S:.0f}s: {pdf_path}"
                ) from exc
        return self._deduplicate_annotations(annotations)

    def _annotations_from_pdfminer_page(
        self,
        page: object,
        *,
        sheet_id: str,
        pdf_path: Path,
        page_number: int,
        page_h: float,
    ) -> list[DrawingAnnotation]:
        from pdfminer.layout import LTTextContainer

        extracted: list[DrawingAnnotation] = []

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
                    extracted.extend(
                        self._extract_annotations_from_region(region, sheet_id, pdf_path)
                    )
                return
            if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
                try:
                    for child in obj:  # type: ignore[union-attr]
                        _walk(child)
                except TypeError:
                    return

        _walk(page)
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
            annotations.extend(self._extract_annotations_from_region(region, sheet_id, image_path))

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

    def _extract_annotations_from_region(
        self,
        region: _TextRegion,
        sheet_id: str,
        source_path: Path,
    ) -> list[DrawingAnnotation]:
        annotations: list[DrawingAnnotation] = []
        for line in self._candidate_lines(region.text):
            structured = self._parse_pipe_line(line, sheet_id, region, source_path)
            if structured is not None:
                annotations.append(structured)
                continue
            regex_match = self._parse_regex_line(line, sheet_id, region, source_path)
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
        source_path: Path,
    ) -> DrawingAnnotation | None:
        if "|" not in line:
            return None
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 6:
            return None
        annotation_id, parsed_sheet_id, target_ref, measure_name, observed_value, unit = parts[:6]
        resolved_annotation_id = annotation_id or self._make_annotation_id(
            region,
            target_ref,
            measure_name,
        )
        return DrawingAnnotation(
            annotation_id=resolved_annotation_id,
            sheet_id=parsed_sheet_id or sheet_id,
            target_ref=target_ref,
            measure_name=self._normalize_measure_name(measure_name),
            observed_value=observed_value,
            unit=unit or None,
            problem_zone=self._make_problem_zone(sheet_id, region),
            source="raster-drawing-analyzer",
        )

    def _parse_regex_line(
        self,
        line: str,
        sheet_id: str,
        region: _TextRegion,
        source_path: Path,
    ) -> DrawingAnnotation | None:
        for pattern in _TEXT_PATTERNS:
            match = pattern.search(line)
            if match is None:
                continue
            measure_name = self._normalize_measure_name(match.group("measure"))
            target_ref = match.group("target").upper()
            observed_value = match.group("value").replace(",", ".")
            unit = match.group("unit")
            return DrawingAnnotation(
                annotation_id=self._make_annotation_id(region, target_ref, measure_name),
                sheet_id=sheet_id,
                target_ref=target_ref,
                measure_name=measure_name,
                observed_value=observed_value,
                unit=unit,
                problem_zone=self._make_problem_zone(sheet_id, region),
                source="raster-drawing-analyzer",
            )
        return None

    def _normalize_measure_name(self, value: str) -> str:
        return _MEASURE_ALIASES.get(value.strip().lower(), value.strip().lower())

    def _make_annotation_id(
        self,
        region: _TextRegion,
        target_ref: str,
        measure_name: str,
    ) -> str:
        stable_hash = abs(hash((region.page_number, region.text, target_ref, measure_name)))
        return f"VIS-{region.page_number:03d}-{stable_hash % 10_000_000:07d}"

    def _make_problem_zone(self, sheet_id: str, region: _TextRegion) -> ProblemZone:
        return ProblemZone(
            sheet_id=sheet_id,
            page_number=region.page_number,
            x=region.x,
            y=region.y,
            width=region.width,
            height=region.height,
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
        deduplicated: dict[tuple[str, str, str, str | None, int | None], DrawingAnnotation] = {}
        for annotation in annotations:
            key = (
                annotation.target_ref,
                annotation.measure_name,
                annotation.observed_value,
                annotation.unit,
                annotation.problem_zone.page_number if annotation.problem_zone else None,
            )
            deduplicated[key] = annotation
        return list(deduplicated.values())
