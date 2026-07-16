"""Audit traceability coverage on a persisted validation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.infrastructure.di.bootstrap import bootstrap_container


def audit_report_traceability(report_id: str, storage_dir: Path | None = None) -> dict[str, object]:
    settings = Settings.from_env()
    if storage_dir is not None:
        from dataclasses import replace

        settings = replace(settings, storage_dir=storage_dir.resolve())

    container = bootstrap_container(settings)
    store = container.resolve(Tokens.AUDIT_REPORT_STORE)
    report = store.get(report_id)
    if report is None:
        raise FileNotFoundError(f"Report not found: {report_id}")

    total = len(report.issues)
    if total == 0:
        return {
            "artifact_type": "issue_traceability_audit",
            "report_id": report_id,
            "issue_count": 0,
            "traceable_count": 0,
            "traceability_ratio": 1.0,
            "pass_threshold_0_90": True,
        }

    traceable = 0
    per_issue: list[dict[str, object]] = []
    for issue in report.issues:
        has_guid = bool(issue.element_guid)
        # Provenance may stamp source_id="unspecified"; that is not a real anchor.
        raw_source = (issue.source_id or "").strip()
        placeholders = {"unspecified", "unknown", "n/a"}
        has_source = bool(raw_source) and raw_source.lower() not in placeholders
        has_zone = issue.problem_zone is not None
        ok = has_guid or has_source or has_zone
        if ok:
            traceable += 1
        per_issue.append(
            {
                "rule_id": issue.rule_id,
                "traceable": ok,
                "element_guid": issue.element_guid,
                "source_id": issue.source_id,
                "has_problem_zone": has_zone,
            }
        )

    ratio = round(traceable / total, 4)
    return {
        "artifact_type": "issue_traceability_audit",
        "schema_version": "1.0.0",
        "report_id": report_id,
        "issue_count": total,
        "traceable_count": traceable,
        "traceability_ratio": ratio,
        "pass_threshold_0_90": ratio >= 0.90,
        "issues": per_issue,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit issue traceability on a stored report")
    parser.add_argument("--report-id", required=True)
    parser.add_argument("--storage-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    payload = audit_report_traceability(args.report_id, args.storage_dir)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(args.output)
    else:
        print(serialized)

    if not payload.get("pass_threshold_0_90"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
