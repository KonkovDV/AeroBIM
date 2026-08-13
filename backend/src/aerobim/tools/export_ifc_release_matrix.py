"""Build tracker IFC2x3 / IFC4 / IFC4x3 matrix from a schema-suite payload.

Numbers come from the measured run only. fixture_only. Not product accuracy.
Needed for tracker meeting 14.08.2026.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from aerobim.tools.benchmark_project_package import (
    SCHEMA_SUITE_DEFAULT_ITERATIONS,
    SCHEMA_SUITE_DEFAULT_WARMUP_ITERATIONS,
    _machine_fingerprint,
    benchmark_schema_suite,
    repo_root,
    schema_suite_pack_paths,
)

CLAIM_LEVEL = "fixture_only"
CLAIM_BOUNDARY = (
    "Fixture schema-suite kernel timing and finding counts. "
    "issue_count is not accuracy. Not customer packages. Not TZ >90%."
)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def build_ifc_release_matrix(suite_payload: dict[str, Any]) -> dict[str, Any]:
    grouped = suite_payload.get("grouped")
    by_schema: dict[str, Any] = {}
    if isinstance(grouped, dict) and isinstance(grouped.get("by_schema"), dict):
        by_schema = cast(dict[str, Any], grouped["by_schema"])

    rows: list[dict[str, Any]] = []
    for schema in ("IFC2X3", "IFC4", "IFC4X3"):
        metrics = by_schema.get(schema)
        if not isinstance(metrics, dict):
            continue
        timing = metrics.get("timing_ms") if isinstance(metrics.get("timing_ms"), dict) else {}
        issues = metrics.get("issue_count") if isinstance(metrics.get("issue_count"), dict) else {}
        reqs = (
            metrics.get("requirement_count")
            if isinstance(metrics.get("requirement_count"), dict)
            else {}
        )
        bytes_list = metrics.get("ifc_bytes") if isinstance(metrics.get("ifc_bytes"), list) else []
        entities = (
            metrics.get("ifc_entity_count")
            if isinstance(metrics.get("ifc_entity_count"), list)
            else []
        )
        rows.append(
            {
                "schema": schema,
                "pack_count": metrics.get("pack_count"),
                "ifc_bytes": bytes_list[0] if bytes_list else None,
                "ifc_entity_count": entities[0] if entities else None,
                "rules_evaluated": reqs.get("last"),
                "findings_emitted": issues.get("last"),
                "timing_ms": {
                    "p50": timing.get("p50_ms"),
                    "p95": timing.get("p95_ms"),
                    "max": timing.get("max_ms"),
                    "spike_max_over_p50": timing.get("spike_ratio_max_over_p50"),
                },
                "pset_name_mismatch_policy": (
                    "Raised as ValidationIssue (ambiguous Pset alignment), never silent skip"
                ),
            }
        )

    payload = {
        "artifact_type": "ifc_release_matrix",
        "schema_version": "1.0.0",
        "claim_level": CLAIM_LEVEL,
        "customer_accuracy_not_established": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "machine": _machine_fingerprint(),
        "source_suite": {
            "generated_at": suite_payload.get("generated_at"),
            "iterations": suite_payload.get("iterations"),
            "warmup_iterations": suite_payload.get("warmup_iterations"),
        },
        "rows": rows,
        "refusals_and_degradations_note": (
            "Schema-suite packs are IFC+IDS wall Pset fixtures. Capability SKIPPED "
            "(clash/raster/MEP) is honesty, not a silent pass. DWG native remains FAILED."
        ),
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    payload["content_sha256"] = _sha256_bytes(encoded)
    return payload


def render_ifc_release_matrix_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# IFC release matrix (tracker 2.1)",
        "",
        f"**claim_level:** `{matrix.get('claim_level')}`",
        f"**customer_accuracy_not_established:** `{matrix.get('customer_accuracy_not_established')}`",
        "",
        str(matrix.get("claim_boundary") or ""),
        "",
        "| Schema | entities | bytes | rules evaluated | findings emitted | p50 ms | p95 ms | max ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in matrix.get("rows") or []:
        if not isinstance(row, dict):
            continue
        timing = row.get("timing_ms") if isinstance(row.get("timing_ms"), dict) else {}
        lines.append(
            "| {schema} | {ent} | {nbytes} | {rules} | {findings} | {p50} | {p95} | {mx} |".format(
                schema=row.get("schema"),
                ent=row.get("ifc_entity_count"),
                nbytes=row.get("ifc_bytes"),
                rules=row.get("rules_evaluated"),
                findings=row.get("findings_emitted"),
                p50=timing.get("p50"),
                p95=timing.get("p95"),
                mx=timing.get("max"),
            )
        )
    lines.extend(
        [
            "",
            str(matrix.get("refusals_and_degradations_note") or ""),
            "",
            f"Generated at: `{matrix.get('generated_at')}`",
            f"content_sha256: `{matrix.get('content_sha256')}`",
            f"machine: `{json.dumps(matrix.get('machine'), ensure_ascii=False)}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_ifc_release_matrix(
    matrix: dict[str, Any],
    *,
    artifacts_json: Path,
    evidence_json: Path,
    evidence_md: Path,
) -> None:
    text = json.dumps(matrix, ensure_ascii=False, indent=2) + "\n"
    for path in (artifacts_json, evidence_json):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    evidence_md.parent.mkdir(parents=True, exist_ok=True)
    evidence_md.write_text(render_ifc_release_matrix_markdown(matrix), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=SCHEMA_SUITE_DEFAULT_ITERATIONS)
    parser.add_argument("--warmup-iterations", type=int, default=SCHEMA_SUITE_DEFAULT_WARMUP_ITERATIONS)
    args = parser.parse_args(argv)
    root = repo_root()
    suite = benchmark_schema_suite(
        pack_paths=schema_suite_pack_paths(root),
        iterations=args.iterations,
        warmup_iterations=args.warmup_iterations,
        group_by="schema",
    )
    matrix = build_ifc_release_matrix(cast(dict[str, Any], suite))
    write_ifc_release_matrix(
        matrix,
        artifacts_json=root / "artifacts" / "ifc-release-matrix.json",
        evidence_json=root / "docs" / "evidence" / "ifc-release-matrix-2026-08.json",
        evidence_md=root / "docs" / "evidence" / "ifc-release-matrix-2026-08.md",
    )
    print(json.dumps(matrix, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
