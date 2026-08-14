"""Advisory VLM drawing pipeline — candidate regions with OCR degrade.

Implements ``MultimodalDrawingPipeline`` by composing the SSRF-guarded
``VlmAdvisoryClient`` with domain-pure ``vlm_grounding``. Mirrors the honesty
posture of ``OcrFallbackMultimodalDrawingPipeline``:

- the result is **always** ``degraded=True`` — VLM output is candidate regions,
  never verified CV; ``cv_human_level`` stays ``MISSING`` (TR-7/7a, honesty gate);
- any not-ready / wrong-mode / failure / schema-deviation path **fails closed**
  to the OCR fallback (or an explicit unavailable result), never a silent VLM OK;
- the deterministic engine and the expert own the verdict (ADR-001 / TR-2/27/31).

Not wired into ``bootstrap_container`` by default: constructed only when
``settings.vlm_advisory_ready()`` and on open-data tiers (see scenario matrix).
"""

from __future__ import annotations

from typing import Literal, Protocol

from aerobim.domain.consistency import MultimodalDrawingResult
from aerobim.domain.models import DrawingSource
from aerobim.domain.vlm_grounding import ground_vlm_drawing_response
from aerobim.infrastructure.adapters.vlm_advisory_client import (
    VlmAdvisoryError,
    VlmReadResult,
)

_VLM_IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
_DEFAULT_MAX_IMAGE_BYTES = 32 * 1024 * 1024
_DEFAULT_PROMPT = (
    "Read engineering-drawing regions (title block fields, marks, dimensions). "
    'Return JSON {"coordinate_system":"page-pixel","regions":[{"bbox":[x1,y1,x2,y2],'
    '"text":"...","field":"...","confidence":0.0-1.0}]}. Do not decide compliance.'
)


class _DrawingReader(Protocol):
    def read_drawing(
        self, image_bytes: bytes, *, media_type: str, sheet_id: str, prompt: str
    ) -> VlmReadResult: ...


class _FallbackPipeline(Protocol):
    def analyze(
        self, source: DrawingSource, *, mode: Literal["auto", "ocr_only", "detector_vlm"]
    ) -> MultimodalDrawingResult: ...


class VlmDrawingPipeline:
    """Advisory VLM reads (provider-agnostic: Yandex/Qwen, vLLM, or Kimi profile)."""

    def __init__(
        self,
        client: _DrawingReader | None,
        *,
        ready: bool,
        model_id: str = "kimi-k3",
        fallback: _FallbackPipeline | None = None,
        min_confidence: float = 0.60,
        prompt: str = _DEFAULT_PROMPT,
        max_image_bytes: int = _DEFAULT_MAX_IMAGE_BYTES,
    ) -> None:
        self._client = client
        self._ready = ready
        self._model_id = model_id
        self._fallback = fallback
        self._min_confidence = min_confidence
        self._prompt = prompt
        self._max_image_bytes = max_image_bytes

    def analyze(
        self,
        source: DrawingSource,
        *,
        mode: Literal["auto", "ocr_only", "detector_vlm"] = "auto",
    ) -> MultimodalDrawingResult:
        # Fail-closed gate: not configured/ready, explicit OCR-only, or no path →
        # never invoke the VLM; degrade to OCR (or unavailable).
        if not self._ready or self._client is None:
            return self._degrade(source, "VLM advisory not ready (fail-closed)")
        if mode == "ocr_only" or source.path is None:
            return self._degrade(source, "VLM not invoked (ocr_only or missing path)")

        media_type = _VLM_IMAGE_MEDIA_TYPES.get(source.path.suffix.lower())
        if media_type is None:
            return self._degrade(
                source, f"Unsupported VLM image type {source.path.suffix!r}; needs raster"
            )

        sheet_id = source.sheet_id or source.path.stem
        try:
            # Size-gate on stat() BEFORE reading, so an oversized file never gets
            # fully buffered into memory (OOM guard).
            if source.path.stat().st_size > self._max_image_bytes:
                return self._degrade(source, "IMAGE_TOO_LARGE: drawing image exceeds VLM size cap")
            image_bytes = source.path.read_bytes()
            read = self._client.read_drawing(
                image_bytes, media_type=media_type, sheet_id=sheet_id, prompt=self._prompt
            )
        except VlmAdvisoryError as exc:
            # §2.4: classified failure (TRUNCATED/EMPTY_CONTENT/SCHEMA_DEVIATION/...)
            # must be surfaced faithfully, never as "found nothing".
            return self._degrade(source, f"VLM read failed (fail-closed, {exc.reason_code}): {exc}")
        except OSError as exc:
            return self._degrade(source, f"VLM read failed (fail-closed, IO): {exc}")
        except Exception as exc:  # noqa: BLE001 — SSRF/transport errors must fail closed, not OK
            return self._degrade(source, f"VLM transport error (fail-closed): {exc}")

        grounded = ground_vlm_drawing_response(
            read.content,
            sheet_id=sheet_id,
            model_id=self._model_id,
            min_confidence=self._min_confidence,
        )
        if not grounded.parse_ok:
            return self._degrade(source, f"VLM schema deviation (fail-closed): {grounded.reason}")

        # Candidate regions only — no fabricated annotations; always degraded.
        return MultimodalDrawingResult(
            annotations=(),
            regions=grounded.regions,
            pipeline_mode_used="vlm_candidate",
            degraded=True,
            reason=(
                f"Advisory VLM candidate regions ({len(grounded.regions)}; "
                f"{grounded.hitl_count} low-confidence → HITL); determinism_basis="
                f"{read.determinism_basis}; cv_human_level remains MISSING; verdict "
                "stays with the deterministic engine and the expert"
            ),
        )

    def _degrade(self, source: DrawingSource, reason: str) -> MultimodalDrawingResult:
        if self._fallback is not None:
            return self._fallback.analyze(source, mode="ocr_only")
        return MultimodalDrawingResult(
            annotations=(),
            regions=(),
            pipeline_mode_used="unavailable",
            degraded=True,
            reason=reason,
        )


# Deprecated alias (historical Kimi-first naming).
KimiVlmDrawingPipeline = VlmDrawingPipeline

__all__ = ["KimiVlmDrawingPipeline", "VlmDrawingPipeline"]
