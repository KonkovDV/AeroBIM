"""One-shot: rewrite broken markdown links after public-docs hygiene."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = {
    "docs/academic-publication-evidence-2026.md": "docs/REPRODUCIBILITY-2026.md",
    "audit/reports/RED_TEAM_DELTA_2026_07_17.md": "audit/reports/CRITICAL_BLOCKERS.md",
    "docs/13-academic-execution-plan-2026.md": "docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md",
    "docs/14-enterprise-storage-foundation.md": "docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md",
    "docs/github-readiness-audit-2026-05-20.md": "docs/REPOSITORY-HYGIENE-2026.md",
    "docs/PROJECT-AUDIT-2026-05-20.md": "docs/REPOSITORY-HYGIENE-2026.md",
    "PROJECT-AUDIT-2026-05-20.md": "REPOSITORY-HYGIENE-2026.md",
    "13-academic-execution-plan-2026.md": "architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md",
    "academic-publication-evidence-2026.md": "REPRODUCIBILITY-2026.md",
    "evidence/EXTERNAL_STANDARDS_CHECK_2026_07_10.md": "evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md",
    "architecture/EXECUTION_PLAN_I8_I9_2026_07.md": "architecture/RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md",
    "EXECUTION_PLAN_I8_I9_2026_07.md": "RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md",
    "EXECUTION_PLAN_NEXT_2026_07.md": "TARGET_HYBRID_ARCHITECTURE_TZ_2026.md",
    "EXECUTION_PLAN_HYPERDEEP_2026_07.md": "TARGET_HYBRID_ARCHITECTURE_TZ_2026.md",
    "../../audit/reports/AUDIT_COMBAT_BACKENDS_I1_I9_2026_07_17.md": "../../audit/reports/CRITICAL_BLOCKERS.md",
    "../architecture/EXECUTION_PLAN_I8_I9_2026_07.md": "../architecture/RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md",
    "../evidence/TRACK_A5_DEMO_PATH_2026_07_11.md": "../evidence/demo-path-pilot-moscow-2026-07-11.json",
    "RED_TEAM_DELTA_2026_07_17.md": "CRITICAL_BLOCKERS.md",
    "post-pilot-go-no-go-memo-2026.md": "../audit/reports/CRITICAL_BLOCKERS.md",
    "post-pilot-fork-2026.md": "../audit/reports/CRITICAL_BLOCKERS.md",
    "optional-adapters-smoke-2026.md": "15-local-quality-gate.md",
    "manuscript-draft-2026.md": "REPRODUCIBILITY-2026.md",
}


def main() -> None:
    targets = list(ROOT.glob("README*.md"))
    targets += list((ROOT / "docs").rglob("*.md"))
    targets += list((ROOT / "audit" / "reports").glob("*.md"))
    changed: list[str] = []
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        orig = text
        for old, new in REPLACEMENTS.items():
            text = text.replace(f"]({old})", f"]({new})")
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="\n")
            changed.append(str(path.relative_to(ROOT)))
    print(f"updated {len(changed)} files")
    for item in changed:
        print(f"  {item}")


if __name__ == "__main__":
    main()
