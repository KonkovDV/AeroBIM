# pyright: reportMissingImports=false

"""CadModelIngestor adapters — ezdxf for DXF; DWG fail-closed without ODA."""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.cad_ingest import CadIngestResult
from aerobim.domain.models import DrawingAnnotation, ProblemZone

_DXF_SUFFIXES = {".dxf"}
_DWG_SUFFIXES = {".dwg"}


class EzdxfCadModelIngestor:
    """Parse DXF TEXT/MTEXT into DrawingAnnotation records via optional ``ezdxf``.

    Native DWG requires a licensed ODA adapter (not shipped here) — ingest returns
    ``supported=False`` with an explicit reason so honesty stays non-OK.
    """

    def ingest(self, path: Path, *, sheet_id: str | None = None) -> CadIngestResult:
        if not path.exists():
            raise FileNotFoundError(path)

        suffix = path.suffix.lower()
        resolved_sheet = sheet_id or path.stem

        if suffix in _DWG_SUFFIXES:
            return CadIngestResult(
                annotations=(),
                format_resolved="dwg",
                entity_count=0,
                degraded=True,
                supported=False,
                reason=(
                    "Native DWG requires ODA/Teigha licensed adapter "
                    "(not configured); convert to DXF or enable ODA extra"
                ),
            )

        if suffix not in _DXF_SUFFIXES:
            return CadIngestResult(
                annotations=(),
                format_resolved=suffix.lstrip(".") or "unknown",
                entity_count=0,
                degraded=True,
                supported=False,
                reason=f"Unsupported CAD suffix {suffix!r}; expected .dxf or .dwg",
            )

        try:
            import ezdxf
        except ModuleNotFoundError:
            return CadIngestResult(
                annotations=(),
                format_resolved="dxf",
                entity_count=0,
                degraded=True,
                supported=False,
                reason="ezdxf optional extra not installed (pip install aerobim-backend[cad])",
            )

        try:
            document = ezdxf.readfile(str(path))
        except Exception as exc:  # noqa: BLE001 — surface parse failures honestly
            return CadIngestResult(
                annotations=(),
                format_resolved="dxf",
                entity_count=0,
                degraded=True,
                supported=False,
                reason=f"ezdxf failed to read DXF: {exc}",
            )

        modelspace = document.modelspace()
        annotations: list[DrawingAnnotation] = []
        entity_count = 0
        for index, entity in enumerate(modelspace):
            entity_count += 1
            dxftype = entity.dxftype()
            if dxftype not in {"TEXT", "MTEXT"}:
                continue
            text = ""
            if dxftype == "TEXT":
                text = str(getattr(entity.dxf, "text", "") or "").strip()
                insert = getattr(entity.dxf, "insert", None)
            else:
                text = str(entity.plain_text() if hasattr(entity, "plain_text") else "").strip()
                insert = getattr(entity.dxf, "insert", None)
            if not text:
                continue
            x = float(insert[0]) if insert is not None else None
            y = float(insert[1]) if insert is not None else None
            annotations.append(
                DrawingAnnotation(
                    annotation_id=f"dxf-{path.stem}-{index}",
                    sheet_id=resolved_sheet,
                    target_ref=text.split()[0] if text.split() else text[:64],
                    measure_name="cad-text",
                    observed_value=text,
                    unit=None,
                    problem_zone=ProblemZone(
                        sheet_id=resolved_sheet,
                        x=x,
                        y=y,
                    ),
                    source="cad-dxf",
                )
            )

        return CadIngestResult(
            annotations=tuple(annotations),
            format_resolved="dxf",
            entity_count=entity_count,
            degraded=False,
            supported=True,
            reason=None,
        )
