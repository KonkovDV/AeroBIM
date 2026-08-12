"""Verify KT#2 fixture handoff pack (L1) — fail-closed, no customer GO.

Exit 0 only when methodology/fixture gates hold and checkpoint stays NO_GO.
Never treats fixture P/R as product accuracy.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(name: str, ok: bool, detail: str, rows: list[dict[str, Any]]) -> None:
    rows.append({"check": name, "ok": ok, "detail": detail})


def verify_kt2_handoff(*, handoff_dir: Path, repo: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    status_path = handoff_dir / "STATUS.json"
    if not status_path.is_file():
        _check("status_present", False, f"missing {status_path}", rows)
        return {"ok": False, "checks": rows, "checkpoint_verdict": None}

    status = _load_json(status_path)
    verdict = status.get("checkpoint_verdict")
    _check(
        "checkpoint_no_go",
        verdict == "NO_GO",
        f"checkpoint_verdict={verdict!r}",
        rows,
    )
    _check(
        "claim_level_fixture",
        status.get("claim_level") == "fixture_only",
        f"claim_level={status.get('claim_level')!r}",
        rows,
    )

    wall = handoff_dir / "wall-guid"
    _check("wall_guid_dir", wall.is_dir(), str(wall), rows)
    if wall.is_dir():
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "aerobim.tools.verify_evidence_bundle",
                "--bundle",
                str(wall),
            ],
            cwd=str(repo / "backend"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        ok_verify = proc.returncode == 0
        if proc.returncode == 0:
            try:
                payload = json.loads(proc.stdout)
                ok_verify = bool(
                    payload.get("ok") is True or payload.get("verification") == "passed"
                )
            except json.JSONDecodeError:
                ok_verify = "passed" in (proc.stdout or "").lower()
        _check("wall_guid_verify", ok_verify, f"exit={proc.returncode}", rows)

    harness = handoff_dir / "harness-dryrun" / "pilot-harness-report.json"
    if harness.is_file():
        report = _load_json(harness)
        _check(
            "harness_not_publishable",
            report.get("publishable") is False,
            f"publishable={report.get('publishable')!r}",
            rows,
        )
    else:
        _check("harness_not_publishable", False, f"missing {harness}", rows)

    slice_summary = handoff_dir / "vertical-slice" / "slice-summary.json"
    _check("vertical_slice_summary", slice_summary.is_file(), str(slice_summary), rows)

    clash_dir = repo / "docs" / "evidence" / "clash-measurement-slice-2026-08"
    clash_status = clash_dir / "STATUS.json"
    if clash_status.is_file():
        clash = _load_json(clash_status)
        _check(
            "clash_fixture_measured",
            clash.get("status") == "fixture_measured" and clash.get("claim_level") == "fixture_only",
            f"status={clash.get('status')} claim={clash.get('claim_level')}",
            rows,
        )
    else:
        _check("clash_fixture_measured", False, "missing clash STATUS", rows)

    clash_pr = clash_dir / "precision-recall.json"
    if clash_pr.is_file():
        pr = _load_json(clash_pr)
        claim = pr.get("precision_claim") if isinstance(pr.get("precision_claim"), dict) else {}
        render = str(claim.get("render") or "")
        honest = (
            pr.get("corpus_kind") != "customer"
            and pr.get("claim_level") == "fixture_only"
            and pr.get("publishable_protocol_gate") is False
            and claim.get("base_publishable") is False
            and claim.get("publishable") is False
            and "withheld" in render
        )
        _check(
            "clash_precision_not_customer",
            honest,
            (
                f"corpus_kind={pr.get('corpus_kind')!r} claim={pr.get('claim_level')!r} "
                f"gate={pr.get('publishable_protocol_gate')!r} "
                f"base={claim.get('base_publishable')!r} pub={claim.get('publishable')!r}"
            ),
            rows,
        )
    else:
        _check("clash_precision_not_customer", False, "missing clash precision-recall.json", rows)

    overlay_status = repo / "docs" / "evidence" / "drawing-overlay-smoke-2026-08" / "STATUS.json"
    if overlay_status.is_file():
        overlay = _load_json(overlay_status)
        _check(
            "overlay_fixture_rendered",
            overlay.get("status") == "fixture_rendered" and overlay.get("claim_level") == "fixture_only",
            f"status={overlay.get('status')} claim={overlay.get('claim_level')}",
            rows,
        )
    else:
        _check("overlay_fixture_rendered", False, "missing overlay STATUS", rows)

    academic = repo / "docs" / "pilot" / "KT2_ACADEMIC_CLOSURE_PLAN_2026_08_12.md"
    align = repo / "docs" / "tz" / "KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md"
    max_eng = repo / "docs" / "pilot" / "KT2_MAX_ENG_PLAN_2026_08_12.md"
    _check("academic_plan", academic.is_file(), str(academic), rows)
    _check("tri_source_alignment", align.is_file(), str(align), rows)
    _check("max_eng_plan", max_eng.is_file(), str(max_eng), rows)

    second_overlay = (
        repo / "docs" / "evidence" / "drawing-overlay-smoke-2026-08" / "overlay-sheet-header.png"
    )
    _check("overlay_second_zone", second_overlay.is_file(), str(second_overlay), rows)

    bcf_t1 = handoff_dir / "bcf-t1" / "bcf-structural-handoff.json"
    if bcf_t1.is_file():
        bcf = _load_json(bcf_t1)
        _check(
            "bcf_t1_structural",
            bool(bcf.get("structural_ok"))
            and (bcf.get("cde_import") or {}).get("status") == "NOT_VERIFIED",
            f"structural_ok={bcf.get('structural_ok')} cde={bcf.get('cde_import')}",
            rows,
        )
    else:
        _check("bcf_t1_structural", False, f"missing {bcf_t1}", rows)

    faq = repo / "docs" / "demo" / "KT2_JURY_FAQ_2026_08_12.md"
    rehearsal = repo / "docs" / "demo" / "KT2_DEMO_REHEARSAL_2026_08_12.md"
    _check("jury_faq", faq.is_file(), str(faq), rows)
    _check("demo_rehearsal", rehearsal.is_file(), str(rehearsal), rows)

    ok = all(bool(r["ok"]) for r in rows)
    return {
        "ok": ok,
        "artifact_type": "kt2_handoff_verification",
        "schema_version": "1.0.0",
        "checkpoint_verdict": verdict,
        "claim_boundary": (
            "L1 fixture/methodology verification only; never flips Checkpoint GO; "
            "not customer accuracy; not TZ >90%."
        ),
        "checks": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--handoff-dir",
        type=Path,
        default=None,
        help="Default: docs/evidence/kt2-handoff-2026-08-11",
    )
    parser.add_argument(
        "--write-status",
        type=Path,
        default=None,
        help="Optional path to write verification JSON",
    )
    args = parser.parse_args(argv)
    repo = _repo_root()
    handoff = args.handoff_dir or (repo / "docs" / "evidence" / "kt2-handoff-2026-08-11")
    result = verify_kt2_handoff(handoff_dir=handoff, repo=repo)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write_status:
        args.write_status.parent.mkdir(parents=True, exist_ok=True)
        args.write_status.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
