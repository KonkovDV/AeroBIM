"""Emit BCF structural handoff evidence (T1). CDE import remains NOT_VERIFIED."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.domain.models import (
    ClashResult,
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.bcf3_exporter import export_bcf3
from aerobim.infrastructure.adapters.bcf_consumers import (
    consume_bcf3_zip,
    consume_bcf21_zip,
    verify_bcf_zip_structure,
)
from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf
from aerobim.tools.benchmark_project_package import repo_root


def _sample_report() -> ValidationReport:
    return ValidationReport(
        report_id=uuid4().hex,
        request_id="bcf-structural-handoff",
        ifc_path=Path("handoff.ifc"),
        created_at=datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=(
            ValidationIssue(
                rule_id="IDS-WallHeight",
                severity=Severity.ERROR,
                message="Wall height below minimum",
                category=FindingCategory.IDS_VALIDATION,
                element_guid="2O2Fr$t4X7Zf8NOew3FLOH",
            ),
        ),
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=1,
            error_count=1,
            warning_count=0,
            passed=False,
        ),
        clash_results=(
            ClashResult(
                element_a_guid="clash-a",
                element_b_guid="clash-b",
                clash_type="hard",
                distance=0.02,
                description="Hard clash",
            ),
        ),
    )


def build_bcf_structural_handoff_evidence() -> dict[str, object]:
    report = _sample_report()
    zip_21 = export_bcf(report)
    zip_30 = export_bcf3(report)
    struct_21 = verify_bcf_zip_structure(zip_21)
    struct_30 = verify_bcf_zip_structure(zip_30)
    topics_21 = consume_bcf21_zip(zip_21)
    topics_30 = consume_bcf3_zip(zip_30)
    titles_21 = sorted(t.title for t in topics_21)
    titles_30 = sorted(t.title for t in topics_30)
    consumers_agree = len(topics_21) == len(topics_30) and titles_21 == titles_30

    return {
        "artifact_type": "bcf_structural_handoff",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "structural_only",
        "bcf_21": struct_21.as_dict(),
        "bcf_30": struct_30.as_dict(),
        "consumer_agreement": {
            "topic_count_21": len(topics_21),
            "topic_count_30": len(topics_30),
            "titles_match": titles_21 == titles_30,
            "ok": consumers_agree,
        },
        "structural_ok": struct_21.ok and struct_30.ok and consumers_agree,
        "cde_import": {
            "status": "NOT_VERIFIED",
            "reason": "No independent CDE import log/screenshot hash in evidence pack",
        },
        "allowed_wording": "BCF ZIP structural OK; CDE import not evidenced",
        "forbidden_wording": ["BCF ready for CDE", "CDE interoperable", "production BCF handoff"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify BCF ZIP structure and emit T1 evidence")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Evidence JSON path (default: audit/evidence/bcf-structural-handoff-YYYY-MM-DD.json)",
    )
    args = parser.parse_args()
    payload = build_bcf_structural_handoff_evidence()
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    out = args.output
    if out is None:
        stamp = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        out = repo_root() / "audit" / "evidence" / f"bcf-structural-handoff-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(serialized, encoding="utf-8")
    tmp.replace(out)
    print(serialized)
    if not payload["structural_ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
