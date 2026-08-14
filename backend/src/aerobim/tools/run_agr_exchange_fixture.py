"""Run AGR exchange-shape checks on a fixture manifest. No new port."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.agr_exchange_checks import (
    CLAIM_BOUNDARY,
    collect_agr_exchange_issues,
    collect_agr_tep_xml_issues,
    collect_agr_vedomost_xsd_issues,
)
from aerobim.tools.benchmark_project_package import _machine_fingerprint, repo_root

CLAIM_LEVEL = "agr_exchange_fixture"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_header_and_body(path: Path) -> tuple[str, str, int]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    return text[: 64 * 1024], text, len(raw)


def run_manifest(manifest_path: Path, *, root: Path) -> dict[str, Any]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases_raw = payload.get("cases") or ()
    rows: list[dict[str, Any]] = []
    for entry in cases_raw:
        if not isinstance(entry, dict):
            continue
        rel = str(entry.get("ifc") or "")
        ifc_path = (root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
        declared = str(entry.get("declared_filename") or ifc_path.name)
        header_text, body_text, size_bytes = _read_header_and_body(ifc_path)
        issues = collect_agr_exchange_issues(
            filename=declared,
            header_text=header_text,
            body_text=body_text,
            size_bytes=size_bytes,
        )
        if entry.get("require_tep_xml"):
            tep_rel = str(entry.get("tep_xml") or "").strip()
            tep_path = (root / tep_rel).resolve() if tep_rel else None
            expected_root = str(entry.get("tep_expected_root") or "").strip() or None
            issues = issues + collect_agr_tep_xml_issues(
                xml_path=tep_path,
                expected_root=expected_root,
            )
        if entry.get("require_vedomost_xsd"):
            ved_rel = str(entry.get("vedomost_xml") or "").strip()
            xsd_rel = str(entry.get("vedomost_xsd") or "").strip()
            ved_path = (root / ved_rel).resolve() if ved_rel else None
            xsd_path = (
                (root / xsd_rel).resolve()
                if xsd_rel
                else root / "samples" / "agr" / "dgp" / "Vedomost_AGR_VED_NEW.xsd"
            )
            issues = issues + collect_agr_vedomost_xsd_issues(
                xml_path=ved_path,
                xsd_path=xsd_path,
            )
        expected = tuple(str(item) for item in (entry.get("expect_rule_ids") or ()))
        observed = tuple(issue.rule_id for issue in issues)
        rows.append(
            {
                "id": str(entry.get("id") or ifc_path.stem),
                "ifc": rel.replace("\\", "/"),
                "declared_filename": declared,
                "size_bytes": size_bytes,
                "expect_rule_ids": list(expected),
                "observed_rule_ids": list(observed),
                "expect_matched": set(expected) == set(observed),
            }
        )
    report_body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "agr_exchange_fixture",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "machine": _machine_fingerprint(),
        "manifest": manifest_path.resolve().relative_to(root).as_posix(),
        "summary": {
            "case_count": len(rows),
            "cases_matching_expect": sum(1 for row in rows if row["expect_matched"]),
        },
        "cases": rows,
    }
    encoded = json.dumps(
        report_body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    report_body["content_sha256"] = _sha256_bytes(encoded)
    return report_body


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        '<!-- claims-lint: allow-file reason="AGR exchange fixture; not moscow_agr profile" -->',
        "---",
        'title: "AGR exchange-shape fixture (class 1)"',
        f"date: {str(payload.get('generated_at') or '')[:10]}",
        f"claim_level: {payload.get('claim_level')}",
        "claim_boundary: >-",
        f"  {payload.get('claim_boundary')}",
        "---",
        "",
        "# AGR exchange-shape fixture",
        "",
        "IFC4 + ReferenceView + no `IfcBuildingElementProxy` + five-field filename + ",
        "500 MB cap + TEP XML sidecar + official ДГП Vedomost XSD. **Not** the frozen ",
        "`moscow_agr` profile (no УКЭП, CRS, MSSK). Not a Samolet pack.",
        "",
        f"- cases: **{summary.get('case_count')}**",
        f"- matching expect: **{summary.get('cases_matching_expect')}**",
        f"- content_sha256: `{payload.get('content_sha256')}`",
        "",
        "| id | expect | observed | match |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload.get("cases") or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            f"| `{row.get('id')}` | `{row.get('expect_rule_ids')}` | "
            f"`{row.get('observed_rule_ids')}` | {row.get('expect_matched')} |"
        )
    lines.extend(
        [
            "",
            "```bash",
            "cd backend",
            "python -m aerobim.tools.run_agr_exchange_fixture",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args(argv)
    root = repo_root()
    manifest = args.manifest or (root / "samples" / "agr" / "exchange-fixture-manifest.json")
    payload = run_manifest(manifest, root=root)
    out_dir = root / "artifacts" / "agr-exchange"
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (out_dir / "agr-exchange.json").write_text(text, encoding="utf-8")
    (root / "docs" / "evidence" / "agr-exchange-2026-08.json").write_text(text, encoding="utf-8")
    (root / "docs" / "evidence" / "agr-exchange-2026-08.md").write_text(
        render_markdown(payload), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    mismatched = [row for row in payload["cases"] if not row["expect_matched"]]
    return 1 if mismatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
