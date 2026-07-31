# Sprint 2.1 engineering baseline report

**Title:** Sprint 2.1 engineering baseline on declared public/synthetic package  
**Date:** 2026-07-31  
**Meeting:** `DATE_TO_BE_CONFIRMED`

> **Warning:** Данный отчёт является инженерным baseline на public/synthetic данных.  
> Он не подтверждает точность продукта на корпусе заказчика, не закрывает RT-001,  
> не подтверждает customer SLA ≤30 минут и не заменяет экспертную оценку.

## Commit / tree

| Field | Value |
|---|---|
| commit (at run) | `64c69b4f9cdd99779e9aac91ec87078367190339` |
| tree (start inventory) | `c8b51c78cac3a68af0ccc1308b78c6f8b3326ef6` |
| package_id | `sprint-2-1-baseline-v1` |
| claim_level | `engineering_baseline_only` |
| customer_evidence | `false` |
| pdf_generation | `PDF_GENERATION_BLOCKED` |

## Environment

- Python 3.13.7 (local reproduction)
- Platform recorded in `artifacts/sprint-2-1/baseline.json`

## Dataset

- Manifest: `samples/benchmarks/sprint-2-1/manifest.json`
- Licenses: `samples/benchmarks/sprint-2-1/LICENSES.md`, `audit/dataset_license_manifest.json`
- Provenance: `samples/benchmarks/sprint-2-1/source-provenance.json`
- Mutations SSOT: `samples/benchmarks/sprint-2-1/mutations/mutation-manifest.json`
- 6 fixture files, 3055 bytes total (IFC/IDS/txt)

Open third-party corpora remain `INTERNAL_ONLY_LICENSE_REVIEW` (not vendored).

## What counts as an error / clash / severity

- Error: expected mutation finding kind in SSOT / Level B linkage
- Clash: geometric hard clash when ifcclash pack present (not measured in lightweight CLI this run)
- Severity: CRITICAL / WARNING / INFO per mutation expected_severity; customer mapping separate (`PROPOSED_NOT_CUSTOMER_APPROVED`)

## TP/FP/FN methodology

Full TP/FP/FN requires: apply mutation to temp copy → Analyze → match expected findings.  
Sprint 2.1 lightweight CLI **honestly reports** `tp/fp/fn = null` and declares ground-truth inventory:

- declared_finding_cases: 3
- declared_not_verifiable_cases: 1

## Baseline results (REPRODUCED)

| Metric | Value |
|---|---|
| time_total_mean_s (3 iter, 1 warmup) | ~0.0021 |
| clashes_expected | 0 |
| clashes_detected | null |
| precision/recall/F1 | null (not claimed) |
| summary.outcome / passed | null (analyze skipped) |
| failed_capabilities | [] |

## Samolet TZ traceability

| Требование ТЗ | Что измеряем | Baseline result | Evidence | Status |
|---|---|---|---|---|
| Коллизии | precision/recall/F1 | not measured | — | fixture/synthetic pending clash pack |
| Расчётные ошибки | evidence matching | partial inventory | Level B | partial |
| Несоответствия | precision/recall/F1 | declared mutations only | mutation-manifest | fixture/synthetic |
| RU/EN замечания | template / LLM advisory mock | mock rows | llm-comparison.json | fixture |
| Стабильность | repeated hash | hash lock OK | baseline.json files | reproduced |
| Масштабирование | size/time curve | pack 3 KB only | baseline.json | engineering |
| ≤30 минут | scoped SLA | not customer | fixture honesty | not customer |
| Снижение нагрузки | user study | not measured | — | blocked |

## Capability / LLM

- `llm_advisory` on `GET /v1/system/capabilities`: status `disabled`, advisory_only, customer deny
- Mock comparison Kimi/Qwen/Gemma: `artifacts/sprint-2-1/llm-comparison.json` (45 rows)
- Cloud provider policies: `CLOUD_DATA_POLICY_UNKNOWN` → synthetic/public only

## Known limitations

- No customer corpus (RT-001 open)
- No full Analyze mutation scoring in this CLI gate
- PDF_GENERATION_BLOCKED
- Outreach not sent

## Reproduction

```bash
cd backend
python -m aerobim.tools.run_sprint_2_1_baseline \
  --pack ../samples/benchmarks/sprint-2-1/baseline-package.json \
  --iterations 3 --warmup-iterations 1 \
  --output ../artifacts/sprint-2-1/baseline.json \
  --report ../artifacts/sprint-2-1/baseline.md
```

## Claims Lock

See `audit/reports/CLAIMS_LOCK_2026_07_17.md` and `audit/sprint-2-1-claims-boundary.md`.

## Next actions

1. License-clear and optionally vendor 1–2 public IFC packs
2. Wire mutation-apply + Analyze for real TP/FP/FN
3. User-approved outreach from lead drafts
4. Keep RT-001/002/003 open until customer evidence
