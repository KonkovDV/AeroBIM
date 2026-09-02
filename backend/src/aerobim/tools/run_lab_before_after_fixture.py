"""Machine elapsed on a git fixture for the lab before/after journal.

Protocol: ``docs/partners/BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md``.
This runner fills ``t_tool_ms`` only. ``t_manual_s`` stays null until a human
timer and HITL confirm. It does not fill A1–A8, is not partner B4, and is not
the published analog −72.1%. Checkpoint ``NO_GO``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.mik_commission_scoring import (
    foreign_labor_cut_as_ours,
    k4_revenue_claimed,
)
from aerobim.domain.models import RequirementSource, ValidationRequest
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools._cli_base import run_cli

CLAIM_BOUNDARY = (
    "Fixture tool elapsed only. t_manual_s is null. Not partner B4. "
    "Not A1-A8. Not the published analog labor cut. Checkpoint NO_GO."
)
SCHEMA_VERSION = "1.0.0"
DEFAULT_IFC_REL = "samples/ifc/wall-fire-rating-rei60.ifc"
DEFAULT_IDS_REL = "samples/ids/wall-fire-rating.ids"
DEFAULT_EVIDENCE_REL = "docs/evidence/lab-before-after-fixture-tool-only-latest.json"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure_fixture_tool_elapsed(
    *,
    ifc_path: Path,
    ids_path: Path,
    storage_dir: Path,
) -> dict[str, Any]:
    """Run IDS+IFC validation once and return elapsed milliseconds plus counts."""

    settings = Settings(
        application_name="aerobim-lab-before-after",
        environment="test",
        host="127.0.0.1",
        port=8080,
        storage_dir=storage_dir,
        debug=True,
    )
    storage_dir.mkdir(parents=True, exist_ok=True)
    container = bootstrap_container(settings)
    use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)
    request = ValidationRequest(
        request_id="lab-before-after-fixture",
        ifc_path=ifc_path,
        requirement_source=RequirementSource(text=""),
        ids_path=ids_path,
    )
    started = time.perf_counter()
    report = use_case.execute(request)
    elapsed_ms = int(round((time.perf_counter() - started) * 1000))
    return {
        "t_tool_ms": elapsed_ms,
        "machine_issue_count": int(report.summary.issue_count),
    }


def build_journal(
    *,
    repo: Path,
    ifc_rel: str = DEFAULT_IFC_REL,
    ids_rel: str = DEFAULT_IDS_REL,
    measured: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    ifc_path = (repo / ifc_rel).resolve()
    ids_path = (repo / ids_rel).resolve()
    if not ifc_path.is_file():
        raise FileNotFoundError(ifc_path)
    if not ids_path.is_file():
        raise FileNotFoundError(ids_path)
    if measured is None:
        with tempfile.TemporaryDirectory(prefix="aerobim-lab-ba-") as tmp:
            measured = measure_fixture_tool_elapsed(
                ifc_path=ifc_path,
                ids_path=ids_path,
                storage_dir=Path(tmp) / "var",
            )
    t_tool_ms = int(measured["t_tool_ms"])
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "lab_before_after_journal",
        "claim_level": "fixture_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "checkpoint": "NO_GO",
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "complete_for_formula": False,
        "fills_a1_a8": False,
        "k4_revenue_claimed": k4_revenue_claimed(),
        "foreign_labor_cut_as_ours": foreign_labor_cut_as_ours(),
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
        "pack_path": ifc_rel.replace("\\", "/"),
        "ids_path": ids_rel.replace("\\", "/"),
        "pack_hash": sha256_file(ifc_path),
        "ids_hash": sha256_file(ids_path),
        "order": None,
        "t_manual_s": None,
        "t_tool_s": t_tool_ms // 1000,
        "t_tool_ms": t_tool_ms,
        "n_remarks_manual": None,
        "n_remarks_tool_confirmed": None,
        "discrepancy": None,
        "hitl_confirmed": False,
        "machine_issue_count": int(measured["machine_issue_count"]),
        "missing_for_formula": [
            "t_manual_s",
            "n_remarks_manual",
            "n_remarks_tool_confirmed",
            "order",
            "discrepancy",
        ],
        "allowed_wording": (
            "Machine elapsed on a git fixture. Human timer and HITL confirm "
            "are still empty. Not partner hours."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--ifc", type=Path, default=None)
    parser.add_argument("--ids", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--also-docs-evidence",
        action="store_true",
        help="Also write docs/evidence/lab-before-after-fixture-tool-only-latest.json",
    )
    args = parser.parse_args(argv)
    root = (args.repo or repo_root()).resolve()
    ifc_rel = args.ifc.as_posix() if args.ifc is not None else DEFAULT_IFC_REL
    ids_rel = args.ids.as_posix() if args.ids is not None else DEFAULT_IDS_REL
    if args.ifc is not None and args.ifc.is_absolute():
        ifc_rel = args.ifc.resolve().relative_to(root).as_posix()
    if args.ids is not None and args.ids.is_absolute():
        ids_rel = args.ids.resolve().relative_to(root).as_posix()
    payload = build_journal(repo=root, ifc_rel=ifc_rel, ids_rel=ids_rel)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out = args.output or (root / "artifacts" / "lab" / "before-after-fixture-tool-only.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if args.also_docs_evidence:
        evidence = root / DEFAULT_EVIDENCE_REL
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(text, encoding="utf-8")
        print(f"docs_evidence={evidence}")
    print(
        json.dumps(
            {
                "output": str(out),
                "claim_level": payload["claim_level"],
                "complete_for_formula": payload["complete_for_formula"],
                "t_manual_s": payload["t_manual_s"],
                "t_tool_ms": payload["t_tool_ms"],
                "pack_hash": payload["pack_hash"],
                "checkpoint": "NO_GO",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(lambda: main()))
