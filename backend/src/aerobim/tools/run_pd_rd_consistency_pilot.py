"""Narrow synthetic PD/RD consistency pilot: IFC wall Width vs drawing thickness.

Corpus is synthetic. Not a customer pack, not CDE import, not product accuracy.
LLM never writes summary.passed (ADR-001) and cannot assign expert status.

Documented command (from backend/):

    python -m aerobim.tools.ensure_pd_rd_pilot_drawings
    python -m aerobim.tools.run_pd_rd_consistency_pilot --variant defect --out var/pd-rd-defect
    python -m aerobim.tools.run_pd_rd_consistency_pilot --variant clean --out var/pd-rd-clean
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

_REPO = Path(__file__).resolve().parents[4]
_SRC = _REPO / "backend" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from aerobim.core.config.settings import Settings  # noqa: E402
from aerobim.core.di.tokens import Tokens  # noqa: E402
from aerobim.domain.checkpoint import CHECKPOINT  # noqa: E402
from aerobim.domain.drawing_ifc_consistency import (  # noqa: E402
    CLAIM_BOUNDARY,
    RULE_AMBIGUOUS,
    RULE_ID,
    RULE_INCOMPLETE,
    RULE_PARSER,
    RULE_REVISION_MIXED,
    RULE_UNSUPPORTED,
    RULE_VERSION,
)
from aerobim.domain.review_event_append import ReviewEventAppendSpec  # noqa: E402
from aerobim.infrastructure.adapters.bcf_consumers import (  # noqa: E402
    consume_bcf21_zip,
    verify_bcf_zip_structure,
)
from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf  # noqa: E402
from aerobim.infrastructure.di.bootstrap import bootstrap_container  # noqa: E402
from aerobim.tools.benchmark_project_package import load_benchmark_pack  # noqa: E402
from aerobim.tools.ensure_pd_rd_pilot_drawings import ensure_pilot_drawings  # noqa: E402

VARIANTS: dict[str, str] = {
    "clean": "manifest-clean.json",
    "defect": "manifest-defect.json",
    "unit": "manifest-unit.json",
    "missing": "manifest-missing.json",
    "ambiguous": "manifest-ambiguous.json",
    "mixed-rev": "manifest-mixed-rev.json",
    "parser-error": "manifest-parser-error.json",
    "unsupported": "manifest-unsupported.json",
    "ifc-missing-width": "manifest-ifc-missing-width.json",
}

_PACK_DIR = _REPO / "samples" / "demo" / "pd-rd-consistency-pilot-2026-09"
_ANONYMOUS_SUBJECTS = frozenset({"", "anonymous-dev", "lab:anonymous"})


def _git_sha() -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=_REPO,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            or None
        )
    except (OSError, subprocess.CalledProcessError):
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ifc_wall_count(ifc_path: Path) -> int:
    try:
        from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_session

        session = open_ifc_session(ifc_path)
        return len(tuple(session.model.by_type("IfcWall")))
    except Exception:
        return -1


def run_pd_rd_consistency_pilot(
    *,
    variant: str,
    output_dir: Path,
    expert_verdict: str | None = None,
    expert_subject: str | None = None,
) -> dict[str, Any]:
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; expected one of {sorted(VARIANTS)}")
    ensure_pilot_drawings(_PACK_DIR)
    manifest = _PACK_DIR / VARIANTS[variant]
    pack = load_benchmark_pack(manifest)
    request = pack.request
    settings = Settings.from_env()
    container = bootstrap_container(settings)
    use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

    started = perf_counter()
    report = use_case.execute(request)
    elapsed_ms = round((perf_counter() - started) * 1000.0, 3)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_json = output_dir / "report.json"
    report_json.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    bcf_bytes = export_bcf(report)
    bcf_path = output_dir / "findings.bcfzip"
    bcf_path.write_bytes(bcf_bytes)
    xsd_dir = _REPO / "samples" / "bcf-xsd" / "release_2_1"
    structural = verify_bcf_zip_structure(
        bcf_bytes, xsd_dir=xsd_dir if xsd_dir.is_dir() else None
    )
    try:
        consumed = consume_bcf21_zip(bcf_bytes)
        consume_error = None
    except Exception as exc:
        consumed = []
        consume_error = f"{type(exc).__name__}: {exc}"

    expert_event: dict[str, Any] | None = None
    if expert_verdict:
        subject = (expert_subject or "").strip()
        if subject.casefold() in _ANONYMOUS_SUBJECTS:
            raise ValueError(
                "expert_subject is required and cannot be anonymous; LLM cannot sign"
            )
        pd_rd = next(
            (issue for issue in report.issues if issue.rule_id == RULE_ID and issue.finding_id),
            None,
        )
        target = pd_rd or next((issue for issue in report.issues if issue.finding_id), None)
        if target is None or not target.finding_id:
            raise ValueError("no finding_id available for expert verdict")
        store = container.resolve(Tokens.REVIEW_EVENT_STORE)
        now = datetime.now(tz=UTC).isoformat()
        opened = store.append_api_event(
            ReviewEventAppendSpec(
                report_id=report.report_id,
                event_type="opened",
                created_at=now,
                actor=subject,
                finding_id=target.finding_id,
                issue_rule_id=target.rule_id,
                note="pilot CLI open before expert verdict",
                idempotency_key=f"pilot-open:{report.report_id}:{target.finding_id}",
            )
        )
        event = store.append_api_event(
            ReviewEventAppendSpec(
                report_id=report.report_id,
                event_type=expert_verdict,
                created_at=datetime.now(tz=UTC).isoformat(),
                actor=subject,
                finding_id=target.finding_id,
                issue_rule_id=target.rule_id,
                previous_state=opened.resulting_state or "opened",
                note="local limited-mode expert verdict; not OIDC multi-user SSO",
                idempotency_key=f"pilot-verdict:{report.report_id}:{target.finding_id}",
            )
        )
        expert_event = asdict(event)

    ifc_path = request.ifc_path
    drawing_paths = [source.path for source in request.drawing_sources if source.path]
    analyzed_bytes = (ifc_path.stat().st_size if ifc_path and ifc_path.is_file() else 0) + sum(
        path.stat().st_size for path in drawing_paths if path.is_file()
    )
    pd_rd_issues = [
        issue
        for issue in report.issues
        if (issue.rule_id or "").startswith("AEROBIM-PD-RD-")
    ]
    summary = {
        "schema_version": "1.0.0",
        "artifact_type": "pd_rd_consistency_pilot_run",
        "checkpoint": CHECKPOINT,
        "customer_go": False,
        "corpus_kind": "synthetic",
        "claim_boundary": CLAIM_BOUNDARY,
        "variant": variant,
        "pack_id": pack.pack_id,
        "rule_id": RULE_ID,
        "rule_version": RULE_VERSION,
        "git_sha": _git_sha(),
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "offline": os.environ.get("AEROBIM_LLM_ADVISORY", "").strip() in {"", "0", "false", "off"},
        "summary_passed": report.summary.passed,
        "outcome": getattr(report.summary.outcome, "value", report.summary.outcome),
        "error_count": report.summary.error_count,
        "warning_count": report.summary.warning_count,
        "pd_rd_rule_ids": sorted({issue.rule_id for issue in pd_rd_issues}),
        "hard_conflict": any(issue.rule_id == RULE_ID for issue in pd_rd_issues),
        "incomplete": any(
            issue.rule_id in {RULE_INCOMPLETE, RULE_PARSER, RULE_UNSUPPORTED, RULE_AMBIGUOUS}
            for issue in pd_rd_issues
        ),
        "mixed_revision": any(issue.rule_id == RULE_REVISION_MIXED for issue in pd_rd_issues),
        "report_id": report.report_id,
        "elapsed_ms": elapsed_ms,
        "cache": "process-local IfcOpenShell open; first call in this process is cold unless reused",
        "machine": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "input": {
            "ifc_path": None if ifc_path is None else str(ifc_path.relative_to(_REPO)).replace(
                "\\", "/"
            ),
            "ifc_bytes": ifc_path.stat().st_size if ifc_path and ifc_path.is_file() else 0,
            "ifc_sha256": _sha256_file(ifc_path) if ifc_path and ifc_path.is_file() else None,
            "ifc_wall_count": _ifc_wall_count(ifc_path) if ifc_path else 0,
            "drawing_bytes": [
                {"path": str(path.relative_to(_REPO)).replace("\\", "/"), "bytes": path.stat().st_size}
                for path in drawing_paths
                if path.is_file()
            ],
            "analyzed_input_bytes": analyzed_bytes,
            "sample_n": 1,
            "not_p95": True,
            "not_sla": True,
        },
        "bcf": {
            "path": str(bcf_path),
            "sha256": hashlib.sha256(bcf_bytes).hexdigest(),
            "structural_ok": structural.ok,
            "xsd_status": getattr(structural, "xsd_status", None),
            "topic_count": structural.topic_count,
            "consumed_topics": len(consumed),
            "consume_error": consume_error,
            "cde_import": "NOT_VERIFIED",
        },
        "expert_event": expert_event,
        "limited_auth_mode": (
            "HTTP default: GET /v1/auth/bff = 501; shared bearer and anonymous-dev "
            "cannot assign expert status. CLI --expert-verdict is a local journal "
            "with an explicit human subject. Not a multi-user SSO pilot."
        ),
        "artifacts": {
            "report_json": str(report_json),
            "bcf": str(bcf_path),
        },
    }
    (output_dir / "run-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "LIMITATIONS.json").write_text(
        json.dumps(
            {
                "corpus_kind": "synthetic",
                "customer_go": False,
                "cde_import": "NOT_VERIFIED",
                "space_area_from_geometry": "not_implemented",
                "oidc_bff": "GET /v1/auth/bff returns 501 unless oidc_bff_phase3_ready",
                "claim_boundary": CLAIM_BOUNDARY,
                "supported_class": (
                    "IfcWall Qto_WallBaseQuantities.Width vs PDF text-layer "
                    "WALL-** thickness/width for a unique Name/Tag"
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=sorted(VARIANTS), default="defect")
    parser.add_argument(
        "--out",
        type=Path,
        default=_REPO / "backend" / "var" / "pd-rd-consistency-pilot",
    )
    parser.add_argument(
        "--expert-verdict",
        choices=("accepted", "rejected"),
        default=None,
        help="Local HITL journal only; requires --expert-subject. Not OIDC.",
    )
    parser.add_argument("--expert-subject", default=None)
    args = parser.parse_args(argv)
    summary = run_pd_rd_consistency_pilot(
        variant=args.variant,
        output_dir=args.out,
        expert_verdict=args.expert_verdict,
        expert_subject=args.expert_subject,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
