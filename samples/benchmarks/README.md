# Benchmark Packs

Manifest-backed packs for repeatable latency rails, ablation studies, and publication artifacts.

Each pack references fixtures under `samples/` and stays license-safe.

## Project-package packs

| Pack | Role |
|---|---|
| `project-package-baseline.json` | Multimodal baseline (IFC, IDS, narrative, calculation, drawing) |
| `project-package-fire-compliance.json` | Fire-compliance profile |
| `project-package-stress-multisource.json` | Stress profile with expanded inputs |
| `project-package-pilot-moscow-v1.json` | Pilot Moscow bundle |
| `project-package-ablation-a0.json` | Ablation A0: IFC + IDS only |
| `project-package-ablation-a1.json` | Ablation A1: + structured requirements |
| `project-package-ablation-a2.json` | Ablation A2: + narrative specification |
| `project-package-ablation-a3.json` | Ablation A3: full multimodal pack |

## Extraction quality

| Artifact | Role |
|---|---|
| `russian-aec-ground-truth.json` | 10 RU documents, 50 annotated requirements |
| `benchmark-extraction-quality.json` | CI metadata for extraction gate |
| `bsdd-pilot-terms.json` | Offline bSDD term map (pilot properties) |
| `loin-rule-metadata.json` | LOIN purpose/milestone/actor per rule prefix |

Threshold profile: `benchmark-thresholds.json` (advisory and enforced modes).

## Commands (from `backend/`)

```bash
python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0
python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
python -m aerobim.tools.run_ablation_study
python -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence
```

Threshold evaluation on CI artifacts:

```bash
python -m aerobim.tools.benchmark_threshold_gate \
  --artifact-dir ../artifacts/ci-benchmark-smoke \
  --threshold-profile ../samples/benchmarks/benchmark-thresholds.json \
  --mode advisory
```
