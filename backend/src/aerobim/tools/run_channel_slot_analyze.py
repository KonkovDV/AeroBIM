"""Analyze one already-received channel slot. No further Samolet answers.

Writes HTML/JSON/PDF/BCF under ``.local/`` only. Does not stamp fixture_demo.
Does not use demo-seed or REI60 IDS. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.channel_slot_pack import (
    CLAIM_BOUNDARY,
    assemble_slot_inputs,
    assert_slot,
)
from aerobim.domain.check_coverage import coverage_from_report, derive_report_scope
from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO
from aerobim.domain.executive_brief import executive_brief
from aerobim.domain.finding_layer import classify_finding_layer
from aerobim.domain.finding_volume import volume_from_findings
from aerobim.domain.models import DrawingSource, RequirementSource, SourceKind, ValidationRequest
from aerobim.domain.owner_files_inventory import require_local_only_output
from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf
from aerobim.presentation.http.report_html import render_report_html
from aerobim.presentation.http.report_pdf import render_report_pdf_bytes
from aerobim.tools._cli_base import bootstrap_container
from aerobim.tools.benchmark_project_package import repo_root

_DEFAULT_KIT = Path(".local/pack-out/three-addresses")


def _git_sha(repo: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if completed.returncode == 0:
            return completed.stdout.strip()
    except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        return ""
    return ""


def _requirement(
    path: Path | None, *, kind: SourceKind, source_id: str
) -> RequirementSource | None:
    if path is None:
        return None
    if path.suffix.lower() not in {".txt", ".md"}:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")[:50_000]
    return RequirementSource(text=text, path=path, source_kind=kind, source_id=source_id)


def _public_payload(report: Any, *, extra: dict[str, Any]) -> dict[str, Any]:
    data = asdict(report)
    data.pop("ifc_path", None)
    data.pop("ifc_object_key", None)
    issues = []
    for issue in data.get("issues") or ():
        if isinstance(issue, dict):
            issue = dict(issue)
            issue["layer"] = classify_finding_layer(issue)
            issues.append(issue)
    data["issues"] = issues
    data["coverage"] = coverage_from_report(report, scope=derive_report_scope(report)).to_dict(
        report=report
    )
    data["finding_volume"] = volume_from_findings(issues)
    data["executive_brief"] = executive_brief(data)
    data.update(extra)
    return data


def build_request(assembled: dict[str, Any], *, request_id: str) -> ValidationRequest:
    tz = assembled.get("technical_spec_path")
    drawings = tuple(
        DrawingSource(
            text="",
            path=path,
            sheet_id=path.stem[:120],
            format="pdf",
        )
        for path in assembled.get("drawing_paths") or ()
    )
    fallback = RequirementSource(
        text="",
        source_kind=SourceKind.STRUCTURED_TEXT,
        source_id="channel-requirements-via-ids",
    )
    tz_source = _requirement(tz, kind=SourceKind.TECHNICAL_SPECIFICATION, source_id="channel-tz")
    return ValidationRequest(
        request_id=request_id,
        ifc_path=assembled["ifc_path"],
        requirement_source=fallback,
        technical_spec_source=tz_source,
        calculation_source=_requirement(
            assembled.get("calculation_path"),
            kind=SourceKind.CALCULATION,
            source_id="channel-calc",
        ),
        drawing_sources=drawings,
        ids_path=assembled["ids_path"],
        origin="channel_existing_files",
        project_name=str(assembled["slot"]),
        discipline="AR" if "_АР_" in assembled["ifc_path"].name.upper() else "KR",
        stage="PD",
        doc_status="Shared",
        package_inventory_path=assembled.get("inventory_path"),
        require_package_completeness=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", required=True, choices=("pack_a", "pack_b", "pack_c"))
    parser.add_argument("--pack-root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--drawing-limit", type=int, default=8)
    args = parser.parse_args(argv)

    os.environ.setdefault("AEROBIM_CUSTOMER_PACK_LLM_EGRESS", "deny")
    repo = repo_root()
    slot = assert_slot(args.slot)
    pack_root = (
        args.pack_root.resolve()
        if args.pack_root is not None
        else (repo / _DEFAULT_KIT / slot).resolve()
    )
    out = args.out.resolve() if args.out is not None else (repo / ".local" / "pack-out" / slot)
    require_local_only_output(repo, out)
    out.mkdir(parents=True, exist_ok=True)

    assembled = assemble_slot_inputs(
        pack_root, slot=slot, repo=repo, drawing_limit=args.drawing_limit
    )
    inventory_path = out / "package-inventory.json"
    inventory_path.write_text(
        json.dumps(assembled["inventory"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    assembled["inventory_path"] = inventory_path

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    request_id = f"channel-{slot}-{stamp}"
    request = build_request(assembled, request_id=request_id)

    settings = Settings.from_env()
    container = bootstrap_container(settings)
    use_case: AnalyzeProjectPackageUseCase = container.resolve(
        Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE
    )
    report = use_case.execute(request)

    extra = {
        "claim_boundary": CLAIM_BOUNDARY,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "waiting_for_samolet": False,
        "fixture_demo": False,
        "slot": slot,
        "git_sha": _git_sha(repo),
        "signoff_profile": settings.signoff_profile,
        "ids_kind": "unsigned_ifc2x3_presence_not_customer_profile",
        "primary_ifc_name": assembled["ifc_path"].name,
        "ifc_over_spf_cap": assembled["ifc_over_spf_cap"],
        "native_rejected": assembled["native_rejected"],
        "drawing_count": len(assembled["drawing_paths"]),
        "hides_negative": False,
        "is_accuracy": False,
        "is_sla": False,
    }
    public = _public_payload(report, extra=extra)
    (out / "report.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out / "report.html").write_text(render_report_html(report.report_id, public), encoding="utf-8")
    (out / "report.pdf").write_bytes(render_report_pdf_bytes(report.report_id, public))
    (out / "findings.bcfzip").write_bytes(export_bcf(report))
    manifest = {
        "slot": slot,
        "report_id": report.report_id,
        "request_id": report.request_id,
        "passed": report.summary.passed,
        "issue_count": report.summary.issue_count,
        "fixture_demo": False,
        "waiting_for_samolet": False,
        "exports": ["html", "json", "pdf", "bcf"],
        **extra,
    }
    (out / "run-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "slot": slot,
                "report_id": report.report_id,
                "issue_count": report.summary.issue_count,
                "passed": report.summary.passed,
                "out": str(out),
                "fixture_demo": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
