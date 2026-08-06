"""Export machine-readable runtime baseline metrics (red-team R5 / WP-01).

Generates LOC / test counts / extraction F1 so docs cannot drift from reality.
Schema 1.2.0 fills backend/frontend pass counts, quality_gates from real runs,
and an environment fingerprint. ``--check-complete`` fails CI when any required
field is null/UNKNOWN.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "1.2.1"
_QUALITY_GATE_KEYS = ("ruff", "mypy", "pytest", "vitest", "build")
_ALLOWED_GATE_VALUES = frozenset({"PASS", "FAIL", "SKIPPED", "UNKNOWN", "NOT_RUN"})
_COMPLETE_GATE_VALUE = "PASS"
_BASELINE_MARKER_BEGIN = "<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->"
_ENV_DOC_MARKER_BEGIN = "<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->"
_ENV_DOC_MARKER_END = "<!-- AEROBIM_DOCUMENTED_ENV:END -->"
_ENV_DOC_LINE_RE = re.compile(r"^AEROBIM_[A-Z][A-Z0-9_]*$")
_ENV_TABLE_CELL_RE = re.compile(r"`(AEROBIM_[A-Z][A-Z0-9_]*)`")
_ENV_MARKER_NOISE = frozenset({"AEROBIM_DOCUMENTED_ENV", "AEROBIM_RUNTIME_BASELINE"})
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


def _git(repo: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _commit_sha(repo: Path) -> str:
    sha = _git(repo, "rev-parse", "HEAD")
    return sha or "unknown"


def _tree_sha(repo: Path) -> str:
    sha = _git(repo, "rev-parse", "HEAD^{tree}")
    return sha or "unknown"


def _working_tree_clean(repo: Path) -> bool | None:
    if not _git(repo, "rev-parse", "--is-inside-work-tree"):
        return None
    return _git(repo, "status", "--porcelain") == ""


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _environment_fingerprint(repo: Path) -> dict[str, object]:
    lock = repo / "backend" / "requirements-lock.txt"
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "lockfile_sha256": _sha256_file(lock),
        "lockfile_path": "backend/requirements-lock.txt",
    }


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
    if value not in _ALLOWED_GATE_VALUES:
        raise argparse.ArgumentTypeError(
            f"invalid gate value {value!r}; expected one of "
            f"{', '.join(sorted(_ALLOWED_GATE_VALUES))}"
        )
    return key, value


def parse_pytest_junit(path: Path) -> dict[str, int]:
    """Parse pytest JUnit XML into passed / skipped / failed / errors counts."""
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    if not suites and root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
    tests = skipped = failures = errors = 0
    for suite in suites:
        tests += int(suite.attrib.get("tests", 0))
        skipped += int(suite.attrib.get("skipped", 0))
        failures += int(suite.attrib.get("failures", 0))
        errors += int(suite.attrib.get("errors", 0))
    failed = failures + errors
    passed = max(tests - skipped - failed, 0)
    return {
        "tests_collected": tests,
        "tests_passed": passed,
        "tests_skipped": skipped,
        "tests_failed": failed,
    }


def completeness_errors(baseline: dict[str, Any]) -> list[str]:
    """Return human-readable errors when baseline is not WP-01 complete."""
    errors: list[str] = []
    if baseline.get("schema_version") != _SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {_SCHEMA_VERSION!r}, got {baseline.get('schema_version')!r}"
        )
    commit = baseline.get("commit_sha")
    if not isinstance(commit, str) or not commit or commit == "unknown":
        errors.append("commit_sha missing or unknown")
    tree = baseline.get("tree_sha")
    if not isinstance(tree, str) or not tree or tree == "unknown":
        errors.append("tree_sha missing or unknown")

    backend = baseline.get("backend")
    if not isinstance(backend, dict):
        errors.append("backend block missing")
    else:
        for key in ("tests_passed", "tests_skipped", "tests_failed", "tests_collected"):
            value = backend.get(key)
            if not isinstance(value, int) or value < 0:
                errors.append(f"backend.{key} must be a non-negative int, got {value!r}")
        if isinstance(backend.get("tests_passed"), int) and backend["tests_passed"] == 0:
            errors.append("backend.tests_passed is 0 (refusing empty run as complete)")

    frontend = baseline.get("frontend")
    if not isinstance(frontend, dict):
        errors.append("frontend block missing")
    else:
        value = frontend.get("tests_passed")
        if not isinstance(value, int) or value < 0:
            errors.append(f"frontend.tests_passed must be a non-negative int, got {value!r}")

    gates = baseline.get("quality_gates")
    if not isinstance(gates, dict):
        errors.append("quality_gates missing")
    else:
        for key in _QUALITY_GATE_KEYS:
            value = gates.get(key)
            if value != _COMPLETE_GATE_VALUE:
                errors.append(
                    f"quality_gates.{key} must be {_COMPLETE_GATE_VALUE!r} for complete "
                    f"baseline, got {value!r}"
                )

    env = baseline.get("environment")
    if not isinstance(env, dict):
        errors.append("environment fingerprint missing")
    else:
        for key in ("python_version", "platform", "lockfile_sha256"):
            if not env.get(key):
                errors.append(f"environment.{key} missing")

    metrics = baseline.get("metrics")
    if not isinstance(metrics, dict) or not isinstance(
        metrics.get("extraction_macro_f1"), int | float
    ):
        errors.append("metrics.extraction_macro_f1 missing")
    return errors


def export_runtime_baseline(
    *,
    backend_root: Path | None = None,
    frontend_tests_passed: int | None = None,
    tests_passed: int | None = None,
    tests_skipped: int | None = None,
    tests_failed: int | None = None,
    tests_collected: int | None = None,
    quality_gates: dict[str, str] | None = None,
    commit_sha: str | None = None,
    tree_sha: str | None = None,
    environment: dict[str, object] | None = None,
) -> dict[str, object]:
    backend = (backend_root or (_repo_root() / "backend")).resolve()
    repo = backend.parent
    src_root = backend / "src" / "aerobim"
    tests_root = backend / "tests"
    src_loc = _count_lines(src_root, "*.py")
    test_loc = _count_lines(tests_root, "*.py")
    test_count = _count_tests(tests_root)
    collected = test_count if tests_collected is None else tests_collected
    macro_f1 = _extraction_macro_f1(backend)
    gates = _default_quality_gates()
    if quality_gates:
        for key, value in quality_gates.items():
            if key in gates:
                gates[key] = value
    f1_display = f"{macro_f1}" if macro_f1 is not None else "n/a"
    env = environment if environment is not None else _environment_fingerprint(repo)
    return {
        "artifact_type": "aerobim_runtime_baseline",
        "schema_version": _SCHEMA_VERSION,
        "commit_sha": commit_sha if commit_sha is not None else _commit_sha(repo),
        "tree_sha": tree_sha if tree_sha is not None else _tree_sha(repo),
        "working_tree_clean": _working_tree_clean(repo),
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "corpus_kind": "fixture",
        "claim_boundary": (
            "Engineering build evidence only. Fixture macro_f1 != product accuracy. "
            "Checkpoint NO_GO until RT-001/002/003."
        ),
        "backend": {
            "tests_collected": collected,
            "tests_passed": tests_passed,
            "tests_skipped": tests_skipped,
            "tests_failed": tests_failed,
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
        "environment": env,
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
        "documented_env_vars": _configuration_env_names(repo / "README.md"),
        "architecture_inventory": _live_architecture_inventory(repo),
    }


def _live_architecture_inventory(repo: Path) -> dict[str, int]:
    """Count public domain Protocols, adapter modules, and DI tokens from source."""
    domain = repo / "backend" / "src" / "aerobim" / "domain"
    adapters_root = repo / "backend" / "src" / "aerobim" / "infrastructure" / "adapters"
    tokens_path = repo / "backend" / "src" / "aerobim" / "core" / "di" / "tokens.py"
    private = {"_GuidLookup", "_HitlEventLike", "_ReportLike"}
    ports: set[str] = set()
    if domain.exists():
        for path in domain.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r"^class\s+(\w+)\s*\([^)]*Protocol", text, re.M):
                name = match.group(1)
                if name not in private:
                    ports.add(name)
    adapters = 0
    if adapters_root.exists():
        adapters = sum(1 for path in adapters_root.glob("*.py") if path.name != "__init__.py")
    tokens = 0
    if tokens_path.exists():
        tokens = len(
            set(
                re.findall(
                    r"^\s+([A-Z][A-Z0-9_]+)\s*=",
                    tokens_path.read_text(encoding="utf-8"),
                    re.M,
                )
            )
        )
    return {
        "public_domain_protocols": len(ports),
        "adapter_modules": adapters,
        "di_tokens": tokens,
    }


def _all_aerobim_names_in_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(set(re.findall(r"\bAEROBIM_[A-Z][A-Z0-9_]*\b", path.read_text(encoding="utf-8"))))


def _symdiff_message(left_label: str, right_label: str, left: set[str], right: set[str]) -> str:
    only_left = sorted(left - right)
    only_right = sorted(right - left)
    return (
        f"{left_label} vs {right_label} AEROBIM_* set mismatch "
        f"(symmetric_difference): only_in_{left_label}={only_left[:12]} "
        f"only_in_{right_label}={only_right[:12]}"
    )


def _configuration_env_names(readme_path: Path) -> list[str]:
    """Env names listed in README.md ``## Configuration`` table (SSOT for documented knobs)."""
    if not readme_path.exists():
        return []
    text = readme_path.read_text(encoding="utf-8")
    start = text.find("## Configuration")
    if start < 0:
        return []
    end = text.find("\n## ", start + 3)
    block = text[start:] if end < 0 else text[start:end]
    names = set(_ENV_TABLE_CELL_RE.findall(block))
    # Deprecated alias mentioned in prose inside the Configuration section.
    if "AEROBIM_LLM_LOCAL_ENABLED" in block:
        names.add("AEROBIM_LLM_LOCAL_ENABLED")
    names -= _ENV_MARKER_NOISE
    return sorted(names)


def _documented_env_marker_names(text: str) -> list[str] | None:
    begin = text.find(_ENV_DOC_MARKER_BEGIN)
    if begin < 0:
        return None
    end = text.find(_ENV_DOC_MARKER_END, begin)
    if end < 0:
        return None
    block = text[begin + len(_ENV_DOC_MARKER_BEGIN) : end]
    names: set[str] = set()
    for line in block.splitlines():
        token = line.strip()
        if _ENV_DOC_LINE_RE.match(token):
            names.add(token)
    names -= _ENV_MARKER_NOISE
    return sorted(names)


def _check_documented_env_sets(repo: Path) -> list[str]:
    """Fail on set inequality (symmetric difference), never on count equality alone."""
    errors: list[str] = []
    expected = _configuration_env_names(repo / "README.md")
    if not expected:
        return ["README.md ## Configuration has no AEROBIM_* names"]

    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    if artifact.exists():
        try:
            stored = json.loads(artifact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("Invalid runtime-baseline-latest.json while checking documented_env_vars")
            stored = None
        if isinstance(stored, dict) and "documented_env_vars" in stored:
            artifact_names = stored.get("documented_env_vars")
            if not isinstance(artifact_names, list):
                errors.append("runtime-baseline-latest.json documented_env_vars must be a list")
            else:
                artifact_set = {str(x) for x in artifact_names}
                if artifact_set != set(expected):
                    errors.append(
                        _symdiff_message(
                            "config",
                            "artifact",
                            set(expected),
                            artifact_set,
                        )
                    )

    marker_sets: dict[str, set[str]] = {}
    for name in ("README.md", "README.ru.md"):
        path = repo / name
        if not path.exists():
            errors.append(f"Missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        names = _documented_env_marker_names(text)
        if names is None:
            errors.append(
                f"{name} missing {_ENV_DOC_MARKER_BEGIN}…{_ENV_DOC_MARKER_END} "
                "(must list the same AEROBIM_* set as README.md Configuration)"
            )
            continue
        marker_sets[name] = set(names)
        if set(names) != set(expected):
            errors.append(
                _symdiff_message(name, "README.md_Configuration", set(names), set(expected))
            )

    if "README.md" in marker_sets and "README.ru.md" in marker_sets:
        if marker_sets["README.md"] != marker_sets["README.ru.md"]:
            errors.append(
                _symdiff_message(
                    "README.md_marker",
                    "README.ru.md_marker",
                    marker_sets["README.md"],
                    marker_sets["README.ru.md"],
                )
            )

    # Full-file unique names must also match (catches prose drift beyond the marker block).
    en_all = set(_all_aerobim_names_in_file(repo / "README.md")) - _ENV_MARKER_NOISE
    ru_all = set(_all_aerobim_names_in_file(repo / "README.ru.md")) - _ENV_MARKER_NOISE
    if en_all and ru_all and en_all != ru_all:
        errors.append(_symdiff_message("README.md_all", "README.ru.md_all", en_all, ru_all))

    return errors


def _check_architecture_inventory(repo: Path) -> list[str]:
    """README must publish the live protocol/adapter/token counts from source."""
    live = _live_architecture_inventory(repo)
    errors: list[str] = []
    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    if artifact.exists():
        try:
            stored = json.loads(artifact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            stored = None
            errors.append(
                "Invalid runtime-baseline-latest.json while checking architecture_inventory"
            )
        if isinstance(stored, dict):
            art = stored.get("architecture_inventory")
            if not isinstance(art, dict):
                errors.append(
                    "runtime-baseline-latest.json missing architecture_inventory "
                    f"(live={live}; regenerate via export_runtime_baseline)"
                )
            else:
                for key, value in live.items():
                    if art.get(key) != value:
                        errors.append(
                            f"architecture_inventory.{key} drift: "
                            f"artifact={art.get(key)!r} live={value}"
                        )

    needles = {
        "public_domain_protocols": (
            f"{live['public_domain_protocols']} domain Protocol",
            f"{live['public_domain_protocols']} Protocol ports",
        ),
        "adapter_modules": (
            f"{live['adapter_modules']} infrastructure adapter",
            f"{live['adapter_modules']} adapter modules",
        ),
        "di_tokens": (
            f"{live['di_tokens']} DI token",
            f"{live['di_tokens']} DI tokens",
        ),
    }
    for readme_name in ("README.md", "README.ru.md"):
        path = repo / readme_name
        if not path.exists():
            errors.append(f"Missing {readme_name}")
            continue
        text = path.read_text(encoding="utf-8")
        for key, variants in needles.items():
            if not any(v in text for v in variants):
                errors.append(
                    f"{readme_name} missing live architecture_inventory.{key}="
                    f"{live[key]} (expected one of {list(variants)})"
                )
    return errors


def _check_readme_markers(repo: Path) -> list[str]:
    errors: list[str] = []
    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    expected_snippet: str | None = None
    if artifact.exists():
        try:
            stored = json.loads(artifact.read_text(encoding="utf-8"))
            if isinstance(stored, dict) and isinstance(stored.get("readme_snippet"), str):
                expected_snippet = stored["readme_snippet"].strip()
        except json.JSONDecodeError:
            errors.append("Invalid runtime-baseline-latest.json while checking README snippets")
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
            continue
        if expected_snippet is None:
            continue
        begin = text.find(_BASELINE_MARKER_BEGIN)
        end = text.find("<!-- AEROBIM_RUNTIME_BASELINE:END -->", begin)
        if end < 0:
            errors.append(f"{name} missing AEROBIM_RUNTIME_BASELINE:END marker")
            continue
        block = text[begin:end]
        if expected_snippet not in block:
            errors.append(
                f"{name} runtime baseline snippet drifts from "
                "docs/evidence/runtime-baseline-latest.json readme_snippet (WP-08)"
            )
    errors.extend(_check_documented_env_sets(repo))
    errors.extend(_check_architecture_inventory(repo))
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


def _check_artifact_complete(repo: Path) -> list[str]:
    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    if not artifact.exists():
        return ["Missing docs/evidence/runtime-baseline-latest.json"]
    try:
        stored = json.loads(artifact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["Invalid runtime-baseline-latest.json"]
    if not isinstance(stored, dict):
        return ["runtime-baseline-latest.json must be an object"]
    return completeness_errors(stored)


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
            "Fail if README.md / README.ru.md lack AEROBIM_RUNTIME_BASELINE markers, "
            "documented-env name *sets* disagree (symmetric difference, not counts), "
            "live architecture_inventory (ports/adapters/tokens) missing from README/artifact, "
            "or committed artifact drifts beyond ±50 on loc/test_functions"
        ),
    )
    parser.add_argument(
        "--check-complete",
        action="store_true",
        help=(
            "Fail if committed runtime-baseline-latest.json has null/UNKNOWN fields "
            "(WP-01). Use with --check-readme in CI."
        ),
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Refuse to write an incomplete baseline artifact",
    )
    parser.add_argument(
        "--frontend-tests-passed",
        type=int,
        default=None,
        metavar="N",
        help="Record frontend vitest pass count in the frontend.tests_passed field",
    )
    parser.add_argument(
        "--tests-passed",
        type=int,
        default=None,
        metavar="N",
        help="Record backend pytest passed count",
    )
    parser.add_argument(
        "--tests-skipped",
        type=int,
        default=None,
        metavar="N",
        help="Record backend pytest skipped count",
    )
    parser.add_argument(
        "--tests-failed",
        type=int,
        default=None,
        metavar="N",
        help="Record backend pytest failed+error count",
    )
    parser.add_argument(
        "--pytest-junit",
        type=Path,
        default=None,
        help="Read tests_passed/skipped/failed from a pytest JUnit XML report",
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

    tests_passed = args.tests_passed
    tests_skipped = args.tests_skipped
    tests_failed = args.tests_failed
    tests_collected: int | None = None
    if args.pytest_junit is not None:
        parsed = parse_pytest_junit(args.pytest_junit)
        tests_passed = parsed["tests_passed"] if tests_passed is None else tests_passed
        tests_skipped = parsed["tests_skipped"] if tests_skipped is None else tests_skipped
        tests_failed = parsed["tests_failed"] if tests_failed is None else tests_failed
        tests_collected = parsed["tests_collected"]

    if args.check_readme or args.check_complete:
        live = export_runtime_baseline(backend_root=repo / "backend", quality_gates=gates)
        errors: list[str] = []
        if args.check_readme:
            errors.extend(_check_readme_markers(repo) + _check_artifact_drift(repo, live))
        if args.check_complete:
            errors.extend(_check_artifact_complete(repo))
        if errors:
            for message in errors:
                print(message, file=sys.stderr)
            return 1
        print("README markers, documented-env sets, runtime baseline drift, and completeness OK")
        return 0

    baseline = export_runtime_baseline(
        backend_root=repo / "backend",
        frontend_tests_passed=args.frontend_tests_passed,
        tests_passed=tests_passed,
        tests_skipped=tests_skipped,
        tests_failed=tests_failed,
        tests_collected=tests_collected,
        quality_gates=gates,
    )
    if args.require_complete:
        errors = completeness_errors(baseline)
        if errors:
            for message in errors:
                print(message, file=sys.stderr)
            return 1

    out = args.out or (repo / "docs" / "evidence" / "runtime-baseline-latest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(baseline, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
