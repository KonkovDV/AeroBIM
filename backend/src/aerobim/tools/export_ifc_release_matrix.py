"""Build tracker IFC2x3 / IFC4 / IFC4x3 matrix from a schema-suite payload.

Numbers come from the measured run only. fixture_only. Not product accuracy.
Tracker paste format for the 14.08.2026 meeting.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from aerobim.domain.models import CapabilityState, ReportCapabilities, ValidationIssue
from aerobim.tools.benchmark_project_package import (
    SCHEMA_SUITE_DEFAULT_ITERATIONS,
    SCHEMA_SUITE_DEFAULT_WARMUP_ITERATIONS,
    _iteration_request,
    _machine_fingerprint,
    benchmark_schema_suite,
    load_benchmark_pack,
    repo_root,
    schema_suite_pack_paths,
)

_CLAIMS_HEADER = (
    "<!-- claims-lint: allow-file reason="
    '"IFC schema-suite matrix; >90% only as non-claim boundary" -->'
)
_REFUSAL_STATES = frozenset(
    {
        CapabilityState.FAILED,
        CapabilityState.MISSING,
        CapabilityState.NOT_IMPLEMENTED,
        CapabilityState.NOT_VERIFIED,
    }
)
_HONESTY_SKIPPED = frozenset({"clash", "raster", "mep_system_clash", "dwg_dxf"})


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _sequence(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


CLAIM_LEVEL = "fixture_only"
CLAIM_BOUNDARY = (
    "Fixture schema-suite kernel timing and finding counts. "
    "issue_count is not accuracy. Not customer packages. Not TZ >90%."
)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest_rules_and_refusals(
    issues: tuple[ValidationIssue, ...] | list[ValidationIssue],
    capabilities: ReportCapabilities | None,
) -> dict[str, Any]:
    """Last-report rule histogram + honesty refusals. Not product accuracy."""
    fired = Counter(issue.rule_id or "UNKNOWN" for issue in issues)
    severity = Counter(
        issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity)
        for issue in issues
    )
    refusals: list[dict[str, str]] = []
    ran_ok: list[str] = []
    if capabilities is not None:
        for field in fields(type(capabilities)):
            status = getattr(capabilities, field.name)
            state = getattr(status, "status", None)
            if not isinstance(state, CapabilityState):
                continue
            reason = str(getattr(status, "reason", "") or "")
            if state in _REFUSAL_STATES or (
                state is CapabilityState.SKIPPED and field.name in _HONESTY_SKIPPED
            ):
                refusals.append(
                    {
                        "capability": field.name,
                        "status": state.value,
                        "reason": reason[:160],
                    }
                )
            elif state is CapabilityState.OK:
                ran_ok.append(field.name)
    return {
        "rules_fired": dict(sorted(fired.items())),
        "severity_counts": dict(sorted(severity.items())),
        "refusals": refusals,
        "capabilities_ok": ran_ok,
    }


def _product_entity_counts(ifc_path: Path | None) -> dict[str, int]:
    if ifc_path is None or not ifc_path.is_file():
        return {}
    try:
        import ifcopenshell
    except ImportError:
        return {}
    model = ifcopenshell.open(str(ifc_path))
    counts: Counter[str] = Counter()
    for entity in model.by_type("IfcProduct"):
        counts[entity.is_a()] += 1
    return dict(sorted(counts.items()))


def attach_live_digests(matrix: dict[str, Any], pack_paths: list[Path]) -> None:
    """One extra analyze per pack after timing; does not enter p50/p95 windows."""
    from aerobim.core.config.settings import Settings
    from aerobim.core.di.tokens import Tokens
    from aerobim.tools._cli_base import bootstrap_container

    settings = Settings.from_env()
    analyze = bootstrap_container(settings).resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
    by_schema: dict[str, dict[str, Any]] = {}
    for pack_path in pack_paths:
        pack = load_benchmark_pack(pack_path)
        schema = str(pack.ifc_schema or "").upper()
        report = analyze.execute(_iteration_request(pack.request, "digest", 1))
        digest = digest_rules_and_refusals(report.issues, report.capabilities)
        digest["summary_passed"] = report.summary.passed
        digest["product_entities"] = _product_entity_counts(pack.request.ifc_path)
        by_schema[schema] = digest
    for row in matrix.get("rows") or []:
        if not isinstance(row, dict):
            continue
        extra = by_schema.get(str(row.get("schema") or "").upper())
        if extra:
            row.update(extra)


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
        timing = _mapping(metrics.get("timing_ms"))
        issues = _mapping(metrics.get("issue_count"))
        reqs = _mapping(metrics.get("requirement_count"))
        bytes_list = _sequence(metrics.get("ifc_bytes"))
        entities = _sequence(metrics.get("ifc_entity_count"))
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
        "schema_version": "1.1.0",
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
            "Schema-suite packs are IFC+IDS wall Pset fixtures. Clash SKIPPED/FAILED "
            "and raster/MEP SKIPPED/NOT_VERIFIED are honesty, not a silent pass. "
            "DWG native remains FAILED."
        ),
        "tracker_task": (
            "Dmitry 14.08 #2: elements / fired rules / wall-clock / refusals. "
            "summary.passed is Shared-gate, not customer GO."
        ),
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    payload["content_sha256"] = _sha256_bytes(encoded)
    return payload


def _rules_fired_cell(row: dict[str, Any]) -> str:
    fired = row.get("rules_fired")
    if not isinstance(fired, dict) or not fired:
        return "—"
    return ", ".join(f"{key}×{fired[key]}" for key in fired)


def _product_cell(row: dict[str, Any]) -> str:
    products = row.get("product_entities")
    if not isinstance(products, dict) or not products:
        return "—"
    return ", ".join(f"{key}×{products[key]}" for key in products)


_TABLE_OMIT_REFUSALS = frozenset(
    {
        "raster",
        "unit_scale",
        "ifc_schema",
        "dwg_dxf",
        "cv_human_level",
        "mep_system_clash",
        "calculation_correctness",
        "qualified_signature",
    }
)


def _refusals_cell(row: dict[str, Any]) -> str:
    items = row.get("refusals")
    if not isinstance(items, list) or not items:
        return "—"
    parts: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cap = str(item.get("capability") or "")
        if cap in _TABLE_OMIT_REFUSALS:
            continue
        parts.append(f"{cap}={item.get('status')}")
    return ", ".join(parts) if parts else "shared honesty only"


def _passed_cell(row: dict[str, Any]) -> str:
    value = row.get("summary_passed")
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "—"


def _suite_banner(matrix: dict[str, Any]) -> str:
    source = _mapping(matrix.get("source_suite"))
    machine = _mapping(matrix.get("machine"))
    iterations = source.get("iterations")
    warmup = source.get("warmup_iterations")
    python = machine.get("python") or "unknown"
    return (
        f"**suite:** n={iterations} warmup={warmup} python=`{python}`. "
        "Shared-gate `summary.passed` is not Checkpoint GO."
    )


def render_tracker_paste_markdown(matrix: dict[str, Any]) -> str:
    """Compact table for the tracker chat (elements / rules / time / refusals)."""
    lines = [
        "## Tracker paste (Dmitry 14.08 #2)",
        "",
        _suite_banner(matrix),
        "",
        "| Schema | Elements | Rules fired | Findings | passed | p50 ms | p95 ms | Refusals |",
        "|---|---|---|---:|---|---:|---:|---|",
    ]
    for row in matrix.get("rows") or []:
        if not isinstance(row, dict):
            continue
        timing = _mapping(row.get("timing_ms"))
        lines.append(
            "| {schema} | {products} | {fired} | {findings} | {passed} | {p50} | {p95} | {refusals} |".format(
                schema=row.get("schema"),
                products=_product_cell(row),
                fired=_rules_fired_cell(row),
                findings=row.get("findings_emitted"),
                passed=_passed_cell(row),
                p50=timing.get("p50"),
                p95=timing.get("p95"),
                refusals=_refusals_cell(row),
            )
        )
    lines.extend(
        [
            "",
            "Paste-ready. Fixture kernel only. IFC4X3 `ids=failed` is fail-closed "
            "`ifcVersion` (BSI 0101), not a product defect. Not customer accuracy.",
            "",
        ]
    )
    return "\n".join(lines)


def render_ifc_release_matrix_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        _CLAIMS_HEADER,
        "# IFC release matrix (tracker 2.1)",
        "",
        f"**claim_level:** `{matrix.get('claim_level')}`",
        f"**customer_accuracy_not_established:** `{matrix.get('customer_accuracy_not_established')}`",
        "",
        str(matrix.get("claim_boundary") or ""),
        "",
        _suite_banner(matrix),
        "",
        "| Schema | IfcProduct | entities | rules eval | rules fired | findings | passed | p50 ms | p95 ms | max ms | refusals |",
        "|---|---|---:|---:|---|---:|---|---:|---:|---:|---|",
    ]
    for row in matrix.get("rows") or []:
        if not isinstance(row, dict):
            continue
        timing = _mapping(row.get("timing_ms"))
        lines.append(
            "| {schema} | {products} | {ent} | {rules} | {fired} | {findings} | {passed} | {p50} | {p95} | {mx} | {refusals} |".format(
                schema=row.get("schema"),
                products=_product_cell(row),
                ent=row.get("ifc_entity_count"),
                rules=row.get("rules_evaluated"),
                fired=_rules_fired_cell(row),
                findings=row.get("findings_emitted"),
                passed=_passed_cell(row),
                p50=timing.get("p50"),
                p95=timing.get("p95"),
                mx=timing.get("max"),
                refusals=_refusals_cell(row),
            )
        )
    lines.extend(
        [
            "",
            str(matrix.get("refusals_and_degradations_note") or ""),
            "",
            "issue_count / rules fired are fixture findings, **not claimed** product accuracy.",
            "",
            "Shared honesty refusals (all three packs, omitted from the refusals column): "
            "raster skipped, dwg_dxf missing, cv_human_level missing, "
            "mep_system_clash not_verified, calculation_correctness not_implemented, "
            "qualified_signature missing, unit_scale/ifc_schema not_verified. "
            "Clash skipped/failed is listed in the refusals column. Tiny wall fixtures "
            "default to clash=skipped via AEROBIM_CLASH_SKIP_TINY (all-skipped still "
            "fail-closed); geom-init FAILED remains honesty, not a silent pass. "
            "Native DWG is **not claimed** DWG-ready.",
            "",
            render_tracker_paste_markdown(matrix).rstrip(),
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
        path.write_text(text, encoding="utf-8", newline="\n")
    evidence_md.parent.mkdir(parents=True, exist_ok=True)
    evidence_md.write_text(
        render_ifc_release_matrix_markdown(matrix), encoding="utf-8", newline="\n"
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=SCHEMA_SUITE_DEFAULT_ITERATIONS)
    parser.add_argument(
        "--warmup-iterations", type=int, default=SCHEMA_SUITE_DEFAULT_WARMUP_ITERATIONS
    )
    args = parser.parse_args(argv)
    root = repo_root()
    suite = benchmark_schema_suite(
        pack_paths=schema_suite_pack_paths(root),
        iterations=args.iterations,
        warmup_iterations=args.warmup_iterations,
        group_by="schema",
    )
    matrix = build_ifc_release_matrix(cast(dict[str, Any], suite))
    attach_live_digests(matrix, schema_suite_pack_paths(root))
    encoded = json.dumps(
        {key: value for key, value in matrix.items() if key != "content_sha256"},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    matrix["content_sha256"] = _sha256_bytes(encoded)
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
