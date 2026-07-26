"""Synthetic VLM fixture corpus (T1-T3) with ground truth by construction.

The VLM/OCR comparison protocol needs labeled sheets for T1 (title block),
T2 (marks/axes) and T3 (spec tables). Expert labeling of real sheets is
customer-blocked — but a *synthetic* corpus inverts the problem: we render
the sheet from structured data, so the ground truth is exact **by
construction** (no annotation step, no inter-annotator noise). This is the
established synthetic-OCR practice (SynthDoG, ECCV 2022; SynthOCR-Gen,
arXiv 2601.16113, Jan 2026; Genalog/DocCreator lineage) applied to RU
engineering-sheet conventions.

Each sheet gets: a title block (шифр / лист / ревизия / стадия), scattered
marks (walls, axes, fire ratings) and a small specification table. Output:
one PDF per sheet + per-sheet ground-truth JSON + corpus manifest with
sha256 provenance. Degraded variants chain through
``generate_degraded_scans`` (T4).

Determinism contract: sheet *content* (ground truth + extractable text) is
fully seed-determined. PDF container bytes may embed library-version
artifacts, so byte-hashes are recorded as provenance of this corpus
instance, not asserted stable across pymupdf versions.

Known v1 limitation (recorded, not hidden): pymupdf Base-14 fonts carry no
Cyrillic glyphs, so v1 uses Latin transliteration of RU sheet conventions
(AR-12.3 / Sheet / Rev / Stage). A Cyrillic variant requires vendoring a
licensed Unicode font (pymupdf-fonts) — tracked in the VLM protocol; the
task structure (title block / marks / table) is unchanged.

Claim boundary: synthetic sheets never demonstrate customer-document
literacy; VLM scores on this corpus are fixture-only (RT-001) and CV/VLM
stays advisory (never sign-off).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import pymupdf

_STAGES = ("P", "R")
_DISCIPLINES = ("AR", "KZH", "OV")
_MARK_POOLS: tuple[tuple[str, ...], ...] = (
    ("WALL-01", "WALL-02", "WALL-07", "WALL-12"),
    ("AXIS A-1", "AXIS B-3", "AXIS C-2", "AXIS D-5"),
    ("REI 45", "REI 90", "REI 120", "REI 180"),
)
_SPEC_ITEMS = (
    ("Door DP-1", "pcs", 4),
    ("Window OK-2", "pcs", 6),
    ("Lintel PR-3", "pcs", 12),
    ("Slab PK-60", "pcs", 8),
    ("Beam B-1", "pcs", 3),
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _make_sheet_content(rng: random.Random, index: int) -> dict[str, Any]:
    """Draw one sheet's structured content (the ground truth)."""

    discipline = rng.choice(_DISCIPLINES)
    title_block = {
        "doc_code": f"{discipline}-{rng.randrange(10, 99)}.{rng.randrange(1, 9)}",
        "sheet": f"Sheet {index + 1}",
        "revision": f"Rev. {rng.randrange(0, 4)}",
        "stage": rng.choice(_STAGES),
    }
    marks = sorted({rng.choice(pool) for pool in _MARK_POOLS for _ in range(2)})
    row_count = rng.randrange(3, 6)
    table_rows = [
        {
            "position": str(row_index + 1),
            "designation": _SPEC_ITEMS[row_index % len(_SPEC_ITEMS)][0],
            "quantity": str(rng.randrange(1, 20)),
        }
        for row_index in range(row_count)
    ]
    return {"title_block": title_block, "marks": marks, "table_rows": table_rows}


def _render_sheet(content: dict[str, Any], rng: random.Random) -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=842, height=595)  # A4 landscape, points

    # T2: marks at seeded positions in the drawing field.
    for mark in content["marks"]:
        x = 60 + rng.random() * 500
        y = 60 + rng.random() * 380
        page.insert_text((x, y), mark, fontsize=10, fontname="helv")

    # T3: specification table (top-right corner), pipe-delimited rows.
    table_x, table_y = 590, 70
    page.insert_text((table_x, table_y), "Pos | Designation | Qty", fontsize=9)
    for row_index, row in enumerate(content["table_rows"]):
        line = f"{row['position']} | {row['designation']} | {row['quantity']}"
        page.insert_text((table_x, table_y + 14 * (row_index + 1)), line, fontsize=9)

    # T1: title block (bottom-right, fixed region per RU sheet convention).
    block = content["title_block"]
    base_y = 520
    page.draw_rect(pymupdf.Rect(560, base_y - 14, 830, base_y + 62), width=0.7)
    for offset, text in enumerate(
        (block["doc_code"], block["sheet"], block["revision"], f"Stage {block['stage']}")
    ):
        page.insert_text((570, base_y + 16 * offset), text, fontsize=11)

    payload = document.tobytes()
    document.close()
    return payload


def generate_vlm_fixture_corpus(
    output_dir: Path,
    *,
    sheet_count: int = 5,
    seed: int = 20260726,
) -> dict[str, Any]:
    """Generate sheets + per-sheet ground truth + provenance manifest."""

    if not 1 <= sheet_count <= 100:
        raise ValueError("sheet_count must lie in [1, 100]")
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    sheets: list[dict[str, Any]] = []
    for index in range(sheet_count):
        content = _make_sheet_content(rng, index)
        pdf_bytes = _render_sheet(content, rng)
        sheet_id = f"sheet-{index + 1:02d}"
        pdf_path = output_dir / f"{sheet_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        ground_truth = {
            "artifact_type": "vlm_sheet_ground_truth",
            "schema_version": "1.0.0",
            "sheet_id": sheet_id,
            "source_pdf": pdf_path.name,
            "t1_title_block": content["title_block"],
            "t2_marks": content["marks"],
            "t3_table_rows": content["table_rows"],
            "provenance": "ground truth by construction (renderer input)",
        }
        gt_path = output_dir / f"{sheet_id}.ground-truth.json"
        gt_bytes = (json.dumps(ground_truth, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        gt_path.write_bytes(gt_bytes)
        sheets.append(
            {
                "sheet_id": sheet_id,
                "pdf": pdf_path.name,
                "pdf_sha256": _sha256_bytes(pdf_bytes),
                "ground_truth": gt_path.name,
                "ground_truth_sha256": _sha256_bytes(gt_bytes),
                "mark_count": len(content["marks"]),
                "table_row_count": len(content["table_rows"]),
            }
        )

    manifest: dict[str, Any] = {
        "artifact_type": "vlm_fixture_corpus",
        "schema_version": "1.0.0",
        "seed": seed,
        "sheet_count": sheet_count,
        "sheets": sheets,
        "degradation_tool": "aerobim.tools.generate_degraded_scans (T4 chain)",
        "claim_boundary": (
            "synthetic corpus; ground truth by construction; VLM scores here "
            "are fixture-only and never customer-document literacy (RT-001); "
            "CV/VLM stays advisory"
        ),
    }
    (output_dir / "corpus-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sheets", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260726)
    args = parser.parse_args(argv)
    manifest = generate_vlm_fixture_corpus(
        args.output.resolve(), sheet_count=args.sheets, seed=args.seed
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
