# AeroBIM Hyperdeep Audit — 2026-08-06

**HEAD:** `d96a59ac6704357336ae46f7d61f6435be4c6a2c`  
**Checkpoint:** **NO_GO**  
**claim_level:** `synthetic_only` / engineering packaging  
**customer_precision_claim_publishable:** `false`  
**Verdict:** **ENGINEERING_READY_CUSTOMER_BLOCKED**

---

## 1. HEAD and post-Jul26 summary

Recent committed tip chain (abbrev):

| SHA | Summary |
|---|---|
| `d96a59a` | fix(ci): complete runtime baseline and unblock lint gate |
| `1804f62` | fix(security): close Red Team hyperdeep gaps on egress and storage jail |
| `c337c00` | docs: refresh tracker baseline PDF with current coverage numbers |
| `3ac50b6` | feat: Renga ToS cite GO + PNST IDS runtime 18/22 clean |
| `aaa1ae2` | feat: GOST 21.101-2026 marks/edition, PNST IDS inventory, AR recount |
| `963c93c` | feat: close KR #2/#4 completeness rules; allow document-only analyze |

**Post–26 Jul engineering arc (honest):** security/path-jail hardening, hybrid advisory contour honesty, PNST/GOST experiment evidence, completeness demonstrators, runtime baseline inventory sync, Sprint 2 synthetic dataset + baseline packaging (uncommitted until this checkpoint lands). **Not claimed:** full architecture test-suite rewrite; live multi-model bake-off PASS; customer precision.

Working tree at audit time includes substantial **uncommitted** Sprint 2 tracker deliverables (baseline aliases, customer exact filenames, release verifier, this audit).

**GH hygiene (2026-08-06 follow-up):** outreach templates under `docs/customer-discovery/` and related partner/tracker notes use `[OPERATOR_NAME]` / `[OPERATOR_FULL_NAME]` placeholders — no operator personal name or phone on the public tree. Live commercial ops remain under gitignored `.local/` only. Accidental local baseline PDFs (`AeroBIM_baseline_*.pdf`, non-canonical `sprint2-synthetic-baseline-2026-08-06+`) are gitignored.

---

## 2. Architecture — four contours + AI invariant

Domain contours (`backend/src/aerobim/domain/architecture.py`):

1. **INGESTION** — version-aware document identity  
2. **DETERMINISTIC_VALIDATION** — Shared-gate owner of findings that drive pass/fail inputs  
3. **AI_ADVISORY** — overlay only; cannot flip `summary.passed` (ADR-001)  
4. **EVIDENCE_REPORTING** — EvidenceAssembler writes Shared-gate status from deterministic inputs + policy  

**AI invariant:** advisory OFF == ON for `summary.passed` / issue signature (`tests/test_advisory_vlm_off_equals_on.py`). No GraphRAG / multi-agent sprawl added in Sprint 2.

---

## 3. Security

Cite Red Team hyperdeep remediations at **`1804f62`** / [`RED_TEAM_HYPERDEEP_2026_08_06.md`](RED_TEAM_HYPERDEEP_2026_08_06.md):

- Trusted fixture prefixes only (no substring `fixture` false public class)  
- Remark LLM request defaults block customer egress unless public_fixture path  
- Cross-tenant path jail → 404 (no prefix oracle)  
- `safe_storage_token` / quota / zip containment hardening  
- Application→Infrastructure / Tools layering fixes for intake + space inventory  

**Not claimed:** formal pen-test attestation, customer SLA security schedule.

---

## 4. Dataset / evaluation / Sprint 2

| Item | Status |
|---|---|
| Mode B synthetic manifest (15 cases, 3 classes) | Present — `samples/benchmarks/sprint2-dataset/MANIFEST.json` |
| Mode A inventory | Inventory-only; **no downloads** |
| Synthetic baseline TP/FP/FN | Fixture planted set: TP=6 FP=2 FN=0; P=0.75 R=1.0 (not product accuracy) |
| Agreement κ/α / nDCG | **N/A** (no dual-human / ranking labels) |
| clashes_count | **0** honesty (geometric clash not planted runnable) |
| Brief filenames | `SPRINT2_BASELINE_REPORT_2026-08-06.{md,pdf}` + `sprint2-baseline-evidence.json` |
| Banner | `SYNTHETIC/FIXTURE ONLY` · `CUSTOMER ACCURACY NOT ESTABLISHED` |

---

## 5. Customer readiness — BLOCKED

| Gate | Status |
|---|---|
| Intake `customer-intake-gate.json` | `BLOCKED_NO_CUSTOMER_DATA` / `not_ready` |
| Dual adjudication (RT-001) | OPEN |
| Licensed customer pack | Absent |
| Severity taxonomy customer approval | PROPOSED only |
| Outreach | TIM row **not_contacted** / prepare outreach — no invented contact event |
| Demo path docs | Present (`CUSTOMER_DEMO_PROTOCOL_2026-08-06.md`, one-pager, discovery, interview) |

---

## 6. Kimi / Qwen / Gemma

| Path | Honesty |
|---|---|
| DI advisory providers + mock comparative bench | Present |
| `docs/ai/LLM_*.md` | Contour / privacy / comparative framing |
| Live Kimi / Qwen / Gemma bake-off | **Not claimed PASS** — requires API keys / local weights; optional |
| Verdict neutrality | Mock schema `affects_summary_passed=false`; OFF==ON tests remain the gate |

---

## 7. Norms / BCF / MEP / DWG / calc gaps

| Capability | Honest status |
|---|---|
| Norm packs / PNST IDS experiments | Partial engineering evidence; not customer GO |
| BCF | Structural export path — **not** CDE-ready claim |
| MEP system clash | **NOT_VERIFIED** / RT-003 class |
| Native DWG | **MISSING** |
| Calc independence | Cross-check fixtures only — **not** independent engineering calc claim |
| Customer SLA | Fixture SLA ≠ customer SLA |

---

## 8. Release governance

- Verifier: `python -m aerobim.tools.verify_release_evidence`  
- Index: [`RELEASE_EVIDENCE_INDEX_2026-08-06.md`](RELEASE_EVIDENCE_INDEX_2026-08-06.md)  
- Status: [`RELEASE_STATUS_2026-08-06.md`](RELEASE_STATUS_2026-08-06.md) + JSON twin  
- Fail-closed on missing brief PDFs, wrong claim levels, publishable without intake, `closes_rt001=true`, commit SHA drift, runtime gates not PASS  

`sprint2-synthetic-baseline-2026-08-04.*` marked **HISTORICAL/SUPERSEDED**.

---

## 9. Claims Lock audit

Against [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md):

| Forbidden claim | This release |
|---|---|
| Product accuracy / >90% | Not claimed |
| Production-ready | Not claimed |
| Native DWG | Not claimed |
| Delivered MEP | Not claimed |
| Calc independence | Not claimed |
| CDE-ready BCF | Not claimed |
| Customer SLA | Not claimed |
| `customer_precision_claim_publishable` | `false` |

---

## 10. Critical risks

1. **Customer-blocked metrics narrative** — any slide using fixture P/R as product accuracy  
2. **Egress regressions** — advisory path must keep public_fixture vs customer separation  
3. **Filename / evidence dual truth** — mitigated by verifier + brief aliases  
4. **SHA pin honesty** — runtime baseline metrics captured in 1804f62→d96a59a window; `commit_sha` pinned to release HEAD with explicit note  
5. **Uncommitted Sprint 2 surface** — large WIP; treat as checkpoint packaging until committed  

---

## 11. 72h plan + 2-week plan

### 72 hours

- Commit Sprint 2 packaging after human review (no invent contacts)  
- Run full pytest if not already recorded; keep focused gates green  
- Prepare TIM outreach draft from discovery script (**do not** mark contacted until sent)  
- Optional: live advisory smoke with keys on public fixtures only  

### 2 weeks

- NDA + one completed-section pack under `samples/customer/` (gitignored)  
- Dual human adjudication → intake gate ratchet  
- Planted geometric clash IFC pair (honesty path for clashes_count)  
- Severity taxonomy workshop → customer approval  
- Re-run demo protocol on real pack; keep Claims Lock  

---

## 12. Reproduction commands

```text
cd backend
.venv\Scripts\python.exe -m aerobim.tools.export_sprint2_dataset_manifest
.venv\Scripts\python.exe -m aerobim.tools.run_sprint2_synthetic_baseline --iterations 1 --dataset-manifest ../samples/benchmarks/sprint2-dataset/MANIFEST.json
.venv\Scripts\python.exe -m ruff format --check src tests
.venv\Scripts\python.exe -m ruff check src tests
.venv\Scripts\python.exe -m mypy src/aerobim --ignore-missing-imports
.venv\Scripts\python.exe -m pytest tests/test_verify_release_evidence.py tests/test_sprint2_dataset_manifest.py tests/test_advisory_vlm_off_equals_on.py -q --tb=line
.venv\Scripts\python.exe -m aerobim.tools.verify_release_evidence
```

---

## 13. Evidence index

See [`RELEASE_EVIDENCE_INDEX_2026-08-06.md`](RELEASE_EVIDENCE_INDEX_2026-08-06.md).

---

## 14. Live quality-gate record

| Gate | Result |
|---|---|
| ruff format --check | **PASS** |
| ruff check | **PASS** |
| mypy | **PASS** (295 source files) |
| focused pytest | **PASS** — 19 passed |
| verify_release_evidence | **PASS** |
| full pytest | **PASS** — 1902 passed, 8 skipped, 159 subtests (~26.7s) |

Honesty: live full pytest counts differ from `runtime-baseline-latest.json` historical 2043/2052 — recorded both; neither is product accuracy.

---

## 15. Verdict

Baseline brief artifacts + customer demo docs + `verify_release_evidence` green; focused and full pytest green.

### **ENGINEERING_READY_CUSTOMER_BLOCKED**

Customer accuracy remains **not established**. Checkpoint remains **NO_GO** for RT-001/002/003.
