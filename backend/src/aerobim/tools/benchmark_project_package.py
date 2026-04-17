from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import TypedDict, cast

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import DrawingSource, RequirementSource, SourceKind, ValidationRequest
from aerobim.infrastructure.di.bootstrap import bootstrap_container


@dataclass(frozen=True)
class BenchmarkPack:
    pack_id: str
    description: str
    request: ValidationRequest


class MeasuredRun(TypedDict):
    iteration: int
    request_id: str
    elapsed_ms: float
    report_id: str
    issue_count: int
    requirement_count: int
    project_name: str | None
    discipline: str | None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_pack_path() -> Path:
    return repo_root() / "samples" / "benchmarks" / "project-package-baseline.json"


def _resolve_repo_path(raw_path: str, repo_root_path: Path) -> Path:
    resolved = (repo_root_path / raw_path).resolve()
    if not resolved.is_relative_to(repo_root_path.resolve()):
        raise ValueError(f"Benchmark pack path escapes repo root: {raw_path}")
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _load_optional_requirement_source(
    request_data: dict[str, object],
    field_name: str,
    source_kind: SourceKind,
    repo_root_path: Path,
) -> RequirementSource | None:
    raw_path = request_data.get(field_name)
    if raw_path is None:
        return None
    resolved_path = _resolve_repo_path(str(raw_path), repo_root_path)
    return RequirementSource(
        text=_read_text(resolved_path),
        path=resolved_path,
        source_kind=source_kind,
        source_id=f"benchmark-{source_kind.value}",
    )


def _load_drawing_sources(
    request_data: dict[str, object], repo_root_path: Path
) -> tuple[DrawingSource, ...]:
    drawing_sources: list[DrawingSource] = []
    raw_drawings = request_data.get("drawings", [])
    if not isinstance(raw_drawings, list):
        raise ValueError("Benchmark pack drawings must be a list")

    for item in raw_drawings:
        if not isinstance(item, dict):
            raise ValueError("Each benchmark drawing entry must be an object")
        drawing_data = cast(dict[str, object], item)
        resolved_path = _resolve_repo_path(str(drawing_data["path"]), repo_root_path)
        drawing_format = str(drawing_data.get("format") or "text")
        drawing_text = ""
        if resolved_path.suffix.lower() in {".txt", ".json", ".md"} or drawing_format.lower() in {
            "text",
            "json",
        }:
            drawing_text = _read_text(resolved_path)
        drawing_sources.append(
            DrawingSource(
                text=drawing_text,
                path=resolved_path,
                sheet_id=str(drawing_data.get("sheet_id"))
                if drawing_data.get("sheet_id")
                else None,
                format=drawing_format,
            )
        )
    return tuple(drawing_sources)


def load_benchmark_pack(manifest_path: Path, repo_root_path: Path | None = None) -> BenchmarkPack:
    resolved_repo_root = (repo_root_path or repo_root()).resolve()
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest_payload, dict):
        raise ValueError("Benchmark manifest must be a JSON object")

    manifest = cast(dict[str, object], manifest_payload)
    raw_request = manifest.get("request")
    if not isinstance(raw_request, dict):
        raise ValueError("Benchmark manifest request must be a JSON object")
    request_data = cast(dict[str, object], raw_request)

    requirement_path = _resolve_repo_path(str(request_data["requirement_path"]), resolved_repo_root)
    ifc_path = _resolve_repo_path(str(request_data["ifc_path"]), resolved_repo_root)
    ids_path_raw = request_data.get("ids_path")

    request = ValidationRequest(
        request_id=f"benchmark-{manifest['pack_id']}",
        ifc_path=ifc_path,
        requirement_source=RequirementSource(
            text=_read_text(requirement_path),
            path=requirement_path,
            source_kind=SourceKind.STRUCTURED_TEXT,
            source_id="benchmark-requirements",
        ),
        technical_spec_source=_load_optional_requirement_source(
            request_data,
            "technical_spec_path",
            SourceKind.TECHNICAL_SPECIFICATION,
            resolved_repo_root,
        ),
        calculation_source=_load_optional_requirement_source(
            request_data,
            "calculation_path",
            SourceKind.CALCULATION,
            resolved_repo_root,
        ),
        drawing_sources=_load_drawing_sources(request_data, resolved_repo_root),
        ids_path=_resolve_repo_path(str(ids_path_raw), resolved_repo_root)
        if ids_path_raw
        else None,
        origin="benchmark",
        project_name=_optional_string(manifest.get("project_name")),
        discipline=_optional_string(manifest.get("discipline")),
    )

    return BenchmarkPack(
        pack_id=str(manifest["pack_id"]),
        description=str(manifest.get("description") or ""),
        request=request,
    )


def summarize_benchmark_runs(measured_runs: list[MeasuredRun]) -> dict[str, float]:
    if not measured_runs:
        raise ValueError("Benchmark summary requires at least one measured run")
    elapsed_values = [run["elapsed_ms"] for run in measured_runs]
    average_ms = round(mean(elapsed_values), 3)
    return {
        "min_ms": round(min(elapsed_values), 3),
        "max_ms": round(max(elapsed_values), 3),
        "avg_ms": average_ms,
        "reports_per_second": round(1000.0 / average_ms, 3) if average_ms > 0 else 0.0,
    }


def _iteration_request(request: ValidationRequest, phase: str, index: int) -> ValidationRequest:
    return replace(request, request_id=f"{request.request_id}-{phase}-{index:03d}")


def run_benchmark(
    analyze_use_case,
    request: ValidationRequest,
    iterations: int,
    warmup_iterations: int = 0,
) -> dict[str, object]:
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    if warmup_iterations < 0:
        raise ValueError("warmup_iterations must be >= 0")

    for warmup_index in range(1, warmup_iterations + 1):
        analyze_use_case.execute(_iteration_request(request, "warmup", warmup_index))

    measured_runs: list[MeasuredRun] = []
    for iteration_index in range(1, iterations + 1):
        iteration_request = _iteration_request(request, "run", iteration_index)
        started_at = perf_counter()
        report = analyze_use_case.execute(iteration_request)
        elapsed_ms = round((perf_counter() - started_at) * 1000.0, 3)
        measured_runs.append(
            {
                "iteration": iteration_index,
                "request_id": iteration_request.request_id,
                "elapsed_ms": elapsed_ms,
                "report_id": report.report_id,
                "issue_count": report.summary.issue_count,
                "requirement_count": report.summary.requirement_count,
                "project_name": report.project_name,
                "discipline": report.discipline,
            }
        )

    return {
        "iterations": iterations,
        "warmup_iterations": warmup_iterations,
        "measured_runs": measured_runs,
        "summary": summarize_benchmark_runs(measured_runs),
    }


def benchmark_project_package(
    pack_path: Path,
    iterations: int,
    warmup_iterations: int,
    storage_dir: Path | None = None,
) -> dict[str, object]:
    benchmark_pack = load_benchmark_pack(pack_path)
    settings = Settings.from_env()
    if storage_dir is not None:
        settings = replace(settings, storage_dir=storage_dir.resolve())

    container = bootstrap_container(settings)
    analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
    payload = run_benchmark(analyze_use_case, benchmark_pack.request, iterations, warmup_iterations)
    payload["pack_id"] = benchmark_pack.pack_id
    payload["description"] = benchmark_pack.description
    payload["storage_dir"] = str(settings.storage_dir.resolve())
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a fixture-backed benchmark rail for analyze/project-package"
    )
    parser.add_argument(
        "--pack", type=Path, default=default_pack_path(), help="Path to a benchmark pack manifest"
    )
    parser.add_argument(
        "--iterations", type=int, default=3, help="Number of measured benchmark iterations"
    )
    parser.add_argument(
        "--warmup-iterations", type=int, default=1, help="Number of unmeasured warmup iterations"
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        default=None,
        help="Optional storage directory for persisted benchmark reports",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON result to this file instead of stdout (written only on success)",
    )
    args = parser.parse_args()

    payload = benchmark_project_package(
        pack_path=args.pack,
        iterations=args.iterations,
        warmup_iterations=args.warmup_iterations,
        storage_dir=args.storage_dir,
    )
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = args.output.with_suffix(".tmp")
        tmp_path.write_text(serialized, encoding="utf-8")
        tmp_path.replace(args.output)
    else:
        print(serialized)


if __name__ == "__main__":
    main()
