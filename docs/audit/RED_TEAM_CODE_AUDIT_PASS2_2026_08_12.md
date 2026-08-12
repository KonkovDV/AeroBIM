<!-- claims-lint: allow-file reason="Red Team code audit pass 2; no Checkpoint GO" -->
---
title: "Red Team code audit pass 2 — 2026-08-12"
date: "2026-08-12"
head_before: "7dab1c489e93ac71be9ac61e1c66a3f9375582d8"
stage: "code"
claim_boundary: "Code honesty / security recheck after Claims Lock fix. Not customer accuracy. Checkpoint remains NO_GO."
---

# Red Team: code audit pass 2 (2026-08-12)

## Scope

Independent re-audit of live `backend/src` after `7dab1c4` (fixture `corpus_kind` fix). Goal: confirm the previous P1 stays closed and close remaining P2 residuals that still had a live code path.

## Reproduction

```text
python -m unittest discover -s tests -p "test_vlm_endpoint_gate.py" -v
python -m unittest discover -s tests -p "test_immutable_security_headers.py" -v
python -m unittest discover -s tests -p "test_architecture_import_gate.py" -v
python -m unittest discover -s tests -p "test_evaluate_detection_precision.py" -v
python -m unittest discover -s tests -p "test_tz_fixture_evidence_2026_08.py" -v
python -m unittest discover -s tests -p "test_i6_precision_intake.py" -v
python -m unittest discover -s tests -p "test_rt_customer_blocker_honesty_lock.py" -v
python -m unittest discover -s tests -p "test_verify_kt2_handoff.py" -v
python -m unittest discover -s tests -p "test_aecv_bench_eval.py" -v
python -m aerobim.tools.verify_kt2_handoff --write-status ../docs/evidence/kt2-handoff-2026-08-11/VERIFY.json
python scripts/lint_claims.py --matrix-guard
```

## Results

| Area | Result | Status |
| --- | --- | --- |
| Clash P/R `corpus_kind` | `fixture`; render withheld; gate false | VERIFIED (prior fix holds) |
| Handoff gate vs P/R JSON | was STATUS-only; now inspects P/R honesty | **FIXED** |
| Exact/suffix Yandex host gate | holds | VERIFIED OK |
| VLM immutable headers | Auth/CT/Accept/logging forced | VERIFIED OK |
| LLM logging extras override | extras could set `true` | **FIXED** |
| Bench `"yandex" in base_url` | substring body-shape | **FIXED** |
| Architecture import gate | 0 violations | VERIFIED OK |
| OIDC BFF | still `NOT_IMPLEMENTED` | VERIFIED OK |
| Checkpoint | `NO_GO` | VERIFIED OK |

## Findings

### RT-CODE-20260812-06 — Handoff verify ignored clash P/R honesty (P1 process)

- **Status:** **FIXED**  
- **Detail:** `verify_kt2_handoff` checked clash `STATUS.json` `claim_level` only. The live defect (`corpus_kind=customer`, `render=1.0000`) would still have passed the handoff gate. New check `clash_precision_not_customer` requires non-customer corpus, closed protocol gate, `publishable=false`, and withheld render.

### RT-CODE-20260812-05 — LLM logging header extras (P2)

- **Status:** **FIXED** (was ACCEPTED residual on pass 1)  
- **Detail:** Operator preference is captured once at construction from DI extras; request extras cannot flip `x-data-logging-enabled`. Folder/logging denied on merge, same pattern as VLM.

### RT-CODE-20260812-04 — Bench host substring (P2)

- **Status:** **FIXED** (was ACCEPTED residual on pass 1)  
- **Detail:** `run_aecv_bench_eval` now uses `endpoint_looks_like_yandex()` (exact/suffix) plus `gpt://` model URI. `not-yandex.evil` no longer shapes Yandex thinking body.

### RT-CODE-20260812-01 — Fixture→customer mapping

- **Status:** VERIFIED still closed on committed `precision-recall.json`.

### Still open (not this pass)

| ID | Why |
| --- | --- |
| RT-001/002/003 | Customer corpus / approved norms / MEP — product NO_GO |
| ODA native DWG | `@sota-stub` honesty lock |
| УКЭП crypto | signature audit ≠ cryptographic chain |
| `"yandex" in name` in orchestrator | provider-name routing, not host gate |
| N43 / RUF100 | calendar: 17.08 / 19.08 |

## P0 open after this pass

**None in audited code paths.** Checkpoint remains **NO_GO**.

## Verdict

Pass 1 fix holds. Pass 2 closed the gate that would have missed a P/R honesty regression, plus two Stage B residuals. **Show YES / customer GO NO.**
