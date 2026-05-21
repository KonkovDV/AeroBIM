# CI artifacts directory (local / Actions only)

This folder is **gitignored**. Contents are produced by:

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) — `benchmark-smoke`, `samolet-sla-smoke`, `extraction-quality`
- Local runs of `benchmark_project_package` / `measure_package_sla`

Do not commit JSON from this directory — paths and timings are machine-specific and go stale.

Download fresh artifacts from **GitHub Actions → workflow run → Artifacts**, or regenerate:

```powershell
cd backend
pip install -e ".[dev,vision]"
python -m aerobim.tools.benchmark_project_package --pack ../samples/benchmarks/project-package-pilot-moscow-v1.json --iterations 1 --output ../artifacts/ci-benchmark-smoke/local-pilot-moscow.json
```

Evidence cited in papers and audits lives under [`docs/evidence/`](../docs/evidence/).
