"""Mutation-kill recall for an ``inject_defects`` manifest (E2 protocol).

For every variant directory produced by ``aerobim.tools.inject_defects`` this
tool runs the deterministic contour (IFC + IDS + structured rules, the same
use case as the lab before/after fixture runner) and diffs the issue multiset
against the unmutated CONTROL variant. A mutant counts as **killed** when the
contour's output changes at all (novel or vanished issues) — standard
mutation-testing semantics, not a semantic confirmation of the defect.

Deviation from ``docs/evidence/DEFECT_INJECTION_RECALL_PLAN_2026_09.md``: the
2026-08-30 plan gated recall on a seam-clean pack passing with
``summary.passed=true``. The 2026-09-03 roadmap command runs E2 on the
house-5 pack from the owner tree, which is **not** seam-clean; attribution is
therefore done via the CONTROL baseline diff instead of a clean-pass gate.
Recall on injected synthetics does not transfer to the partner pack.

Claim boundary: synthetic mutation test on a local NDA pack. Not Samolet
accuracy. Not product accuracy >90%. Does not close RT-001/002/003.
Checkpoint NO_GO.

Example::

    python -m aerobim.tools.evaluate_injection_recall \
        --manifest var/e2-injection/injected/injection_manifest.json \
        --ids samples/ids/wall-fire-rating.ids \
        --rules samples/requirements/techlab-demo-rules.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.study_design import wilson_interval
from aerobim.tools._cli_base import run_cli

SCHEMA_VERSION = "1.0.0"
CLAIM_BOUNDARY = (
    "Mutation-kill recall on injected synthetics. Output-sensitivity proxy, "
    "not semantic defect confirmation. Not Samolet accuracy. Not product "
    "accuracy. Does not close RT-001/002/003. Checkpoint NO_GO."
)
PLAN_DEVIATION = (
    "DEFECT_INJECTION_RECALL_PLAN_2026_09 (2026-08-30) gated recall on a "
    "seam-clean pack passing summary.passed=true. Attribution in this CLI "
    "uses the CONTROL baseline issue-multiset diff instead, because the "
    "2026-09-03 E2 command runs on packs that are not seam-clean."
)
CONTROL_CLASS = "CONTROL"
_IFC_SUFFIXES = {".ifc", ".ifcxml"}

IssueRecord = Mapping[str, Any]
AnalyzeFn = Callable[[Path, str], list[IssueRecord]]


def issue_key(issue: IssueRecord) -> tuple[str, ...]:
    """Stable identity of a finding for multiset diffing."""

    return (
        str(issue.get("rule_id") or ""),
        str(issue.get("ifc_entity") or ""),
        str(issue.get("target_ref") or ""),
        str(issue.get("property_name") or ""),
        str(issue.get("observed_value") or ""),
        str(issue.get("element_guid") or ""),
    )


def diff_issue_multisets(
    baseline: Counter[tuple[str, ...]],
    variant: Counter[tuple[str, ...]],
) -> tuple[Counter[tuple[str, ...]], Counter[tuple[str, ...]]]:
    """Return (novel, vanished) issue counts of ``variant`` vs ``baseline``."""

    return variant - baseline, baseline - variant


def evaluate_manifest(
    manifest: Mapping[str, Any],
    issues_by_class: Mapping[str, list[IssueRecord]],
    analyze_errors: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Compute per-class kill rows and aggregate recall with a Wilson interval."""

    if CONTROL_CLASS not in issues_by_class:
        raise ValueError("CONTROL variant issues are required as the baseline")
    baseline = Counter(issue_key(issue) for issue in issues_by_class[CONTROL_CLASS])
    errors = analyze_errors or {}

    rows: list[dict[str, Any]] = []
    for variant in manifest.get("variants", []):
        defect_class = str(variant.get("class") or "")
        if defect_class == CONTROL_CLASS:
            continue
        applied = bool(variant.get("applied"))
        error = errors.get(defect_class)
        counts = Counter(issue_key(issue) for issue in issues_by_class.get(defect_class, []))
        novel, vanished = diff_issue_multisets(baseline, counts)
        novel_count = sum(novel.values())
        vanished_count = sum(vanished.values())
        # A contour that refuses the mutated pack (fail-closed parse/ingest
        # error) visibly reacts to the mutant, so it counts as killed with the
        # direction recorded as the error rather than as issue movement.
        killed = applied and (error is not None or (novel_count + vanished_count) > 0)
        rows.append(
            {
                "class": defect_class,
                "applied": applied,
                "injector_note": variant.get("note"),
                "novel_issues": novel_count,
                "vanished_issues": vanished_count,
                "killed": killed,
                "analyze_error": error,
            }
        )

    applied_rows = [row for row in rows if row["applied"]]
    not_applied = [row["class"] for row in rows if not row["applied"]]
    killed_count = sum(1 for row in applied_rows if row["killed"])
    trials = len(applied_rows)
    recall_block: dict[str, Any]
    if trials == 0:
        recall_block = {"defined": False, "reason": "no applied injections"}
    else:
        recall_block = {
            "defined": True,
            **wilson_interval(killed_count, trials, alpha=0.05).as_dict(),
        }
    return {
        "rows": rows,
        "not_applied_classes": not_applied,
        "control_issue_count": sum(baseline.values()),
        "aggregate": {
            "killed": killed_count,
            "trials": trials,
            "recall_point": (killed_count / trials) if trials else None,
            "wilson_95": recall_block,
            "denominator_note": (
                "CONTROL excluded; classes with applied=false excluded (no defect "
                "was injected there)."
            ),
        },
    }


def _issue_to_record(issue: Any) -> IssueRecord:
    return {
        "rule_id": getattr(issue, "rule_id", None),
        "ifc_entity": getattr(issue, "ifc_entity", None),
        "target_ref": getattr(issue, "target_ref", None),
        "property_name": getattr(issue, "property_name", None),
        "observed_value": getattr(issue, "observed_value", None),
        "element_guid": getattr(issue, "element_guid", None),
    }


def _iter_ifc_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in _IFC_SUFFIXES
    )


def make_deterministic_analyze(
    *,
    ids_path: Path,
    rules_text: str,
    storage_dir: Path,
) -> AnalyzeFn:
    """Bind the deterministic IDS+rules contour as an ``AnalyzeFn``."""

    from aerobim.core.config.settings import Settings
    from aerobim.core.di.tokens import Tokens
    from aerobim.domain.models import RequirementSource, ValidationRequest
    from aerobim.infrastructure.di.bootstrap import bootstrap_container

    if not ids_path.is_file():
        raise FileNotFoundError(ids_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    settings = Settings(
        application_name="aerobim-injection-recall",
        environment="test",
        host="127.0.0.1",
        port=8080,
        storage_dir=storage_dir,
        debug=True,
    )
    container = bootstrap_container(settings)
    use_case = container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE)

    def _analyze(pack_dir: str | Path, request_prefix: str) -> list[IssueRecord]:
        del request_prefix  # request ids derive from the pack path hash
        pack = Path(pack_dir)
        records: list[IssueRecord] = []
        for ifc_file in _iter_ifc_files(pack):
            digest = hashlib.sha256(ifc_file.read_bytes()).hexdigest()[:16]
            report = use_case.execute(
                ValidationRequest(
                    request_id=f"e2-injection-{digest}",
                    ifc_path=ifc_file,
                    requirement_source=RequirementSource(text=rules_text),
                    ids_path=ids_path,
                )
            )
            records.extend(_issue_to_record(issue) for issue in report.issues)
        return records

    return _analyze


def _git_commit(repo: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = completed.stdout.strip()
    return commit or None


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_artifact(
    *,
    manifest: Mapping[str, Any],
    manifest_path: Path,
    evaluation: Mapping[str, Any],
    determinism_check: Mapping[str, Any],
    git_commit: str | None,
    source_label: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "defect_injection_recall_run",
        "claim_level": "synthetic_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "checkpoint": "NO_GO",
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
        "git_commit": git_commit,
        "seed": manifest.get("seed"),
        "source_label": source_label,
        "source_path_sha256": _source_tree_hash(manifest),
        "source_content_hashed": False,
        "manifest_sha256": _sha256_file(manifest_path),
        "frozen_formula": (
            f"On the frozen source {source_label} (path-string hash only; IFC "
            f"bytes not in git) at commit {git_commit or 'UNVERIFIED'} with "
            f"seed {manifest.get('seed')} the mutation-kill recall below was "
            "obtained."
        ),
        "detection_proxy": (
            "killed = issue multiset of the mutated variant differs from the "
            "unmutated CONTROL variant (novel or vanished findings). Direction "
            "is reported per class; a vanished alarm is recorded as a hide, "
            "not as confirmation of the intended defect."
        ),
        "plan_deviation": PLAN_DEVIATION,
        "determinism_check": determinism_check,
        "per_class": evaluation["rows"],
        "not_applied_classes": evaluation["not_applied_classes"],
        "control_issue_count": evaluation["control_issue_count"],
        "aggregate": evaluation["aggregate"],
    }


def _source_tree_hash(manifest: Mapping[str, Any]) -> str | None:
    """Hash the recorded source path string, never the NDA tree content."""

    source = manifest.get("source")
    if not source:
        return None
    return hashlib.sha256(str(source).encode("utf-8")).hexdigest()


def render_markdown(artifact: Mapping[str, Any]) -> str:
    aggregate = artifact["aggregate"]
    wilson = aggregate.get("wilson_95") or {}
    lines = [
        '<!-- claims-lint: allow-file reason="Injection recall run; synthetic mutation test; NO_GO" -->',
        "---",
        'title: "Defect-injection recall run — mutation-kill, synthetic-only"',
        'date: "2026-09-03"',
        'last_updated: "2026-09-03"',
        "status: active",
        f'version: "{SCHEMA_VERSION}"',
        "closes_rt001: false",
        "closes_rt002: false",
        "closes_rt003: false",
        "claim_boundary: >",
        "  Mutation-kill recall on injected synthetics. Output-sensitivity",
        "  proxy, not semantic defect confirmation. Not Samolet accuracy.",
        "  Not product accuracy. Checkpoint NO_GO.",
        "---",
        "",
        "# Recall на инъекциях — прогон E2 (синтетика, не партнёр)",
        "",
        f"- Источник: `{artifact['source_label']}`.",
        f"- Seed: **{artifact['seed']}** · коммит: `{artifact.get('git_commit') or 'UNVERIFIED'}`",
        f"- Манифест sha256: `{artifact['manifest_sha256']}`",
        f"- Детерминизм (source ≡ CONTROL): **{artifact['determinism_check']['status']}**",
        "",
        "## Отклонение от плана 2026-08-30",
        "",
        "План требовал шовно-чистый пакет с `summary.passed=true`. По команде",
        "дорожной карты 2026-09-03 источник — дом-5 (дерево владельца), который",
        "чистым не является; атрибуция — через CONTROL-дифф мультимножеств находок.",
        "Recall на синтетике **не** переносится на комплект Самолёта.",
        "",
        "## По классам инъекций",
        "",
        "| Класс | Инъекция | Новых находок | Исчезнувших | Мутант убит |",
        "|---|---|---|---|---|",
    ]
    for row in artifact["per_class"]:
        applied = "да" if row["applied"] else f"нет ({row.get('injector_note') or '—'})"
        if row.get("analyze_error"):
            killed = f"да (fail-closed: {row['analyze_error'].split(':', 1)[0]})"
        else:
            killed = "да" if row["killed"] else "нет"
        lines.append(
            f"| {row['class']} | {applied} | {row['novel_issues']} | "
            f"{row['vanished_issues']} | {killed} |"
        )
    lines += [
        "",
        "## Итог",
        "",
    ]
    if wilson.get("defined"):
        lines += [
            f"- Mutation-kill recall: **{aggregate['killed']}/{aggregate['trials']}** "
            f"(точечно {aggregate['recall_point']:.3f})",
            f"- Wilson 95%: [{wilson['lower']:.3f}; {wilson['upper']:.3f}] — "
            f"публикуется **нижняя** граница {wilson['lower']:.3f}",
            f"- База CONTROL: {artifact['control_issue_count']} находок до инъекций",
        ]
    else:
        lines.append("- Recall не определён: ни одна инъекция не применилась.")
    if artifact["not_applied_classes"]:
        lines.append(
            f"- Не применились (вне знаменателя): {', '.join(artifact['not_applied_classes'])}"
        )
    lines += [
        "",
        "Граница: прокси — чувствительность выхода контура, не семантическое",
        "подтверждение дефекта. `claim_level=synthetic_only`. Checkpoint NO_GO.",
        "RT-001/002/003 остаются OPEN.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="injection_manifest.json")
    parser.add_argument("--ids", type=Path, required=True, help="IDS file for the contour")
    parser.add_argument("--rules", type=Path, required=True, help="Structured rules text file")
    parser.add_argument(
        "--source-label",
        default="house_5_s1_3_kr",
        help="NDA-safe label of the frozen source (block id, not a path)",
    )
    parser.add_argument(
        "--storage",
        type=Path,
        default=None,
        help="Contour storage dir (default: temp dir, discarded)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evidence/defect-injection-recall-run-latest.json"),
    )
    parser.add_argument(
        "--md",
        type=Path,
        default=Path("docs/evidence/DEFECT_INJECTION_RECALL_RUN_2026_09.md"),
    )
    args = parser.parse_args(argv)

    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    injection_root = manifest_path.parent
    rules_text = args.rules.read_text(encoding="utf-8")

    storage = args.storage
    temp_storage: tempfile.TemporaryDirectory[str] | None = None
    if storage is None:
        temp_storage = tempfile.TemporaryDirectory(prefix="aerobim-e2-recall-")
        storage = Path(temp_storage.name) / "var"

    try:
        analyze = make_deterministic_analyze(
            ids_path=args.ids.resolve(),
            rules_text=rules_text,
            storage_dir=storage.resolve(),
        )
        issues_by_class: dict[str, list[IssueRecord]] = {}
        analyze_errors: dict[str, str] = {}
        for variant in manifest.get("variants", []):
            defect_class = str(variant.get("class") or "")
            variant_dir = injection_root / defect_class.lower()
            if not variant_dir.is_dir():
                raise FileNotFoundError(f"variant directory missing: {variant_dir}")
            try:
                issues_by_class[defect_class] = analyze(variant_dir, f"e2-{defect_class}")
            except Exception as exc:  # fail-closed contour reaction is a signal
                issues_by_class[defect_class] = []
                analyze_errors[defect_class] = f"{type(exc).__name__}: {exc}"[:300]

        source_dir = Path(str(manifest["source"]))
        source_issues = analyze(source_dir, "e2-source")
        control_counter = Counter(issue_key(i) for i in issues_by_class[CONTROL_CLASS])
        source_counter = Counter(issue_key(i) for i in source_issues)
        determinism_status = "pass" if source_counter == control_counter else "fail"
        determinism_check = {
            "status": determinism_status,
            "source_issue_count": sum(source_counter.values()),
            "control_issue_count": sum(control_counter.values()),
            "method": "analyze(source) multiset == analyze(CONTROL) multiset",
        }
        if determinism_status != "pass":
            raise ValueError(
                "Non-deterministic contour: pristine source and CONTROL variant "
                "produced different issue multisets; recall is not computable."
            )
    finally:
        if temp_storage is not None:
            temp_storage.cleanup()

    evaluation = evaluate_manifest(manifest, issues_by_class, analyze_errors)
    artifact = build_artifact(
        manifest=manifest,
        manifest_path=manifest_path,
        evaluation=evaluation,
        determinism_check=determinism_check,
        git_commit=_git_commit(Path(__file__).resolve().parents[4]),
        source_label=args.source_label,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.md.parent.mkdir(parents=True, exist_ok=True)
    args.md.write_text(render_markdown(artifact), encoding="utf-8")

    print(
        json.dumps(
            {
                "output": str(args.output),
                "md": str(args.md),
                "claim_level": artifact["claim_level"],
                "determinism_check": determinism_check["status"],
                "aggregate": artifact["aggregate"],
                "checkpoint": "NO_GO",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(lambda: main()))
