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
import os
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "1.4.0"
_QUALITY_GATE_KEYS = ("ruff", "mypy", "pytest", "vitest", "build")
_ALLOWED_GATE_VALUES = frozenset({"PASS", "FAIL", "SKIPPED", "UNKNOWN", "NOT_RUN"})
_COMPLETE_GATE_VALUE = "PASS"
_REQUIRED_GATES_ATTESTED = frozenset(
    {
        "test",
        "frontend",
        "supply-chain-audit",
        "sprint-2-1-gates",
        "security-regression",
        "offline-bundle-smoke",
        "openapi-contract",
    }
)
_CODE_ENV_RE = re.compile(
    r"os\.(?:getenv|environ\.get)\(\s*[\"'](AEROBIM_[A-Z][A-Z0-9_]*)[\"']"
    r"|os\.environ\[\s*[\"'](AEROBIM_[A-Z][A-Z0-9_]*)[\"']\s*\]"
)
_HELPER_ENV_RE = re.compile(
    r"_(?:read_int|read_bool|read_float|read_optional_int|optional_bool)"
    r"\(\s*[\"'](AEROBIM_[A-Z][A-Z0-9_]*)[\"']"
)
_IN_ENVIRON_RE = re.compile(r"[\"'](AEROBIM_[A-Z][A-Z0-9_]*)[\"']\s+in\s+os\.environ")
_ENV_PREFER_CALL_RE = re.compile(
    r"_(?:env_prefer|read_optional_int_prefer)\(([^)]*)\)",
    re.DOTALL,
)
_QUOTED_AEROBIM_RE = re.compile(r"[\"'](AEROBIM_[A-Z][A-Z0-9_]*)[\"']")
_EXTRA_ENV_SCAN_RELPATHS = ("backend/src/aerobim/tools/export_runtime_baseline.py",)
_BASELINE_MARKER_BEGIN = "<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->"
_ENV_DOC_MARKER_BEGIN = "<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->"
_ENV_DOC_MARKER_END = "<!-- AEROBIM_DOCUMENTED_ENV:END -->"
_ENV_DOC_LINE_RE = re.compile(r"^AEROBIM_[A-Z][A-Z0-9_]*$")
_ENV_TABLE_CELL_RE = re.compile(r"`(AEROBIM_[A-Z][A-Z0-9_]*)`")
_ENV_MARKER_NOISE = frozenset({"AEROBIM_DOCUMENTED_ENV", "AEROBIM_RUNTIME_BASELINE"})
_DRIFT_KEYS = ("backend_src_loc", "backend_test_loc", "backend_test_functions")
_DRIFT_TOLERANCE = 50
_COMMITTED_BASELINE = "docs/evidence/runtime-baseline-latest.json"
_LOCAL_BASELINE_DIR = "docs/evidence/local"


def _complete_github_actions_env() -> dict[str, str] | None:
    """Return required GITHUB_* vars only when the Actions environment is complete."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return None
    run_id = os.environ.get("GITHUB_RUN_ID")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT")
    workflow_ref = os.environ.get("GITHUB_WORKFLOW_REF")
    github_sha = os.environ.get("GITHUB_SHA")
    if not run_id or not run_attempt or not workflow_ref or not github_sha:
        return None
    return {
        "run_id": run_id,
        "run_attempt": run_attempt,
        "workflow_ref": workflow_ref,
        "github_sha": github_sha,
    }


def _gates_attested_from_env(*, ci_complete: bool) -> list[str]:
    """N-23: AEROBIM_GATES_ATTESTED is honored only under complete CI attestation.

    Locally the variable is ignored (empty gates_attested). In CI the value must
    equal ``_REQUIRED_GATES_ATTESTED`` exactly; otherwise attestation is incomplete.
    """
    if not ci_complete:
        return []
    raw = os.environ.get("AEROBIM_GATES_ATTESTED", "")
    from_env = sorted(part.strip() for part in raw.split(",") if part.strip())
    if set(from_env) != _REQUIRED_GATES_ATTESTED:
        return from_env
    return sorted(_REQUIRED_GATES_ATTESTED)


def _resolve_attestation_from_environment() -> dict[str, object]:
    """WP-A1b / N-18: attestation is derived from the process environment only."""
    ci = _complete_github_actions_env()
    gates = _gates_attested_from_env(ci_complete=ci is not None)
    attestation: dict[str, object] = {
        "attested_by": "local",
        "run_id": None,
        "run_attempt": None,
        "workflow_ref": None,
        "github_sha": None,
        "runner_os": os.environ.get("RUNNER_OS") or platform.system(),
        "runner_python": platform.python_version(),
        "gates_attested": gates,
    }
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return attestation
    if ci is None:
        attestation["attestation_environment_incomplete"] = True
        return attestation
    if set(gates) != _REQUIRED_GATES_ATTESTED:
        attestation["attestation_environment_incomplete"] = True
        attestation["attestation_gates_attested_invalid"] = True
        return attestation
    attestation.update(
        {
            "attested_by": "ci",
            "run_id": ci["run_id"],
            "run_attempt": int(ci["run_attempt"]),
            "workflow_ref": ci["workflow_ref"],
            "github_sha": ci["github_sha"],
        }
    )
    return attestation


def _default_baseline_output(repo: Path) -> Path:
    attestation = _resolve_attestation_from_environment()
    if attestation.get("attested_by") == "ci":
        return repo / _COMMITTED_BASELINE
    return repo / _LOCAL_BASELINE_DIR / "runtime-baseline-local.json"


def _is_committed_baseline_path(repo: Path, path: Path) -> bool:
    try:
        return path.resolve() == (repo / _COMMITTED_BASELINE).resolve()
    except OSError:
        return False


def _sanitize_tool_name(tool: object) -> str:
    """N-24: never publish absolute local interpreter/tool paths."""
    raw = str(tool or "")
    if not raw:
        return "unknown"
    lowered = raw.replace("\\", "/").lower()
    if (
        lowered.endswith("/python")
        or lowered.endswith("/python.exe")
        or lowered.endswith("python3")
    ):
        return "python"
    if lowered.endswith("/node") or lowered.endswith("/node.exe"):
        return "node"
    if lowered.endswith("/npm") or lowered.endswith("/npm.cmd"):
        return "npm"
    name = Path(raw).name
    if name.lower() in {"python", "python.exe", "python3", "python3.exe"}:
        return "python"
    return name or raw


def _sanitize_repo_path(repo: Path, value: object) -> str | None:
    """N-24: store repo-relative POSIX paths only."""
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    try:
        path = Path(text)
        if path.is_absolute():
            return path.resolve().relative_to(repo.resolve()).as_posix()
    except (OSError, ValueError):
        pass
    return text.replace("\\", "/")


def _parent_commit_shas(repo: Path, commit: str) -> list[str]:
    """Return first/second parents (merge commits expose the PR tip as ^2)."""
    parents: list[str] = []
    for index in (1, 2):
        parent = _git(repo, "rev-parse", f"{commit}^{index}")
        if parent:
            parents.append(parent)
    return parents


def _tree_sha_for_commit(repo: Path, commit: str) -> str | None:
    tree = _git(repo, "rev-parse", f"{commit}^{{tree}}")
    return tree or None


# Evidence tip may sit several commits behind PR merge-ref / follow-up fixes.
# Depth is loaded from governance/baseline_integrity_policy.json (N-43).
_SHA_ANCESTOR_DEPTH_DEFAULT = 50
_BASELINE_POLICY_REL = "governance/baseline_integrity_policy.json"


def _load_baseline_integrity_policy(repo: Path | None = None) -> dict[str, object]:
    root = repo or _repo_root()
    path = root / _BASELINE_POLICY_REL
    if not path.is_file():
        return {
            "max_commits_behind": _SHA_ANCESTOR_DEPTH_DEFAULT,
            "allowed_lag_paths": [
                "docs/evidence/runtime-baseline-latest.json",
                "README.md",
            ],
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"max_commits_behind": _SHA_ANCESTOR_DEPTH_DEFAULT, "allowed_lag_paths": []}
    return payload if isinstance(payload, dict) else {}


def _max_commits_behind(repo: Path | None = None) -> int:
    policy = _load_baseline_integrity_policy(repo)
    raw = policy.get("max_commits_behind", _SHA_ANCESTOR_DEPTH_DEFAULT)
    if isinstance(raw, bool):
        return _SHA_ANCESTOR_DEPTH_DEFAULT
    if isinstance(raw, int):
        return max(0, raw)
    if isinstance(raw, str):
        try:
            return max(0, int(raw.strip()))
        except ValueError:
            return _SHA_ANCESTOR_DEPTH_DEFAULT
    return _SHA_ANCESTOR_DEPTH_DEFAULT


def _allowed_lag_paths(repo: Path | None = None) -> frozenset[str]:
    policy = _load_baseline_integrity_policy(repo)
    paths = policy.get("allowed_lag_paths") or []
    if not isinstance(paths, list):
        return frozenset()
    return frozenset(str(p).replace("\\", "/") for p in paths)


def _diff_paths_between(repo: Path, older: str, newer: str) -> list[str]:
    raw = _git(repo, "diff", "--name-only", f"{older}..{newer}")
    if not raw:
        return []
    return [line.replace("\\", "/") for line in raw.splitlines() if line.strip()]


def _one_commit_lag_allowed(repo: Path, artifact_commit: str, head: str) -> bool:
    """True when artifact is exactly HEAD~1 and the tip commit only touches allowlisted paths."""

    parent = _git(repo, "rev-parse", f"{head}~1")
    if not parent or parent != artifact_commit:
        return False
    changed = _diff_paths_between(repo, artifact_commit, head)
    allowed = _allowed_lag_paths(repo)
    return bool(changed) and all(path in allowed for path in changed)


def _sha_matches_head_or_parent(repo: Path | None, value: object, head: object) -> bool:
    """Allow evidence commit to bind to HEAD or a recent ancestor (WP-A11 / N-43).

    Walks both merge parents so pull_request merge refs can reach the PR tip.
    When max_commits_behind==1, only exact HEAD or a one-commit allowlisted lag.
    """
    if value == head:
        return True
    if repo is None or not isinstance(value, str) or not isinstance(head, str):
        return False
    max_behind = _max_commits_behind(repo)
    if max_behind == 1:
        return _one_commit_lag_allowed(repo, value, head)
    frontier = [head]
    seen: set[str] = {head}
    for _ in range(max_behind):
        next_frontier: list[str] = []
        for current in frontier:
            for parent in _parent_commit_shas(repo, current):
                if parent == value:
                    return True
                if parent not in seen:
                    seen.add(parent)
                    next_frontier.append(parent)
        frontier = next_frontier
        if not frontier:
            break
    return False


def _tree_matches_head_or_parent(
    repo: Path | None, value: object, head_tree: object, head: str | None
) -> bool:
    if value == head_tree:
        return True
    if repo is None or not isinstance(value, str) or not head:
        return False
    max_behind = _max_commits_behind(repo)
    if max_behind == 1:
        if not _one_commit_lag_allowed(repo, _git(repo, "rev-parse", f"{head}~1") or "", head):
            return False
        parent_tree = _tree_sha_for_commit(repo, _git(repo, "rev-parse", f"{head}~1") or "")
        return value == parent_tree
    frontier = [head]
    seen: set[str] = {head}
    for _ in range(max_behind):
        next_frontier: list[str] = []
        for current in frontier:
            for parent in _parent_commit_shas(repo, current):
                parent_tree = _tree_sha_for_commit(repo, parent)
                if value == parent_tree:
                    return True
                if parent not in seen:
                    seen.add(parent)
                    next_frontier.append(parent)
        frontier = next_frontier
        if not frontier:
            break
    return False


def committed_baseline_attestation_errors(repo: Path | None = None) -> list[str]:
    """WP-A11: committed baseline in git must be CI-attested and publishable."""
    root = repo or _repo_root()
    artifact = root / _COMMITTED_BASELINE
    if not artifact.is_file():
        return [f"missing_committed_baseline: {_COMMITTED_BASELINE}"]
    try:
        stored = json.loads(artifact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"invalid_committed_baseline: {_COMMITTED_BASELINE}"]
    if not isinstance(stored, dict):
        return [f"committed_baseline_not_object: {_COMMITTED_BASELINE}"]
    head = _commit_sha(root)
    tree = _tree_sha(root)
    return publishability_errors(
        stored,
        expected_commit_sha=head or None,
        expected_tree_sha=tree or None,
        repo=root,
        allow_parent_sha=True,
    )


def compare_baseline_snapshots(
    committed: dict[str, object],
    generated: dict[str, object],
    *,
    repo: Path | None = None,
) -> list[str]:
    """Compare committed vs CI-generated baseline (WP-A11)."""
    errors: list[str] = []
    root = repo or _repo_root()
    head = generated.get("commit_sha")
    head_tree = generated.get("tree_sha")
    if not _sha_matches_head_or_parent(root, committed.get("commit_sha"), head):
        errors.append(
            f"baseline_field_mismatch:commit_sha committed={committed.get('commit_sha')!r} "
            f"generated={head!r}"
        )
    if not _tree_matches_head_or_parent(
        root, committed.get("tree_sha"), head_tree, head if isinstance(head, str) else None
    ):
        errors.append(
            f"baseline_field_mismatch:tree_sha committed={committed.get('tree_sha')!r} "
            f"generated={head_tree!r}"
        )
    if committed.get("schema_version") != generated.get("schema_version"):
        errors.append(
            f"baseline_field_mismatch:schema_version committed={committed.get('schema_version')!r} "
            f"generated={generated.get('schema_version')!r}"
        )
    committed_metrics = committed.get("metrics")
    generated_metrics = generated.get("metrics")
    if isinstance(committed_metrics, dict) and isinstance(generated_metrics, dict):
        for key in _DRIFT_KEYS:
            c_val = int(committed_metrics.get(key, -1))
            g_val = int(generated_metrics.get(key, -2))
            if abs(c_val - g_val) > _DRIFT_TOLERANCE:
                errors.append(f"baseline_metrics_drift:{key} committed={c_val} generated={g_val}")
    committed_att = committed.get("attestation")
    generated_att = generated.get("attestation")
    if committed_att != generated_att:
        # Bootstrap: local committed vs fresh CI-generated attestation differs by design.
        # Lag: two CI attestations (different run_id / github_sha) while tip catches up.
        both_ci = (
            isinstance(committed_att, dict)
            and committed_att.get("attested_by") == "ci"
            and isinstance(generated_att, dict)
            and generated_att.get("attested_by") == "ci"
        )
        local_vs_ci = (
            isinstance(committed_att, dict)
            and committed_att.get("attested_by") == "local"
            and isinstance(generated_att, dict)
            and generated_att.get("attested_by") == "ci"
        )
        if not (both_ci or local_vs_ci):
            errors.append("attestation_mismatch")
    if generated.get("publishable") is not True:
        errors.append("generated_baseline_not_publishable")
    return errors


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


def _iter_test_definition_ids(tests_root: Path) -> set[str]:
    """Collect pytest-style node ids for module-level and class test methods."""
    import ast

    ids: set[str] = set()
    if not tests_root.exists():
        return ids
    for path in sorted(tests_root.rglob("test_*.py")):
        rel = path.relative_to(tests_root.parent).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                ids.add(f"{rel}::{node.name}")
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                        ids.add(f"{rel}::{node.name}::{item.name}")
            elif isinstance(node, ast.If):
                for branch in (*node.body, *node.orelse):
                    if isinstance(branch, ast.FunctionDef) and branch.name.startswith("test_"):
                        ids.add(f"{rel}::{branch.name}")
    return ids


def _count_tests(tests_root: Path) -> int:
    """AST count of ``test_*`` functions / methods. Not pytest's collected item count.

    Parametrize expands one definition into many items. Optional extras
    (``pdf-agpl``, kitchen secrets) skip collection. Equality with
    ``tests_collected`` is not an invariant.
    """

    return len(_iter_test_definition_ids(tests_root))


def _collected_definition_id(nodeid: str) -> str:
    """Map a pytest node id to the AST definition id (drop parametrize suffix)."""

    token = nodeid.strip().replace("\\", "/")
    bracket = token.find("[")
    if bracket != -1:
        token = token[:bracket]
    return token


def _pytest_collected_ids(backend_root: Path) -> set[str]:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=backend_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    if completed.returncode not in {0, 5}:
        return set()
    collected: set[str] = set()
    for line in completed.stdout.splitlines():
        token = line.strip()
        if "::test_" in token and not token.startswith("="):
            collected.add(token)
    return collected


def _test_collection_inventory(backend_root: Path) -> dict[str, object]:
    """Compare AST definitions to ``pytest --collect-only`` node ids.

    ``test_functions`` (AST) and ``tests_collected`` (pytest) are different
    metrics. SSOT for the published pin is pytest JUnit ``tests_collected`` /
    ``tests_passed`` in ``runtime-baseline-latest.json``.
    """

    tests_root = backend_root / "tests"
    definitions = _iter_test_definition_ids(tests_root)
    collected = _pytest_collected_ids(backend_root)
    collected_defs = {_collected_definition_id(item) for item in collected}
    uncollected = sorted(definitions - collected_defs)
    return {
        "test_definitions": len(definitions),
        "tests_collected_live": len(collected),
        "uncollected": uncollected,
    }


def _env_names_from_settings_source(text: str) -> set[str]:
    """Settings.py reads via getenv *and* typed helpers ``_read_int`` / ``_env_prefer``.

    The 2026-08 CI pin only matched ``os.getenv`` / ``os.environ.get`` / ``os.environ[]``,
    so documented knobs such as ``AEROBIM_MAX_IFC_BYTES`` were absent from
    ``code_env_vars`` even though ``Settings.from_env`` reads them. That was a
    scanner defect, not a no-op flag.
    """

    names: set[str] = set()
    for match in _CODE_ENV_RE.finditer(text):
        name = match.group(1) or match.group(2)
        if name:
            names.add(name)
    names.update(_HELPER_ENV_RE.findall(text))
    names.update(_IN_ENVIRON_RE.findall(text))
    for match in _ENV_PREFER_CALL_RE.finditer(text):
        names.update(_QUOTED_AEROBIM_RE.findall(match.group(1)))
    return names - _ENV_MARKER_NOISE


def _code_env_names(repo: Path) -> list[str]:
    names: set[str] = set()
    settings_path = repo / "backend" / "src" / "aerobim" / "core" / "config" / "settings.py"
    if settings_path.is_file():
        names |= _env_names_from_settings_source(
            settings_path.read_text(encoding="utf-8", errors="ignore")
        )
    for rel in _EXTRA_ENV_SCAN_RELPATHS:
        path = repo / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in _CODE_ENV_RE.finditer(text):
            name = match.group(1) or match.group(2)
            if name:
                names.add(name)
    return sorted(names - _ENV_MARKER_NOISE)


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


def _gate_status(value: object) -> str:
    if isinstance(value, dict):
        raw = value.get("status")
        return str(raw).upper() if raw is not None else "UNKNOWN"
    return str(value).upper()


def _normalize_gate(value: object, *, reason: str | None = None) -> dict[str, object]:
    if isinstance(value, dict):
        payload = dict(value)
        payload["status"] = _gate_status(payload)
        if payload["status"] == "UNKNOWN" and reason and not payload.get("reason"):
            payload["reason"] = reason
        return payload
    status = str(value).upper()
    gate: dict[str, object] = {"status": status}
    if status == "UNKNOWN" and reason:
        gate["reason"] = reason
    return gate


def _default_quality_gates() -> dict[str, dict[str, object]]:
    return {
        key: _normalize_gate(
            "UNKNOWN",
            reason="gate not executed in this export run",
        )
        for key in _QUALITY_GATE_KEYS
    }


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


def _run_subprocess_gate(
    label: str,
    cmd: list[str],
    *,
    cwd: Path,
    timeout_s: int = 900,
) -> dict[str, object]:
    from time import perf_counter

    started = perf_counter()
    run_cmd = cmd
    if platform.system() == "Windows" and cmd and cmd[0] == "npm":
        run_cmd = ["cmd", "/c", *cmd]
    try:
        completed = subprocess.run(
            run_cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_s,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "FAIL",
            "tool": _sanitize_tool_name(cmd[0] if cmd else label),
            "exit_code": -1,
            "duration_ms": round((perf_counter() - started) * 1000.0, 1),
            "reason": f"{type(exc).__name__}: {exc}",
        }
    status = "PASS" if completed.returncode == 0 else "FAIL"
    payload: dict[str, object] = {
        "status": status,
        "tool": _sanitize_tool_name(cmd[0] if cmd else label),
        "exit_code": completed.returncode,
        "duration_ms": round((perf_counter() - started) * 1000.0, 1),
    }
    if status == "FAIL":
        tail = (completed.stderr or completed.stdout or "").strip()[-400:]
        if tail:
            payload["reason"] = tail
    return payload


def run_quality_gates(
    repo: Path, *, junit_path: Path | None = None
) -> dict[str, dict[str, object]]:
    """Execute local quality gates and return structured gate payloads."""
    backend = repo / "backend"
    frontend = repo / "frontend"
    junit = junit_path or (repo / "backend" / "var" / "reports" / "pytest-junit.xml")
    junit.parent.mkdir(parents=True, exist_ok=True)
    gates: dict[str, dict[str, object]] = {}
    gates["ruff"] = _run_subprocess_gate(
        "ruff",
        [sys.executable, "-m", "ruff", "format", "--check", "src", "tests"],
        cwd=backend,
    )
    if _gate_status(gates["ruff"]) == "PASS":
        gates["ruff_check"] = _run_subprocess_gate(
            "ruff_check",
            [sys.executable, "-m", "ruff", "check", "src", "tests"],
            cwd=backend,
        )
        # Merge ruff check into ruff gate status for publishable baseline.
        if _gate_status(gates["ruff_check"]) != "PASS":
            gates["ruff"] = dict(gates["ruff_check"])
            gates["ruff"]["tool"] = "ruff"
    gates["mypy"] = _run_subprocess_gate(
        "mypy",
        [
            sys.executable,
            "-m",
            "mypy",
            "src/aerobim",
            "--strict",
            "--ignore-missing-imports",
        ],
        cwd=backend,
    )
    gates["pytest"] = _run_subprocess_gate(
        "pytest",
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            f"--junitxml={junit.as_posix()}",
        ],
        cwd=backend,
        timeout_s=1200,
    )
    vitest_json = frontend / "var" / "vitest-results.json"
    if frontend.is_dir() and (frontend / "package.json").is_file():
        vitest_json.parent.mkdir(parents=True, exist_ok=True)
        gates["vitest"] = _run_subprocess_gate(
            "vitest",
            [
                "npm",
                "test",
                "--",
                "--run",
                "--reporter=json",
                "--outputFile=var/vitest-results.json",
            ],
            cwd=frontend,
        )
        gates["build"] = _run_subprocess_gate(
            "build",
            ["npm", "run", "build"],
            cwd=frontend,
        )
    else:
        gates["vitest"] = _normalize_gate(
            "SKIPPED",
            reason="frontend/package.json missing",
        )
        gates["build"] = _normalize_gate(
            "SKIPPED",
            reason="frontend/package.json missing",
        )
    # Publishable contract expects these five keys exactly.
    return {
        "ruff": gates["ruff"],
        "mypy": gates["mypy"],
        "pytest": gates["pytest"],
        "vitest": gates["vitest"],
        "build": gates["build"],
    }


def parse_vitest_json(path: Path) -> dict[str, int]:
    """Parse vitest JSON reporter output into passed / failed / skipped counts."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("vitest JSON root must be an object")
    passed = int(payload.get("numPassedTests", 0))
    failed = int(payload.get("numFailedTests", 0))
    skipped = int(payload.get("numPendingTests", 0) or payload.get("numTodoTests", 0))
    total = int(payload.get("numTotalTests", passed + failed + skipped))
    return {
        "tests_collected": total,
        "tests_passed": passed,
        "tests_skipped": skipped,
        "tests_failed": failed,
    }


def parse_pytest_junit(path: Path) -> dict[str, int]:
    """Parse pytest JUnit XML into passed / skipped / failed / errors counts.

    pytest 9 native subtests inflate the testsuite header ``tests`` attribute
    (subtest nodes add no ``<testcase>`` element), which breaks parity against
    the AST/collect-only definition inventory. Count real ``<testcase>``
    elements when present; fall back to header attributes for header-only
    suites.
    """
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    if not suites and root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
    tests = skipped = failures = errors = 0
    for suite in suites:
        cases = list(suite.findall("testcase"))
        if cases:
            tests += len(cases)
            skipped += sum(1 for case in cases if case.find("skipped") is not None)
            failures += sum(1 for case in cases if case.find("failure") is not None)
            errors += sum(1 for case in cases if case.find("error") is not None)
        else:
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
        unaccounted = backend.get("tests_unaccounted")
        if unaccounted is not None:
            if not isinstance(unaccounted, int) or unaccounted < 0:
                errors.append(
                    f"backend.tests_unaccounted must be a non-negative int, got {unaccounted!r}"
                )
            elif all(
                isinstance(backend.get(key), int)
                for key in ("tests_collected", "tests_passed", "tests_skipped", "tests_failed")
            ):
                expected = (
                    backend["tests_collected"]
                    - backend["tests_passed"]
                    - backend["tests_skipped"]
                    - backend["tests_failed"]
                )
                if unaccounted != expected:
                    errors.append(
                        "backend.tests_unaccounted must equal collected − passed − skipped − "
                        f"failed ({expected}), got {unaccounted}"
                    )

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
            if _gate_status(value) != _COMPLETE_GATE_VALUE:
                errors.append(
                    f"quality_gates.{key} must be {_COMPLETE_GATE_VALUE!r} for complete "
                    f"baseline, got {_gate_status(value)!r}"
                )
            if isinstance(value, dict) and _gate_status(value) == "UNKNOWN":
                if not str(value.get("reason") or "").strip():
                    errors.append(f"quality_gates.{key} UNKNOWN requires non-empty reason")

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


_BASELINE_ARTIFACT_REL = "docs/evidence/runtime-baseline-latest.json"


def _commits_behind(repo: Path, artifact_commit: str, head: str) -> int | None:
    if artifact_commit == head:
        return 0
    count = 0
    current = head
    while current and current != artifact_commit:
        parent = _git(repo, "rev-parse", f"{current}~1")
        if not parent:
            return None
        count += 1
        current = parent
    return count if current == artifact_commit else None


def _self_declared_publishability_errors(baseline: dict[str, Any]) -> list[str]:
    """Checks that only apply to a finished artifact (not while computing publishable)."""
    errors: list[str] = []
    if baseline.get("publishable") is not True:
        errors.append("publishable_not_true")
    if baseline.get("artifact_completeness") != "full":
        errors.append("artifact_incomplete")
    return errors


def _publishability_core_errors(
    baseline: dict[str, Any],
    *,
    expected_commit_sha: str | None = None,
    expected_tree_sha: str | None = None,
    repo: Path | None = None,
    allow_parent_sha: bool = False,
) -> list[str]:
    """Core publishability rules without self-referential publishable/completeness keys."""
    errors = list(completeness_errors(baseline))
    if baseline.get("working_tree_clean") is not True:
        errors.append("working_tree_dirty")

    attestation = baseline.get("attestation")
    if not isinstance(attestation, dict):
        errors.append("attestation_missing")
    else:
        attested_by = attestation.get("attested_by")
        if attested_by != "ci":
            errors.append(f"attestation_not_ci: got {attested_by!r}")
        if attestation.get("attestation_environment_incomplete"):
            errors.append("attestation_environment_incomplete")
        github_sha = attestation.get("github_sha")
        commit = baseline.get("commit_sha")
        if (
            attested_by == "ci"
            and isinstance(github_sha, str)
            and isinstance(commit, str)
            and github_sha != commit
        ):
            errors.append(
                f"attestation_sha_mismatch: attestation.github_sha={github_sha!r} "
                f"commit_sha={commit!r}"
            )
        gates_attested = attestation.get("gates_attested")
        if not isinstance(gates_attested, list):
            errors.append("attestation_gates_attested_missing")
        else:
            missing = sorted(_REQUIRED_GATES_ATTESTED - {str(g) for g in gates_attested})
            if missing:
                errors.append(f"attestation_gates_attested_missing: {missing}")

    commit = baseline.get("commit_sha")
    if expected_commit_sha and isinstance(commit, str):
        matched = commit == expected_commit_sha
        if not matched and allow_parent_sha:
            matched = _sha_matches_head_or_parent(repo, commit, expected_commit_sha)
        if not matched:
            behind = (
                _commits_behind(repo, commit, expected_commit_sha) if repo is not None else None
            )
            if behind is None:
                errors.append(
                    f"commit_sha_mismatch: artifact={commit!r} expected HEAD={expected_commit_sha!r}"
                )
            else:
                errors.append(
                    f"baseline_stale_by_{behind}_commits: regenerate {_COMMITTED_BASELINE}"
                )
    tree = baseline.get("tree_sha")
    if expected_tree_sha and isinstance(tree, str):
        matched_tree = tree == expected_tree_sha
        if not matched_tree and allow_parent_sha and isinstance(expected_commit_sha, str):
            matched_tree = _tree_matches_head_or_parent(
                repo, tree, expected_tree_sha, expected_commit_sha
            )
        if not matched_tree:
            errors.append(
                f"tree_sha_mismatch: artifact={tree!r} expected HEAD tree={expected_tree_sha!r}"
            )

    backend = baseline.get("backend")
    if isinstance(backend, dict):
        # AST ``test_functions`` and pytest ``tests_collected`` are different
        # metrics (parametrize expands items; optional extras skip collection).
        # Publishability fails only when AST defs are missing from collection
        # after stripping parametrize suffixes — not when the two counts differ.
        uncollected = backend.get("uncollected")
        if isinstance(uncollected, list) and uncollected:
            detail = f" ({uncollected[:5]}...)" if uncollected else ""
            errors.append(
                f"uncollected_test_definitions: {len(uncollected)} AST "
                f"test_functions not in pytest collection{detail}"
            )

    frontend = baseline.get("frontend")
    if isinstance(frontend, dict):
        vitest_source = frontend.get("vitest_artifact")
        if not vitest_source:
            errors.append("frontend_vitest_artifact_missing")
    return errors


def publishability_errors(
    baseline: dict[str, Any],
    *,
    expected_commit_sha: str | None = None,
    expected_tree_sha: str | None = None,
    repo: Path | None = None,
    allow_parent_sha: bool = False,
) -> list[str]:
    """Stricter than completeness: CI attestation + HEAD/tree match + clean tree."""
    return _self_declared_publishability_errors(baseline) + _publishability_core_errors(
        baseline,
        expected_commit_sha=expected_commit_sha,
        expected_tree_sha=expected_tree_sha,
        repo=repo,
        allow_parent_sha=allow_parent_sha,
    )


def _compute_publishable(
    baseline: dict[str, Any],
    *,
    require_clean_tree: bool,
) -> tuple[bool, str]:
    del require_clean_tree  # suffix/exit policy only; publishable always needs clean tree
    # Must NOT call publishability_errors(): it self-checks publishable/completeness keys
    # that are assigned only after this function returns (circular lock).
    if _publishability_core_errors(baseline):
        return False, "partial"
    return True, "full"


def export_runtime_baseline(
    *,
    backend_root: Path | None = None,
    frontend_tests_passed: int | None = None,
    frontend_tests_failed: int | None = None,
    tests_passed: int | None = None,
    tests_skipped: int | None = None,
    tests_failed: int | None = None,
    tests_collected: int | None = None,
    quality_gates: Mapping[str, object] | None = None,
    commit_sha: str | None = None,
    tree_sha: str | None = None,
    environment: dict[str, object] | None = None,
    require_clean_tree: bool = False,
    vitest_json_path: str | None = None,
    attestation: dict[str, object] | None = None,
) -> dict[str, object]:
    backend = (backend_root or (_repo_root() / "backend")).resolve()
    repo = backend.parent
    src_root = backend / "src" / "aerobim"
    tests_root = backend / "tests"
    src_loc = _count_lines(src_root, "*.py")
    test_loc = _count_lines(tests_root, "*.py")
    test_count = _count_tests(tests_root)
    collection = _test_collection_inventory(backend)
    collected_live = collection["tests_collected_live"]
    if not isinstance(collected_live, int):
        raise TypeError(f"tests_collected_live must be int, got {type(collected_live).__name__}")
    collected = tests_collected if tests_collected is not None else collected_live
    uncollected = collection["uncollected"]
    macro_f1 = _extraction_macro_f1(backend)
    gates = _default_quality_gates()
    if quality_gates:
        for key, value in quality_gates.items():
            if key in gates:
                gate = _normalize_gate(value)
                if "tool" in gate:
                    gate["tool"] = _sanitize_tool_name(gate["tool"])
                gates[key] = gate
    commit = commit_sha if commit_sha is not None else _commit_sha(repo)
    backend_passed = tests_passed if tests_passed is not None else "n/a"
    frontend_passed = frontend_tests_passed if frontend_tests_passed is not None else "n/a"
    f1_display = f"{macro_f1}" if macro_f1 is not None else "n/a"
    env = environment if environment is not None else _environment_fingerprint(repo)
    attestation_block = (
        attestation if attestation is not None else _resolve_attestation_from_environment()
    )
    safe_vitest = _sanitize_repo_path(repo, vitest_json_path)
    payload: dict[str, object] = {
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
            "tests_unaccounted": (
                collected - tests_passed - tests_skipped - tests_failed
                if (
                    collected is not None
                    and tests_passed is not None
                    and tests_skipped is not None
                    and tests_failed is not None
                )
                else None
            ),
            "tests_unaccounted_note": (
                "collected − passed − skipped − failed; remainder is typically "
                "deselected/xfail vs the CI JUnit pin (HD-DOC-02)"
                if all(
                    isinstance(value, int)
                    for value in (collected, tests_passed, tests_skipped, tests_failed)
                )
                else None
            ),
            "source_loc": src_loc,
            "test_loc": test_loc,
            "test_functions": test_count,
            "test_functions_source": "ast_test_defs",
            "tests_collected_source": "pytest_collect_only",
            "uncollected": uncollected,
        },
        "frontend": {
            "tests_passed": frontend_tests_passed,
            "tests_failed": frontend_tests_failed,
            "vitest_artifact": safe_vitest,
            "note": (
                "Recorded from vitest JSON artifact when provided; "
                "manual --frontend-tests-passed without artifact is not publishable"
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
            f"tests_passed: backend={backend_passed}, frontend={frontend_passed}; "
            f"commit {commit[:12]}; see docs/evidence/runtime-baseline-latest.json · "
            f"src ~{src_loc} LOC; tests ~{test_loc} LOC; "
            f"extraction macro_f1={f1_display} (fixture corpus; not product accuracy)"
        ),
        "documented_env_vars": _configuration_env_names(repo / "README.md"),
        "code_env_vars": _code_env_names(repo),
        "architecture_inventory": _live_architecture_inventory(repo),
        "attestation": attestation_block,
    }
    publishable, completeness = _compute_publishable(payload, require_clean_tree=require_clean_tree)
    payload["artifact_completeness"] = completeness
    payload["publishable"] = publishable
    return payload


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


def _check_documented_env_sets(repo: Path, *, compare_artifact: bool = True) -> list[str]:
    """Fail on set inequality (symmetric difference), never on count equality alone."""
    errors: list[str] = []
    expected = _configuration_env_names(repo / "README.md")
    if not expected:
        return ["README.md ## Configuration has no AEROBIM_* names"]

    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    if compare_artifact and artifact.exists():
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
        missing_in_marker = set(expected) - set(names)
        if missing_in_marker:
            errors.append(
                f"{name} documented-env marker missing Configuration table names: "
                f"{sorted(missing_in_marker)}"
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


_INTERNAL_ENV_REGISTRY = "audit/internal_env_vars.json"


def _internal_env_names(repo: Path) -> set[str]:
    """Load explicit allowlist of Settings knobs intentionally outside Configuration table."""
    path = repo / _INTERNAL_ENV_REGISTRY
    if not path.is_file():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if not isinstance(payload, dict):
        return set()
    entries = payload.get("vars")
    if not isinstance(entries, dict):
        return set()
    return {str(name) for name in entries}


def _check_code_env_documented(repo: Path, *, compare_artifact: bool = True) -> list[str]:
    """Fail when Settings reads AEROBIM_* knobs absent from README Configuration + registry.

    N-20: marker-only parity can hide holes published as documented_env_vars vs code_env_vars.
    Require code ⊆ (Configuration table ∪ audit/internal_env_vars.json).
    Require documented ⊆ code (docs→code). The 2026-08 pin compared only getenv
    literals, so ~29 documented names were missing from code_env_vars; that was a
    scanner defect. After expanding the scanner, live code_env_vars may be a
    **superset** of the pinned artifact until CI regenerates the pin.
    """
    errors: list[str] = []
    readme = repo / "README.md"
    if not readme.exists():
        return ["Missing README.md"]
    marker = _documented_env_marker_names(readme.read_text(encoding="utf-8"))
    if marker is None:
        return [
            f"README.md missing {_ENV_DOC_MARKER_BEGIN}…{_ENV_DOC_MARKER_END} "
            "for code/settings env parity"
        ]
    code_names = set(_code_env_names(repo))
    config_names = set(_configuration_env_names(readme))
    internal = _internal_env_names(repo)
    missing_readme = sorted(code_names - set(marker) - internal)
    if missing_readme:
        errors.append(
            f"settings.py reads undocumented AEROBIM_* vars (not in README marker "
            f"and not in {_INTERNAL_ENV_REGISTRY}): {missing_readme}"
        )
    missing_config = sorted(code_names - config_names - internal)
    if missing_config:
        errors.append(
            "settings.py AEROBIM_* vars missing from README ## Configuration table "
            f"(and not listed in {_INTERNAL_ENV_REGISTRY}): {missing_config}"
        )
    unexplained_internal = sorted(internal - code_names)
    if unexplained_internal:
        errors.append(
            f"{_INTERNAL_ENV_REGISTRY} lists vars not read by settings.py: {unexplained_internal}"
        )
    missing_from_code = sorted((set(marker) | config_names) - code_names)
    if missing_from_code:
        errors.append(
            "documented AEROBIM_* vars not read by settings.py/tools "
            f"(docs→code gate): {missing_from_code}"
        )
    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    if compare_artifact and artifact.exists():
        try:
            stored = json.loads(artifact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return errors + ["Invalid runtime-baseline-latest.json while checking code_env_vars"]
        if isinstance(stored, dict):
            artifact_names = stored.get("code_env_vars")
            if isinstance(artifact_names, list):
                artifact_set = {str(x) for x in artifact_names}
                lost = sorted(artifact_set - code_names)
                if lost:
                    errors.append(
                        "code_env_vars lost names vs runtime-baseline pin "
                        f"(scanner regression): {lost}"
                    )
    return errors


def _check_readme_numeric_claims(repo: Path, live: dict[str, object]) -> list[str]:
    errors: list[str] = []
    backend = live.get("backend")
    inv = live.get("architecture_inventory")
    if not isinstance(backend, dict) or not isinstance(inv, dict):
        return ["Live baseline missing backend/architecture_inventory for README numeric check"]
    stale_patterns = (
        (r"171\s+tests", "stale backend test count 171"),
        (r"1\.9K\s+LOC", "stale ~1.9K LOC claim"),
        (r"9\s+domain\s+ports", "stale 9 domain ports claim"),
        (r"12\s+infrastructure\s+adapters", "stale 12 adapters claim"),
        (r"13\s+DI\s+tokens", "stale 13 DI tokens claim"),
    )
    for readme_name in ("README.md", "README.ru.md"):
        path = repo / readme_name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, label in stale_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(f"{readme_name} contains {label}")
    return errors


_JURY_PIN_SURFACES = (
    "audit/reports/CRITICAL_BLOCKERS.md",
    "docs/TIER0_INDEX.md",
    "docs/pilot-claim-boundary-2026.md",
    "docs/quality/KT3_FIXTURE_VALIDATION_COVER_2026_08.md",
    "docs/capability-claim-matrix-2026.md",
    "submission/README.md",
    "submission/01-repository/README.md",
)


def _check_jury_surfaces_pin_echo(repo: Path) -> list[str]:
    """Jury markdown must point at the JSON pin, not duplicate its integers."""

    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    if not artifact.is_file():
        return ["Missing docs/evidence/runtime-baseline-latest.json"]
    try:
        stored = json.loads(artifact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["Invalid runtime-baseline-latest.json"]
    backend = stored.get("backend") if isinstance(stored, dict) else None
    if not isinstance(backend, dict):
        return ["runtime-baseline-latest.json missing backend"]
    needles: list[str] = []
    passed = backend.get("tests_passed")
    collected = backend.get("tests_collected")
    if isinstance(passed, int):
        needles.extend(
            (
                f"**{passed}**",
                f"{passed} passed",
                f"backend={passed}",
                f"backend **{passed}**",
            )
        )
    if isinstance(collected, int):
        needles.extend((f"**{collected}**", f"{collected} collected"))
    errors: list[str] = []
    for rel in _JURY_PIN_SURFACES:
        path = repo / rel
        if not path.is_file():
            errors.append(f"missing jury surface {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if "runtime-baseline-latest.json" not in text:
            errors.append(f"{rel} must cite runtime-baseline-latest.json as the test-count SSOT")
        for needle in needles:
            if needle in text:
                errors.append(f"{rel} embeds pin count {needle!r}; cite the JSON instead")
    return errors


def _check_architecture_inventory(repo: Path, *, compare_artifact: bool = True) -> list[str]:
    """README must publish the live protocol/adapter/token counts from source."""
    live = _live_architecture_inventory(repo)
    errors: list[str] = []
    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    if compare_artifact and artifact.exists():
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


def _check_readme_markers(repo: Path, *, compare_artifact: bool = True) -> list[str]:
    errors: list[str] = []
    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    expected_snippet: str | None = None
    if compare_artifact and artifact.exists():
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
    errors.extend(_check_documented_env_sets(repo, compare_artifact=compare_artifact))
    errors.extend(_check_code_env_documented(repo, compare_artifact=compare_artifact))
    errors.extend(_check_architecture_inventory(repo, compare_artifact=compare_artifact))
    live = export_runtime_baseline(backend_root=repo / "backend")
    errors.extend(_check_readme_numeric_claims(repo, live))
    errors.extend(_check_jury_surfaces_pin_echo(repo))
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
    # N-43 countdown: how many tip commits until max_commits_behind is exceeded.
    if isinstance(stored, dict):
        head = _commit_sha(repo)
        artifact_commit = stored.get("commit_sha")
        if isinstance(artifact_commit, str) and head:
            behind = _commits_behind(repo, artifact_commit, head)
            max_behind = _max_commits_behind(repo)
            if behind is None:
                print(
                    f"baseline_commits_behind=unknown max_commits_behind={max_behind} "
                    f"artifact={artifact_commit[:12]} head={head[:12]}"
                )
            else:
                until = max(0, max_behind - behind)
                print(
                    f"baseline_commits_behind={behind} max_commits_behind={max_behind} "
                    f"commits_until_baseline_break={until} "
                    f"artifact={artifact_commit[:12]} head={head[:12]}"
                )
                if behind > max_behind:
                    errors.append(
                        f"baseline_stale_by_{behind}_commits: exceeds max_commits_behind={max_behind} "
                        f"(N-43 / {_BASELINE_POLICY_REL})"
                    )
    return errors


def _check_artifact_publishable(repo: Path) -> list[str]:
    artifact = repo / "docs" / "evidence" / "runtime-baseline-latest.json"
    if not artifact.exists():
        return ["Missing docs/evidence/runtime-baseline-latest.json"]
    try:
        stored = json.loads(artifact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["Invalid runtime-baseline-latest.json"]
    if not isinstance(stored, dict):
        return ["runtime-baseline-latest.json must be an object"]
    # N-25: non-publishable committed artifact is an error, not a silent skip.
    if stored.get("publishable") is not True:
        return [
            "committed_baseline_not_publishable: docs/evidence/runtime-baseline-latest.json "
            "must have publishable=true (bootstrap: commit CI-generated artifact)"
        ]
    head = _commit_sha(repo)
    tree = _tree_sha(repo)
    return publishability_errors(
        stored,
        expected_commit_sha=head or None,
        expected_tree_sha=tree or None,
        repo=repo,
        allow_parent_sha=True,
    )


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
        help="Write JSON artifact (default: docs/evidence/local/ locally; committed path in CI)",
    )
    parser.add_argument(
        "--check-readme",
        action="store_true",
        help=(
            "Fail if README.md / README.ru.md lack AEROBIM_RUNTIME_BASELINE markers, "
            "documented-env name *sets* disagree (symmetric difference, not counts), "
            "live architecture_inventory (ports/adapters/tokens) missing from README/artifact, "
            "jury markdown embeds the JSON pin integers, "
            "or committed artifact drifts beyond ±50 on loc/test_functions"
        ),
    )
    parser.add_argument(
        "--skip-artifact-drift",
        action="store_true",
        help=(
            "With --check-readme: compare README vs live source only. "
            "Skip committed runtime-baseline-latest.json loc/env/snippet parity. "
            "Lint job uses this; baseline-integrity owns artifact freshness."
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
        "--check-publishable",
        action="store_true",
        help=(
            "Fail if committed runtime-baseline-latest.json is not publishable "
            "(complete + clean tree + commit_sha == HEAD)"
        ),
    )
    parser.add_argument(
        "--require-clean-tree",
        action="store_true",
        help="Mark artifact publishable=false when working tree is dirty; add -dirty suffix to --out",
    )
    parser.add_argument(
        "--run-gates",
        action="store_true",
        help="Execute ruff/mypy/pytest/vitest/build and record structured quality_gates",
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
        "--vitest-json",
        type=Path,
        default=None,
        help="Vitest JSON reporter artifact for frontend pass/fail counts",
    )
    parser.add_argument(
        "--check-committed-baseline",
        action="store_true",
        help=(
            "WP-A11: fail if docs/evidence/runtime-baseline-latest.json is not CI-attested "
            "and publishable on HEAD"
        ),
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
    junit_path: Path | None = None
    vitest_json_path: Path | None = None
    if args.run_gates:
        junit_path = repo / "backend" / "var" / "reports" / "pytest-junit.xml"
        vitest_json_path = repo / "frontend" / "var" / "vitest-results.json"
        gates = run_quality_gates(repo, junit_path=junit_path)
    for raw in args.gate:
        key, value = _parse_gate(raw)
        gates[key] = _normalize_gate(value)

    tests_passed = args.tests_passed
    tests_skipped = args.tests_skipped
    tests_failed = args.tests_failed
    tests_collected: int | None = None
    frontend_tests_passed = args.frontend_tests_passed
    frontend_tests_failed: int | None = None
    junit_for_parse = args.pytest_junit or junit_path
    if junit_for_parse is not None and junit_for_parse.is_file():
        parsed = parse_pytest_junit(junit_for_parse)
        tests_passed = parsed["tests_passed"] if tests_passed is None else tests_passed
        tests_skipped = parsed["tests_skipped"] if tests_skipped is None else tests_skipped
        tests_failed = parsed["tests_failed"] if tests_failed is None else tests_failed
        # Do not override tests_collected from JUnit: suite totals can include
        # non-definition nodes and break uncollected parity vs AST inventory.
    vitest_for_parse = args.vitest_json or vitest_json_path
    vitest_artifact: str | None = None
    attestation = _resolve_attestation_from_environment()
    if vitest_for_parse is not None and vitest_for_parse.is_file():
        vitest_parsed = parse_vitest_json(vitest_for_parse)
        vitest_artifact = vitest_for_parse.as_posix()
        if frontend_tests_passed is None:
            frontend_tests_passed = vitest_parsed["tests_passed"]
        frontend_tests_failed = vitest_parsed["tests_failed"]
    elif args.frontend_tests_passed is not None and attestation.get("attested_by") == "ci":
        print(
            "--frontend-tests-passed without --vitest-json is not allowed under CI attestation",
            file=sys.stderr,
        )
        return 1

    if (
        args.check_readme
        or args.check_complete
        or args.check_publishable
        or args.check_committed_baseline
    ):
        live = export_runtime_baseline(
            backend_root=repo / "backend",
            quality_gates=gates,
            require_clean_tree=args.require_clean_tree,
        )
        errors: list[str] = []
        if args.check_readme:
            compare_artifact = not args.skip_artifact_drift
            errors.extend(_check_readme_markers(repo, compare_artifact=compare_artifact))
            if compare_artifact:
                errors.extend(_check_artifact_drift(repo, live))
        if args.check_complete:
            errors.extend(_check_artifact_complete(repo))
        if args.check_publishable:
            errors.extend(_check_artifact_publishable(repo))
        if args.check_committed_baseline:
            errors.extend(committed_baseline_attestation_errors(repo))
        if errors:
            for message in errors:
                print(message, file=sys.stderr)
            return 1
        print("README markers, documented-env sets, runtime baseline drift, and completeness OK")
        return 0

    baseline = export_runtime_baseline(
        backend_root=repo / "backend",
        frontend_tests_passed=frontend_tests_passed,
        frontend_tests_failed=frontend_tests_failed,
        tests_passed=tests_passed,
        tests_skipped=tests_skipped,
        tests_failed=tests_failed,
        tests_collected=tests_collected,
        quality_gates=gates,
        require_clean_tree=args.require_clean_tree,
        vitest_json_path=vitest_artifact,
        attestation=attestation,
    )
    if args.require_complete:
        errors = completeness_errors(baseline)
        if errors:
            for message in errors:
                print(message, file=sys.stderr)
            return 1

    out = args.out or _default_baseline_output(repo)
    # N-26: refuse overwriting the committed public baseline with a local/non-CI attestation.
    if _is_committed_baseline_path(repo, out) and attestation.get("attested_by") != "ci":
        print(
            "refusing to write non-CI-attested baseline to "
            f"{_COMMITTED_BASELINE} (N-26); omit --out or write under docs/evidence/local/",
            file=sys.stderr,
        )
        return 2
    if args.require_clean_tree and baseline.get("working_tree_clean") is not True:
        out = out.with_name(f"{out.stem}-dirty{out.suffix}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(baseline, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
