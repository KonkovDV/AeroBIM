from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def count_jsonl_records(file_path: Path) -> int:
    return sum(1 for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip())


def run_train_smoke(config_path: Path, manifest_path: Path, output_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    train_path = Path(manifest["splits"]["train"]["path"])
    val_path = Path(manifest["splits"]["val"]["path"])
    holdout_path = Path(manifest["splits"]["holdout"]["path"])

    train_count = count_jsonl_records(train_path)
    val_count = count_jsonl_records(val_path)
    holdout_count = count_jsonl_records(holdout_path)

    checks = [
        {
            "name": "config_exists",
            "passed": config_path.exists(),
            "details": str(config_path),
        },
        {
            "name": "train_min_examples",
            "passed": train_count >= int(manifest["splits"]["train"]["expected_min_examples"]),
            "details": f"train={train_count}",
        },
        {
            "name": "val_min_examples",
            "passed": val_count >= int(manifest["splits"]["val"]["expected_min_examples"]),
            "details": f"val={val_count}",
        },
        {
            "name": "holdout_min_examples",
            "passed": holdout_count >= int(manifest["splits"]["holdout"]["expected_min_examples"]),
            "details": f"holdout={holdout_count}",
        },
    ]

    status = "APPROVED" if all(check["passed"] for check in checks) else "DEGRADED"

    report = {
        "artifact_type": "aerobim_ft_train_smoke_report",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "status": status,
        "config_path": str(config_path),
        "manifest_path": str(manifest_path),
        "split_counts": {
            "train": train_count,
            "val": val_count,
            "holdout": holdout_count,
        },
        "checks": checks,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="AeroBIM FT train smoke")
    parser.add_argument("--config", type=Path, default=Path("llm/configs/aerobim_spec_extraction_ft_config_v1.json"))
    parser.add_argument("--manifest", type=Path, default=Path("llm/datasets/manifest_v1.json"))
    parser.add_argument("--output", type=Path, default=Path("llm/artifacts/train/smoke_train_report_v1.json"))
    args = parser.parse_args()

    report = run_train_smoke(args.config.resolve(), args.manifest.resolve(), args.output.resolve())
    print(json.dumps({"status": report["status"], "output": str(args.output.resolve())}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "APPROVED" else 1)


if __name__ == "__main__":
    main()
