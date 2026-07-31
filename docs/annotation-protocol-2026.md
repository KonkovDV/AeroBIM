# Annotation protocol (2026) — Level A/B/C

## Level A — engine regression

Known IFC+IDS → expected pass/fail. Deterministic CI.

## Level B — injected defects

Catalog: `samples/benchmarks/injected-defects-level-b.json` + Sprint 2.1 mutation SSOT.  
Each defect: `defect_id`, mutation_type, expected finding/severity/status.

## Level C — human expert corpus (customer)

Before labeling freeze:

- finding unit, duplicate rule, FP/FN definitions, uncertain, severity, evidence link, not-verifiable, out-of-scope
- ≥2 independent blind annotators + adjudication
- metrics: precision/recall/F1, per-discipline/severity/rule, Wilson CI, IAA (κ/α) with **task-justified** threshold (not magic 0.8)
- stratify AR/KR/MEP/PDF/scan/size/severity

**Status:** Level C = BLOCKED until customer corpus + protocol sign-off (RT-001).
