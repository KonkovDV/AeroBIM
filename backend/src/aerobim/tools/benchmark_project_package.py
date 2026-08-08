from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import sys
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any, TypedDict, cast

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import (
    DocStatus,
    DrawingSource,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container

# Schema-suite defaults: with n=5 nearest-rank p95 ≡ max, so one OS/MEP spike
# (seen historically on IFC4 iter 5 ≈ 568 ms) polluted the headline. n≥20 keeps
# p95 distinct from a single max outlier; warmup≥2 primes DI/IfcOpenShell/MEP path.
SCHEMA_SUITE_DEFAULT_ITERATIONS = 20
SCHEMA_SUITE_DEFAULT_WARMUP_ITERATIONS = 2
SPIKE_RATIO_WARN = 5.0


@dataclass(frozen=True)
class BenchmarkPack:
    pack_id: str
    pack_version: str
    manifest_schema_version: str
    description: str
    request: ValidationRequest
    ifc_schema: str | None = None
    corpus_kind: str | None = None
    pack_path: Path | None = None


class MeasuredRun(TypedDict):
    iteration: int
    request_id: str
    elapsed_ms: float
    report_id: str
    issue_count: int
    requirement_count: int
    project_name: str | None
    discipline: str | None


SCHEMA_SUITE_PACK_RELATIVE = (
    "samples/benchmarks/project-package-ifc2x3-schema.json",
    "samples/benchmarks/project-package-ifc4-schema.json",
    "samples/benchmarks/project-package-ifc4x3-schema.json",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_pack_path() -> Path:
    return repo_root() / "samples" / "benchmarks" / "project-package-baseline.json"


def schema_suite_pack_paths(repo_root_path: Path | None = None) -> list[Path]:
    root = (repo_root_path or repo_root()).resolve()
    return [(root / relative).resolve() for relative in SCHEMA_SUITE_PACK_RELATIVE]


def _resolve_repo_path(raw_path: str, repo_root_path: Path) -> Path:
    resolved = (repo_root_path / raw_path).resolve()
    if not resolved.is_relative_to(repo_root_path.resolve()):
        raise ValueError(f"Benchmark pack path escapes repo root: {raw_path}")
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_doc_status(value: object) -> DocStatus | None:
    if value is None:
        return None
    normalized = str(value)
    if normalized in {"WIP", "Shared", "Published", "Archived"}:
        return cast(DocStatus, normalized)
    return None


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
    pack_schema_version = str(manifest.get("schema_version") or "1.0.0")
    pack_version = str(manifest.get("pack_version") or "1.0.0")
    raw_request = manifest.get("request")
    if not isinstance(raw_request, dict):
        raise ValueError("Benchmark manifest request must be a JSON object")
    request_data = cast(dict[str, object], raw_request)

    ifc_path = _resolve_repo_path(str(request_data["ifc_path"]), resolved_repo_root)
    ids_path_raw = request_data.get("ids_path")

    requirement_source: RequirementSource | None = None
    requirement_path_raw = request_data.get("requirement_path")
    if requirement_path_raw is not None:
        requirement_path = _resolve_repo_path(str(requirement_path_raw), resolved_repo_root)
        requirement_source = RequirementSource(
            text=_read_text(requirement_path),
            path=requirement_path,
            source_kind=SourceKind.STRUCTURED_TEXT,
            source_id="benchmark-requirements",
        )

    request = ValidationRequest(
        request_id=f"benchmark-{manifest['pack_id']}",
        ifc_path=ifc_path,
        requirement_source=requirement_source
        or RequirementSource(
            text="",
            source_kind=SourceKind.STRUCTURED_TEXT,
            source_id="benchmark-requirements-empty",
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
        stage=_optional_string(manifest.get("stage") or request_data.get("stage")),
        information_container_id=_optional_string(
            manifest.get("information_container_id") or request_data.get("information_container_id")
        ),
        revision=_optional_string(manifest.get("revision") or request_data.get("revision")),
        doc_status=_optional_doc_status(
            manifest.get("doc_status") or request_data.get("doc_status")
        ),
    )

    return BenchmarkPack(
        pack_id=str(manifest["pack_id"]),
        pack_version=pack_version,
        manifest_schema_version=pack_schema_version,
        description=str(manifest.get("description") or ""),
        request=request,
        ifc_schema=_optional_string(manifest.get("ifc_schema")),
        corpus_kind=_optional_string(manifest.get("corpus_kind")),
        pack_path=manifest_path.resolve(),
    )


def _percentile_nearest_rank(values: list[float], percentile: float) -> float:
    """Inclusive nearest-rank percentile (p in 0..100). Single sample → that sample."""

    if not values:
        raise ValueError("percentile requires at least one value")
    if percentile < 0 or percentile > 100:
        raise ValueError("percentile must be in [0, 100]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = max(1, int(round(percentile / 100.0 * len(ordered))))
    return ordered[min(rank, len(ordered)) - 1]


def summarize_benchmark_runs(measured_runs: list[MeasuredRun]) -> dict[str, Any]:
    if not measured_runs:
        raise ValueError("Benchmark summary requires at least one measured run")
    elapsed_values = [run["elapsed_ms"] for run in measured_runs]
    average_ms = round(mean(elapsed_values), 3)
    p50_ms = round(_percentile_nearest_rank(elapsed_values, 50.0), 3)
    p95_ms = round(_percentile_nearest_rank(elapsed_values, 95.0), 3)
    max_ms = round(max(elapsed_values), 3)
    min_ms = round(min(elapsed_values), 3)
    sample_n = len(elapsed_values)
    spike_ratio = round(max_ms / p50_ms, 3) if p50_ms > 0 else None
    return {
        "min_ms": min_ms,
        "max_ms": max_ms,
        "avg_ms": average_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "reports_per_second": round(1000.0 / average_ms, 3) if average_ms > 0 else 0.0,
        "sample_n": sample_n,
        "p95_equals_max": p95_ms == max_ms,
        "spike_ratio_max_over_p50": spike_ratio,
        "timing_stability_note": (
            "With small n, nearest-rank p95 equals max; prefer schema-suite n≥20."
            if sample_n < 20 and p95_ms == max_ms
            else (
                f"max/p50={spike_ratio} exceeds {SPIKE_RATIO_WARN}x — OS/MEP/GC noise possible."
                if spike_ratio is not None and spike_ratio >= SPIKE_RATIO_WARN
                else None
            )
        ),
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

    # Drop warmup allocations before measured window (reduces GC mid-suite spikes).
    gc.collect()

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


def _machine_fingerprint() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "machine": platform.machine(),
        "system": platform.system(),
    }


def _dependency_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in ("ifcopenshell", "ifctester", "fastapi"):
        try:
            module = __import__(name)
            versions[name] = getattr(module, "__version__", None)
        except Exception:  # noqa: BLE001 — inventory best-effort
            versions[name] = None
    return versions


def _ifc_file_metrics(ifc_path: Path | None) -> dict[str, object]:
    if ifc_path is None or not ifc_path.exists():
        return {
            "bytes": None,
            "entity_count": None,
            "schema_from_header": None,
        }
    metrics: dict[str, object] = {
        "bytes": ifc_path.stat().st_size,
        "entity_count": None,
        "schema_from_header": None,
    }
    try:
        import ifcopenshell

        model = ifcopenshell.open(str(ifc_path))
        metrics["schema_from_header"] = model.schema
        metrics["entity_count"] = len(list(model))
    except Exception:  # noqa: BLE001 — metrics are best-effort for evidence
        try:
            text = ifc_path.read_text(encoding="utf-8", errors="ignore")
            for line in text.splitlines()[:40]:
                if "FILE_SCHEMA" in line.upper():
                    metrics["schema_from_header"] = line.strip()
                    break
            metrics["entity_count"] = sum(
                1 for line in text.splitlines() if line.startswith("#") and "=" in line
            )
        except OSError:
            pass
    return metrics


def benchmark_project_package(
    pack_path: Path,
    iterations: int,
    warmup_iterations: int,
    storage_dir: Path | None = None,
    *,
    analyze_use_case: Any | None = None,
    settings: Settings | None = None,
) -> dict[str, object]:
    benchmark_pack = load_benchmark_pack(pack_path)
    if settings is None:
        settings = Settings.from_env()
        if storage_dir is not None:
            settings = replace(settings, storage_dir=storage_dir.resolve())
    elif storage_dir is not None and settings.storage_dir != storage_dir.resolve():
        settings = replace(settings, storage_dir=storage_dir.resolve())

    if analyze_use_case is None:
        container = bootstrap_container(settings)
        analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
    ifc_path = benchmark_pack.request.ifc_path
    file_metrics = _ifc_file_metrics(ifc_path)
    import tracemalloc

    tracemalloc.start()
    try:
        payload = run_benchmark(
            analyze_use_case, benchmark_pack.request, iterations, warmup_iterations
        )
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    payload["artifact_type"] = "benchmark_project_package"
    payload["schema_version"] = "1.2.0"
    payload["generated_at"] = datetime.now(tz=UTC).isoformat()
    payload["claim_level"] = "fixture_only"
    payload["customer_accuracy_not_established"] = True
    payload["accuracy_measured"] = False
    payload["accuracy_note"] = (
        "No adjudicated finding ground truth for these packs; issue_count is not accuracy."
    )
    payload["benchmark_pack"] = {
        "pack_id": benchmark_pack.pack_id,
        "pack_version": benchmark_pack.pack_version,
        "manifest_schema_version": benchmark_pack.manifest_schema_version,
        "description": benchmark_pack.description,
        "ifc_schema": benchmark_pack.ifc_schema,
        "corpus_kind": benchmark_pack.corpus_kind or "fixture",
        "pack_path": str(pack_path.resolve()),
    }
    payload["pack_id"] = benchmark_pack.pack_id
    payload["pack_version"] = benchmark_pack.pack_version
    payload["description"] = benchmark_pack.description
    payload["ifc_schema"] = benchmark_pack.ifc_schema
    payload["corpus_kind"] = benchmark_pack.corpus_kind or "fixture"
    payload["pack_path"] = str(pack_path.resolve())
    payload["ifc_sha256"] = _sha256_file(ifc_path) if ifc_path is not None else None
    payload["ifc_bytes"] = file_metrics.get("bytes")
    payload["ifc_entity_count"] = file_metrics.get("entity_count")
    payload["ifc_schema_from_header"] = file_metrics.get("schema_from_header")
    payload["peak_traced_memory_bytes"] = int(peak)
    payload["dependencies"] = _dependency_versions()
    payload["machine"] = _machine_fingerprint()
    payload["storage_dir"] = str(settings.storage_dir.resolve())
    return payload


def benchmark_schema_suite(
    pack_paths: list[Path],
    iterations: int,
    warmup_iterations: int,
    storage_dir: Path | None = None,
    group_by: str | None = None,
) -> dict[str, object]:
    """Run schema packs with a shared DI container to reduce cold-bootstrap noise."""
    settings = Settings.from_env()
    if storage_dir is not None:
        settings = replace(settings, storage_dir=storage_dir.resolve())
    container = bootstrap_container(settings)
    analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

    # Process-level prime: one unmeasured execute on the first pack so MEP fail-closed
    # path / IfcOpenShell schema caches are warm before any measured schema window.
    if pack_paths:
        first_pack = load_benchmark_pack(pack_paths[0])
        analyze_use_case.execute(
            _iteration_request(first_pack.request, "suite-prime", 1)
        )
        gc.collect()

    pack_results = [
        benchmark_project_package(
            pack_path=path,
            iterations=iterations,
            warmup_iterations=warmup_iterations,
            storage_dir=storage_dir,
            analyze_use_case=analyze_use_case,
            settings=settings,
        )
        for path in pack_paths
    ]
    payload: dict[str, object] = {
        "artifact_type": "ifc_release_benchmark_suite",
        "schema_version": "1.1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "fixture_only",
        "customer_accuracy_not_established": True,
        "machine": _machine_fingerprint(),
        "iterations": iterations,
        "warmup_iterations": warmup_iterations,
        "suite_process_prime": True,
        "shared_container": True,
        "stability_policy": (
            "Schema suite reuses one DI container, primes once, warms per pack, "
            f"gc.collect after warmup, and defaults to n={SCHEMA_SUITE_DEFAULT_ITERATIONS} "
            "so nearest-rank p95 is not identical to a single OS/MEP spike (historical "
            "IFC4 n=5 max≈568ms)."
        ),
        "pack_results": pack_results,
    }
    if group_by == "schema":
        payload["grouped"] = group_benchmark_results_by_schema(pack_results)
    return payload


def group_benchmark_results_by_schema(pack_results: list[dict[str, object]]) -> dict[str, object]:
    buckets: dict[str, list[dict[str, object]]] = defaultdict(list)
    for result in pack_results:
        schema = str(result.get("ifc_schema") or "UNKNOWN")
        buckets[schema].append(result)

    by_schema: dict[str, object] = {}
    for schema, rows in sorted(buckets.items()):
        elapsed_values: list[float] = []
        issue_counts: list[int] = []
        requirement_counts: list[int] = []
        for row in rows:
            measured = row.get("measured_runs")
            if not isinstance(measured, list):
                continue
            for run in measured:
                if not isinstance(run, dict):
                    continue
                if "elapsed_ms" in run:
                    elapsed_values.append(float(run["elapsed_ms"]))
                if "issue_count" in run:
                    issue_counts.append(int(run["issue_count"]))
                if "requirement_count" in run:
                    requirement_counts.append(int(run["requirement_count"]))
        timing = (
            summarize_benchmark_runs(
                [
                    {
                        "iteration": index,
                        "request_id": f"agg-{index}",
                        "elapsed_ms": value,
                        "report_id": "",
                        "issue_count": 0,
                        "requirement_count": 0,
                        "project_name": None,
                        "discipline": None,
                    }
                    for index, value in enumerate(elapsed_values, start=1)
                ]
            )
            if elapsed_values
            else {}
        )
        by_schema[schema] = {
            "pack_count": len(rows),
            "pack_paths": [str(row.get("pack_path")) for row in rows],
            "ifc_sha256": [row.get("ifc_sha256") for row in rows],
            "ifc_bytes": [row.get("ifc_bytes") for row in rows],
            "ifc_entity_count": [row.get("ifc_entity_count") for row in rows],
            "peak_traced_memory_bytes": [row.get("peak_traced_memory_bytes") for row in rows],
            "dependencies": [row.get("dependencies") for row in rows],
            "timing_ms": timing,
            "issue_count": {
                "min": min(issue_counts) if issue_counts else None,
                "max": max(issue_counts) if issue_counts else None,
                "last": issue_counts[-1] if issue_counts else None,
            },
            "requirement_count": {
                "min": min(requirement_counts) if requirement_counts else None,
                "max": max(requirement_counts) if requirement_counts else None,
                "last": requirement_counts[-1] if requirement_counts else None,
            },
            "packs": [_pack_row_summary(row) for row in rows],
        }
    return {
        "group_by": "schema",
        "by_schema": by_schema,
    }


def _pack_row_summary(row: dict[str, object]) -> dict[str, object]:
    measured = row.get("measured_runs")
    last: dict[str, object] = {}
    if isinstance(measured, list) and measured and isinstance(measured[-1], dict):
        last = cast(dict[str, object], measured[-1])
    return {
        "pack_id": row.get("pack_id"),
        "pack_path": row.get("pack_path"),
        "ifc_sha256": row.get("ifc_sha256"),
        "summary": row.get("summary"),
        "issue_count": last.get("issue_count"),
        "requirement_count": last.get("requirement_count"),
    }


def write_ifc_release_evidence(
    suite_payload: dict[str, object],
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(suite_payload, ensure_ascii=False, indent=2)
    tmp = json_path.with_suffix(".tmp")
    tmp.write_text(serialized, encoding="utf-8")
    tmp.replace(json_path)

    grouped = suite_payload.get("grouped")
    by_schema: dict[str, object] = {}
    if isinstance(grouped, dict):
        raw = grouped.get("by_schema")
        if isinstance(raw, dict):
            by_schema = raw

    iterations = suite_payload.get("iterations")
    warmup = suite_payload.get("warmup_iterations")
    lines = [
        "# IFC release benchmark (2026-08)",
        "",
        "**claim_level:** `fixture_only` / fixture-scoped",
        "**customer_accuracy_not_established:** `true`",
        "**accuracy_measured:** `false` "
        "(no adjudicated GT for these packs; issue_count is not accuracy)",
        "",
        "Fixture-only schema suite over IFC2X3 / IFC4 / IFC4X3 wall Pset packs. "
        "Not a product accuracy claim. Real customer packages: **not run**.",
        "",
        f"Stability: shared DI container + suite prime; "
        f"measured iterations={iterations}, warmup={warmup}. "
        "With n<20 nearest-rank p95 can equal max (historical IFC4 spike).",
        "",
        "| Schema | Packs | bytes | entities | p50 ms | p95 ms | max ms | spike max/p50 | issues | reqs |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for schema, metrics in sorted(by_schema.items()):
        if not isinstance(metrics, dict):
            continue
        timing_raw = metrics.get("timing_ms")
        timing: dict[str, object] = (
            cast(dict[str, object], timing_raw) if isinstance(timing_raw, dict) else {}
        )
        issues_raw = metrics.get("issue_count")
        issues: dict[str, object] = (
            cast(dict[str, object], issues_raw) if isinstance(issues_raw, dict) else {}
        )
        reqs_raw = metrics.get("requirement_count")
        reqs: dict[str, object] = (
            cast(dict[str, object], reqs_raw) if isinstance(reqs_raw, dict) else {}
        )
        bytes_list = metrics.get("ifc_bytes") if isinstance(metrics.get("ifc_bytes"), list) else []
        entities_list = (
            metrics.get("ifc_entity_count")
            if isinstance(metrics.get("ifc_entity_count"), list)
            else []
        )
        bytes_v = bytes_list[0] if bytes_list else "—"
        entities_v = entities_list[0] if entities_list else "—"
        row = (
            f"| {schema} | {metrics.get('pack_count')} | {bytes_v} | {entities_v} | "
            f"{timing.get('p50_ms')} | {timing.get('p95_ms')} | "
            f"{timing.get('max_ms')} | {timing.get('spike_ratio_max_over_p50')} | "
            f"{issues.get('last')} | {reqs.get('last')} |"
        )
        lines.append(row)
    stability = suite_payload.get("stability_policy")
    if stability:
        lines.extend(["", f"Policy: {stability}"])
    lines.extend(
        [
            "",
            f"Generated at: `{suite_payload.get('generated_at')}`",
            f"JSON evidence: `{json_path.as_posix()}`",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a fixture-backed benchmark rail for analyze/project-package"
    )
    parser.add_argument("--pack", type=Path, default=None, help="Path to a benchmark pack manifest")
    parser.add_argument(
        "--packs",
        type=Path,
        action="append",
        default=None,
        help="Repeatable pack paths (schema suite or custom set)",
    )
    parser.add_argument(
        "--schema-suite",
        action="store_true",
        help="Run IFC2X3/IFC4/IFC4X3 schema packs from samples/benchmarks",
    )
    parser.add_argument(
        "--group-by",
        choices=("schema",),
        default=None,
        help="Aggregate multi-pack results (schema)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help=(
            "Measured iterations "
            f"(default: {SCHEMA_SUITE_DEFAULT_ITERATIONS} for --schema-suite, else 3)"
        ),
    )
    parser.add_argument(
        "--warmup-iterations",
        type=int,
        default=None,
        help=(
            "Unmeasured warmup iterations "
            f"(default: {SCHEMA_SUITE_DEFAULT_WARMUP_ITERATIONS} for --schema-suite, else 1)"
        ),
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
    parser.add_argument(
        "--write-evidence",
        action="store_true",
        help="Write docs/evidence + audit/evidence IFC release benchmark artifacts",
    )
    args = parser.parse_args()

    pack_paths: list[Path] = []
    if args.schema_suite:
        pack_paths.extend(schema_suite_pack_paths())
    if args.packs:
        pack_paths.extend(path.resolve() for path in args.packs)
    if args.pack is not None:
        pack_paths.append(args.pack.resolve())
    if not pack_paths:
        pack_paths = [default_pack_path()]

    multi = len(pack_paths) > 1 or args.schema_suite or args.group_by == "schema"
    if args.schema_suite:
        iterations = (
            SCHEMA_SUITE_DEFAULT_ITERATIONS if args.iterations is None else args.iterations
        )
        warmup_iterations = (
            SCHEMA_SUITE_DEFAULT_WARMUP_ITERATIONS
            if args.warmup_iterations is None
            else args.warmup_iterations
        )
    else:
        iterations = 3 if args.iterations is None else args.iterations
        warmup_iterations = 1 if args.warmup_iterations is None else args.warmup_iterations

    if multi:
        payload = benchmark_schema_suite(
            pack_paths=pack_paths,
            iterations=iterations,
            warmup_iterations=warmup_iterations,
            storage_dir=args.storage_dir,
            group_by=args.group_by or ("schema" if args.schema_suite else None),
        )
        if args.write_evidence:
            root = repo_root()
            write_ifc_release_evidence(
                payload,
                json_path=root / "audit" / "evidence" / "ifc-release-benchmark-2026-08.json",
                markdown_path=root / "docs" / "evidence" / "ifc-release-benchmark-2026-08.md",
            )
    else:
        payload = benchmark_project_package(
            pack_path=pack_paths[0],
            iterations=iterations,
            warmup_iterations=warmup_iterations,
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
