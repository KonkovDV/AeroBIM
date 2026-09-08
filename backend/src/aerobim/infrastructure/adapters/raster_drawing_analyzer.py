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
from aerobim.infrastructure.adapters.drawing_annotation_identity import (
    canonical_coord,
    drawing_annotation_digest,
    drawing_annotation_id,
)
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
        """Parse PDF text in the calling process. Used only by the isolate worker."""

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
            extracted.extend(
                self._annotations_from_pdfminer_page(
                    page,
                    sheet_id=sheet_id,
                    page_number=page_number,
                    page_h=page_h,
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
                    extracted.extend(self._extract_annotations_from_region(region, sheet_id))
                return
            if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
                try:
                    for child in obj:
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
