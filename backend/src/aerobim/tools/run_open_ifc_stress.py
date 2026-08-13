"""Open-IFC header stress on a directory. GNI 223 stays SKIPPED without a local root.

Needed for demo 20.08: a measured open/parse table without claiming GNI product accuracy.
Header-only by default (first 64 KiB). Optional IfcOpenShell open skips files over
``--open-max-bytes`` so the upstream 536 MB unloadable architectural model does not OOM.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.domain.ids_schema_gate import parse_ifc_file_schema, parse_ifc_view_definition
from aerobim.tools.benchmark_project_package import _machine_fingerprint, repo_root

CLAIM_LEVEL = "open_ifc_stress"
CLAIM_BOUNDARY = (
    "Header-level open/parse timing on IFC files present on disk. "
    "Not GNI 223 unless AEROBIM_GNI_BIM_ROOT is set. Student GNI models are not "
    "product accuracy. GPLv3 IFC-Bench models are not scanned from this tree. "
    "IfcOpenShell entity counts are optional and skip oversized files."
)
HEADER_BYTES = 64 * 1024
DEFAULT_OPEN_MAX_BYTES = 200 * 1024 * 1024
_PAIR_RE = re.compile(r"^(?P<stem>.+)_(?P<role>arc|structure)\.ifc$", re.IGNORECASE)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def discover_ifc(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.ifc") if path.is_file())


def _rel_to(path: Path, base: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.name


def stress_file(
    path: Path,
    *,
    base: Path,
    open_model: bool = False,
    open_max_bytes: int = DEFAULT_OPEN_MAX_BYTES,
) -> dict[str, Any]:
    started = perf_counter()
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            header_raw = handle.read(HEADER_BYTES)
        header = header_raw.decode("utf-8", errors="replace")
        schema = parse_ifc_file_schema(header)
        view = parse_ifc_view_definition(header)
        elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
        row: dict[str, Any] = {
            "path": _rel_to(path, base),
            "bytes": size,
            "schema": schema,
            "view": view,
            "open_ok": True,
            "elapsed_ms": elapsed_ms,
            "error": None,
            "ifc_open": "not_requested",
            "ifc_product_count": None,
        }
        if open_model:
            _try_ifcopenshell_open(path, row, open_max_bytes=open_max_bytes)
        return row
    except OSError as exc:
        return {
            "path": str(path),
            "bytes": None,
            "schema": None,
            "view": None,
            "open_ok": False,
            "elapsed_ms": round((perf_counter() - started) * 1000.0, 3),
            "error": f"{type(exc).__name__}: {exc}",
            "ifc_open": "not_requested",
            "ifc_product_count": None,
        }


def _try_ifcopenshell_open(path: Path, row: dict[str, Any], *, open_max_bytes: int) -> None:
    size = int(row.get("bytes") or 0)
    if size > open_max_bytes:
        row["ifc_open"] = "skipped_oversize"
        row["ifc_open_detail"] = (
            f"bytes={size} > open_max_bytes={open_max_bytes}; "
            "matches GNI upstream skip of the unloadable ~536 MB architectural file"
        )
        return
    started = perf_counter()
    try:
        import ifcopenshell

        model = ifcopenshell.open(str(path))
        row["ifc_product_count"] = len(model.by_type("IfcProduct"))
        row["ifc_open"] = "ok"
        row["ifc_open_ms"] = round((perf_counter() - started) * 1000.0, 3)
    except Exception as exc:  # noqa: BLE001 — stress must not abort the pack
        row["ifc_open"] = "error"
        row["ifc_open_detail"] = f"{type(exc).__name__}: {exc}"
        row["ifc_open_ms"] = round((perf_counter() - started) * 1000.0, 3)


def detect_arc_structure_pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, str]] = {}
    sizes: dict[str, dict[str, int | None]] = {}
    schemas: dict[str, dict[str, str | None]] = {}
    for row in rows:
        name = Path(str(row.get("path") or "")).name
        match = _PAIR_RE.match(name)
        if match is None:
            continue
        stem = match.group("stem").lower()
        role = match.group("role").lower()
        buckets.setdefault(stem, {})[role] = str(row.get("path"))
        sizes.setdefault(stem, {})[role] = row.get("bytes")
        schemas.setdefault(stem, {})[role] = row.get("schema")
    pairs: list[dict[str, Any]] = []
    for stem, roles in sorted(buckets.items()):
        pairs.append(
            {
                "stem": stem,
                "paired": "arc" in roles and "structure" in roles,
                "arc": roles.get("arc"),
                "structure": roles.get("structure"),
                "arc_bytes": (sizes.get(stem) or {}).get("arc"),
                "structure_bytes": (sizes.get(stem) or {}).get("structure"),
                "schema_match": (
                    (schemas.get(stem) or {}).get("arc")
                    == (schemas.get(stem) or {}).get("structure")
                    if "arc" in roles and "structure" in roles
                    else None
                ),
            }
        )
    return pairs


def _subset_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    tallies = {"fundamentals_2025": 0, "projects_2026": 0, "other": 0}
    for row in rows:
        path = str(row.get("path") or "").replace("\\", "/").lower()
        if "2025_bimfundamentals" in path or "bimfundamentals" in path:
            tallies["fundamentals_2025"] += 1
        elif "2026_bimprojects" in path or "bimprojects" in path:
            tallies["projects_2026"] += 1
        else:
            tallies["other"] += 1
    return tallies


def build_payload(
    *,
    fixture_dir: Path,
    gni_root: Path | None,
    repo: Path,
    open_model: bool = False,
    open_max_bytes: int = DEFAULT_OPEN_MAX_BYTES,
) -> dict[str, Any]:
    fixture_rows = [
        stress_file(
            path,
            base=repo,
            open_model=open_model,
            open_max_bytes=open_max_bytes,
        )
        for path in discover_ifc(fixture_dir)
    ]
    gni_status = "SKIPPED"
    gni_reason = "AEROBIM_GNI_BIM_ROOT not set; 223-model stress not run; dataset stays on Zenodo"
    gni_rows: list[dict[str, Any]] = []
    if gni_root is not None and gni_root.is_dir():
        gni_status = "RUN"
        gni_reason = str(gni_root)
        gni_rows = [
            stress_file(
                path,
                base=gni_root,
                open_model=open_model,
                open_max_bytes=open_max_bytes,
            )
            for path in discover_ifc(gni_root)
        ]
    try:
        fixture_rel = fixture_dir.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        fixture_rel = str(fixture_dir)
    pairs = detect_arc_structure_pairs(gni_rows)
    gni_failures = [row for row in gni_rows if not row.get("open_ok")]
    largest = max(gni_rows, key=lambda row: int(row.get("bytes") or 0), default=None)
    body: dict[str, Any] = {
        "schema_version": "1.1.0",
        "artifact_type": "open_ifc_stress",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "machine": _machine_fingerprint(),
        "open_model": open_model,
        "open_max_bytes": open_max_bytes,
        "gni": {
            "status": gni_status,
            "reason": gni_reason,
            "doi": "10.5281/zenodo.19722012",
            "file_count": len(gni_rows),
            "open_ok": sum(1 for row in gni_rows if row["open_ok"]),
            "open_fail": len(gni_failures),
            "schema_counts": _count(gni_rows, "schema"),
            "subset_counts": _subset_counts(gni_rows),
            "bytes_total": sum(int(row["bytes"] or 0) for row in gni_rows),
            "pairs": pairs,
            "pairs_complete": sum(1 for pair in pairs if pair["paired"]),
            "ifc_open_counts": _count(gni_rows, "ifc_open") if open_model else {"not_requested": len(gni_rows)},
            "largest": (
                {"path": largest.get("path"), "bytes": largest.get("bytes")}
                if largest
                else None
            ),
            "failures": gni_failures,
        },
        "fixture": {
            "dir": fixture_rel,
            "file_count": len(fixture_rows),
            "open_ok": sum(1 for row in fixture_rows if row["open_ok"]),
            "schema_counts": _count(fixture_rows, "schema"),
        },
        "fixture_rows": fixture_rows,
        "gni_rows": gni_rows,
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def _count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    tallies: dict[str, int] = {}
    for row in rows:
        token = str(row.get(key) or "unknown")
        tallies[token] = tallies.get(token, 0) + 1
    return dict(sorted(tallies.items()))


def render_markdown(payload: dict[str, Any]) -> str:
    fixture = payload.get("fixture") or {}
    gni = payload.get("gni") or {}
    pairs = gni.get("pairs") or []
    pair_lines = [
        f"| `{pair.get('stem')}` | {pair.get('paired')} | {pair.get('schema_match')} |"
        for pair in pairs
    ]
    pair_table = (
        "\n".join(["| stem | paired | schema_match |", "| --- | --- | --- |", *pair_lines])
        if pair_lines
        else "_no `*_arc.ifc` / `*_structure.ifc` pairs in this root_"
    )
    return "\n".join(
        [
            "<!-- claims-lint: allow-file reason=\"Open IFC stress; GNI student models are not product accuracy\" -->",
            "---",
            'title: "Open IFC header stress"',
            f"date: {str(payload.get('generated_at') or '')[:10]}",
            f"claim_level: {payload.get('claim_level')}",
            "claim_boundary: >-",
            f"  {payload.get('claim_boundary')}",
            "---",
            "",
            "# Open IFC header stress",
            "",
            f"- fixture files: **{fixture.get('file_count')}** open_ok **{fixture.get('open_ok')}**",
            f"- schemas: `{json.dumps(fixture.get('schema_counts'), ensure_ascii=False)}`",
            f"- GNI: **{gni.get('status')}** files **{gni.get('file_count')}** open_ok **{gni.get('open_ok')}** fail **{gni.get('open_fail')}**",
            f"- GNI schemas: `{json.dumps(gni.get('schema_counts'), ensure_ascii=False)}`",
            f"- GNI subsets: `{json.dumps(gni.get('subset_counts'), ensure_ascii=False)}`",
            f"- GNI bytes_total: **{gni.get('bytes_total')}**",
            f"- AR+STR pairs complete: **{gni.get('pairs_complete')}** / {len(pairs)} stems (upstream: 7 of 9 teams)",
            f"- largest file: `{json.dumps(gni.get('largest'), ensure_ascii=False)}` (upstream could not load ~536 MB architecture; header-only still opens)",
            f"- IfcOpenShell: `{json.dumps(gni.get('ifc_open_counts'), ensure_ascii=False)}`",
            f"- DOI: [{gni.get('doi')}](https://doi.org/{gni.get('doi')})",
            f"- content_sha256: `{payload.get('content_sha256')}`",
            "",
            "## Paired architectural + structural stems",
            "",
            pair_table,
            "",
            "Student GNI models are **not** product accuracy. Checkpoint stays NO_GO.",
            "",
            "```bash",
            "cd backend",
            "python -m aerobim.tools.run_open_ifc_stress --gni-root ../.local/gni-bim --open-model",
            "```",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", type=Path, default=None)
    parser.add_argument("--gni-root", type=Path, default=None)
    parser.add_argument(
        "--open-model",
        action="store_true",
        help="IfcOpenShell-open each file under --open-max-bytes (default 200 MiB)",
    )
    parser.add_argument("--open-max-bytes", type=int, default=DEFAULT_OPEN_MAX_BYTES)
    args = parser.parse_args(argv)
    root = repo_root()
    fixture_dir = args.fixture_dir or (root / "samples" / "ifc")
    gni_env = args.gni_root or os.environ.get("AEROBIM_GNI_BIM_ROOT")
    gni_root = Path(gni_env) if gni_env else None
    payload = build_payload(
        fixture_dir=fixture_dir,
        gni_root=gni_root,
        repo=root,
        open_model=bool(args.open_model),
        open_max_bytes=int(args.open_max_bytes),
    )
    out = root / "artifacts" / "open-ifc-stress"
    out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (out / "open-ifc-stress.json").write_text(text, encoding="utf-8")
    (root / "docs" / "evidence" / "open-ifc-stress-2026-08.json").write_text(
        text, encoding="utf-8"
    )
    (root / "docs" / "evidence" / "open-ifc-stress-2026-08.md").write_text(
        render_markdown(payload), encoding="utf-8"
    )
    summary = {
        "fixture": payload["fixture"],
        "gni": {
            key: payload["gni"][key]
            for key in (
                "status",
                "file_count",
                "open_ok",
                "open_fail",
                "schema_counts",
                "subset_counts",
                "bytes_total",
                "pairs_complete",
                "largest",
                "ifc_open_counts",
                "doi",
            )
        },
        "content_sha256": payload["content_sha256"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    fixture_ok = payload["fixture"]["open_ok"] == payload["fixture"]["file_count"]
    gni_ok = payload["gni"]["status"] != "RUN" or payload["gni"]["open_fail"] == 0
    return 0 if fixture_ok and gni_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
