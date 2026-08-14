"""Bundle the honest maximum for ТР-11/14/15 / RT-001–003 without Samolet files.

Writes artifacts only by default. Does not mark blockers CLOSED. Does not
open GPLv3 IFC-Bench trees. Optional duplex IfcClash is off unless flagged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.tz_proxy_constructs import (
    CLAIM_BOUNDARY,
    CLAIM_LEVEL,
    construct_validity_frame,
    geometric_clash_proxy,
    jurisdiction_ids_proxy,
    typical_remark_taxonomy_proxy,
    tz_row_proxy_map,
)
from aerobim.infrastructure.adapters.ifc_clash_detector import IfcClashDetector
from aerobim.tools.benchmark_project_package import _machine_fingerprint, repo_root
from aerobim.tools.export_moexp_ids_coverage import discover_ids

DUPLEX_ARC_REL = ".local/ifc-bench-v2/projects/duplex/arc.ifc"
DUPLEX_MEP_REL = ".local/ifc-bench-v2/projects/duplex/mep.ifc"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _ci_environment() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true"


def _clash_row(
    *,
    label: str,
    status: str,
    reason: str | None = None,
    clash_count: int | None = None,
    elapsed_ms: float | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "label": label,
        "status": status,
        "closes_rt003": False,
        "mep_system_clash": "NOT_VERIFIED",
        "geometry_verified": False,
    }
    if reason is not None:
        row["reason"] = reason
    if clash_count is not None:
        row["clash_count"] = clash_count
    if elapsed_ms is not None:
        row["elapsed_ms"] = round(elapsed_ms, 3)
    if extra:
        row.update(extra)
    return row


def run_planted_clash(repo: Path) -> dict[str, Any]:
    path = repo / "samples" / "ifc" / "clash-two-overlapping-boxes.ifc"
    extra = {"path": path.relative_to(repo).as_posix(), "engine": "ifcclash"}
    if not path.is_file():
        return _clash_row(label="planted_overlapping_boxes", status="MISSING", extra=extra)
    started = perf_counter()
    try:
        results = IfcClashDetector().detect(path)
    except ClashCapabilityError as exc:
        return _clash_row(
            label="planted_overlapping_boxes",
            status=exc.status.upper(),
            reason=exc.reason,
            elapsed_ms=(perf_counter() - started) * 1000.0,
            extra=extra,
        )
    return _clash_row(
        label="planted_overlapping_boxes",
        status="RUN",
        clash_count=len(results),
        elapsed_ms=(perf_counter() - started) * 1000.0,
        extra={
            **extra,
            "note": (
                "Tiny fixture; zero IfcClash hits is not a clean-model claim. "
                "Measured L2 AABB P/R lives in clash-measurement-slice-2026-08."
            ),
        },
    )


def run_federated_duplex(repo: Path) -> dict[str, Any]:
    arc = repo / DUPLEX_ARC_REL
    mep = repo / DUPLEX_MEP_REL
    extra = {
        "path_a": DUPLEX_ARC_REL,
        "path_b": DUPLEX_MEP_REL,
        "engine": "ifcclash",
        "license": "public_ifc_bench_non_gpl",
    }
    if not arc.is_file() or not mep.is_file():
        return _clash_row(
            label="duplex_arc_vs_mep",
            status="SKIPPED",
            reason="IFC-Bench duplex files not on disk (gitignored .local/)",
            extra=extra,
        )
    started = perf_counter()
    try:
        results = IfcClashDetector().detect_between(arc, mep)
    except ClashCapabilityError as exc:
        return _clash_row(
            label="duplex_arc_vs_mep",
            status=exc.status.upper(),
            reason=exc.reason,
            elapsed_ms=(perf_counter() - started) * 1000.0,
            extra=extra,
        )
    return _clash_row(
        label="duplex_arc_vs_mep",
        status="RUN",
        clash_count=len(results),
        elapsed_ms=(perf_counter() - started) * 1000.0,
        extra={
            **extra,
            "note": ("Open federated pair, no coordinator BCF gold. Hits ≠ MEP delivered."),
        },
    )


def moexp_live_pointer(repo: Path) -> dict[str, Any]:
    pointer = jurisdiction_ids_proxy()
    pack = repo / pointer["ids_pack_rel"]
    ids = discover_ids(pack) if pack.is_dir() else []
    pointer["ids_file_count"] = len(ids)
    coverage_path = repo / str(pointer["coverage_evidence"])
    if coverage_path.is_file():
        try:
            coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            coverage = {}
        summary = coverage.get("summary") if isinstance(coverage, dict) else None
        if isinstance(summary, dict):
            pointer["specification_count"] = summary.get("specification_count")
            pointer["ids_file_count_from_coverage"] = summary.get("ids_file_count")
            pointer["unsupported_from_coverage"] = summary.get("unsupported")
    return pointer


def build_payload(
    *,
    repo: Path,
    include_open_federated: bool = False,
) -> dict[str, Any]:
    clashes = [run_planted_clash(repo)]
    if include_open_federated:
        clashes.append(run_federated_duplex(repo))
    else:
        clashes.append(
            _clash_row(
                label="duplex_arc_vs_mep",
                status="SKIPPED",
                reason="pass --include-open-federated to run IfcClash on local duplex",
                extra={"path_a": DUPLEX_ARC_REL, "path_b": DUPLEX_MEP_REL},
            )
        )
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "tz_proxy_rehearsal",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "machine": _machine_fingerprint(),
        "ci": _ci_environment(),
        "checkpoint": "NO_GO",
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "construct_validity": construct_validity_frame(),
        "tz_rows": tz_row_proxy_map(),
        "rt001_typical_remark_taxonomy": typical_remark_taxonomy_proxy(),
        "rt002_jurisdiction_ids": moexp_live_pointer(repo),
        "rt003_geometric_clash": {
            **geometric_clash_proxy(),
            "runs": clashes,
        },
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def render_markdown(payload: dict[str, Any]) -> str:
    validity = payload.get("construct_validity") or {}
    taxonomy = payload.get("rt001_typical_remark_taxonomy") or {}
    ids = payload.get("rt002_jurisdiction_ids") or {}
    clash = payload.get("rt003_geometric_clash") or {}
    lines = [
        '<!-- claims-lint: allow-file reason="TZ proxy rehearsal; RT blockers stay OPEN" -->',
        "---",
        'title: "TZ proxy rehearsal without Samolet files"',
        f"date: {str(payload.get('generated_at') or '')[:10]}",
        f"claim_level: {payload.get('claim_level')}",
        "claim_boundary: >-",
        f"  {payload.get('claim_boundary')}",
        "closes_rt001: false",
        "closes_rt002: false",
        "closes_rt003: false",
        "---",
        "",
        "# TZ proxy rehearsal (без корпуса «Самолёта»)",
        "",
        f"- checkpoint: **{payload.get('checkpoint')}**",
        f"- closes_rt001: **{payload.get('closes_rt001')}**",
        f"- closes_rt002: **{payload.get('closes_rt002')}**",
        f"- closes_rt003: **{payload.get('closes_rt003')}**",
        f"- theory: {validity.get('theory')}",
        f"- MOEXP IDS files on disk: **{ids.get('ids_file_count')}**",
        f"- MOEXP specs (coverage artifact): **{ids.get('specification_count')}**",
        f"- customer_signed: **{ids.get('customer_signed')}**",
        f"- samolet_alias: **{ids.get('samolet_alias')}**",
        f"- mep_system_clash: **{clash.get('mep_system_clash')}**",
        f"- content_sha256: `{payload.get('content_sha256')}`",
        "",
        "## Typical-remark coverage (Exp B, not precision)",
        "",
        "| catalog | n | detectable | share |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in taxonomy.get("catalogs") or []:
        lines.append(
            f"| {row.get('id')} | {row.get('n')} | {row.get('detectable')} | "
            f"{row.get('detectable_share')} |"
        )
    lines.extend(
        [
            "",
            "## IfcClash runs",
            "",
            "| label | status | clash_count | ms |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for row in clash.get("runs") or []:
        lines.append(
            f"| {row.get('label')} | {row.get('status')} | "
            f"{row.get('clash_count', '')} | {row.get('elapsed_ms', '')} |"
        )
    lines.extend(["", f"Claim boundary: {payload.get('claim_boundary')}", ""])
    return "\n".join(lines)


def write_payload(
    payload: dict[str, Any],
    *,
    artifacts_json: Path,
    artifacts_md: Path | None = None,
) -> None:
    artifacts_json.parent.mkdir(parents=True, exist_ok=True)
    artifacts_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if artifacts_md is not None:
        artifacts_md.parent.mkdir(parents=True, exist_ok=True)
        artifacts_md.write_text(render_markdown(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Honest TZ proxy rehearsal without Samolet customer files."
    )
    parser.add_argument(
        "--include-open-federated",
        action="store_true",
        help="Run IfcClash on local IFC-Bench duplex (may be slow). Still NOT_VERIFIED.",
    )
    parser.add_argument(
        "--write-docs-evidence",
        action="store_true",
        help="Also write docs/evidence (default: artifacts/ only).",
    )
    args = parser.parse_args(argv)
    root = repo_root()
    payload = build_payload(repo=root, include_open_federated=args.include_open_federated)
    write_payload(
        payload,
        artifacts_json=root / "artifacts" / "tz-proxy-rehearsal" / "latest.json",
        artifacts_md=root / "artifacts" / "tz-proxy-rehearsal" / "latest.md",
    )
    if args.write_docs_evidence:
        write_payload(
            payload,
            artifacts_json=root / "docs" / "evidence" / "tz-proxy-rehearsal-latest.json",
            artifacts_md=root / "docs" / "evidence" / "tz-proxy-rehearsal-2026-08.md",
        )
    print(
        json.dumps(
            {
                "checkpoint": payload["checkpoint"],
                "closes_rt001": payload["closes_rt001"],
                "closes_rt002": payload["closes_rt002"],
                "closes_rt003": payload["closes_rt003"],
                "ids_file_count": payload["rt002_jurisdiction_ids"].get("ids_file_count"),
                "clash_runs": [
                    {"label": row.get("label"), "status": row.get("status")}
                    for row in payload["rt003_geometric_clash"].get("runs") or []
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
