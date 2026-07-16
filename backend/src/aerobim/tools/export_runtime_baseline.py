"""Export machine-readable runtime baseline metrics (red-team R5).

Generates LOC / test counts / extraction F1 so docs cannot drift from reality.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    # tools/ -> aerobim/ -> src/ -> backend/ -> repo root
    return Path(__file__).resolve().parents[4]


def _count_lines(root: Path, pattern: str) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob(pattern):
        if any(
            part in {".venv", "__pycache__", ".mypy_cache", ".ruff_cache"} for part in path.parts
        ):
            continue
        try:
            total += sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return total


def _count_tests(tests_root: Path) -> int:
    if not tests_root.exists():
        return 0
    count = 0
    for path in tests_root.rglob("test_*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        count += sum(
            1
            for line in text.splitlines()
            if line.lstrip().startswith("def test_") or line.lstrip().startswith("async def test_")
        )
    return count


def _extraction_macro_f1(backend_root: Path) -> float | None:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "aerobim.tools.evaluate_extraction", "--min-macro-f1", "0.0"],
            cwd=backend_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode not in {0, 1}:
        return None
    text = completed.stdout.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    value = payload.get("macro_f1")
    return float(value) if isinstance(value, int | float) else None


def export_runtime_baseline(*, backend_root: Path | None = None) -> dict[str, object]:
    backend = (backend_root or (_repo_root() / "backend")).resolve()
    src_root = backend / "src" / "aerobim"
    tests_root = backend / "tests"
    src_loc = _count_lines(src_root, "*.py")
    test_loc = _count_lines(tests_root, "*.py")
    test_count = _count_tests(tests_root)
    macro_f1 = _extraction_macro_f1(backend)
    return {
        "artifact_type": "aerobim_runtime_baseline",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "author_relationship": "self",
        "corpus_kind": "fixture",
        "metrics": {
            "backend_src_loc": src_loc,
            "backend_test_loc": test_loc,
            "backend_test_functions": test_count,
            "extraction_macro_f1": macro_f1,
        },
        "readme_snippet": (
            f"Backend src ~{src_loc} LOC; tests ~{test_loc} LOC; "
            f"{test_count}+ test functions; extraction macro_f1="
            f"{macro_f1 if macro_f1 is not None else 'n/a'} (generated)"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write JSON artifact (default: docs/evidence/runtime-baseline-latest.json)",
    )
    parser.add_argument(
        "--check-readme",
        action="store_true",
        help="Fail if README lacks AEROBIM_RUNTIME_BASELINE marker block",
    )
    args = parser.parse_args(argv)
    repo = _repo_root()
    baseline = export_runtime_baseline(backend_root=repo / "backend")
    out = args.out or (repo / "docs" / "evidence" / "runtime-baseline-latest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(baseline, ensure_ascii=False, indent=2))
    if args.check_readme:
        readme = (repo / "README.md").read_text(encoding="utf-8")
        if "<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->" not in readme:
            print(
                "README missing <!-- AEROBIM_RUNTIME_BASELINE:BEGIN --> marker; "
                "insert generated snippet before claiming LOC/test counts.",
                file=sys.stderr,
            )
            return 1
        artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
        if not artifact.exists():
            print("Missing docs/evidence/runtime-baseline-latest.json", file=sys.stderr)
            return 1
        try:
            stored = json.loads(artifact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("Invalid runtime-baseline-latest.json", file=sys.stderr)
            return 1
        stored_metrics = stored.get("metrics") if isinstance(stored, dict) else None
        live_metrics = baseline.get("metrics")
        if not isinstance(stored_metrics, dict) or not isinstance(live_metrics, dict):
            print("Baseline metrics missing", file=sys.stderr)
            return 1
        for key in ("backend_src_loc", "backend_test_functions"):
            stored_value = int(stored_metrics.get(key, -1))
            live_value = int(live_metrics.get(key, -2))
            # Allow small churn from concurrent edits within the same gate run.
            if abs(stored_value - live_value) > 50:
                print(
                    f"Baseline drift for {key}: artifact={stored_value} live={live_value}",
                    file=sys.stderr,
                )
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
