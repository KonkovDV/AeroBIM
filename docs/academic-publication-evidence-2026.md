---
title: "Academic Publication Evidence 2026"
status: active
---

# Academic Publication Evidence (2026)

Reproducibility SSOT: [`REPRODUCIBILITY-2026.md`](REPRODUCIBILITY-2026.md). Latest pre-push lane: [`evidence/pre-push-verification-2026-05-21.md`](evidence/pre-push-verification-2026-05-21.md).

## Evidence rail

| Artifact | Command / path |
|---|---|
| Unit tests | `cd AeroBIM/backend && python -m pytest tests -q` |
| Extraction gate | `python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` |
| Runtime baseline | `python -m aerobim.tools.export_runtime_baseline` |
| Publication bundle | `python -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence` |
| Ablation study | `python -m aerobim.tools.run_ablation_study` |
| Conflict breakdown (pilot) | `python -m aerobim.tools.summarize_conflict_breakdown` |

## Corpus

- Annotation protocol: [`annotation-protocol-2026.md`](annotation-protocol-2026.md)
- Ground truth: [`../samples/benchmarks/russian-aec-ground-truth.json`](../samples/benchmarks/russian-aec-ground-truth.json) (10 fixtures, 50 requirements)
- Ablation packs: `project-package-ablation-a0.json` … `a3.json`

## Manuscript

- Draft: [`manuscript-draft-2026.md`](manuscript-draft-2026.md)
- Case study: [`pilot-case-study-report-2026.md`](pilot-case-study-report-2026.md)
- Template: [`benchmark-report-template.md`](benchmark-report-template.md)
- Citation: [`CITATION.bib`](CITATION.bib)

## Frozen pre-pilot tag

Tag **`pilot-2026-pre`** — evidence under [`evidence/`](evidence/) (`pre-pilot-*-2026-05-21.*`, `pre-pilot-gates-evidence-2026-05-21.md`). Macro F1 ≈ **0.86** on RU corpus.

## CI release

Tag `v*` triggers [`.github/workflows/academic-benchmark-release.yml`](../.github/workflows/academic-benchmark-release.yml) (benchmark JSON, extraction quality, rendered MD).

## Claim boundary

Deterministic multimodal QA kernel with provenance — not full-code compliance or non-deterministic drawing sign-off.

## Prior pilot bundle

See [`academic-pilot-evidence-2026.md`](academic-pilot-evidence-2026.md) and [`evidence/pre-pilot-gates-evidence-2026-05-21.md`](evidence/pre-pilot-gates-evidence-2026-05-21.md) (F1 ≈ 0.86, APPROVED runtime).
