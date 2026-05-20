---
title: "AeroBIM Benchmark Report Template"
status: active
version: "1.0.0"
---

# AeroBIM Benchmark Report — {{DATE}}

## 1. Hypothesis

Deterministic multimodal validation (IFC + IDS + structured + narrative + cross-doc) yields auditable sign-off evidence with lower regression risk than opaque model-only QA for regulated AEC deliverables.

## 2. Methods

- Pipeline: IFC validation → IDS → requirement extraction → cross-document contradiction detection → BCF export.
- Conflict taxonomy: `unit-mismatch`, `hard-conflict`, `ambiguous-mapping`.
- Quantity comparison: UCUM-aligned `si_compare` with ε-tolerance.

## 3. Fixtures

| Fixture set | Documents | Annotated requirements | Disciplines |
|---|---:|---:|---|
| RU narrative corpus | 10 | 50 | architecture, structure, fire-safety, mep |

## 4. Results

### 4.1 Extraction quality

| Metric | Value |
|---|---:|
| Macro F1 | {{MACRO_F1}} |
| Macro precision | {{MACRO_PRECISION}} |
| Macro recall | {{MACRO_RECALL}} |

### 4.2 Per-discipline F1

{{PER_DISCIPLINE_TABLE}}

### 4.3 Multimodal ablation

| Configuration | Components | Issues | Cross-doc |
|---|---|---:|---:|
| A0 | IFC + IDS | {{A0_ISSUES}} | {{A0_CROSS_DOC}} |
| A1 | A0 + structured | {{A1_ISSUES}} | {{A1_CROSS_DOC}} |
| A2 | A1 + narrative | {{A2_ISSUES}} | {{A2_CROSS_DOC}} |
| A3 | A2 + calc + drawings | {{A3_ISSUES}} | {{A3_CROSS_DOC}} |

### 4.4 Latency

{{LATENCY_TABLE}}

## 5. Pilot case study (Section 5 placeholder)

See [`pilot-case-study-report-2026.md`](pilot-case-study-report-2026.md).

## 6. Threats to validity

- Fixture size and regex maintenance cost.
- No stochastic vision-model sign-off in production path.
- Single-site pilot KPI (N=1) — illustrative only.

## 7. Reproducibility

```bash
cd AeroBIM/backend
python -m pytest tests -q
python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
python -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence
```
