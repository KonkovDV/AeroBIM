
"""Local pack probe (operator tool) — tracker SIG-02 columns, git-safe aggregate.

Runs fully offline against a local quarantine copy of the pack. Writes:
- ``pack-local.json`` — per-file rows WITH relative paths and sha256
  (quarantine only; never commit, never show on camera);
- ``pack-tracker.tsv`` — tracker columns (file / format / processed / priority /
  legal flag) plus MIME and hash; same quarantine rule;
- ``pack-aggregate.json`` — counts by bucket / section; no names, no paths,
  no hashes. Not a claim that the channel pack was processed.

Claim boundary: counts are an inventory of a local copy, not RT closure,
not customer accuracy, not «43 GB processed».
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from aerobim.core.security.upload_limits import (
    DEV_DEFAULT_UPLOAD_BYTES,
    SAMOLET_STATED_MODEL_BYTES,
)
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.owner_files_inventory import require_local_only_output
from aerobim.domain.pack_family_facts import LIRA_NAMED_EXT
from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.pack_archive_overlap import iter_files, rel_posix, win_long

CLAIM_BOUNDARY = (
    "Local copy inventory. Names/paths/hashes stay in quarantine. "
    "Not RT closure; not customer accuracy; not channel-pack processed. "
    "Archives are counted unexpanded. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
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
IFC_CAP_BYTES = DEV_DEFAULT_UPLOAD_BYTES
INGEST_CAP_BYTES = SAMOLET_STATED_MODEL_BYTES

_SUPPORTED_YES = {".ifc", ".pdf"}
_SUPPORTED_PARTIAL = {".dxf"}
_OFFICE = {
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".odt",
    ".ods",
    ".rtf",
    ".csv",
}
_ARCHIVE = {".zip", ".7z", ".rar", ".gz", ".tgz", ".tar"}
_NWD = {".nwd", ".nwc"}
_RVT = {".rvt", ".rfa", ".rte"}
_MIME_OVERRIDE = {
    ".ifc": "application/x-step",
    ".rvt": "application/octet-stream",
    ".nwd": "application/octet-stream",
    ".nwc": "application/octet-stream",
    ".dwg": "image/vnd.dwg",
    ".lir": "application/octet-stream",
}
BUCKETS = ("ifc", "pdf", "rvt", "nwd", "dwg", "office", "archive", "other")
TRACKER_COLUMNS = (
    "file",
    "format",
    "processed_now",
    "priority",
    "legal_flag",
    "mime",
    "bytes",
    "sha256",
    "section",
    "object_key",
    "format_bucket",
)


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


def format_bucket(ext: str) -> str:
    if ext == ".ifc":
        return "ifc"
    if ext == ".pdf":
        return "pdf"
    if ext in _RVT:
        return "rvt"
    if ext in _NWD:
        return "nwd"
    if ext == ".dwg":
        return "dwg"
    if ext in _OFFICE:
        return "office"
    if ext in _ARCHIVE:
        return "archive"
    return "other"


def processed_now_for(ext: str) -> str:
    if ext in _SUPPORTED_YES:
        return "yes"
    if ext in _SUPPORTED_PARTIAL:
        return "partial"
    return "no"


def _wrapper_name(root: Path) -> str | None:
    dirs = sorted(path.name for path in root.iterdir() if path.is_dir())
    files = any(path.is_file() for path in root.iterdir())
    if len(dirs) == 1 and not files:
        return dirs[0]
    return None


def object_key(rel: str, wrapper: str | None) -> str:
    parts = Path(rel).parts
    if wrapper and parts and parts[0] == wrapper:
        parts = parts[1:]
    if len(parts) >= 2:
        return parts[0]
    return "_root"


def _assign_priorities(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Priority 1 = processable files in a cross-section object with IFC+PDF."""

    by_object: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_object[row["object_key"]].append(row)
    meta: dict[str, dict[str, Any]] = {}
    for key, group in by_object.items():
        sections = {row["section"] for row in group if row["section"] != "UNKNOWN"}
        exts = {row["ext"] for row in group}
        runnable = len(sections) >= 2 and ".ifc" in exts and ".pdf" in exts
        cross = len(sections) >= 2
        meta[key] = {
            "section_count": len(sections),
            "runnable_complete": runnable,
            "cross_section": cross,
            "file_count": len(group),
            "bytes": sum(row["bytes"] for row in group),
        }
        for row in group:
            if row["legal_flag"] == "internal_regs_skip":
                row["priority"] = 3
            elif row["processed_now"] == "no":
                row["priority"] = 3
            elif runnable:
                row["priority"] = 1
            else:
                row["priority"] = 2
    return meta


def probe_pack(
    root: Path,
    *,
    progress: bool = False,
    compute_hash: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Walk ``root``; return (rows_with_paths, aggregate_without_names)."""
    root = root.resolve()
    wrapper = _wrapper_name(root)
    rows: list[dict[str, Any]] = []
    by_ext: Counter[str] = Counter()
    by_section: Counter[str] = Counter()
    by_class: Counter[int] = Counter()
    notes: Counter[str] = Counter()
    hashed = 0

    for path in sorted(iter_files(root), key=lambda item: rel_posix(item, root)):
        longp = win_long(path)
        try:
            size = longp.stat().st_size
        except OSError:
            continue
        rel = rel_posix(path, root)
        ext = path.suffix.lower()
        low = rel.lower()
        upper = rel.upper()
        section = next((s for s in SECTIONS if s in upper), "UNKNOWN")
        tz_class = next(
            (v for k, v in TZ_CLASS_TOKENS.items() if k.lower() in low),
            0,
        )
        mime = (
            _MIME_OVERRIDE.get(ext)
            or mimetypes.guess_type(path.name)[0]
            or ("application/octet-stream")
        )
        processed = processed_now_for(ext)
        bucket = format_bucket(ext)
        legal = (
            "internal_regs_skip" if any(token in low for token in ORD_TOKENS) else "project_data"
        )
        record: dict[str, Any] = {
            "ext": ext,
            "bytes": size,
            "mime": mime,
            "section": section,
            "tz_class": tz_class,
            "processed_now": processed,
            "priority": 3,
            "format_bucket": bucket,
            "object_key": object_key(rel, wrapper),
            "legal_flag": legal,
            "sha256": _sha256(longp) if compute_hash else "",
        }
        hashed += 1
        if progress and hashed % 100 == 0:
            verb = "hashed" if compute_hash else "walked"
            print(f"pack_probe {verb} {hashed} files", file=sys.stderr)
        if ext == ".ifc":
            record["schema"] = _ifc_schema(longp)
            notes[f"ifc_{record['schema']}"] += 1
            if size > IFC_CAP_BYTES:
                notes["ifc_over_spf"] += 1
                notes["ifc_over_cap"] += 1
            if size > INGEST_CAP_BYTES:
                notes["ifc_over_ingest"] += 1
        if ext == ".dwg":
            magic = _head(longp, 6)
            if magic.isascii() and magic.isprintable():
                notes["dwg_magic_" + magic] += 1
        if ext == ".pdf":
            notes["pdf_vector" if _pdf_has_text_layer(longp) else "pdf_scan"] += 1
        if ext in LIRA_NAMED_EXT:
            notes["lira_named_ext"] += 1
        if legal == "internal_regs_skip":
            record["ord_candidate"] = True
            notes["ord_candidate"] += 1
        if size > IFC_CAP_BYTES:
            notes["files_over_spf"] += 1
            notes[f"over_spf_{bucket}"] += 1
        rows.append(dict(record, path=rel, name=Path(rel).name))
        by_ext[ext] += 1
        by_section[section] += 1
        by_class[tz_class] += 1
        notes[f"processed_{processed}"] += 1

    object_meta = _assign_priorities(rows)
    total_bytes = sum(row["bytes"] for row in rows)
    bucket_bytes = {bucket: 0 for bucket in BUCKETS}
    bucket_files = {bucket: 0 for bucket in BUCKETS}
    for row in rows:
        bucket_bytes[row["format_bucket"]] += row["bytes"]
        bucket_files[row["format_bucket"]] += 1
    unsupported_bytes = sum(row["bytes"] for row in rows if row["processed_now"] == "no")
    legal_skip_bytes = sum(
        row["bytes"] for row in rows if row["legal_flag"] == "internal_regs_skip"
    )
    p1 = [row for row in rows if row["priority"] == 1]
    aggregate: dict[str, Any] = {
        "artifact_type": "pack_probe_aggregate",
        "claim_level": "local_inventory_not_processed",
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "file_count": len(rows),
        "total_bytes": total_bytes,
        "total_gib": round(total_bytes / (1024**3), 3),
        "by_ext": dict(by_ext),
        "by_section": dict(by_section),
        "by_tz_class": {str(k): v for k, v in sorted(by_class.items())},
        "notes": dict(notes),
        "bytes_by_ext": {
            ext: sum(row["bytes"] for row in rows if row["ext"] == ext) for ext in sorted(by_ext)
        },
        "bytes_by_bucket": bucket_bytes,
        "files_by_bucket": bucket_files,
        "gib_by_bucket": {bucket: round(bucket_bytes[bucket] / (1024**3), 3) for bucket in BUCKETS},
        "files_over_spf_cap": notes["files_over_spf"],
        "spf_cap_bytes": IFC_CAP_BYTES,
        "ingest_cap_bytes": INGEST_CAP_BYTES,
        "raises_spf_default": False,
        "archives_unexpanded": True,
        "unsupported_now_bytes": unsupported_bytes,
        "unsupported_now_gib": round(unsupported_bytes / (1024**3), 3),
        "unsupported_now_pct": (
            round(100.0 * unsupported_bytes / total_bytes, 2) if total_bytes else 0.0
        ),
        "legal_skip_bytes": legal_skip_bytes,
        "legal_skip_gib": round(legal_skip_bytes / (1024**3), 3),
        "object_count": len(object_meta),
        "objects_cross_section": sum(1 for item in object_meta.values() if item["cross_section"]),
        "objects_runnable_complete": sum(
            1 for item in object_meta.values() if item["runnable_complete"]
        ),
        "priority_counts": {
            "1": sum(1 for row in rows if row["priority"] == 1),
            "2": sum(1 for row in rows if row["priority"] == 2),
            "3": sum(1 for row in rows if row["priority"] == 3),
        },
        "sig01_run_set_files": len(p1),
        "sig01_run_set_bytes": sum(row["bytes"] for row in p1),
        "hashes_computed": compute_hash,
        "pd_filename_inventory": {
            "statutory_pp87": False,
            "engine_mandatory_latin": ["PZ", "AR", "KZH"],
            "has_pz": "ПЗ" in by_section,
            "has_ar": "АР" in by_section,
            "has_kr": "КР" in by_section,
            "has_kzh": "КЖ" in by_section,
            "engine_kzh_vs_pack_kr": (
                "pack_kr_not_engine_kzh"
                if ("КР" in by_section and "КЖ" not in by_section)
                else "see_by_section"
            ),
        },
        "tz_class_2_rd_files": int(by_class.get(2, 0)),
        "lira_named_ext_files": notes["lira_named_ext"],
        "uncompressed_gib_in_git": False,
        "names_in_output": False,
        "hashes_in_output": False,
    }
    return rows, aggregate


def write_tracker_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACKER_COLUMNS, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "file": row["path"],
                    "format": row["ext"] or "(none)",
                    "processed_now": row["processed_now"],
                    "priority": row["priority"],
                    "legal_flag": row["legal_flag"],
                    "mime": row["mime"],
                    "bytes": row["bytes"],
                    "sha256": row["sha256"],
                    "section": row["section"],
                    "object_key": row["object_key"],
                    "format_bucket": row["format_bucket"],
                }
            )


def write_chat_summary(path: Path, aggregate: dict[str, Any]) -> None:
    gib = aggregate["gib_by_bucket"]
    lines = [
        "# SIG-02 inventory (local copy; not «processed»)",
        "",
        f"Files: {aggregate['file_count']}. Bytes: {aggregate['total_bytes']}"
        f" ({aggregate['total_gib']} GiB).",
        f"Objects: {aggregate['object_count']}"
        f" (cross-section {aggregate['objects_cross_section']},"
        f" IFC+PDF complete {aggregate['objects_runnable_complete']}).",
        "",
        "## Format slice (GiB)",
        "",
        "| Bucket | GiB | Files |",
        "|---|---:|---:|",
    ]
    for bucket in BUCKETS:
        lines.append(f"| {bucket} | {gib[bucket]} | {aggregate['files_by_bucket'][bucket]} |")
    lines.extend(
        [
            "",
            f"Over SPF 256 MiB: {aggregate['files_over_spf_cap']} files (not an SPF-cap raise).",
            f"Unsupported now (processed=no): {aggregate['unsupported_now_gib']} GiB "
            f"= {aggregate['unsupported_now_pct']} % of the copy.",
            f"Legal-skip (developer internal regs heuristic): {aggregate['legal_skip_gib']} GiB.",
            f"SIG-01 run set (priority 1): {aggregate['sig01_run_set_files']} files, "
            f"{round(aggregate['sig01_run_set_bytes'] / (1024**3), 3)} GiB.",
            "Archives counted unexpanded. Checkpoint GO (regulatory_measurement_mvp; customer_go false). Owner pastes this + TSV.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="quarantine copy of the pack")
    parser.add_argument(
        "out",
        type=Path,
        help="output dir under <repo>/.local/ or outside the git tree",
    )
    parser.add_argument("--progress", action="store_true")
    parser.add_argument(
        "--skip-hash",
        action="store_true",
        help="Inventory without sha256 (faster; TSV still needs a hashed run)",
    )
    args = parser.parse_args(argv)
    try:
        require_local_only_output(repo_root(), args.out)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    rows, aggregate = probe_pack(
        args.root,
        progress=args.progress,
        compute_hash=not args.skip_hash,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "pack-local.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    (args.out / "pack-aggregate.json").write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    write_tracker_tsv(args.out / "pack-tracker.tsv", rows)
    write_chat_summary(args.out / "pack-chat-summary.md", aggregate)
    print(json.dumps(aggregate, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
