"""Export machine-readable runtime baseline metrics (red-team R5).

Generates LOC / test counts / extraction F1 so docs cannot drift from reality.
Schema 1.1.0 adds commit SHA, backend/frontend blocks, and quality_gates.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

_SCHEMA_VERSION = "1.1.0"
_QUALITY_GATE_KEYS = ("ruff", "mypy", "pytest", "vitest", "build")
_BASELINE_MARKER_BEGIN = "<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->"
_DRIFT_KEYS = ("backend_src_loc", "backend_test_loc", "backend_test_functions")
_DRIFT_TOLERANCE = 50


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


def _commit_sha(repo: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    if completed.returncode != 0:
        return "unknown"
    sha = completed.stdout.strip()
    return sha or "unknown"


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


def _default_quality_gates() -> dict[str, str]:
    return {key: "UNKNOWN" for key in _QUALITY_GATE_KEYS}


def _parse_gate(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"gate must be KEY=VALUE, got {raw!r}")
    key, value = raw.split("=", 1)
    key = key.strip().lower()
    value = value.strip().upper()
    if key not in _QUALITY_GATE_KEYS:
        raise argparse.ArgumentTypeError(
            f"unknown gate key {key!r}; expected one of {', '.join(_QUALITY_GATE_KEYS)}"
        )
    if not value:
        raise argparse.ArgumentTypeError(f"empty gate value for {key}")
    return key, value


def export_runtime_baseline(
    *,
    backend_root: Path | None = None,
    frontend_tests_passed: int | None = None,
    quality_gates: dict[str, str] | None = None,
    commit_sha: str | None = None,
) -> dict[str, object]:
    backend = (backend_root or (_repo_root() / "backend")).resolve()
    repo = backend.parent
    src_root = backend / "src" / "aerobim"
    tests_root = backend / "tests"
    src_loc = _count_lines(src_root, "*.py")
    test_loc = _count_lines(tests_root, "*.py")
    test_count = _count_tests(tests_root)
    macro_f1 = _extraction_macro_f1(backend)
    gates = _default_quality_gates()
    if quality_gates:
        for key, value in quality_gates.items():
            if key in gates:
                gates[key] = value
    f1_display = f"{macro_f1}" if macro_f1 is not None else "n/a"
    return {
        "artifact_type": "aerobim_runtime_baseline",
        "schema_version": _SCHEMA_VERSION,
        "commit_sha": commit_sha if commit_sha is not None else _commit_sha(repo),
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "corpus_kind": "fixture",
        "backend": {
            "tests_collected": test_count,
            "tests_passed": None,
            "tests_skipped": None,
            "source_loc": src_loc,
            "test_loc": test_loc,
            "test_functions": test_count,
        },
        "frontend": {
            "tests_passed": frontend_tests_passed,
            "note": (
                "Recorded from last CI/local vitest run when provided via --frontend-tests-passed"
            ),
        },
        "quality_gates": gates,
        "metrics": {
            "backend_src_loc": src_loc,
            "backend_test_loc": test_loc,
            "backend_test_functions": test_count,
            "extraction_macro_f1": macro_f1,
        },
        "readme_snippet": (
            f"Backend src ~{src_loc} LOC; tests ~{test_loc} LOC; "
            f"{test_count}+ test functions; extraction macro_f1={f1_display} "
            f"(fixture corpus; not product accuracy)"
        ),
    }


def _check_readme_markers(repo: Path) -> list[str]:
    errors: list[str] = []
    for name in ("README.md", "README.ru.md"):
        path = repo / name
        if not path.exists():
            errors.append(f"Missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        if _BASELINE_MARKER_BEGIN not in text:
            errors.append(
                f"{name} missing {_BASELINE_MARKER_BEGIN} marker; "
                "insert generated snippet before claiming LOC/test counts."
            )
    return errors


def _check_artifact_drift(repo: Path, live: dict[str, object]) -> list[str]:
    errors: list[str] = []
    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    if not artifact.exists():
        return ["Missing docs/evidence/runtime-baseline-latest.json"]
    try:
        stored = json.loads(artifact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["Invalid runtime-baseline-latest.json"]
    stored_metrics = stored.get("metrics") if isinstance(stored, dict) else None
    live_metrics = live.get("metrics")
    if not isinstance(stored_metrics, dict) or not isinstance(live_metrics, dict):
        return ["Baseline metrics missing"]
    for key in _DRIFT_KEYS:
        stored_value = int(stored_metrics.get(key, -1))
        live_value = int(live_metrics.get(key, -2))
        # Allow small churn from concurrent edits within the same gate run.
        if abs(stored_value - live_value) > _DRIFT_TOLERANCE:
            errors.append(f"Baseline drift for {key}: artifact={stored_value} live={live_value}")
    return errors


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
        help=(
            "Fail if README.md / README.ru.md lack AEROBIM_RUNTIME_BASELINE markers "
            "or if committed artifact drifts beyond ±50 on loc/test_functions"
        ),
    )
    parser.add_argument(
        "--frontend-tests-passed",
        type=int,
        default=None,
        metavar="N",
        help="Record frontend vitest pass count in the frontend.tests_passed field",
    )
    parser.add_argument(
        "--gate",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Set a quality_gates entry (repeatable). "
            f"Keys: {', '.join(_QUALITY_GATE_KEYS)}. Example: --gate ruff=PASS"
        ),
    )
    args = parser.parse_args(argv)
    repo = _repo_root()
    gates = _default_quality_gates()
    for raw in args.gate:
        key, value = _parse_gate(raw)
        gates[key] = value
    baseline = export_runtime_baseline(
        backend_root=repo / "backend",
        frontend_tests_passed=args.frontend_tests_passed,
        quality_gates=gates,
    )
    if args.check_readme:
        errors = _check_readme_markers(repo) + _check_artifact_drift(repo, baseline)
        if errors:
            for message in errors:
                print(message, file=sys.stderr)
            return 1
        print("README markers and runtime baseline drift OK")
        return 0

    out = args.out or (repo / "docs" / "evidence" / "runtime-baseline-latest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(baseline, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
