# ADR-006: Evaluation Harness and Benchmark Framework

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** AeroBIM Principal Engineering  
**Related:** ADR-001 (verdict ownership), ADR-007 (regulation model, not on the analyze path)

---

## Context

AeroBIM had a basic `evaluate_extraction` utility but lacked a formal
benchmark framework with:
- Immutable test manifests (leakage protection)
- Explicit corpus type separation (PUBLIC / SYNTHETIC / CUSTOMER)
- Per-rule FN/FP/precision/recall
- False Negative Rate as a first-class metric
- Double annotation with inter-annotator agreement
- Reproducible benchmark runs tied to norm pack and engine versions

For a compliance-checking product, hidden False Negatives are a primary
safety risk. Aggregate accuracy metrics are insufficient: a system that
silently misses 30% of violations is worse than one that abstains.

`macro_f1=0.86` from the runtime baseline is measured on **SYNTHETIC**
fixtures. It cannot be presented as a production claim without explicit
corpus-type labelling.

---

## Decision

### 1. Formal benchmark manifest with leakage protection

`BenchmarkDatasetManifest` is a sealed artefact:
- Each case has a `case_hash = sha256(input_hash + gold_label + rule_id + corpus_type)`
- The manifest has a `manifest_hash = sha256(all case_hashes)`
- Any change to a case invalidates the manifest hash
- A change requires creating a **new version** (`change_reason` is required)
- Development fixtures (`test/fixtures/`) are **never** used as evaluation cases

This prevents the most common benchmark leakage pattern:
```
fixture used for development
→ same fixture used for published evaluation
→ inflated metrics
```

### 2. Corpus type separation: PUBLIC / SYNTHETIC / CUSTOMER

Metrics are **always** reported separately per `CorpusType`:
```
PUBLIC    — external public BIM/ACC datasets (AEC-Bench, IFC-Bench V2, GNI BIM Dataset)
SYNTHETIC — AeroBIM-generated cases
CUSTOMER  — real customer data (not in Git; secure storage)
```

**Never merge these into a single number without explicit breakdown.**

Specifically:
- `macro_f1=0.86 (SYNTHETIC)` is not the same as `macro_f1=0.86 (CUSTOMER)`
- `customer_go=true` requires CUSTOMER corpus evaluation and external sign-off
- CUSTOMER files are never committed to Git; use secure storage + immutable hashes

### 3. False Negative Rate as a first-class metric

Every `RuleMetrics` object computes and exposes:
```python
@property
def false_negative_rate(self) -> Optional[float]:
    """FNR = FN / (FN + TP). Never hidden in aggregate."""
    denom = self.fn + self.tp
    return self.fn / denom if denom else None
```

`macro_fn_rate` (mean FNR across rules) is in every `BenchmarkRunResult`.

For a compliance product:
- FN = missed violation = safety risk
- FNR must be reported even when F1 looks good
- Abstention (`NOT_VERIFIED`) is counted separately; it is not a TP

### 4. Double annotation protocol (P1-H)

See `backend/src/aerobim/domain/annotation_protocol.py`.

Gold labels come from:
1. Agreement between two independent annotators, or
2. Adjudication by a third expert where they disagree

Raw labels are never deleted. Disagreement categories are tracked.
Cohen's kappa is computed and reported.

Annotation protocol is SSOT in `docs/evaluation/annotation-protocol.md`
(to be created in P1-H completion task).

### 5. Benchmark run is tied to provenance hashes

Every `BenchmarkRunResult` stores:
```
manifest_id + manifest_version
engine_version
norm_pack_hash
run_at
```

This means a benchmark run is reproducible:
same engine_version + norm_pack_hash + manifest_version → same result
(subject to deterministic checker; AI outputs excluded from gold evaluation).

### 6. Per-rule metrics, not just aggregate

`per_rule: list[RuleMetrics]` is required on every run.
Aggregate (macro/micro) is derived; per-rule is primary.

This matters because:
- A rule with high FNR might be masked by rules with low FNR in aggregate
- Each rule has a different evidence requirement; per-rule analysis is essential

---

## Consequences

### Positive
- Benchmark leakage is detectable and prevented structurally
- FN is always visible; it cannot be hidden in aggregate F1
- Corpus types are never mixed without explicit labels
- Benchmark runs are reproducible by version hashes
- `customer_go` remains `false` until CUSTOMER corpus is evaluated

### Negative / mitigations
- Building a real PUBLIC corpus requires licensing review for each dataset
  Mitigation: start with SYNTHETIC; add PUBLIC after license verification
- Double annotation requires annotator time
  Mitigation: prioritise rules with highest user-impact first

### Neutral
- Does not change IFC parsing or rule evaluation
- Does not add new runtime dependencies
- Benchmark manifests are JSON files; no new storage system needed

---

## Current Evaluation Status (as of 2026-09-22)

| Metric | Value | Corpus | Notes |
|---|---|---|---|
| macro_f1 | 0.86 | SYNTHETIC | From runtime-baseline-latest.json, fixture only |
| macro_f1 | NOT_VERIFIED | PUBLIC | No public dataset evaluation run yet |
| macro_f1 | NOT_VERIFIED | CUSTOMER | customer_go=false; no customer corpus |
| FNR | NOT_VERIFIED | Any | Requires new benchmark run with new harness |
| kappa | NOT_VERIFIED | Any | Double annotation not yet completed |

`customer_go=false` remains the honest state.

---

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Use existing `evaluate_extraction` as-is | No manifest integrity; no FN visibility; no corpus split |
| MLflow / W&B for tracking | External dependency; over-engineered for current scale |
| Single aggregate F1 as primary metric | Hides FNR; unacceptable for compliance product |
| Mix PUBLIC+SYNTHETIC in one run | Creates misleading metrics; explicitly prohibited |

---

## References

- `backend/src/aerobim/tools/evaluate_benchmark.py`
- `backend/src/aerobim/domain/annotation_protocol.py`
- `backend/tests/test_p0_p1_upgrade.py::TestEvaluationBenchmark`
- `audit/evidence/runtime-baseline-latest.json`
- ADR-001: Verdict ownership (EvidenceAssembler; LLM does not write summary.passed)
- ADR-005: Regulatory Information Model
