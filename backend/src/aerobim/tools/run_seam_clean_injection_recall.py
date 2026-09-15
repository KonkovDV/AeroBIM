"""Seam-clean FireRating injection recall on the wall+IDS CONTROL fixture.

Ten targeted mutants vs ``summary.passed=true`` CONTROL. Attribution is
rule_id + GUID + norm/target, not the house-5 CONTROL-multiset. Synthetic
only; does not close RT-001. Checkpoint GO; customer_go false.

Not registered in the operator catalog (cap ≤40).
"""

from __future__ import annotations

import argparse
import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.tools._cli_base import run_cli
from aerobim.tools.evaluate_injection_recall import (
    CONTROL_CLASS,
    PLAN_DEVIATION_SEAM_CLEAN,
    _git_commit,
    build_artifact,
    evaluate_manifest,
    make_deterministic_analyze,
    render_markdown,
    targeted_issue_key,
)

WALL_GUID = "38FRviGan7WhU9JrK165gm"
SEED = 20260915
SOURCE_LABEL = "wall_fire_rating_rei60_seam_clean"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _mut_value(text: str, new: str) -> str:
    return text.replace("IFCLABEL('REI60')", f"IFCLABEL('{new}')")


def _mut_unlink_pset(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("#8=")) + "\n"


def _mut_class_swap(text: str) -> str:
    return text.replace("IFCWALL(", "IFCCOLUMN(")


def _mut_rename_prop(text: str) -> str:
    return text.replace("'FireRating'", "'FireRatingX'")


def _mut_drop_wall(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("#6=")) + "\n"


Mutation = tuple[str, str, Callable[[str], str], str | None]

MUTATIONS: tuple[Mutation, ...] = (
    ("IDS_FIRE_REI45", "FireRating REI60→REI45", lambda t: _mut_value(t, "REI45"), WALL_GUID),
    ("IDS_FIRE_REI30", "FireRating REI60→REI30", lambda t: _mut_value(t, "REI30"), WALL_GUID),
    ("IDS_FIRE_REI90", "FireRating REI60→REI90", lambda t: _mut_value(t, "REI90"), WALL_GUID),
    ("IDS_FIRE_REI15", "FireRating REI60→REI15", lambda t: _mut_value(t, "REI15"), WALL_GUID),
    ("IDS_FIRE_EI60", "FireRating REI60→EI60", lambda t: _mut_value(t, "EI60"), WALL_GUID),
    ("IDS_FIRE_REI120", "FireRating REI60→REI120", lambda t: _mut_value(t, "REI120"), WALL_GUID),
    ("IDS_PSET_UNLINK", "removed IFCRELDEFINESBYPROPERTIES", _mut_unlink_pset, WALL_GUID),
    ("IDS_CLASS_SWAP", "IFCWALL→IFCCOLUMN", _mut_class_swap, None),
    ("IDS_PROP_RENAME", "FireRating→FireRatingX", _mut_rename_prop, WALL_GUID),
    ("IDS_WALL_REMOVED", "removed IFCWALL entity", _mut_drop_wall, None),
)


def write_seam_clean_tree(*, root: Path, source_ifc: Path) -> Path:
    """Write CONTROL + 10 mutant dirs and an injection manifest. Return manifest path."""

    text = source_ifc.read_text(encoding="utf-8")
    root.mkdir(parents=True, exist_ok=True)
    source_dir = root / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / source_ifc.name).write_text(text, encoding="utf-8")

    variants: list[dict[str, Any]] = [
        {
            "class": CONTROL_CLASS,
            "applied": True,
            "locator": source_ifc.name,
            "note": "unmutated-control",
        }
    ]
    control_dir = root / CONTROL_CLASS.lower()
    control_dir.mkdir(parents=True, exist_ok=True)
    (control_dir / source_ifc.name).write_text(text, encoding="utf-8")

    for class_name, note, mutator, expected_guid in MUTATIONS:
        variant_dir = root / class_name.lower()
        variant_dir.mkdir(parents=True, exist_ok=True)
        (variant_dir / source_ifc.name).write_text(mutator(text), encoding="utf-8")
        row: dict[str, Any] = {
            "class": class_name,
            "applied": True,
            "locator": source_ifc.name,
            "note": note,
        }
        if expected_guid:
            row["expected_element_guid"] = expected_guid
        variants.append(row)

    manifest = {
        "artifact": "injection_manifest",
        "seed": SEED,
        "source": str(source_dir.resolve()),
        "attribution": "targeted",
        "variants": variants,
    }
    manifest_path = root / "injection_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def evaluate_seam_clean_tree(
    *,
    injection_root: Path,
    manifest_path: Path,
    ids_path: Path,
    storage_dir: Path,
) -> dict[str, Any]:
    rules_path = injection_root / "empty-rules.txt"
    rules_path.write_text("", encoding="utf-8")
    analyze = make_deterministic_analyze(
        ids_path=ids_path,
        rules_text="",
        storage_dir=storage_dir,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    issues_by_class: dict[str, list[Any]] = {}
    analyze_errors: dict[str, str] = {}
    for variant in manifest.get("variants", []):
        defect_class = str(variant.get("class") or "")
        variant_dir = injection_root / defect_class.lower()
        try:
            issues_by_class[defect_class] = analyze(variant_dir, f"seam-{defect_class}")
        except Exception as exc:
            issues_by_class[defect_class] = []
            analyze_errors[defect_class] = f"{type(exc).__name__}: {exc}"[:300]

    source_dir = Path(str(manifest["source"]))
    source_issues = analyze(source_dir, "seam-source")
    from collections import Counter

    control_counter = Counter(targeted_issue_key(i) for i in issues_by_class[CONTROL_CLASS])
    source_counter = Counter(targeted_issue_key(i) for i in source_issues)
    if source_counter != control_counter:
        raise ValueError("Non-deterministic contour: source and CONTROL targeted keys differ")
    evaluation = evaluate_manifest(
        manifest,
        issues_by_class,
        analyze_errors,
        key_fn=targeted_issue_key,
        require_clean_control=True,
    )
    determinism_check = {
        "status": "pass",
        "source_issue_count": sum(source_counter.values()),
        "control_issue_count": sum(control_counter.values()),
        "method": "analyze(source) targeted key == analyze(CONTROL) targeted key",
    }
    return build_artifact(
        manifest=manifest,
        manifest_path=manifest_path,
        evaluation=evaluation,
        determinism_check=determinism_check,
        git_commit=_git_commit(repo_root()),
        source_label=SOURCE_LABEL,
        plan_deviation=PLAN_DEVIATION_SEAM_CLEAN,
        detection_proxy=(
            "killed = targeted (rule_id, element_guid, norm_clause|target_ref) "
            "multiset differs from seam-clean CONTROL, or fail-closed analyze error"
        ),
        schema_version="1.1.0",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--md", type=Path, default=None)
    parser.add_argument("--write-docs-evidence", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    root = repo_root()
    source_ifc = root / "samples" / "ifc" / "wall-fire-rating-rei60.ifc"
    ids_path = root / "samples" / "ids" / "wall-fire-rating.ids"
    temp: tempfile.TemporaryDirectory[str] | None = None
    work = args.work_dir
    if work is None:
        temp = tempfile.TemporaryDirectory(prefix="aerobim-seam-clean-")
        work = Path(temp.name)

    try:
        storage = work / "var"
        injection_root = work / "injected"
        manifest_path = write_seam_clean_tree(root=injection_root, source_ifc=source_ifc)
        artifact = evaluate_seam_clean_tree(
            injection_root=injection_root,
            manifest_path=manifest_path,
            ids_path=ids_path,
            storage_dir=storage,
        )
    finally:
        if temp is not None:
            # Artifact already built; tree can go.
            pass

    text = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    out = args.output
    if args.write_docs_evidence:
        out = root / "docs" / "evidence" / "defect-injection-recall-run-latest.json"
        md = args.md or (
            root / "docs" / "evidence" / "DEFECT_INJECTION_RECALL_SEAM_CLEAN_2026_09.md"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        md.write_text(render_markdown(artifact), encoding="utf-8")
        print(f"docs_evidence={out}")
        print(f"md={md}")
    elif out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        if args.md:
            args.md.write_text(render_markdown(artifact), encoding="utf-8")

    if temp is not None:
        temp.cleanup()

    print(
        json.dumps(
            {
                "status": "EXECUTED",
                "claim_level": artifact["claim_level"],
                "aggregate": artifact["aggregate"],
                "control_issue_count": artifact["control_issue_count"],
                "checkpoint": CHECKPOINT,
                "closes_rt001": False,
            },
            ensure_ascii=False,
        )
    )
    trials = int(artifact["aggregate"]["trials"])
    killed = int(artifact["aggregate"]["killed"])
    if trials < 10 or killed < 9:
        return 1
    if int(artifact["control_issue_count"]) != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(lambda: main()))
