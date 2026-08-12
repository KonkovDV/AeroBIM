<!-- claims-lint: allow-file reason="Red Team code audit 2026-08-12; documents FIXED Claims Lock defect; no Checkpoint GO" -->
---
title: "Red Team code audit — 2026-08-12 evening"
date: "2026-08-12"
head_before: "58d921a3c6ba6e2b280486f10522f8539193cfcc"
stage: "code"
claim_boundary: "Code honesty / security recheck. Not customer accuracy. Checkpoint remains NO_GO."
---

# Red Team: code audit (2026-08-12)

## Scope

Live `backend/src` controls after KT#2 densify + benchmark hygiene tip `58d921a`:

1. Stage B VLM/LLM headers + host gate + architecture import gate  
2. Claims Lock / precision publishable path (clash fixture)  
3. OIDC BFF / ADS / signing honesty residuals  
4. KT2 evidence tools subprocess / path hygiene  

## Reproduction

```text
python -m unittest discover -s tests -p "test_vlm_endpoint_gate.py" -v
python -m unittest discover -s tests -p "test_immutable_security_headers.py" -v
python -m unittest discover -s tests -p "test_architecture_import_gate.py" -v
python -m unittest discover -s tests -p "test_evaluate_detection_precision.py" -v
python -m unittest discover -s tests -p "test_tz_fixture_evidence_2026_08.py" -v
python -m unittest discover -s tests -p "test_i6_precision_kpi.py" -v
python -m unittest discover -s tests -p "test_rt_customer_blocker_honesty_lock.py" -v
python -m aerobim.tools.measure_extent_clash_fixture --write-fixture
python scripts/lint_claims.py --matrix-guard
```

## Results

| Area | Result | Status |
| --- | --- | --- |
| Exact/suffix Yandex host gate | no `"yandex" in host` substring promotion | VERIFIED OK |
| Immutable VLM/LLM headers | Auth/CT/Accept forced | VERIFIED OK |
| Architecture import gate | core/domain/application direction clean | VERIFIED OK |
| OIDC BFF | still `NOT_IMPLEMENTED` / 501 | VERIFIED OK |
| Fixture clash P/R honesty | was `corpus_kind=customer` + `render=1.0000` | **FIXED** |
| Checkpoint GO | no fixture flip path | VERIFIED OK |
| matrix-guard | OK | VERIFIED |

## Findings

### RT-CODE-20260812-01 — Fixture labels promoted to `corpus_kind=customer` (P1 live / P0 latent)

- **Status:** **FIXED** in this commit  
- **Root cause:** `evaluate_detection_precision` mapped `dataset_status=adjudicated` → `customer` and ignored `claim_level=fixture_only`. Clash measure also called with `require_agreement_for_publishable=False`, so `held_out_split=true` would have made `publishable=true`.  
- **Live artifact before fix:** `docs/evidence/clash-measurement-slice-2026-08/precision-recall.json` had `corpus_kind=customer`, `base_publishable=true`, `render=macro_precision=1.0000`.  
- **Fix:**
  - `_resolve_corpus_kind()` honors `_NON_CUSTOMER_CLAIM_LEVELS` (incl. `fixture_only`)
  - non-customer claim_level forces `publishable_protocol_gate=false`
  - non-customer corpus always requires agreement (blocks debug escape)
  - clash measure uses `require_agreement_for_publishable=True`
  - regenerated evidence: `corpus_kind=fixture`, render **withheld**
  - regression tests added

### RT-CODE-20260812-02 — Stage B transport controls hold

- **Status:** VERIFIED OK  
- Exact host/suffix gate, immutable headers, SSRF `safe_urlopen` on advisory path.

### RT-CODE-20260812-03 — OIDC / ADS / signing residuals

- **Status:** VERIFIED honesty intact (known product gaps remain: RT-001/002/003, ODA stub, no УКЭП crypto)  
- Not regressions of closed P0 security fixes.

### RT-CODE-20260812-04 — Tools layer host substring (bench)

- **Severity:** P2 residual  
- **Status:** ACCEPTED (tools exemption); `run_aecv_bench_eval.py` still uses `"yandex" in base_url` for body shaping; egress still allowlisted/SSRF-gated.

### RT-CODE-20260812-05 — LLM logging header asymmetry vs VLM

- **Severity:** P2  
- **Status:** ACCEPTED residual; VLM forces `x-data-logging-enabled=false`; LLM leaves operator setting.

## P0 open after this pass

**None in audited code paths.** Product Checkpoint remains **NO_GO** (customer corpus / norms / MEP — RT-001/002/003).

## Verdict

Code audit found and closed a Claims Lock honesty defect in the precision harness. Stage B security controls remain green. **Show YES / customer GO NO.**
