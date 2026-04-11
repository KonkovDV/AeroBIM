from __future__ import annotations

import json
from pathlib import Path

from aerobim.domain.models import DrawingAnnotation, DrawingSource, ProblemZone


class StructuredDrawingAnalyzer:
    def analyze(self, source: DrawingSource) -> list[DrawingAnnotation]:
        raw_text = source.text.strip()
        if not raw_text and source.path is not None:
            raw_text = self._load_text(source.path)

        if source.path is not None and source.path.suffix.lower() == ".json":
            return self._parse_json(raw_text, source)

        return self._parse_text(raw_text, source)

    def _parse_text(self, raw_text: str, source: DrawingSource) -> list[DrawingAnnotation]:
        annotations: list[DrawingAnnotation] = []
        for line_number, line in enumerate(raw_text.splitlines(), start=1):
            normalized = line.strip()
            if not normalized or normalized.startswith("#"):
                continue

            parts = [part.strip() for part in normalized.split("|")]
            if len(parts) < 6:
                raise ValueError(
                    f"Malformed drawing annotation at line {line_number}: expected at least 6 pipe-separated columns"
                )

            annotation_id, sheet_id, target_ref, measure_name, observed_value, unit, *zone_parts = parts
            problem_zone = self._build_problem_zone(sheet_id or source.sheet_id, zone_parts)
            annotations.append(
                DrawingAnnotation(
                    annotation_id=annotation_id,
                    sheet_id=sheet_id or source.sheet_id or "unknown-sheet",
                    target_ref=target_ref,
                    measure_name=measure_name,
                    observed_value=observed_value,
                    unit=unit or None,
                    problem_zone=problem_zone,
                    source=str(source.path) if source.path else "drawing-text",
                )
            )

        return annotations

    def _parse_json(self, raw_text: str, source: DrawingSource) -> list[DrawingAnnotation]:
        payload = json.loads(raw_text)
        if not isinstance(payload, list):
            raise ValueError("Drawing annotation JSON must be a list of annotation objects")

        annotations: list[DrawingAnnotation] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("Each drawing annotation must be a JSON object")

            problem_zone = self._build_problem_zone(
                item.get("sheet_id") or source.sheet_id,
                [
                    str(item.get("page_number", "")),
                    str(item.get("x", "")),
                    str(item.get("y", "")),
                    str(item.get("width", "")),
                    str(item.get("height", "")),
                ],
            )
            annotations.append(
                DrawingAnnotation(
                    annotation_id=str(item["annotation_id"]),
                    sheet_id=str(item.get("sheet_id") or source.sheet_id or "unknown-sheet"),
                    target_ref=str(item["target_ref"]),
                    measure_name=str(item["measure_name"]),
                    observed_value=str(item["observed_value"]),
                    unit=str(item["unit"]) if item.get("unit") else None,
                    problem_zone=problem_zone,
                    source=str(source.path) if source.path else "drawing-json",
                )
            )

        return annotations

    def _build_problem_zone(self, sheet_id: str | None, zone_parts: list[str]) -> ProblemZone | None:
        if len(zone_parts) < 5:
            return None

        page_number = self._to_int(zone_parts[0])
        x = self._to_float(zone_parts[1])
        y = self._to_float(zone_parts[2])
        width = self._to_float(zone_parts[3])
        height = self._to_float(zone_parts[4])
        if page_number is None and x is None and y is None and width is None and height is None:
            return None

        return ProblemZone(
            sheet_id=sheet_id,
            page_number=page_number,
            x=x,
            y=y,
            width=width,
            height=height,
        )

    def _load_text(self, source_path: Path) -> str:
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        return source_path.read_text(encoding="utf-8")

    def _to_float(self, value: str) -> float | None:
        if not value:
            return None
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None

    def _to_int(self, value: str) -> int | None:
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None