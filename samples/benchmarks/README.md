# Benchmark Packs

Store manifest-backed benchmark packs here for repeatable throughput and latency rails.

Each pack should reference representative fixtures under `samples/` and stay license-safe.

Run the current baseline rail from `backend/`:

```bash
python -m aerobim.tools.benchmark_project_package
```