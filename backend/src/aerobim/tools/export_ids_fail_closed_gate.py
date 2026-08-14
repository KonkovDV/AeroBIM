"""Export IDS fail-closed gate evidence (brief 0.4 / tracker 14.08).

Proves FILE_SCHEMA vs IDS ifcVersion is checked by AeroBIM, not IfcTester.
Walks vendored buildingSMART IDS TestCases for schema mismatches (no invented
counts). Live IfcTester run is limited to the canonical metadata case 0101
unless ``--with-ifctester`` is passed.

Needed for demo 20.08: silent skip in our fail-closed contour is closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.domain.ids_schema_gate import (
    RULE_IFC_VERSION,
    RULE_SKIPPED,
    collect_schema_mismatches,
    parse_ids_specification_versions,
    parse_ifc_file_schema,
)
from aerobim.tools.benchmark_project_package import _machine_fingerprint, repo_root

CLAIM_LEVEL = "ids_fail_closed_gate"
CLAIM_BOUNDARY = (
    "AeroBIM fail-closes IDS ifcVersion vs IFC FILE_SCHEMA and IfcTester SKIPPED "
    "specs. buildingSMART case 0101 documents version-as-metadata; we disagree "
    "on purpose. Not product accuracy. Not CIM compliance. Not Samolet acceptance."
)
CASE_0101 = "pass-specification_version_is_purely_metadata_and_does_not_impact_pass_or_fail_result"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _as_repo_path(raw: str, root: Path | None = None) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return ((root or repo_root()) / path).resolve()


def default_cases_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "samples" / "ids" / "buildingsmart-testcases" / "cases"


def discover_bsi_pairs(cases_dir: Path, *, root: Path | None = None) -> list[dict[str, str]]:
    base = (root or repo_root()).resolve()
    pairs: list[dict[str, str]] = []
    for ids_path in sorted(cases_dir.glob("*/*.ids")):
        stem = ids_path.stem
        ifc_path = ids_path.with_suffix(".ifc")
        if not ifc_path.is_file():
            continue
        if stem.startswith("pass-"):
            expected = "pass"
        elif stem.startswith("fail-"):
            expected = "fail"
        else:
            expected = "unknown"
        pairs.append(
            {
                "case_id": stem,
                "case_dir": ids_path.parent.name,
                "ids_path": ids_path.resolve().relative_to(base).as_posix(),
                "ifc_path": ifc_path.resolve().relative_to(base).as_posix(),
                "bsi_filename_expected": expected,
            }
        )
    return pairs


def schema_gate_row(pair: dict[str, str], *, root: Path | None = None) -> dict[str, Any]:
    ids_path = _as_repo_path(pair["ids_path"], root)
    ifc_path = _as_repo_path(pair["ifc_path"], root)
    ids_xml = ids_path.read_text(encoding="utf-8", errors="replace")
    header = ifc_path.read_bytes()[: 64 * 1024].decode("utf-8", errors="replace")
    model_schema = parse_ifc_file_schema(header)
    specs = parse_ids_specification_versions(ids_xml)
    mismatches = collect_schema_mismatches(model_schema=model_schema, specs=specs)
    return {
        "case_id": pair["case_id"],
        "case_dir": pair["case_dir"],
        "bsi_filename_expected": pair["bsi_filename_expected"],
        "model_schema": model_schema,
        "spec_count": len(specs),
        "mismatch_count": len(mismatches),
        "mismatch_specs": [
            {
                "name": item.spec_name,
                "ids_versions": list(item.ids_versions),
                "model_schema": item.model_schema,
            }
            for item in mismatches
        ],
        "ids_sha256": _sha256_file(ids_path),
        "ifc_sha256": _sha256_file(ifc_path),
    }


def run_ifctester_case(ids_path: Path, ifc_path: Path) -> dict[str, Any]:
    from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator

    started = perf_counter()
    issues = IfcTesterIdsValidator().validate(ids_path, ifc_path)
    elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
    version_hits = [issue for issue in issues if issue.rule_id == RULE_IFC_VERSION]
    skipped_hits = [issue for issue in issues if issue.rule_id == RULE_SKIPPED]
    return {
        "issue_count": len(issues),
        "elapsed_ms": elapsed_ms,
        "has_ifc_version_error": bool(version_hits),
        "has_skipped_error": bool(skipped_hits),
        "version_messages": [issue.message[:240] for issue in version_hits[:5]],
        "skipped_messages": [issue.message[:240] for issue in skipped_hits[:5]],
        "rule_ids": sorted({issue.rule_id for issue in issues}),
    }


def build_payload(
    *,
    root: Path,
    with_ifctester: bool = False,
) -> dict[str, Any]:
    cases_dir = default_cases_dir(root)
    pairs = discover_bsi_pairs(cases_dir, root=root)
    gate_rows = [schema_gate_row(pair, root=root) for pair in pairs]
    mismatched = [row for row in gate_rows if int(row["mismatch_count"]) > 0]
    pass_expected_mismatched = [row for row in mismatched if row["bsi_filename_expected"] == "pass"]
    fail_expected_mismatched = [row for row in mismatched if row["bsi_filename_expected"] == "fail"]

    live: dict[str, Any] = {}
    case_0101 = next((pair for pair in pairs if pair["case_id"] == CASE_0101), None)
    if case_0101 is not None:
        live["case_0101"] = {
            **case_0101,
            **run_ifctester_case(
                _as_repo_path(case_0101["ids_path"], root),
                _as_repo_path(case_0101["ifc_path"], root),
            ),
        }

    ifctester_rows: list[dict[str, Any]] = []
    if with_ifctester:
        for pair in pairs:
            ifctester_rows.append(
                {
                    "case_id": pair["case_id"],
                    **run_ifctester_case(
                        _as_repo_path(pair["ids_path"], root),
                        _as_repo_path(pair["ifc_path"], root),
                    ),
                }
            )

    body = {
        "schema_version": "1.0.0",
        "artifact_type": "ids_fail_closed_gate",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "cli_flags": {"with_ifctester": with_ifctester},
        "machine": _machine_fingerprint(),
        "source": {
            "cases_dir": "samples/ids/buildingsmart-testcases/cases",
            "license": "CC-BY-ND-4.0",
            "canonical_case": CASE_0101,
        },
        "summary": {
            "bsi_pairs_discovered": len(pairs),
            "schema_mismatch_pairs": len(mismatched),
            "pass_filename_with_schema_mismatch": len(pass_expected_mismatched),
            "fail_filename_with_schema_mismatch": len(fail_expected_mismatched),
            "case_0101_has_ifc_version_error": bool(
                live.get("case_0101", {}).get("has_ifc_version_error")
            ),
        },
        "pass_filename_schema_mismatches": [
            {
                "case_id": row["case_id"],
                "case_dir": row["case_dir"],
                "model_schema": row["model_schema"],
                "mismatch_specs": row["mismatch_specs"],
            }
            for row in pass_expected_mismatched
        ],
        "live_ifctester": live,
        "ifctester_all_cases": ifctester_rows,
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    body["content_sha256"] = _sha256_bytes(encoded)
    return body


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    live = (payload.get("live_ifctester") or {}).get("case_0101") or {}
    rows = payload.get("pass_filename_schema_mismatches") or []
    lines = [
        '<!-- claims-lint: allow-file reason="IDS fail-closed evidence; BSI case names are measurements not product claims" -->',
        "---",
        'title: "IDS fail-closed gate (ifcVersion vs FILE_SCHEMA)"',
        f"date: {str(payload.get('generated_at') or '')[:10]}",
        "claim_level: ids_fail_closed_gate",
        "claim_boundary: >-",
        f"  {payload.get('claim_boundary')}",
        "---",
        "",
        "# IDS fail-closed — silent skip closed",
        "",
        "IfcTester records `is_ifc_version` but still executes the spec",
        "(`should_filter_version` defaults to false). buildingSMART case 0101",
        "says version is metadata. AeroBIM emits `AEROBIM-IDS-IFC-VERSION`",
        "and treats SKIPPED specs as FAILED under the IDS contour.",
        "",
        "## Measured",
        "",
        f"- BSI pairs discovered: **{summary.get('bsi_pairs_discovered')}**",
        f"- Schema-mismatch pairs: **{summary.get('schema_mismatch_pairs')}**",
        f"- `pass-*` filename + schema mismatch: **{summary.get('pass_filename_with_schema_mismatch')}**",
        f"- Case 0101 `AEROBIM-IDS-IFC-VERSION`: **{summary.get('case_0101_has_ifc_version_error')}**",
        f"- content_sha256: `{payload.get('content_sha256')}`",
        "",
        "## Canonical live case 0101",
        "",
        f"- issues: {live.get('issue_count')}",
        f"- elapsed_ms: {live.get('elapsed_ms')}",
        f"- rule_ids: {live.get('rule_ids')}",
        "",
        "## `pass-*` cases our gate fails (intentional)",
        "",
        "| case_id | dir | FILE_SCHEMA |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row.get('case_id')}` | {row.get('case_dir')} | `{row.get('model_schema')}` |"
        )
    lines.extend(
        [
            "",
            "Labeled in `samples/ids/buildingsmart-testcases/AEROBIM_FAIL_CLOSED_DIVERGENCES.json`.",
            "Do not treat this list as product accuracy.",
            "",
            "```bash",
            "cd backend",
            "python -m aerobim.tools.export_ids_fail_closed_gate",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_evidence(payload: dict[str, Any], *, evidence_json: Path, evidence_md: Path) -> None:
    evidence_json.parent.mkdir(parents=True, exist_ok=True)
    evidence_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    evidence_md.write_text(render_markdown(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-ifctester",
        action="store_true",
        help="Run IfcTester on every BSI pair (slow). Default: schema-gate all + live 0101.",
    )
    args = parser.parse_args(argv)
    root = repo_root()
    payload = build_payload(root=root, with_ifctester=bool(args.with_ifctester))
    write_evidence(
        payload,
        evidence_json=root / "docs" / "evidence" / "ids-fail-closed-2026-08.json",
        evidence_md=root / "docs" / "evidence" / "ids-fail-closed-2026-08.md",
    )
    artifacts = root / "artifacts" / "ids-fail-closed"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "ids-fail-closed-2026-08.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload.get("summary"), ensure_ascii=False, indent=2))
    print("content_sha256", payload.get("content_sha256"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
