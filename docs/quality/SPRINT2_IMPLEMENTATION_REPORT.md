<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# Sprint 2 — Implementation Report

**Date:** 2026-08-06  
**Base HEAD:** `d96a59a`  
**Checkpoint:** **NO_GO**  
**claim_level:** `synthetic_only` / `fixture_only`  
**customer_precision_claim_publishable:** `false`

## Findings

- Stage 0 gap analysis was accurate: extend `run_sprint2_synthetic_baseline`, do not add a fourth baseline runner.
- Mode B dataset track unified three classes from existing GT / Level-B / drawing-advisory fixtures (15 cases).
- Mode A inventory references open-source search doc only — **no downloads**.
- Baseline now emits canonical `docs/evidence/sprint2-baseline-report.{json,md,pdf,html}` plus dated synthetic aliases.
- Agreement κ/α and nDCG explicitly **N/A** (no dual-human / ranking labels).
- `clashes_count=0` with honesty note (geometric clash not planted runnable).
- Advisory comparative mock schema extended; OFF==ON verdict tests still green.

## Gaps closed vs Stage 0

| Gap | Status |
|---|---|
| Sprint 2 dataset manifest + regen command | CLOSED |
| Canonical sprint2-baseline-report.* (19 sections) | CLOSED |
| Samolet TZ Sprint-2 matrix statuses | CLOSED |
| `docs/customer/*` templates | CLOSED |
| `docs/ai/*` + mock bench schema | CLOSED |
| Focused determinism / claim / PDF tests | CLOSED |
| Customer precision publishable | Still **BLOCKED_BY_CUSTOMER_DATA** |

## Files created / changed

### Created
- `backend/src/aerobim/tools/export_sprint2_dataset_manifest.py`
- `backend/tests/test_sprint2_dataset_manifest.py`
- `samples/benchmarks/sprint2-dataset/MANIFEST.json`
- `samples/benchmarks/sprint2-dataset/MODE_A_INVENTORY.json`
- `docs/quality/SPRINT2_SAMOLET_TZ_BASELINE_MATRIX.md`
- `docs/customer/DEMO_PROTOCOL_COMPLETED_PROJECT.md`
- `docs/customer/CUSTOMER_DISCOVERY_SCRIPT.md`
- `docs/customer/CUSTOMER_PILOT_ONE_PAGER.md`
- `docs/customer/CUSTOMER_INTERVIEW_FORM.md`
- `docs/customer/CUSTOMER_OUTREACH_TRACKER_TEMPLATE.csv`
- `docs/ai/LLM_ADVISORY_CONTOUR.md`
- `docs/ai/LLM_COMPARATIVE_BENCHMARK.md`
- `docs/ai/LLM_DATA_PRIVACY.md`
- `docs/evidence/sprint2-baseline-report.json`
- `docs/evidence/sprint2-baseline-report.md`
- `docs/evidence/sprint2-baseline-report.pdf`
- `docs/evidence/sprint2-baseline-report.html`
- `docs/evidence/sprint2-synthetic-baseline-2026-08-06.{json,md,pdf}`
- `docs/quality/SPRINT2_IMPLEMENTATION_REPORT.md` (this file)

### Changed
- `backend/src/aerobim/tools/run_sprint2_synthetic_baseline.py` (extend; `--dataset-manifest`; richer metrics; canonical reports)
- `backend/src/aerobim/tools/benchmark_llm_advisory.py` (latency/cost/json/agreement/placeholders/repro)
- `samples/DATASET_MANIFEST.json` (add sprint2-dataset entries only; preserve vendored `cc_by_nd_4.0`)

## Commands

```text
cd backend
.venv\Scripts\python.exe -m aerobim.tools.export_sprint2_dataset_manifest
.venv\Scripts\python.exe -m aerobim.tools.run_sprint2_synthetic_baseline --iterations 1 --dataset-manifest ../samples/benchmarks/sprint2-dataset/MANIFEST.json
.venv\Scripts\python.exe -m pytest tests/test_sprint2_dataset_manifest.py tests/test_sprint2_synthetic_gt.py tests/test_advisory_vlm_off_equals_on.py -q --tb=line
.venv\Scripts\python.exe -m ruff check src tests
.venv\Scripts\python.exe -m ruff format --check src tests
.venv\Scripts\python.exe -m mypy src/aerobim --ignore-missing-imports
```

## Baseline results (synthetic_only)

| Metric | Value |
|---|---|
| TP / FP / FN | 6 / 2 / 0 |
| precision / recall | 0.75 / 1.0 |
| remarks_count | 6 |
| clashes_count | 0 (honesty) |
| agreement / nDCG | N/A |
| dataset cases | 15 |
| dataset reproducibility_hash | `59f903a936a66625b50ea914241a808f63ea8a4243d20272926fbbe3cd56310f` |
| commit_sha | `d96a59ac6704357336ae46f7d61f6435be4c6a2c` |

## Allowed vs forbidden claims

**Allowed:** synthetic_only / fixture_only engineering measurements; NO_GO checkpoint; fixture P/R on planted set with Wilson; remarks vs clashes honesty; N/A agreement.

**Forbidden:** product accuracy, >90%, production-ready, native DWG, delivered MEP clash, calc independence, CDE-ready BCF, customer SLA from fixtures, invented customer orgs/results.

## Customer-blocked

- Dual expert adjudication (RT-001)
- Licensed customer corpus / intake gates
- Customer SLA proof
- Severity taxonomy customer approval

## Architecture note (Stage 7)

No GraphRAG. Contour remains ingestion → deterministic Shared-gate → advisory → evidence/HITL → honesty. See `docs/ai/LLM_ADVISORY_CONTOUR.md`.

## Next sprint

1. Plant runnable geometric clash IFC pair (still synthetic until customer).  
2. Dual-human adjudication CSV path for RT-001.  
3. License-cleared Mode A local clone under review (not KAAN).  
4. Keep advisory mock CI; live bake-off opt-in only.
