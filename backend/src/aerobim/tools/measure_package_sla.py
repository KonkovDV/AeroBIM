"""Measure project-package analysis SLA against Samolet TechLab target (≤ 30 min)."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.architecture import DEFAULT_PACKAGE_STAGE_BUDGET, StageBudget
from aerobim.tools.benchmark_project_package import (
    benchmark_project_package,
    default_pack_path,
    repo_root,
)


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _pack_file_inventory(pack_path: Path) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = [
        {
            "path": str(pack_path.as_posix()),
            "bytes": pack_path.stat().st_size,
            "sha256": _sha256_file(pack_path),
        }
    ]
    try:
        manifest = json.loads(pack_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return inventory
    if not isinstance(manifest, dict):
        return inventory

    root = pack_path.parent
    candidates: list[Path] = []
    for key in ("ifc_path", "ids_path", "drawing_path", "calculation_path"):
        raw = manifest.get(key)
        if isinstance(raw, str) and raw.strip():
            candidates.append(Path(raw))
    for key in ("drawings", "requirements", "assets"):
        raw = manifest.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    candidates.append(Path(item))
                elif isinstance(item, dict):
                    for nested in ("path", "ifc_path", "drawing_path"):
                        value = item.get(nested)
                        if isinstance(value, str) and value.strip():
                            candidates.append(Path(value))

    seen: set[str] = {str(pack_path.resolve())}
    for rel in candidates:
        path = rel if rel.is_absolute() else (root / rel)
        if not path.is_file():
            # Manifests often use repo-root-relative paths.
            alt = repo_root() / rel
            path = alt if alt.is_file() else path
        try:
            resolved = str(path.resolve())
        except OSError:
            continue
        if resolved in seen or not path.is_file():
            continue
        seen.add(resolved)
        inventory.append(
            {
                "path": str(path.as_posix()),
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    return inventory


def _machine_fingerprint() -> dict[str, object]:
    ram_gb: float | None = None
    try:
        import psutil  # type: ignore[import-untyped]

        ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    except Exception:
        ram_gb = None
    return {
        "os": platform.platform(),
        "cpu": platform.processor() or platform.machine(),
        "ram_gb": ram_gb,
        "python": platform.python_version(),
    }


def _machine_fingerprint_complete(machine: dict[str, object]) -> bool:
    """Require stable OS/CPU/Python identity for customer-measurable SLA claims."""

    os_name = machine.get("os")
    cpu = machine.get("cpu")
    python = machine.get("python")
    return (
        isinstance(os_name, str)
        and bool(os_name.strip())
        and isinstance(cpu, str)
        and bool(cpu.strip())
        and isinstance(python, str)
        and bool(python.strip())
    )


def measure_package_sla(
    pack_path: Path,
    *,
    max_minutes: float,
    iterations: int = 1,
    warmup_iterations: int = 0,
    stage_budget: StageBudget | None = None,
    corpus_kind: str = "fixture",
    claim_level: str | None = None,
    command: str | None = None,
    mandatory_capabilities_complete: bool = False,
) -> dict[str, object]:
    if corpus_kind not in {"fixture", "customer"}:
        raise ValueError("corpus_kind must be 'fixture' or 'customer'")
    resolved_claim = claim_level or (
        "customer_measurable" if corpus_kind == "customer" else "fixture_only"
    )
    if resolved_claim not in {"fixture_only", "customer_measurable"}:
        raise ValueError("claim_level must be 'fixture_only' or 'customer_measurable'")
    if resolved_claim == "customer_measurable" and corpus_kind != "customer":
        raise ValueError("customer_measurable claim_level requires corpus_kind=customer")

    pack_path = pack_path.resolve()
    budget = stage_budget or DEFAULT_PACKAGE_STAGE_BUDGET
    if abs(budget.total_minutes - max_minutes) > 1e-6 and stage_budget is None:
        # Scale default contour budgets proportionally to the requested ceiling.
        scale = max_minutes / DEFAULT_PACKAGE_STAGE_BUDGET.total_minutes
        budget = StageBudget(
            ingestion_minutes=round(DEFAULT_PACKAGE_STAGE_BUDGET.ingestion_minutes * scale, 4),
            deterministic_validation_minutes=round(
                DEFAULT_PACKAGE_STAGE_BUDGET.deterministic_validation_minutes * scale, 4
            ),
            ai_advisory_minutes=round(DEFAULT_PACKAGE_STAGE_BUDGET.ai_advisory_minutes * scale, 4),
            evidence_reporting_minutes=round(
                DEFAULT_PACKAGE_STAGE_BUDGET.evidence_reporting_minutes * scale, 4
            ),
        )

    inventory = _pack_file_inventory(pack_path)
    package_sha256 = _sha256_file(pack_path)
    machine = _machine_fingerprint()

    if resolved_claim == "customer_measurable":
        missing: list[str] = []
        if corpus_kind != "customer":
            missing.append("corpus_kind=customer")
        if not package_sha256:
            missing.append("pack_hash")
        if not _machine_fingerprint_complete(machine):
            missing.append("machine_fingerprint")
        if not mandatory_capabilities_complete:
            missing.append("mandatory_capabilities_complete")
        if missing:
            raise ValueError(
                "customer_measurable claim refused: missing "
                + ", ".join(missing)
                + " (fixture runs must stay claim_level=fixture_only)"
            )

    cold_payload = benchmark_project_package(
        pack_path=pack_path,
        iterations=iterations,
        warmup_iterations=0,
        storage_dir=None,
    )
    warm_payload: dict[str, object] | None = None
    if warmup_iterations > 0:
        warm_payload = benchmark_project_package(
            pack_path=pack_path,
            iterations=max(1, iterations),
            warmup_iterations=warmup_iterations,
            storage_dir=None,
        )

    def _minutes(payload: dict[str, object]) -> tuple[float, float]:
        summary = payload["summary"]
        if not isinstance(summary, dict):
            raise TypeError("benchmark summary must be a dict")
        max_ms = float(summary["max_ms"])
        avg_ms = float(summary["avg_ms"])
        return round(max_ms / 60_000.0, 4), round(avg_ms / 60_000.0, 4)

    cold_max, cold_avg = _minutes(cold_payload)
    warm_max: float | None = None
    warm_avg: float | None = None
    if warm_payload is not None:
        warm_max, warm_avg = _minutes(warm_payload)

    # Primary SLA observation uses cold run (worst realistic first-touch).
    max_minutes_observed = cold_max
    avg_minutes_observed = cold_avg
    sla_pass = max_minutes_observed <= max_minutes
    stage_budget_consistent = abs(budget.total_minutes - max_minutes) <= 1e-6

    resolved_command = command or (
        f"python -m aerobim.tools.measure_package_sla --pack {pack_path} "
        f"--max-minutes {max_minutes} --iterations {iterations} "
        f"--warmup-iterations {warmup_iterations}"
    )

    return {
        "artifact_type": "samolet_package_sla",
        "schema_version": "1.3.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "customer_reference": "https://i.moscow/techlab/samolet",
        "sla_target_minutes": max_minutes,
        "sla_pass": sla_pass,
        "max_minutes_observed": max_minutes_observed,
        "avg_minutes_observed": avg_minutes_observed,
        "stage_budgets": budget.as_dict(),
        "stage_budget_consistent": stage_budget_consistent,
        "package_sha256": package_sha256,
        "pack_hash": package_sha256,
        "file_inventory": inventory,
        "machine": machine,
        "machine_fingerprint": machine,
        "mandatory_capabilities_complete": mandatory_capabilities_complete,
        "cold_run": {
            "max_minutes": cold_max,
            "avg_minutes": cold_avg,
            "benchmark": cold_payload,
        },
        "warm_run": {
            "max_minutes": warm_max,
            "avg_minutes": warm_avg,
            "benchmark": warm_payload,
        },
        "command": resolved_command,
        "corpus_kind": corpus_kind,
        "claim_level": resolved_claim,
        "allowed_wording": (
            "Fixture wall-clock only; not customer комплект SLA"
            if resolved_claim == "fixture_only"
            else "Customer package SLA measurement"
        ),
        "benchmark": cold_payload,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure analyze/project-package wall time vs Samolet ≤30 min SLA"
    )
    parser.add_argument(
        "--pack",
        type=Path,
        default=default_pack_path(),
        help="Benchmark pack manifest (default: pilot-moscow if exists, else baseline)",
    )
    parser.add_argument(
        "--max-minutes",
        type=float,
        default=30.0,
        help="SLA ceiling in minutes (Samolet task page default: 30)",
    )
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--warmup-iterations", type=int, default=0)
    parser.add_argument(
        "--corpus-kind",
        choices=("fixture", "customer"),
        default="fixture",
    )
    parser.add_argument(
        "--claim-level",
        choices=("fixture_only", "customer_measurable"),
        default=None,
    )
    parser.add_argument(
        "--mandatory-capabilities-complete",
        action="store_true",
        help=(
            "Required for customer_measurable claims; affirms mandatory pilot "
            "capabilities completed on the measured customer package"
        ),
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    pilot_pack = repo_root() / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
    pack_path = args.pack
    if pack_path == default_pack_path() and pilot_pack.exists():
        pack_path = pilot_pack

    result = measure_package_sla(
        pack_path,
        max_minutes=args.max_minutes,
        iterations=args.iterations,
        warmup_iterations=args.warmup_iterations,
        corpus_kind=args.corpus_kind,
        claim_level=args.claim_level,
        mandatory_capabilities_complete=args.mandatory_capabilities_complete,
    )
    serialized = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(args.output)
    else:
        print(serialized)

    if not result["sla_pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
