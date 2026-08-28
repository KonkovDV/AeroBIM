"""Local pack probe (operator tool) — two outputs, one git-safe.

Runs fully offline against a local quarantine copy of the pack. Writes:
- ``pack-local.json`` — per-file rows WITH relative paths and sha256
  (quarantine only; never commit, never show on camera);
- ``pack-aggregate.json`` — counts by extension / section / TZ appendix class
  plus heuristic notes; no names, no paths, no hashes. This is the only output
  allowed out of the quarantine, and only after the organizers' answer.

Claim boundary: counts are an inventory of a local copy, not pack contents
knowledge, not RT closure, not customer accuracy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "Aggregate counts only; names/paths/hashes stay in quarantine; "
    "not RT closure; not customer accuracy; publish aggregate only after "
    "the organizers' answer."
)

SECTIONS: tuple[str, ...] = (
    "КЖ",
    "КР",
    "АР",
    "АС",
    "ОВ",
    "ВК",
    "ЭОМ",
    "СС",
    "АУПТ",
    "ПЗ",
    "ТХ",
)
TZ_CLASS_TOKENS: dict[str, int] = {
    "проектная": 1,
    "ПД": 1,
    "рабочая": 2,
    "РД": 2,
    "стандарт": 3,
    "СТО": 3,
    "техническое задание": 4,
    "ТЗ": 4,
    "ошибк": 5,
    "расчет": 6,
    "расчёт": 6,
    "ЛИРА": 6,
}
ORD_TOKENS: tuple[str, ...] = (
    "регламент",
    "порядок действи",
    "осс",
    "дебитор",
    "обращени",
    "страхов",
)
IFC_CAP_BYTES = 256 * 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _head(path: Path, size: int = 4096) -> str:
    with path.open("rb") as handle:
        return handle.read(size).decode("latin-1", "ignore")


def _ifc_schema(path: Path) -> str:
    upper = _head(path).upper()
    return next((t for t in ("IFC4X3", "IFC4", "IFC2X3") if t in upper), "UNKNOWN")


def _pdf_has_text_layer(path: Path) -> bool:
    return "/Font" in _head(path, 1 << 18)


def probe_pack(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Walk ``root``; return (rows_with_paths, aggregate_without_names)."""
    root = root.resolve()
    rows: list[dict[str, Any]] = []
    by_ext: Counter[str] = Counter()
    by_section: Counter[str] = Counter()
    by_class: Counter[int] = Counter()
    notes: Counter[str] = Counter()

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        ext = path.suffix.lower()
        size = path.stat().st_size
        low = rel.lower()
        upper = rel.upper()
        section = next((s for s in SECTIONS if s in upper), "UNKNOWN")
        tz_class = next(
            (v for k, v in TZ_CLASS_TOKENS.items() if k.lower() in low),
            0,
        )
        record: dict[str, Any] = {
            "ext": ext,
            "bytes": size,
            "section": section,
            "tz_class": tz_class,
            "sha256": _sha256(path),
        }
        if ext == ".ifc":
            record["schema"] = _ifc_schema(path)
            notes[f"ifc_{record['schema']}"] += 1
            if size > IFC_CAP_BYTES:
                notes["ifc_over_cap"] += 1
        if ext == ".dwg":
            notes["dwg_magic_" + _head(path, 6)] += 1
        if ext == ".pdf":
            notes["pdf_vector" if _pdf_has_text_layer(path) else "pdf_scan"] += 1
        if any(token in low for token in ORD_TOKENS):
            record["ord_candidate"] = True
            notes["ord_candidate"] += 1
        rows.append(dict(record, path=rel))
        by_ext[ext] += 1
        by_section[section] += 1
        by_class[tz_class] += 1

    aggregate: dict[str, Any] = {
        "artifact_type": "pack_probe_aggregate",
        "claim_boundary": CLAIM_BOUNDARY,
        "file_count": len(rows),
        "total_bytes": sum(row["bytes"] for row in rows),
        "by_ext": dict(by_ext),
        "by_section": dict(by_section),
        "by_tz_class": {str(k): v for k, v in sorted(by_class.items())},
        "notes": dict(notes),
        "names_in_output": False,
        "hashes_in_output": False,
    }
    return rows, aggregate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="quarantine copy of the pack")
    parser.add_argument(
        "out",
        type=Path,
        help="output dir OUTSIDE the git tree",
    )
    args = parser.parse_args(argv)
    rows, aggregate = probe_pack(args.root)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "pack-local.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    (args.out / "pack-aggregate.json").write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(json.dumps(aggregate, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
