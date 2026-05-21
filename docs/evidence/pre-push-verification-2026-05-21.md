---
title: "Pre-Push Verification 2026-05-21"
status: active
environment: "Windows, Python 3.13, backend/.venv-pilot"
frozen_tag: pilot-2026-pre
frozen_commit: 1a5c03e
rolling_main_before_commit: efcf6e5
---

# Pre-Push Verification (2026-05-21)

Academic release lane executed locally before `docs(academic): REPRODUCIBILITY SSOT` commit.

## Summary

| Check | Result |
|---|---|
| `pytest tests -q` | **292 passed**, 2 skipped |
| `ruff check src tests` | pass |
| `ruff format --check src tests` | pass (99 files) |
| `mypy src/aerobim --ignore-missing-imports` | pass (62 files) |
| `evaluate_extraction --min-macro-f1 0.70` | pass, macro F1 ≈ **0.86** |
| `export_runtime_baseline` | `verification.status` = **APPROVED** |
| `generate_benchmark_report` | [`benchmark-report-2026-05-21.md`](benchmark-report-2026-05-21.md) |
| `run_ablation_study` | [`ablation-study-report.json`](ablation-study-report.json) updated |

## Commands (PowerShell)

```powershell
cd AeroBIM\backend
.\.venv-pilot\Scripts\python.exe -m pytest tests -q
.\.venv-pilot\Scripts\python.exe -m ruff check src tests
.\.venv-pilot\Scripts\python.exe -m ruff format --check src tests
.\.venv-pilot\Scripts\python.exe -m mypy src/aerobim --ignore-missing-imports
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.export_runtime_baseline
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.run_ablation_study --output ../docs/evidence/ablation-study-report.json
```

## Ablation snapshot (A0–A3)

| Mode | Issues | Cross-doc |
|---|---:|---:|
| A0 | 2 | 0 |
| A1 | 8 | 0 |
| A2 | 17 | 3 |
| A3 | 8 | 0 |

## Tag policy

Do **not** move tag `pilot-2026-pre` (frozen at `1a5c03e`). This verification run applies to rolling `main` documentation ahead of the tag.
