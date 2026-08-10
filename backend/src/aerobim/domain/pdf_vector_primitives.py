"""Extract vector primitives from PDF (P2) — pdfminer lines/curves/text.

Claim: vector extraction baseline, not CAD object model and not symbol spotting.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

PrimitiveKind = Literal["line", "rect", "curve", "text"]


@dataclass(frozen=True)
class PdfVectorPrimitive:
    kind: PrimitiveKind
    page_number: int
    bbox: tuple[float, float, float, float]  # x0,y0,x1,y1 page points (bottom-left origin)
    points: tuple[tuple[float, float], ...] = ()
    text: str | None = None
    layer_hint: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PdfVectorExtraction:
    source_path: str
    page_count: int
    primitives: tuple[PdfVectorPrimitive, ...]
    method: str = "pdfminer_layout"
    claim: str = "vector extraction baseline, not CAD symbol spotting"

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "page_count": self.page_count,
            "method": self.method,
            "claim": self.claim,
            "primitive_counts": _counts(self.primitives),
            "primitives": [p.as_dict() for p in self.primitives[:500]],
            "truncated": len(self.primitives) > 500,
        }


def _counts(primitives: tuple[PdfVectorPrimitive, ...]) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in primitives:
        out[p.kind] = out.get(p.kind, 0) + 1
    return out


def extract_pdf_vector_primitives(
    pdf_path: Path, *, max_primitives: int = 2000
) -> PdfVectorExtraction:
    """Walk pdfminer layout for lines, rects, curves, and text boxes."""

    try:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import (
            LTCurve,
            LTLine,
            LTRect,
            LTTextContainer,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError("pdfminer.six required for PDF vector extraction") from exc

    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    collected: list[PdfVectorPrimitive] = []
    page_count = 0

    def _bbox(obj: object) -> tuple[float, float, float, float]:
        x0, y0, x1, y1 = obj.bbox  # type: ignore[attr-defined]
        return (float(x0), float(y0), float(x1), float(y1))

    def _walk(obj: object, page_number: int) -> None:
        if len(collected) >= max_primitives:
            return
        if isinstance(obj, LTLine):
            collected.append(
                PdfVectorPrimitive(
                    kind="line",
                    page_number=page_number,
                    bbox=_bbox(obj),
                    points=((float(obj.x0), float(obj.y0)), (float(obj.x1), float(obj.y1))),
                )
            )
            return
        if isinstance(obj, LTRect):
            collected.append(
                PdfVectorPrimitive(kind="rect", page_number=page_number, bbox=_bbox(obj))
            )
            return
        if isinstance(obj, LTCurve) and not isinstance(obj, LTLine):
            pts = tuple((float(p[0]), float(p[1])) for p in (getattr(obj, "pts", None) or ()))
            collected.append(
                PdfVectorPrimitive(
                    kind="curve",
                    page_number=page_number,
                    bbox=_bbox(obj),
                    points=pts,
                )
            )
            return
        if isinstance(obj, LTTextContainer):
            text = (obj.get_text() or "").strip()
            if text:
                collected.append(
                    PdfVectorPrimitive(
                        kind="text",
                        page_number=page_number,
                        bbox=_bbox(obj),
                        text=text[:200],
                    )
                )
            return
        if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
            try:
                for child in obj:
                    _walk(child, page_number)
            except TypeError:
                return

    for page_number, page in enumerate(extract_pages(str(pdf_path)), start=1):
        page_count = page_number
        _walk(page, page_number)
        if len(collected) >= max_primitives:
            break

    return PdfVectorExtraction(
        source_path=str(pdf_path),
        page_count=page_count,
        primitives=tuple(collected),
    )


@dataclass(frozen=True)
class SymbolCandidate:
    """P2 research contour — candidate only, never a verified door/window count."""

    candidate_id: str
    kind: str
    page_number: int
    bbox: tuple[float, float, float, float]
    score: float
    basis: str
    claim: str = "symbol candidate heuristic; NOT_CHECKED as verified count"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def propose_symbol_candidates_from_vectors(
    extraction: PdfVectorExtraction,
    *,
    max_candidates: int = 20,
) -> list[SymbolCandidate]:
    """Heuristic: small closed-ish rects near text marks → door/window *candidates*.

    Explicitly NOT a verified count. Requires labeled corpus before any claim.
    """

    texts = [p for p in extraction.primitives if p.kind == "text" and p.text]
    rects = [p for p in extraction.primitives if p.kind == "rect"]
    candidates: list[SymbolCandidate] = []
    for i, rect in enumerate(rects):
        if len(candidates) >= max_candidates:
            break
        x0, y0, x1, y1 = rect.bbox
        w, h = abs(x1 - x0), abs(y1 - y0)
        if w < 2 or h < 2 or w > 80 or h > 80:
            continue
        aspect = max(w, h) / max(min(w, h), 1e-6)
        if aspect > 4.0:
            continue
        nearby_text = ""
        for t in texts:
            if t.page_number != rect.page_number:
                continue
            tx0, ty0, tx1, ty1 = t.bbox
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if tx0 - 40 <= cx <= tx1 + 40 and ty0 - 40 <= cy <= ty1 + 40:
                nearby_text = (t.text or "").upper()
                break
        kind = "unknown_symbol"
        if any(k in nearby_text for k in ("DOOR", "ДВ")):
            kind = "door_candidate"
        elif any(k in nearby_text for k in ("WINDOW", "OKNO", "OK")):
            kind = "window_candidate"
        candidates.append(
            SymbolCandidate(
                candidate_id=f"SYM-{rect.page_number}-{i}",
                kind=kind,
                page_number=rect.page_number,
                bbox=rect.bbox,
                score=0.25 if kind == "unknown_symbol" else 0.4,
                basis="rect_aspect+nearby_text_heuristic",
            )
        )
    return candidates


__all__ = [
    "PdfVectorExtraction",
    "PdfVectorPrimitive",
    "SymbolCandidate",
    "extract_pdf_vector_primitives",
    "propose_symbol_candidates_from_vectors",
]
