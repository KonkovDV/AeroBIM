# Sprint 2 — Gap Analysis (Stage 0)

**Date:** 2026-08-06  
**Audit HEAD:** `d96a59a` (user-cited `7786337` is historical; live tip is post-baseline CI fix)  
**Checkpoint:** **NO_GO** (RT-001 / RT-002 / RT-003 open)  
**Claims Lock:** [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md)  
**Intake gate:** [`audit/evidence/customer-intake-gate.json`](../../audit/evidence/customer-intake-gate.json) — all gates `false`, `claim_level=not_ready`

## Method

Read-only inventory of `backend/src/aerobim/tools`, `samples/`, `docs/{quality,evidence,pilot,customer-demo,customer-discovery,dataset,ai}`, `audit/`, DI advisory contour. Preference: extend existing runners; do **not** invent parallel baselines.

## Tool map (summary)

| Capability | Primary entrypoint | E2E on fixtures? | Notes |
|---|---|---|---|
| Synthetic corpus | `generate_vlm_fixture_corpus`, Level-B defects, `sprint2-synthetic-ground-truth.json` | Yes | Expand classes; keep `synthetic` provenance |
| Degraded scans | `generate_degraded_scans` | Yes (pymupdf) | Fixture-only T4 |
| Analyze project package | `AnalyzeProjectPackageUseCase` + `POST /v1/analyze/project-package` + `benchmark_project_package` | Yes | Customer packs blocked by intake |
| Detection P/R/F1 | `evaluate_detection_precision` | Yes | Never publishable without dual adjudication |
| nDCG | `evaluate_ranking_quality` | Yes | Tie-aware; fixture rankings ≠ customer |
| Agreement κ/α | `measure_adjudicator_agreement` | Yes (template) | Needs real dual-human CSV for RT-001 |
| Pilot harness | `run_pilot_harness` | Yes | Aggregates agreement+precision+optional nDCG |
| Timing / TTFF | `export_evidence_bundle` (`time_to_first_finding_ms`), `measure_package_sla`, sprint2 p95 | Partial | Batch TTFF ≠ streaming; sprint-2.1 TTFF null |
| Evidence bundle | `export_evidence_bundle` + `verify_evidence_bundle` | Yes | |
| PDF/HTML/JSON | evidence bundle HTML; `run_sprint2_synthetic_baseline` JSON/MD/PDF; tracker PDF | Yes | Need canonical `sprint2-baseline-report.*` |
| LLM advisory | `LLM_ADVISORY_PROVIDER`, Kimi/Yandex/OpenAI-compat, `MockLlmProvider` | Mock yes; live partial | Never mutates verdict |
| Runtime / golden | `export_runtime_baseline`, `test_golden_report` | Yes | Eng metrics only |
| One-command Sprint 2 baseline | `run_sprint2_synthetic_baseline` | Yes | Closest SSOT; extend rather than replace |

**Missing directories (required by Sprint 2 brief):** `docs/customer/` (content lives under `docs/customer-demo/` + `docs/customer-discovery/`), `docs/ai/`.

**SSOT artifacts:** `samples/DATASET_MANIFEST.json`, `docs/evidence/runtime-baseline-latest.json`, `audit/reports/TZ_RUNTIME_MATRIX.md`, Claims Lock, customer-intake-gate.

## Duplication / reuse policy

| Area | Duplicate risk | Decision |
|---|---|---|
| Sprint 2 baseline vs Sprint 2.1 vs pilot harness | Three runners | Keep `run_sprint2_synthetic_baseline` as Sprint 2 demo SSOT; wrap pilot harness metrics into its report; do not fork a fourth runner |
| Customer docs | `customer-demo` + `customer-discovery` vs required `docs/customer/` | Create `docs/customer/*` as canonical templates; link/point to existing RU materials — no CRM |
| LLM bake-off | `benchmark_llm_advisory` (mock) + `run_yandex_remarks_bakeoff` (live) | Keep both; add `docs/ai/*` + ensure comparative tool covers Kimi/Qwen/Gemma abstractions |
| Dataset manifests | `DATASET_MANIFEST` vs open-corpora vs sprint2 GT | Add Sprint 2 dataset track manifest that **references** existing corpora; regenerate via one command |

## Gap table

| Требование спринта | Существующий код/артефакт | Статус | Gap | План закрытия | Evidence |
|---|---|---|---|---|---|
| Stage 0 audit before code | this file | **CLOSED** | — | Freeze inventory before edits | `docs/quality/SPRINT2_GAP_ANALYSIS.md` |
| Dataset Mode A: open/customer-like corpus | `docs/dataset/*`, open-corpora profiles, BSI IDS import, IFC-Bench smoke, `samples/customer/` placeholder | **PARTIAL** | No licensed customer pack; external benches need local clones; KAAN not vendored | Inventory + license pin only; no dubious downloads; document Mode A in Sprint 2 dataset manifest | `samples/benchmarks/sprint2-dataset/MODE_A_INVENTORY.json` |
| Dataset Mode B: synthetic 3 classes | Level-B + sprint2 GT + VLM corpus + degraded scans | **CLOSED** (synthetic_only) | Clash/drawing↔model still not planted runnable | Extended GT into Sprint 2 dataset manifest (15 cases, 3 classes) | `samples/benchmarks/sprint2-dataset/MANIFEST.json` |
| Byte determinism / provenance tests | `test_sprint2_dataset_manifest` | **CLOSED** | — | Determinism + synthetic claim tests | `backend/tests/test_sprint2_dataset_manifest.py` |
| One-command baseline: analyze + quality + speed | `run_sprint2_synthetic_baseline` | **CLOSED** (synthetic_only) | Agreement/nDCG N/A without labels; clashes=0 honesty | Extended runner → canonical reports | `docs/evidence/sprint2-baseline-report.*` |
| Metrics honesty (fixture_only / synthetic_only; no product accuracy) | Claims Lock + sprint2 `claim_level=synthetic_only` + detection publishable gate | **CLOSED** (policy) | Must preserve in new report filenames | Keep `customer_precision_claim_publishable=false`; separate extraction F1 vs detection vs agreement | Claims Lock; detection precision tool |
| `docs/evidence/sprint2-baseline-report.md` + `.pdf` | canonical report set | **CLOSED** | — | Generated from JSON/MD via script | `docs/evidence/sprint2-baseline-report.{md,pdf,json,html}` |
| Samolet TZ baseline matrix for Sprint 2 | `SPRINT2_SAMOLET_TZ_BASELINE_MATRIX.md` | **CLOSED** | Never VERIFIED without customer | Sprint-2-scoped statuses | `docs/quality/SPRINT2_SAMOLET_TZ_BASELINE_MATRIX.md` |
| Customer demo protocol | `docs/customer/DEMO_PROTOCOL_COMPLETED_PROJECT.md` | **CLOSED** | Needs customer pack for live demo | Canonical under `docs/customer/` | demo protocol |
| Discovery / one-pager / interview / outreach CSV | `docs/customer/*` | **CLOSED** | Empty tracker only | Templates only; no invented orgs | customer templates |
| LLM advisory-only contour | DI + `docs/ai/*` + mock bench | **CLOSED** (docs+mock); live **PARTIAL** | Live keys optional | Documented; mock comparative; verdict-neutral | `docs/ai/LLM_*.md` |
| Comparative Kimi/Qwen/Gemma bench | `benchmark_llm_advisory` | **CLOSED** (fixture_only mock) | Live bake-off needs API key | Mock comparative schema extended | `benchmark_llm_advisory.py` |
| Architecture: ingestion / deterministic / advisory / evidence / HITL / honesty | ADR-001 hybrid already | **CLOSED** for Sprint 2 scope | Avoid GraphRAG/agent sprawl | Only wire gaps that unblock baseline/demo | architecture docs |
| E2E tests dataset→analyze→evaluate→evidence→PDF | `test_sprint2_dataset_manifest` + synthetic GT | **CLOSED** (focused) | Broader customer E2E blocked | Focused Sprint 2 suite green | pytest |
| Quality gates green | pytest/ruff/mypy/vitest | **CLOSED** at delivery | Must stay green after further edits | 1893 pytest passed locally | gates |
| Final implementation report | `SPRINT2_IMPLEMENTATION_REPORT.md` | **CLOSED** | — | Stage 9 written | implementation report |
| Customer claims publishable | intake gate + RT-001 | **BLOCKED_BY_CUSTOMER_DATA** | Dual expert labels + customer corpus absent | Do not raise status; keep NO_GO | `customer-intake-gate.json`, CRITICAL_BLOCKERS |
| Native DWG / delivered MEP clash / CDE-ready BCF / calc independence / fixture SLA as customer SLA | honesty surfaces + TZ matrix | **NOT_VERIFIED / BLOCKED** | Explicit forbidden claims | Preserve claim boundaries in all new docs/PDF | Claims Lock + capability matrix |

## Already closed vs Sprint 2 brief (honest)

- Pilot harness, κ/α, detection precision, tie-aware nDCG, reproducibility hash, VLM fixture corpus, degraded scan generator, evidence bundle, golden/runtime baselines, Claims Lock, hybrid advisory≠verdict — **exist and run on fixtures**.
- Sprint 2 synthetic baseline JSON/MD/PDF already produced once (`synthetic_only`).
- Open-source search and license honesty docs exist for Mode A.

## Sprint 2 implementation order (post–Stage 0)

1. **Dataset track** — Sprint 2 dataset manifest + regen command + tests (extend GT / generators).  
2. **Baseline orchestrator** — extend `run_sprint2_synthetic_baseline` (or thin `run_sprint2_demo_contour`) → `sprint2-baseline-report.{json,md,pdf}`.  
3. **TZ matrix** — Sprint-2-scoped statuses only.  
4. **Customer templates** — `docs/customer/*` from existing demo/discovery.  
5. **LLM docs + comparative mock bench** — `docs/ai/*`; no verdict mutation.  
6. **Tests + gates** — then implementation report.

## Explicit non-goals this sprint

- Publishing product accuracy / >90% / production-ready.  
- Vendoring KAAN or other non-cleared corpora.  
- GraphRAG / multi-agent orchestration / mandatory triple live LLM path.  
- Invented customer organizations or outreach results in git.
