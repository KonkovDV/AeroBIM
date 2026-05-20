---
title: "Academic Publication Evidence 2026"
status: active
---

# Academic Publication Evidence (2026)

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

## CI release

Tag `v*` triggers [`.github/workflows/academic-benchmark-release.yml`](../.github/workflows/academic-benchmark-release.yml) (benchmark JSON, extraction quality, rendered MD).

## Claim boundary

Deterministic multimodal QA kernel with provenance — not full-code compliance or VLM sign-off.

## Prior pilot bundle

See [`academic-pilot-evidence-2026.md`](academic-pilot-evidence-2026.md) for pre-publication pilot closure (F1 ≈ 0.83, APPROVED runtime).
