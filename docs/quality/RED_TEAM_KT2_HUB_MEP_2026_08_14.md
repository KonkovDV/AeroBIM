---
title: "Red Team — Hub IFC-Bench / West Riverside / AEC prefetch (ca6801d)"
status: active
version: "1.0.0"
last_updated: "2026-08-14"
claim_boundary: >-
  open_bench_only. Checkpoint remains NO_GO. 25/1026 is a countable IFC-Bench
  subset, not product accuracy and not 514 false-pass. West Riverside is inventory,
  not QA. Harbor AEC-Bench agent trial is NOT_RUN. Does not close RT-001/002/003.
---

# Red Team — Hub models + federated MEP (`ca6801d`)

**Author relationship:** Internal self-assessment  
**Scope:** commit `ca6801d` vs parent `cd67925` (Hub IFC-Bench v2 probes, West Riverside IFC4 inventory, AEC-Bench prefetch/docs evidence) plus mitigations in this commit  
**Checkpoint:** **`NO_GO`** (unchanged)  
**Security review:** internal (no external ticket).

## Verdict

| Lane | Result |
|---|---|
| Application security (Critical/High) | **0** |
| Integrity (Medium) | **3 found → mitigated in this commit** |
| Claims Lock / open-bench framing | **PASS with notes** — no product >90%, no Harbor false-pass, no RT-003 delivered |
| Customer Checkpoint | Still **NO_GO** (RT-001/002/003) |

## Findings

| ID | Sev | Status | Finding | Mitigation |
|---|---|---|---|---|
| RT-HUB-01 | MED | **MITIGATED** | AEC-Bench prefetch joined `manifest.dest` onto `environment/` with no jail (`../../../evil.pdf` could write outside the instance tree) | `resolve_storage_path()`; PathJailError recorded as download error; unit test |
| RT-HUB-02 | MED | **MITIGATED** | Unvalidated `manifest.key` → `urllib.request.urlopen` + unbounded `read()` (`file://`, SSRF, oversized body) | HTTPS + `nomic-public-data.com` allowlist, then `safe_urlopen` (SSRF/DNS pin/no redirects); 200 MiB cap; unit tests |
| RT-HUB-03 | MED | **MITIGATED** | `docs/evidence/*-smoke-latest.json` fingerprinted the machine: absolute `dataset_root` / `output_path`, boolean `*_key_present` (no raw keys) | Docs copy is repo-relative; `output_path` and credential flags omitted; artifacts dump may still keep the full local dump under gitignored `artifacts/` |
| RT-HUB-04 | INFO | OPEN | Remaining ~1001 IFC-Bench NL rows stay `skipped`; do not quote `exact_match_rate_on_scored: 1.0` without **25/1026** | Documented |
| RT-HUB-05 | INFO | OPEN | West Riverside has **0** v2 QA CSV rows; IFC4 inventory ≠ clash, ≠ RT-003 | Documented; `mep_system_clash=NOT_VERIFIED` |
| RT-HUB-06 | INFO | OPEN | AEC-Bench Harbor / Mushkani 160 drawing-reading false-pass remains **NOT_MEASURED**; gold `null_always_clean` 134 FP / 50 TN / 184 is not an agent | Documented |

## Claims Lock spot-check

| Invariant | Status |
|---|---|
| No product >90% | Intact |
| IFC-Bench 25/1026 ≠ 514 eval-split false-pass | Intact (12 test / 13 train of the 25 scored) |
| AECV `macro_extended=0.4325` is a different bench from Harbor AEC-Bench | Intact |
| Harbor agent trial NOT_RUN; Yandex Completions key must not be pasted into Harbor | Intact |
| West Riverside = IFC4 inventory, not QA score | Intact |
| GPLv3 IFC-Bench models not in the MIT tree / not in `CANDIDATES` | Intact |
| Checkpoint NO_GO | Intact |

## Residual risks

1. Cherry-picking `exact_match_rate_on_scored: 1.0` without the **25/1026** denominator.  
2. Treating West Riverside terminal counts as a clash or customer MEP result.  
3. Treating gold `null_always_clean` 0.7283 as a Harbor / Mushkani agent false-pass.  
4. Historical `docs/evidence/` JSON outside this smoke pair still contains absolute machine paths (pre-existing; not opened as a new High).

## Not claimed closed

RT-001 (RF expertise corpus), RT-002 (Samolet-signed profile), RT-003 (delivered MEP clash), Harbor AEC-Bench agent scores, native DWG.
