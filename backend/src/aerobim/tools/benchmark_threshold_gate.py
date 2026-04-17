from __future__ import annotations

import argparse
import json
from pathlib import Path


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def load_threshold_profile(profile_path: Path) -> dict[str, object]:
    return json.loads(profile_path.read_text(encoding="utf-8"))


def load_benchmark_artifacts(artifact_dir: Path) -> dict[str, dict[str, object]]:
    payloads: dict[str, dict[str, object]] = {}
    for artifact_path in sorted(artifact_dir.glob("project-package-*.json")):
        raw = artifact_path.read_text(encoding="utf-8").strip()
        if not raw:
            raise ValueError(
                f"Benchmark artifact is empty — the benchmark pack that produced it likely "
                f"failed before writing any output: {artifact_path}"
            )
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Benchmark artifact contains invalid JSON: {artifact_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Benchmark artifact must be a JSON object: {artifact_path}")
        pack_id = payload.get("pack_id")
        if isinstance(pack_id, str) and pack_id:
            payloads[pack_id] = payload
    return payloads


def evaluate_thresholds(
    payloads: dict[str, dict[str, object]],
    threshold_profile: dict[str, object],
) -> dict[str, object]:
    profile_packs = threshold_profile.get("packs")
    if not isinstance(profile_packs, dict):
        raise ValueError("Threshold profile must contain a packs object")

    checks: list[dict[str, object]] = []
    has_failure = False

    for pack_id, raw_pack_thresholds in profile_packs.items():
        if not isinstance(raw_pack_thresholds, dict):
            raise ValueError(f"Threshold profile pack entry must be an object: {pack_id}")

        payload = payloads.get(pack_id)
        if payload is None:
            has_failure = True
            checks.append(
                {
                    "pack_id": pack_id,
                    "status": "missing",
                    "violations": ["benchmark artifact not found"],
                }
            )
            continue

        summary = payload.get("summary")
        if not isinstance(summary, dict):
            raise ValueError(f"Benchmark artifact summary must be an object: {pack_id}")

        avg_ms = _as_float(summary.get("avg_ms"))
        reports_per_second = _as_float(summary.get("reports_per_second"))
        max_avg_ms = _as_float(raw_pack_thresholds.get("max_avg_ms"))
        min_reports_per_second = _as_float(raw_pack_thresholds.get("min_reports_per_second"))

        violations: list[str] = []
        if max_avg_ms is not None and avg_ms is not None and avg_ms > max_avg_ms:
            violations.append(f"avg_ms {avg_ms} exceeds max_avg_ms {max_avg_ms}")
        if (
            min_reports_per_second is not None
            and reports_per_second is not None
            and reports_per_second < min_reports_per_second
        ):
            violations.append(
                "reports_per_second "
                f"{reports_per_second} below min_reports_per_second "
                f"{min_reports_per_second}"
            )

        status = "pass" if not violations else "failed"
        if violations:
            has_failure = True

        checks.append(
            {
                "pack_id": pack_id,
                "status": status,
                "avg_ms": avg_ms,
                "reports_per_second": reports_per_second,
                "max_avg_ms": max_avg_ms,
                "min_reports_per_second": min_reports_per_second,
                "violations": violations,
            }
        )

    return {
        "checks": checks,
        "has_failure": has_failure,
    }


def render_markdown(evaluation: dict[str, object], mode: str, profile_path: Path) -> str:
    checks = evaluation["checks"]
    assert isinstance(checks, list)

    lines = [
        "## Benchmark Threshold Advisory",
        "",
        f"Mode: `{mode}`",
        f"Profile: `{profile_path.as_posix()}`",
        "",
        "| Pack | Status | Avg ms | Max avg ms | Reports/s | Min reports/s |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for check in checks:
        assert isinstance(check, dict)
        lines.append(
            "| {pack} | {status} | {avg} | {max_avg} | {rps} | {min_rps} |".format(
                pack=check.get("pack_id", "unknown"),
                status=check.get("status", "unknown"),
                avg=check.get("avg_ms", "n/a"),
                max_avg=check.get("max_avg_ms", "n/a"),
                rps=check.get("reports_per_second", "n/a"),
                min_rps=check.get("min_reports_per_second", "n/a"),
            )
        )

        violations = check.get("violations")
        if isinstance(violations, list) and violations:
            for violation in violations:
                lines.append(f"- `{check.get('pack_id', 'unknown')}`: {violation}")

    lines.append("")
    return "\n".join(lines)


def run_threshold_gate(
    artifact_dir: Path,
    profile_path: Path,
    mode: str,
) -> dict[str, object]:
    if mode not in {"advisory", "enforced"}:
        raise ValueError("mode must be advisory or enforced")

    payloads = load_benchmark_artifacts(artifact_dir)
    threshold_profile = load_threshold_profile(profile_path)
    evaluation = evaluate_thresholds(payloads, threshold_profile)

    has_failure = bool(evaluation["has_failure"])
    gate_passed = not has_failure or mode == "advisory"

    return {
        "mode": mode,
        "profile_path": str(profile_path),
        "artifact_dir": str(artifact_dir),
        "gate_passed": gate_passed,
        "has_failure": has_failure,
        **evaluation,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate benchmark-smoke outputs against a threshold profile"
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="Directory containing benchmark JSON artifacts",
    )
    parser.add_argument(
        "--threshold-profile",
        type=Path,
        required=True,
        help="Path to benchmark threshold profile JSON",
    )
    parser.add_argument("--mode", choices=["advisory", "enforced"], default="advisory")
    parser.add_argument(
        "--markdown-output", type=Path, default=None, help="Optional path to write markdown summary"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON evaluation payload to this file instead of stdout",
    )
    args = parser.parse_args()

    payload = run_threshold_gate(args.artifact_dir, args.threshold_profile, args.mode)
    if args.markdown_output is not None:
        args.markdown_output.write_text(
            render_markdown(payload, args.mode, args.threshold_profile),
            encoding="utf-8",
        )

    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = args.output.with_suffix(".tmp")
        tmp_path.write_text(serialized, encoding="utf-8")
        tmp_path.replace(args.output)
    else:
        print(serialized)

    if args.mode == "enforced" and not payload["gate_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
