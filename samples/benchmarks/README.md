# Benchmark Packs

Store manifest-backed benchmark packs here for repeatable throughput and latency rails.

Each pack should reference representative fixtures under `samples/` and stay license-safe.

Current packs:

- `project-package-baseline.json` — multimodal baseline pack with IFC, IDS, narrative, calculation, and drawing inputs.
- `project-package-fire-compliance.json` — smaller fire-compliance profile for a second throughput comparison point.
- `project-package-stress-multisource.json` — stress-oriented profile with expanded requirement set plus dual drawing sources.

Threshold profile:

- `benchmark-thresholds.json` — initial advisory performance budget profile used by CI summary and threshold evaluation rails.

Run the current baseline rail from `backend/`:

```bash
python -m aerobim.tools.benchmark_project_package
```

Run the alternate pack explicitly:

```bash
python -m aerobim.tools.benchmark_project_package --pack ../samples/benchmarks/project-package-fire-compliance.json
```

Run the stress multisource pack:

```bash
python -m aerobim.tools.benchmark_project_package --pack ../samples/benchmarks/project-package-stress-multisource.json
```

Evaluate collected benchmark artifacts against advisory thresholds:

```bash
python -m aerobim.tools.benchmark_threshold_gate \
	--artifact-dir ../artifacts/ci-benchmark-smoke \
	--threshold-profile ../samples/benchmarks/benchmark-thresholds.json \
	--mode advisory
```