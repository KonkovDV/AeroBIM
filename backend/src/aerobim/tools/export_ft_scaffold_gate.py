from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "llm/configs/aerobim_spec_extraction_ft_config_v1.json",
    "llm/datasets/manifest_v1.json",
    "llm/datasets/split_policy_v1.md",
    "llm/train/smoke_train.py",
    "llm/eval/smoke_eval.py",
    "llm/serve/smoke_serve.py",
    "llm/README.md",
)


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    started = datetime.now(tz=UTC)
    process = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    duration_ms = int((datetime.now(tz=UTC) - started).total_seconds() * 1000)
    output_summary = f"{process.stdout}\n{process.stderr}".strip()
    if len(output_summary) > 1400:
        output_summary = output_summary[:1400] + "\n...truncated"

    return {
        "command": " ".join(command),
        "passed": process.returncode == 0,
        "exit_code": process.returncode,
        "duration_ms": duration_ms,
        "output_summary": output_summary,
    }


def build_ft_scaffold_gate_report(
    command_checks: list[dict[str, Any]],
    criteria: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "project": "AeroBIM",
        "artifact_type": "aerobim_ft_scaffold_gate_report",
        "generated_at": _utc_now(),
        "version": "v1",
        "command_bundle": [check["command"] for check in command_checks],
        "command_checks": command_checks,
        "criteria": criteria,
        "gate_passed": all(check["passed"] for check in command_checks)
        and all(criterion["passed"] for criterion in criteria),
        "known_limits_non_claims": [
            "Scaffold gate verifies train/eval/serve preconditions only.",
            "No claim of production FT extraction quality.",
            "No claim of deployment-grade serving readiness.",
        ],
    }


def export_ft_scaffold_gate(output_path: Path) -> dict[str, Any]:
    root = project_root()

    commands = [
        [sys.executable, "llm/train/smoke_train.py"],
        [sys.executable, "llm/eval/smoke_eval.py"],
        [sys.executable, "llm/serve/smoke_serve.py"],
    ]
    command_checks = [run_command(command, root) for command in commands]

    file_criteria = [
        {
            "name": f"required_file:{relative_path}",
            "passed": (root / relative_path).exists(),
            "details": str((root / relative_path).resolve()),
        }
        for relative_path in REQUIRED_FILES
    ]

    train_report_path = root / "llm/artifacts/train/smoke_train_report_v1.json"
    eval_report_path = root / "llm/artifacts/eval/smoke_eval_report_v1.json"
    serve_report_path = root / "llm/artifacts/serve/smoke_serve_report_v1.json"

    train_report = json.loads(train_report_path.read_text(encoding="utf-8")) if train_report_path.exists() else {}
    eval_report = json.loads(eval_report_path.read_text(encoding="utf-8")) if eval_report_path.exists() else {}
    serve_report = json.loads(serve_report_path.read_text(encoding="utf-8")) if serve_report_path.exists() else {}

    runtime_criteria = [
        {
            "name": "train_smoke_entrypoint",
            "passed": train_report.get("status") == "APPROVED",
            "details": str(train_report_path),
        },
        {
            "name": "eval_machine_readable_output",
            "passed": eval_report.get("status") == "APPROVED"
            and eval_report.get("artifact_type") == "aerobim_ft_eval_smoke_report",
            "details": str(eval_report_path),
        },
        {
            "name": "serve_smoke_output",
            "passed": serve_report.get("status") == "APPROVED",
            "details": str(serve_report_path),
        },
    ]

    report = build_ft_scaffold_gate_report(command_checks, [*file_criteria, *runtime_criteria])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Export AeroBIM FT scaffold gate report")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("../reports/aerobim_ft_scaffold_gate_report_v1.json"),
    )
    args = parser.parse_args()

    report = export_ft_scaffold_gate(args.output.resolve())
    print(json.dumps({"gate_passed": report["gate_passed"], "output": str(args.output.resolve())}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["gate_passed"] else 1)


if __name__ == "__main__":
    main()
