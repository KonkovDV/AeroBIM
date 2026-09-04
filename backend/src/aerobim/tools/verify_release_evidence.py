"""Verify Sprint 2 / release evidence consistency (fail-closed).

Loads runtime baseline + sprint2 baseline evidence and checks claim locks,
required filenames, intake gate honesty, and commit SHA alignment.

Exit 0 only when consistent. Never greenwashes customer claims.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT

DEFAULT_RELEASE_EVIDENCE_DAY = "latest"
ALLOWED_SYNTHETIC_CLAIM_LEVELS = frozenset({"synthetic_only", "fixture_only"})
FORBIDDEN_CUSTOMER_CLAIM_LEVELS = frozenset(
    {
        "customer",
        "customer_ready",
        "product",
        "production",
        "production_ready",
        "publishable",
    }
)
REQUIRED_RUNTIME_GATES = ("ruff", "mypy", "pytest")
_RELEASE_STATUS_DAY_RE = re.compile(r"^release-status-(\d{4}-\d{2}-\d{2})\.json$")


def resolve_release_evidence_day(repo: Path, day: str | None) -> tuple[str | None, str | None]:
    """Resolve ``latest`` to the max dated ``release-status-YYYY-MM-DD.json``.

    Missing dated artifacts fail closed — never silently reuse 2026-08-06.
    """

    requested = (day or DEFAULT_RELEASE_EVIDENCE_DAY).strip() or DEFAULT_RELEASE_EVIDENCE_DAY
    if requested != "latest":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", requested):
            return None, f"invalid --day {requested!r}; expected YYYY-MM-DD or latest"
        return requested, None
    evidence = repo / "docs" / "evidence"
    if not evidence.is_dir():
        return None, "no docs/evidence directory; pass --day YYYY-MM-DD explicitly"
    dates = [
        match.group(1)
        for path in evidence.iterdir()
        if path.is_file() and (match := _RELEASE_STATUS_DAY_RE.fullmatch(path.name))
    ]
    if not dates:
        return None, ("no release-status-YYYY-MM-DD.json found; pass --day YYYY-MM-DD explicitly")
    return max(dates), None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_json(path: Path, errors: list[str], *, label: str) -> dict[str, Any] | None:
    if not path.is_file():
        errors.append(f"missing required evidence file: {label} ({path.as_posix()})")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: unreadable JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{label}: expected JSON object")
        return None
    return payload


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _resolve_sprint2_payload(
    repo: Path, errors: list[str]
) -> tuple[dict[str, Any] | None, Path | None]:
    evidence = repo / "docs" / "evidence"
    evidence_alias = evidence / "sprint2-baseline-evidence.json"
    report_json = evidence / "sprint2-baseline-report.json"
    for path, label in (
        (evidence_alias, "sprint2-baseline-evidence.json"),
        (report_json, "sprint2-baseline-report.json"),
    ):
        if path.is_file():
            payload = _load_json(path, errors, label=label)
            return payload, path
    errors.append(
        "missing sprint2 baseline JSON "
        "(expected docs/evidence/sprint2-baseline-evidence.json "
        "or docs/evidence/sprint2-baseline-report.json)"
    )
    return None, None


def _check_claim_locks(sprint2: dict[str, Any], errors: list[str]) -> None:
    claim_level = str(sprint2.get("claim_level") or "").strip()
    if not claim_level:
        errors.append("sprint2 claim_level missing")
    elif claim_level in FORBIDDEN_CUSTOMER_CLAIM_LEVELS:
        errors.append(f"sprint2 claim_level forbidden for release packaging: {claim_level!r}")
    elif claim_level not in ALLOWED_SYNTHETIC_CLAIM_LEVELS:
        errors.append(
            f"sprint2 claim_level unexpected for synthetic baseline: {claim_level!r} "
            f"(expected one of {sorted(ALLOWED_SYNTHETIC_CLAIM_LEVELS)})"
        )

    publishable = _as_bool(sprint2.get("customer_precision_claim_publishable"))
    if publishable is None:
        # Accept precision_claim_publishable alias if present.
        publishable = _as_bool(sprint2.get("precision_claim_publishable"))
    if publishable is None:
        errors.append(
            "sprint2 customer_precision_claim_publishable / precision_claim_publishable missing"
        )
    elif publishable is True:
        errors.append("customer_precision_claim_publishable must be false without intake gate")

    precision_alias = _as_bool(sprint2.get("precision_claim_publishable"))
    if precision_alias is True:
        errors.append("precision_claim_publishable=true is forbidden without intake gate")

    accuracy = _as_bool(sprint2.get("customer_accuracy_not_established"))
    if accuracy is False:
        errors.append("customer_accuracy_not_established must be true for synthetic baseline")

    if sprint2.get("closes_rt001") is True:
        errors.append("synthetic report must not claim closes_rt001=true")


def _check_intake_vs_publishable(
    *,
    sprint2: dict[str, Any],
    intake: dict[str, Any] | None,
    errors: list[str],
) -> None:
    publishable = bool(
        sprint2.get("customer_precision_claim_publishable")
        or sprint2.get("precision_claim_publishable")
    )
    if not publishable:
        return
    if intake is None:
        errors.append("customer_precision true but intake gate artifact missing")
        return
    raw_gates = intake.get("gates")
    gates: dict[str, Any] = raw_gates if isinstance(raw_gates, dict) else {}
    intake_ok = bool(gates.get("precision_claim_publishable")) and str(
        intake.get("claim_level") or ""
    ) not in {"", "not_ready"}
    if not intake_ok:
        errors.append(
            "customer_precision true without intake gate precision_claim_publishable=true "
            "and claim_level beyond not_ready"
        )


def _check_runtime_gates(
    runtime: dict[str, Any],
    errors: list[str],
    *,
    complete: bool,
) -> None:
    gates = runtime.get("quality_gates")
    if not isinstance(gates, dict):
        errors.append("runtime-baseline-latest.json quality_gates missing")
        return
    required = list(REQUIRED_RUNTIME_GATES)
    if complete:
        required.extend(["vitest", "build"])
    for name in required:
        status = str(gates.get(name) or "").upper()
        if status != "PASS":
            errors.append(f"runtime quality_gates.{name} not PASS (got {status!r})")


def _check_required_files(repo: Path, errors: list[str], day: str) -> None:
    evidence = repo / "docs" / "evidence"
    required = [
        evidence / "runtime-baseline-latest.json",
        evidence / f"SPRINT2_BASELINE_REPORT_{day}.md",
        evidence / f"SPRINT2_BASELINE_REPORT_{day}.pdf",
        evidence / "sprint2-baseline-report.md",
        evidence / "sprint2-baseline-report.pdf",
        repo / "docs" / "customer" / "CUSTOMER_ONE_PAGER.md",
        repo / "docs" / "customer" / f"CUSTOMER_DEMO_PROTOCOL_{day}.md",
        evidence / f"release-status-{day}.json",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing required evidence file: {path.as_posix()}")
        elif path.suffix.lower() == ".pdf" and path.stat().st_size < 100:
            errors.append(f"PDF too small / empty: {path.as_posix()}")

    evidence_json = evidence / "sprint2-baseline-evidence.json"
    report_json = evidence / "sprint2-baseline-report.json"
    if not evidence_json.is_file() and not report_json.is_file():
        errors.append(
            "missing sprint2 baseline JSON "
            "(sprint2-baseline-evidence.json or sprint2-baseline-report.json)"
        )


def _check_commit_alignment(
    *,
    release_status: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    sprint2: dict[str, Any] | None,
    errors: list[str],
) -> None:
    if release_status is None:
        return
    release_sha = str(release_status.get("commit_sha") or "").strip()
    if not release_sha:
        errors.append("release-status commit_sha missing")
        return

    if runtime is not None:
        runtime_sha = str(runtime.get("commit_sha") or "").strip()
        if runtime_sha and runtime_sha != release_sha:
            errors.append(
                f"commit_sha mismatch: release-status={release_sha} runtime-baseline={runtime_sha}"
            )

    if sprint2 is not None:
        sprint_sha = str(sprint2.get("commit_sha") or "").strip()
        if sprint_sha and sprint_sha != release_sha:
            errors.append(f"commit_sha mismatch: release-status={release_sha} sprint2={sprint_sha}")


def verify_release_evidence(
    *,
    repo: Path | None = None,
    day: str = "latest",
    complete: bool = True,
) -> dict[str, Any]:
    root = repo or _repo_root()
    errors: list[str] = []
    evidence = root / "docs" / "evidence"
    resolved_day, day_error = resolve_release_evidence_day(root, day)
    if resolved_day is None:
        errors.append(day_error or "release evidence day unresolved")
        return {
            "artifact_type": "aerobim_release_evidence_verification",
            "schema_version": "1.0.0",
            "ok": False,
            "verification": "failed",
            "errors": errors,
            "day": day,
            "complete": complete,
            "sprint2_path": None,
            "claim_boundary": (
                "Engineering release packaging only. Synthetic/fixture evidence "
                "never establishes customer accuracy. Checkpoint remains NO_GO."
            ),
        }
    day = resolved_day

    _check_required_files(root, errors, day)

    runtime = _load_json(
        evidence / "runtime-baseline-latest.json",
        errors,
        label="runtime-baseline-latest.json",
    )
    sprint2, sprint2_path = _resolve_sprint2_payload(root, errors)
    release_status = _load_json(
        evidence / f"release-status-{day}.json",
        errors,
        label=f"release-status-{day}.json",
    )
    intake = _load_json(
        root / "audit" / "evidence" / "customer-intake-gate.json",
        errors,
        label="customer-intake-gate.json",
    )

    if sprint2 is not None:
        _check_claim_locks(sprint2, errors)
        _check_intake_vs_publishable(sprint2=sprint2, intake=intake, errors=errors)
        # Alias wrapper must still carry synthetic claim locks.
        if sprint2.get("artifact_type") == "sprint2_baseline_evidence_alias":
            if sprint2.get("canonical_artifact_type") not in {
                "sprint2_synthetic_baseline",
                None,
            }:
                errors.append("sprint2-baseline-evidence.json alias has unexpected canonical type")

    if runtime is not None:
        _check_runtime_gates(runtime, errors, complete=complete)

    _check_commit_alignment(
        release_status=release_status,
        runtime=runtime,
        sprint2=sprint2,
        errors=errors,
    )

    if release_status is not None:
        verdict = str(
            release_status.get("verdict_candidate") or release_status.get("verdict") or ""
        )
        checkpoint = str(release_status.get("checkpoint") or "")
        if checkpoint and checkpoint not in {CHECKPOINT, "NO_GO"}:
            errors.append(
                f"release-status checkpoint must be GO or historical NO_GO (got {checkpoint!r})"
            )
        if verdict and verdict not in {
            "ENGINEERING_READY_CUSTOMER_BLOCKED",
            "NO_GO",
        }:
            errors.append(f"release-status verdict unexpected: {verdict!r}")

    ok = not errors
    return {
        "artifact_type": "aerobim_release_evidence_verification",
        "schema_version": "1.0.0",
        "ok": ok,
        "verification": "passed" if ok else "failed",
        "errors": errors,
        "day": day,
        "complete": complete,
        "sprint2_path": (
            str(sprint2_path.relative_to(root)).replace("\\", "/")
            if sprint2_path is not None and sprint2_path.is_relative_to(root)
            else (str(sprint2_path) if sprint2_path else None)
        ),
        "claim_boundary": (
            "Engineering release packaging only. Synthetic/fixture evidence "
            "never establishes customer accuracy. Checkpoint remains NO_GO."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument(
        "--day",
        default=DEFAULT_RELEASE_EVIDENCE_DAY,
        help="Dated evidence day (YYYY-MM-DD). Default latest = max dated release-status-*.json.",
    )
    parser.add_argument(
        "--complete",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require full runtime quality_gates including vitest/build (default: true)",
    )
    args = parser.parse_args(argv)
    result = verify_release_evidence(
        repo=args.repo.resolve() if args.repo else None,
        day=args.day,
        complete=bool(args.complete),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("complete", True):
        print("NOTE: verification ran with complete=false (relaxed gates).")
    if result["ok"]:
        print("OK: release evidence consistent (synthetic_only; customer blocked).")
        return 0
    print("\nRelease evidence verification FAILED:", file=sys.stderr)
    for err in result["errors"]:
        print(f"  - {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
