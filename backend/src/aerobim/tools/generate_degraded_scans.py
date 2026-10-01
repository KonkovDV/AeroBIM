"""Deterministic degraded-scan generator for the VLM robustness track (T4).

The VLM/OCR comparison protocol (docs/pilot/VLM_OCR_COMPARISON_PROTOCOL_
2026_08.md) requires degraded variants of fixture sheets: task T4 measures
metric drop under low resolution, rotation and sensor noise. This tool
produces those variants **deterministically** (fixed seed, pinned params)
with a provenance manifest binding every variant to the source sha256 —
the same derived-input honesty rule the DWG route uses.

Degradations (pure pymupdf, no new dependencies):

- ``lowres_<dpi>``  — page rendered at reduced DPI (scan resolution loss);
- ``rotate_<deg>``  — small skew via render matrix (misaligned scan);
- ``noise_<pct>``   — seeded salt-and-pepper on the rendered pixmap
  (sensor/compression artifacts); Phipson-style determinism: same seed →
  byte-identical PNG.

Claim boundary: degraded fixtures are synthetic robustness probes — they
never stand in for real customer scans, and T4 results remain fixture-only
(RT-001).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import pymupdf

_DEFAULT_DPI_VARIANTS = (150, 96, 72)
_DEFAULT_ANGLES = (1.0, 3.0)
_DEFAULT_NOISE_PERCENTS = (1.0, 5.0)
_BASE_DPI = 200  # protocol rasterization baseline (Enginuity practice)
_MAX_SOURCE_BYTES = 50 * 1024 * 1024


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _render_page(page: pymupdf.Page, *, dpi: int, rotate_degrees: float = 0.0) -> pymupdf.Pixmap:
    try:
        import pymupdf
    except ModuleNotFoundError as exc:  # optional AGPL extra
        raise RuntimeError(
            "Degraded-scan generation requires PyMuPDF. Install the optional 'pdf-agpl' extra."
        ) from exc

    matrix = pymupdf.Matrix(dpi / 72.0, dpi / 72.0)
    if rotate_degrees:
        matrix = matrix * pymupdf.Matrix(rotate_degrees)
    return page.get_pixmap(matrix=matrix, alpha=False)


def _apply_salt_pepper(pixmap: pymupdf.Pixmap, *, percent: float, seed: int) -> bytes:
    """Flip ``percent`` of pixels to black/white using a seeded RNG.

    Uses the version-stable ``set_pixel`` API (raw-buffer Pixmap
    constructors changed across pymupdf releases) — deterministic for a
    given (image, percent, seed) triple. Mutates the passed pixmap, so
    callers must hand in a fresh render per variant.
    """

    # pymupdf stubs sometimes type Pixmap.width/height as Callable; coerce via Any.
    width = int(cast(Any, pixmap.width))
    height = int(cast(Any, pixmap.height))
    pixel_count = width * height
    flips = int(pixel_count * percent / 100.0)
    rng = random.Random(seed)
    for _ in range(flips):
        pixel_index = rng.randrange(pixel_count)
        value = 0 if rng.random() < 0.5 else 255
        pixmap.set_pixel(pixel_index % width, pixel_index // width, (value, value, value))
    return cast(bytes, pixmap.tobytes("png"))


def generate_degraded_scans(
    source_path: Path,
    output_dir: Path,
    *,
    page_number: int = 0,
    dpi_variants: tuple[int, ...] = _DEFAULT_DPI_VARIANTS,
    angles: tuple[float, ...] = _DEFAULT_ANGLES,
    noise_percents: tuple[float, ...] = _DEFAULT_NOISE_PERCENTS,
    seed: int = 20260726,
) -> dict[str, Any]:
    """Render baseline + degraded PNG variants with a provenance manifest."""

    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if source_path.stat().st_size > _MAX_SOURCE_BYTES:
        raise ValueError(f"{source_path}: source exceeds {_MAX_SOURCE_BYTES} bytes")
    for dpi in dpi_variants:
        if not 24 <= dpi < _BASE_DPI:
            raise ValueError(f"lowres dpi must lie in [24, {_BASE_DPI}), got {dpi}")
    for angle in angles:
        if not 0.0 < abs(angle) <= 15.0:
            raise ValueError(f"rotation angle must lie in (0, 15] degrees, got {angle}")
    for percent in noise_percents:
        if not 0.0 < percent <= 20.0:
            raise ValueError(f"noise percent must lie in (0, 20], got {percent}")

    source_bytes = source_path.read_bytes()
    source_sha = _sha256_bytes(source_bytes)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import pymupdf
    except ModuleNotFoundError as exc:  # optional AGPL extra
        raise RuntimeError(
            "Degraded-scan generation requires PyMuPDF. Install the optional 'pdf-agpl' extra."
        ) from exc

    document = pymupdf.open(source_path)
    try:
        if not 0 <= page_number < document.page_count:
            raise ValueError(f"page_number {page_number} out of range 0..{document.page_count - 1}")
        page = document[page_number]

        variants: list[dict[str, Any]] = []

        def emit(name: str, payload: bytes, params: dict[str, Any]) -> None:
            file_path = output_dir / f"{name}.png"
            file_path.write_bytes(payload)
            variants.append(
                {
                    "variant": name,
                    "file": file_path.name,
                    "sha256": _sha256_bytes(payload),
                    "params": params,
                }
            )

        baseline = _render_page(page, dpi=_BASE_DPI).tobytes("png")
        emit("baseline_200dpi", baseline, {"dpi": _BASE_DPI})

        for dpi in dpi_variants:
            payload = _render_page(page, dpi=dpi).tobytes("png")
            emit(f"lowres_{dpi}dpi", payload, {"dpi": dpi})

        for angle in angles:
            payload = _render_page(page, dpi=_BASE_DPI, rotate_degrees=angle).tobytes("png")
            emit(f"rotate_{angle:g}deg", payload, {"dpi": _BASE_DPI, "rotate_degrees": angle})

        for percent in noise_percents:
            # Fresh render per variant: _apply_salt_pepper mutates in place.
            fresh = _render_page(page, dpi=_BASE_DPI)
            payload = _apply_salt_pepper(fresh, percent=percent, seed=seed)
            emit(
                f"noise_{percent:g}pct",
                payload,
                {"dpi": _BASE_DPI, "noise_percent": percent, "seed": seed},
            )
    finally:
        document.close()

    manifest: dict[str, Any] = {
        "artifact_type": "degraded_scan_set",
        "schema_version": "1.0.0",
        "source": {
            "path": str(source_path),
            "sha256": source_sha,
            "page_number": page_number,
        },
        "base_dpi": _BASE_DPI,
        "seed": seed,
        "variants": variants,
        "claim_boundary": (
            "synthetic degradation probes for VLM/OCR robustness (protocol "
            "T4); never a substitute for real customer scans; results are "
            "fixture-only (RT-001)"
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Source PDF sheet")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--page", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260726)
    args = parser.parse_args(argv)
    manifest = generate_degraded_scans(
        args.source.resolve(),
        args.output.resolve(),
        page_number=args.page,
        seed=args.seed,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
