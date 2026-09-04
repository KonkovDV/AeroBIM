
"""Compare pack zip/7z members to the already-extracted tree. No names in aggregate.

Does not unpack by default. ``--extract-missing-ifc-pdf`` writes hashed IFC/PDF
under ``.local/``. ``--extract-all`` streams every zip member under
``out/unpacked-all`` (Windows long paths). 7z listing/extract still needs 7-Zip.
Does not close RT. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat as stat_mod
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import IO, Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.owner_files_inventory import require_local_only_output
from aerobim.tools.benchmark_project_package import repo_root

CLAIM_BOUNDARY = (
    "Archive overlap vs local copy. Not unpacked-as-processed. "
    "Not channel pack processed. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)
_EXTRACT_EXT = {".ifc", ".pdf"}
_ARCHIVE_EXT = {".zip", ".7z"}
_MAX_EXTRACT_MEMBER_BYTES = 512 * 1024 * 1024
_STREAM_CHUNK = 1 << 20
_DISK_RESERVE_BYTES = 512 * 1024 * 1024
_NESTED_ZIP_PASSES = 4


def win_long(path: Path) -> Path:
    raw = os.path.abspath(str(path))
    if os.name != "nt":
        return Path(raw)
    if raw.startswith("\\\\?\\"):
        return Path(raw)
    if raw.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + raw[2:])
    return Path("\\\\?\\" + raw)


def strip_win_long(path: Path) -> str:
    raw = os.path.abspath(str(path))
    if raw.startswith("\\\\?\\UNC\\"):
        return "\\\\" + raw[8:]
    if raw.startswith("\\\\?\\"):
        return raw[4:]
    return raw


def rel_posix(path: Path, root: Path) -> str:
    return os.path.relpath(strip_win_long(path), strip_win_long(root)).replace("\\", "/")


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    start = str(win_long(root))
    for dirpath, _dirnames, filenames in os.walk(start):
        for name in filenames:
            files.append(Path(dirpath) / name)
    return files


def _member_rel(info: zipfile.ZipInfo) -> str:
    name = info.filename.replace("\\", "/").lstrip("/")
    if name.endswith("/"):
        return ""
    return name


def zip_members(path: Path) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    with zipfile.ZipFile(win_long(path), "r") as archive:
        for info in archive.infolist():
            rel = _member_rel(info)
            if not rel:
                continue
            out.append((rel, int(info.file_size)))
    return out


def _exists_same_size(path: Path, size: int) -> bool:
    try:
        st = win_long(path).stat()
    except OSError:
        return False
    return stat_mod.S_ISREG(st.st_mode) and st.st_size == size


def build_name_size_index(root: Path) -> set[tuple[str, int]]:
    seen: set[tuple[str, int]] = set()
    for path in iter_files(root):
        try:
            size = win_long(path).stat().st_size
        except OSError:
            continue
        seen.add((path.name.lower(), int(size)))
    return seen


def match_member(
    zip_path: Path,
    member: str,
    size: int,
    name_size: set[tuple[str, int]],
) -> bool:
    posix = member.replace("\\", "/")
    base = Path(posix).name.lower()
    if (base, size) in name_size:
        return True
    parent = zip_path.parent
    stem = zip_path.stem
    tails = [posix, Path(posix).name]
    roots = [
        parent,
        parent / "_unpacked",
        parent / stem,
        parent / "_unpacked" / stem,
    ]
    for root in roots:
        for tail in tails:
            if _exists_same_size(root / Path(tail), size):
                return True
    return False


def probe_archives(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = root.resolve()
    rows: list[dict[str, Any]] = []
    notes: Counter[str] = Counter()
    missing_ext: Counter[str] = Counter()
    missing_bytes_ext: Counter[str] = Counter()
    name_size = build_name_size_index(root)
    disk_files = iter_files(root)
    unpacked_dirs = 0
    for dirpath, _dirnames, _filenames in os.walk(str(win_long(root))):
        if Path(dirpath).name == "_unpacked":
            unpacked_dirs += 1
    for path in disk_files:
        ext = path.suffix.lower()
        if ext not in _ARCHIVE_EXT:
            continue
        rel = rel_posix(path, root)
        record: dict[str, Any] = {
            "path": rel,
            "ext": ext,
            "bytes": path.stat().st_size,
            "kind": "zip" if ext == ".zip" else "sevenzip",
        }
        if ext != ".zip":
            record["status"] = "list_unsupported"
            notes["sevenzip_unlisted"] += 1
            rows.append(record)
            continue
        try:
            members = zip_members(path)
        except zipfile.BadZipFile:
            record["status"] = "bad_zip"
            notes["bad_zip"] += 1
            rows.append(record)
            continue
        matched = 0
        matched_bytes = 0
        missing = 0
        missing_bytes = 0
        missing_extract = 0
        missing_extract_bytes = 0
        for member, size in members:
            if match_member(path, member, size, name_size):
                matched += 1
                matched_bytes += size
                continue
            missing += 1
            missing_bytes += size
            suffix = Path(member).suffix.lower()
            missing_ext[suffix or "(none)"] += 1
            missing_bytes_ext[suffix or "(none)"] += size
            if suffix in _EXTRACT_EXT:
                missing_extract += 1
                missing_extract_bytes += size
        total = matched + missing
        record.update(
            {
                "member_count": total,
                "matched_count": matched,
                "missing_count": missing,
                "matched_bytes": matched_bytes,
                "missing_bytes": missing_bytes,
                "missing_ifc_pdf_count": missing_extract,
                "missing_ifc_pdf_bytes": missing_extract_bytes,
                "status": "fully_on_disk"
                if missing == 0
                else ("partial" if matched else "not_on_disk"),
            }
        )
        notes[record["status"]] += 1
        rows.append(record)
    missing_ifc_pdf_bytes = sum(row.get("missing_ifc_pdf_bytes", 0) for row in rows)
    aggregate: dict[str, Any] = {
        "artifact_type": "pack_archive_overlap",
        "claim_level": "local_inventory_not_processed",
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "archive_count": len(rows),
        "disk_file_count": len(disk_files),
        "unpacked_dir_count": unpacked_dirs,
        "zip_count": sum(1 for row in rows if row["ext"] == ".zip"),
        "sevenzip_count": sum(1 for row in rows if row["ext"] == ".7z"),
        "notes": dict(notes),
        "missing_member_ext_files": dict(missing_ext),
        "missing_member_ext_bytes": dict(missing_bytes_ext),
        "missing_ifc_pdf_bytes": missing_ifc_pdf_bytes,
        "missing_ifc_pdf_gib": round(missing_ifc_pdf_bytes / (1024**3), 3),
        "recommend_extract_ifc_pdf": missing_ifc_pdf_bytes > 0,
        "names_in_output": False,
        "hashes_in_output": False,
    }
    return rows, aggregate


def _safe_member_path(base: Path, member: str) -> Path:
    rel = member.replace("\\", "/").lstrip("/")
    parts: list[str] = []
    for part in rel.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("zip_slip")
        cleaned = "".join("_" if char in '<>:"|?*' else char for char in part)
        cleaned = cleaned.rstrip(". ")
        if not cleaned:
            cleaned = "_"
        parts.append(cleaned)
    if not parts:
        raise ValueError("empty_member")
    out = base.joinpath(*parts)
    base_s = os.path.normcase(os.path.abspath(str(base)))
    out_s = os.path.normcase(os.path.abspath(str(out)))
    if out_s != base_s and not out_s.startswith(base_s + os.sep):
        raise ValueError("zip_slip")
    return Path(out_s)


def _archive_unpack_dir(dest_root: Path, archive_rel: str) -> Path:
    rel = Path(archive_rel.replace("\\", "/"))
    return dest_root.joinpath(*rel.with_suffix("").parts)


def _stream_copy(src: IO[bytes], dest: Path) -> int:
    win_long(dest.parent).mkdir(parents=True, exist_ok=True)
    written = 0
    with open(str(win_long(dest)), "wb") as handle:
        while True:
            chunk = src.read(_STREAM_CHUNK)
            if not chunk:
                break
            handle.write(chunk)
            written += len(chunk)
    return written


def _free_bytes(path: Path) -> int:
    drive = os.path.splitdrive(os.path.abspath(str(path)))[0]
    return shutil.disk_usage(drive + os.sep).free


def extract_one_zip(archive: Path, dest: Path) -> dict[str, Any]:
    """Stream every member of one zip into ``dest``. Skip existing same-size files."""

    stats: dict[str, Any] = {
        "ok": 0,
        "ok_bytes": 0,
        "skip_exists": 0,
        "bad_header": 0,
        "slip": 0,
        "error": 0,
        "error_os": 0,
        "error_runtime": 0,
        "members": 0,
        "status": "done",
    }
    try:
        archive_handle = zipfile.ZipFile(win_long(archive), "r")
    except zipfile.BadZipFile:
        stats["status"] = "bad_zip"
        stats["error"] = 1
        return stats
    win_long(dest).mkdir(parents=True, exist_ok=True)
    with archive_handle:
        for info in archive_handle.infolist():
            member = _member_rel(info)
            if not member:
                continue
            stats["members"] += 1
            try:
                target = _safe_member_path(dest, member)
            except ValueError:
                stats["slip"] += 1
                continue
            size = int(info.file_size)
            try:
                existing = win_long(target).stat().st_size
            except OSError:
                existing = None
            if existing == size and size > 0:
                stats["skip_exists"] += 1
                continue
            if size > 0 and _free_bytes(dest) < size + _DISK_RESERVE_BYTES:
                stats["status"] = "disk_full"
                stats["error"] += 1
                return stats
            try:
                with archive_handle.open(info, "r") as src:
                    stats["ok_bytes"] += _stream_copy(src, target)
                stats["ok"] += 1
            except zipfile.BadZipFile:
                stats["bad_header"] += 1
            except OSError:
                stats["error"] += 1
                stats["error_os"] += 1
            except RuntimeError:
                stats["error"] += 1
                stats["error_runtime"] += 1
    return stats


def extract_all_zips(root: Path, dest: Path) -> dict[str, Any]:
    """Unpack every ``.zip`` under ``root`` into ``dest``. Nested zips get a second pass."""

    dest = dest.resolve()
    win_long(dest).mkdir(parents=True, exist_ok=True)
    totals: dict[str, Any] = {
        "archives": 0,
        "bad_zip": 0,
        "ok": 0,
        "ok_bytes": 0,
        "skip_exists": 0,
        "bad_header": 0,
        "slip": 0,
        "error": 0,
        "error_os": 0,
        "error_runtime": 0,
        "nested_passes": 0,
        "disk_full": False,
        "sevenzip_unextracted": 0,
        "dest": str(dest),
        "checkpoint": CHECKPOINT,
    }
    for path in iter_files(root):
        if path.suffix.lower() == ".7z":
            totals["sevenzip_unextracted"] += 1
            continue
        if path.suffix.lower() != ".zip":
            continue
        totals["archives"] += 1
        rel = rel_posix(path, root)
        print(
            f"extract_all {totals['archives']} {rel[-80:]}",
            file=sys.stderr,
        )
        stats = extract_one_zip(path, _archive_unpack_dir(dest, rel))
        for key in (
            "ok",
            "ok_bytes",
            "skip_exists",
            "bad_header",
            "slip",
            "error",
            "error_os",
            "error_runtime",
        ):
            totals[key] += int(stats.get(key) or 0)
        print(
            (
                f"extract_all done {rel[-80:]} ok={stats['ok']} "
                f"skip={stats['skip_exists']} bad_hdr={stats['bad_header']} "
                f"err={stats['error']} os={stats.get('error_os', 0)} "
                f"rt={stats.get('error_runtime', 0)} {stats.get('status')}"
            ),
            file=sys.stderr,
        )
        if stats.get("status") == "bad_zip":
            totals["bad_zip"] += 1
        if stats.get("status") == "disk_full":
            totals["disk_full"] = True
            return totals

    seen: set[str] = set()
    for pass_no in range(_NESTED_ZIP_PASSES):
        nested = [
            path
            for path in iter_files(dest)
            if path.suffix.lower() == ".zip" and strip_win_long(path) not in seen
        ]
        if not nested:
            break
        totals["nested_passes"] = pass_no + 1
        for path in nested:
            seen.add(strip_win_long(path))
            stats = extract_one_zip(path, Path(strip_win_long(path) + ".d"))
            for key in (
                "ok",
                "ok_bytes",
                "skip_exists",
                "bad_header",
                "slip",
                "error",
                "error_os",
                "error_runtime",
            ):
                totals[key] += int(stats.get(key) or 0)
            if stats.get("status") == "disk_full":
                totals["disk_full"] = True
                return totals
    totals["ok_gib"] = round(totals["ok_bytes"] / (1024**3), 3)
    return totals


def extract_missing_ifc_pdf(root: Path, dest: Path) -> dict[str, Any]:
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    written = 0
    written_bytes = 0
    skipped_exists = 0
    index = build_name_size_index(root)
    for path in iter_files(root):
        if path.suffix.lower() != ".zip":
            continue
        try:
            zip_members(path)
        except zipfile.BadZipFile:
            continue
        with zipfile.ZipFile(win_long(path), "r") as archive:
            for info in archive.infolist():
                member = _member_rel(info)
                if not member:
                    continue
                size = int(info.file_size)
                suffix = Path(member).suffix.lower()
                if suffix not in _EXTRACT_EXT:
                    continue
                if size > _MAX_EXTRACT_MEMBER_BYTES:
                    continue
                if match_member(path, member, size, index):
                    skipped_exists += 1
                    continue
                digest = hashlib.sha256(f"{path}:{member}".encode()).hexdigest()[:16]
                target = dest / f"{digest}{suffix}"
                if target.exists() and target.stat().st_size == size:
                    skipped_exists += 1
                    continue
                try:
                    with archive.open(info) as src:
                        payload = src.read()
                except zipfile.BadZipFile:
                    continue
                target.write_bytes(payload)
                written += 1
                written_bytes += len(payload)
                sidecar = dest / f"{digest}.json"
                sidecar.write_text(
                    json.dumps(
                        {
                            "member": member,
                            "source_archive": rel_posix(path, root),
                            "bytes": len(payload),
                        },
                        ensure_ascii=False,
                    )
                    + "\n",
                    encoding="utf-8",
                )
    return {
        "written": written,
        "written_bytes": written_bytes,
        "skipped_already_on_disk": skipped_exists,
        "dest": str(dest),
        "checkpoint": CHECKPOINT,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument(
        "--extract-missing-ifc-pdf",
        action="store_true",
        help="Write missing IFC/PDF under out/extracted with short names",
    )
    parser.add_argument(
        "--extract-all",
        action="store_true",
        help="Stream every zip member under out/unpacked-all (7z still skipped)",
    )
    args = parser.parse_args(argv)
    root_repo = repo_root()
    try:
        require_local_only_output(root_repo, args.out)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    rows, aggregate = probe_archives(args.root)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "archive-local.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    if args.extract_missing_ifc_pdf:
        extracted = extract_missing_ifc_pdf(args.root, args.out / "extracted")
        aggregate["extract"] = {
            k: extracted[k] for k in ("written", "written_bytes", "skipped_already_on_disk")
        }
        aggregate["extract"]["written_gib"] = round(extracted["written_bytes"] / (1024**3), 3)
    if args.extract_all:
        unpacked = extract_all_zips(args.root, args.out / "unpacked-all")
        aggregate["extract_all"] = {
            k: unpacked[k]
            for k in (
                "archives",
                "bad_zip",
                "ok",
                "ok_bytes",
                "ok_gib",
                "skip_exists",
                "bad_header",
                "slip",
                "error",
                "error_os",
                "error_runtime",
                "nested_passes",
                "disk_full",
                "sevenzip_unextracted",
            )
            if k in unpacked
        }
    (args.out / "archive-aggregate.json").write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(json.dumps(aggregate, ensure_ascii=True, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
