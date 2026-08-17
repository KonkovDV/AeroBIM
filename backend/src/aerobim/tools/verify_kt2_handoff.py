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
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def _check(name: str, ok: bool, detail: str, rows: list[dict[str, Any]]) -> None:
    rows.append({"check": name, "ok": ok, "detail": detail})


def _readme_demo_block(readme_text: str) -> str:
    """First install/demo section: historical Quick Start or current Try it heading."""
    for heading in ("## Quick Start", "## Try it"):
        start = readme_text.find(heading)
        if start < 0:
            continue
        end = readme_text.find("\n## ", start + 3)
        if end > start:
            return readme_text[start:end]
        return readme_text[start:]
    return ""


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
        detail = f"exit={proc.returncode}"
        if not ok_verify:
            err = (proc.stderr or "").strip().replace("\n", " ")
            out = (proc.stdout or "").strip().replace("\n", " ")
            if err:
                detail = f"{detail} stderr={err[:400]}"
            elif out:
                detail = f"{detail} stdout={out[:400]}"
        _check("wall_guid_verify", ok_verify, detail, rows)

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
            clash.get("status") == "fixture_measured"
            and clash.get("claim_level") == "fixture_only",
            f"status={clash.get('status')} claim={clash.get('claim_level')}",
            rows,
        )
    else:
        _check("clash_fixture_measured", False, "missing clash STATUS", rows)

    clash_pr = clash_dir / "precision-recall.json"
    if clash_pr.is_file():
        pr = _load_json(clash_pr)
        precision_claim = pr.get("precision_claim")
        claim: dict[str, Any] = precision_claim if isinstance(precision_claim, dict) else {}
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
            overlay.get("status") == "fixture_rendered"
            and overlay.get("claim_level") == "fixture_only",
            f"status={overlay.get('status')} claim={overlay.get('claim_level')}",
            rows,
        )
    else:
        _check("overlay_fixture_rendered", False, "missing overlay STATUS", rows)

    align = repo / "docs" / "tz" / "KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md"
    ask = repo / "docs" / "partners" / "SAMOLET_KT2_ASK_2026_08_15.md"
    _check("tri_source_alignment", align.is_file(), str(align), rows)
    _check("samolet_kt2_ask", ask.is_file(), str(ask), rows)

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
    video = repo / "docs" / "demo" / "KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md"
    _check("jury_faq", faq.is_file(), str(faq), rows)
    _check("kt2_video_script", video.is_file(), str(video), rows)
    video_text = video.read_text(encoding="utf-8") if video.is_file() else ""
    _check(
        "rehearsal_forbids_wall_guid_html",
        "wall-guid/report.html" in video_text and "Не открывать" in video_text,
        "video notice must forbid wall-guid/report.html as overlay demo",
        rows,
    )
    _check(
        "kt2_video_not_recorded",
        "не записываем" in video_text and "не прилагаем" in video_text,
        "KT#2 video is withdrawn; live CLI is the demo",
        rows,
    )

    handoff_readme = handoff_dir / "README.md"
    handoff_text = handoff_readme.read_text(encoding="utf-8") if handoff_readme.is_file() else ""
    _check(
        "handoff_readme_live_cli",
        "run_demo_vertical_slice" in handoff_text
        and "Do not open" in handoff_text
        and "wall-guid/report.html" in handoff_text,
        "handoff README must lead with live CLI and forbid snapshot HTML overlay",
        rows,
    )

    snapshot_html = handoff_dir / "vertical-slice" / "report.html"
    snapshot = snapshot_html.read_text(encoding="utf-8") if snapshot_html.is_file() else ""
    _check(
        "snapshot_html_not_overlay_demo",
        (not snapshot_html.is_file()) or ("kt2-overlay" not in snapshot),
        "11.08 snapshot HTML must be unpublished or remain without #kt2-overlay (live CLI is the demo)",
        rows,
    )

    readme = repo / "README.md"
    readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    quick_start = _readme_demo_block(readme_text)
    required_installs = [
        line
        for line in quick_start.splitlines()
        if "pip install -e" in line and not line.lstrip().startswith("#")
    ]
    core_demo_install = any(
        '".[dev,raster]"' in line and "pdf-agpl" not in line for line in required_installs
    )
    _check(
        "readme_quickstart_demo_core_pdf",
        core_demo_install and "run_demo_vertical_slice" in quick_start,
        "README demo section must install .[dev,raster] without requiring pdf-agpl for the live CLI",
        rows,
    )

    docs_mp4 = sorted((repo / "docs").rglob("*.mp4"))
    _check(
        "kt2_demo_mp4_not_in_docs",
        not docs_mp4,
        "none" if not docs_mp4 else ",".join(p.as_posix() for p in docs_mp4),
        rows,
    )
    local_primary = repo / "artifacts" / "demo" / "kt2-demo.mp4"
    local_fallback = repo / "artifacts" / "demo" / "kt2-demo-fallback.mp4"
    if local_primary.is_file() or local_fallback.is_file():
        mp4_status = "PRESENT_LOCAL_NOT_IN_GIT"
    else:
        mp4_status = "NOT_IN_GIT"
    # Video is withdrawn. Missing mp4 is the intended state, not a CI failure.
    _check("kt2_demo_mp4_status", True, mp4_status, rows)

    ok = all(bool(r["ok"]) for r in rows)
    return {
        "ok": ok,
        "artifact_type": "kt2_handoff_verification",
        "schema_version": "1.1.0",
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
