# AeroBIM FT Scaffold (AER-201)

This directory provides a deterministic FT scaffold gate package for Sunrise P2.

## Purpose

The scaffold certifies train/eval/serve smoke entrypoints and machine-readable outputs.
It does not claim production FT quality for spec extraction.

## Reproducibility Commands

1. `python llm/train/smoke_train.py`
2. `python llm/eval/smoke_eval.py`
3. `python llm/serve/smoke_serve.py`
4. `python -m aerobim.tools.export_ft_scaffold_gate`

## Expected Artifacts

- `llm/artifacts/train/smoke_train_report_v1.json`
- `llm/artifacts/eval/smoke_eval_report_v1.json`
- `llm/artifacts/serve/smoke_serve_report_v1.json`
- `../reports/aerobim_ft_scaffold_gate_report_v1.json`

## Non-Claim Discipline

- No claim of production model readiness.
- No claim of benchmark superiority.
- Gate proves readiness prerequisites only.
