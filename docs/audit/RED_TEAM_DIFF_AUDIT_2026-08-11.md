<!-- claims-lint: allow-file reason="Red Team Stage A diff audit; reproductions only where marked VERIFIED" -->
---
title: "AeroBIM Red Team Diff Audit — 3..11 Aug 2026"
date: "2026-08-11"
head_sha: "a818bfe2eeeaa2cf2b5c98cdd331887e519aacf7"
stage: "A"
claim_boundary: "Diff + spot reproduction. Not full Phase 2–20 closure. Not customer accuracy."
---

# RED TEAM DIFF AUDIT — 2026-08-03 … 2026-08-11 (Stage A)

**HEAD:** `a818bfe2eeeaa2cf2b5c98cdd331887e519aacf7`  
**Parent of HEAD:** `7c75155bb79e6b52ac7cda4a0847166dd5bed1b4`  
**Window:** `--since=2026-08-03 00:00:00 --until=2026-08-12 00:00:00`  
**Counts:** **158** commits (`--all`); **134** first-parent on `main`; **641** unique paths.

Full commit TSV: `docs/audit/_window_commits_2026-08-11.tsv`  
Unique files: `docs/audit/_window_unique_files_2026-08-11.txt`  
First-parent list: `docs/audit/_fp_commits_2026-08-11.txt`

---

## 1. Executive diff summary

| Theme | What actually landed | Threat / requirement | Residual risk at HEAD |
| --- | --- | --- | --- |
| Grant / Yandex LLM contour (03.08) | Host allowlist, budget, stamp/PII dual-gate, Studio defects D-1..D-6 | SSRF / PII egress / advisory budget | Contour matured; VLM header immutability **not** at LLM parity |
| KT#2 / open bench / AECV (03–04.08) | Hash-chain evidence, IDS baselines, AECV scorer, IFC-Bench smoke | Honesty of open benchmarks | Fixture ≠ customer |
| Red Team waves / Class A honesty (05–09.08) | Headers, export sanitize, HITL locks, signing windows, baseline integrity, publishable circular-lock fixes | False GO / provenance | Many controls deferred or lag-tolerant |
| CV P0–P4 baseline (10.08) | Heuristics, region metrics, vectors, geo, VLM schema | Drawing pipeline honesty | **Not** trained CV; claim must stay heuristic |
| VLM rename Kimi→VLM (10.08) | Provider-agnostic env / client rename | Alias confusion | Gate still substring-based; missing gate unit tests |
| Mentor / vertical slice demos (10–11.08) | PDF text-layer slice + mentor pack | Demo without over-claim | Advisory-only |
| Customer blocker eng pack (11.08) | ODA honesty, OIDC PKCE 2.5, allowlists | Honest 501 / missing native DWG | OIDC still 501; ODA not product |
| A4 signing ACTIVE (11.08) | `enforce_ci` + fail unverifiable | Supply-chain provenance | Historical unsigned majority remains |
| TZ fixture clash + overlay (11.08) | AABB P/R n=5 + overlay PNG | Freeze TZ pair §8 | **fixture_only**; not TZ >90% |

**Churn (first-parent approx.):** +103k / −15k lines — documentation and evidence dominate path count (`docs` 283 / `backend` 267 unique paths in `--all` window).

---

## 2. Commit catalogue (first-parent `main`, newest → oldest)

Signature legend: `G` = good; `N` = no signature. Full SHA in TSV.

### 2.1 2026-08-11 (signed tip cluster)

| Short | Sig | Subject | Security / claims impact |
| --- | --- | --- | --- |
| `a818bfe` | G | feat(tz): fixture clash measure + drawing overlay evidence | Fixture P/R + overlay PNG; claim_level fixture_only |
| `7c75155` | G | gov(a4): activate commit-signing enforcement | Policy flip ACTIVE |
| `60c84b9` | G | fix(rt): push-gate residuals (ADS, Yandex IP, OIDC allowlist) | Hardening; re-verify still required for new gate gaps |
| `5ef40c0` | G | eng pack: ODA honesty, OIDC PKCE 2.5 | Honesty pack; not production SSO |
| `07f4118` | G | full-repo RT: Windows ADS, VLM gate | Windows + gate fixes |
| `cfdf084` | G | VLM mentor path + cache honesty | Cache namespace honesty |
| `c8232ad` | G | mentor pack evidence-only | Docs |
| `b56b199` | G | mentor pack folder | Docs |

### 2.2 2026-08-10 (CV + VLM rename + vertical slice)

| Short | Sig | Subject | Notes |
| --- | --- | --- | --- |
| `4ad3d9b` | G | refactor(vlm): Kimi → provider-agnostic VLM | Alias / env migration surface |
| `b32e6ac` | G | CV P1–P4 baselines | Metrics/vectors/geo/schema |
| `9b80ede` | G | CV P0–P4 roadmap execution | Heuristics + guards |
| `251e20d` | G | CV roadmap docs | Evidence-first plan |
| `9d0dcd2` | G | vertical slice envelope/metrics | Demo honesty |
| `2e0c3f1` | G | vertical slice PDF text-layer | **Not** CV product |

### 2.3 2026-08-09 (governance / Red Team / merges)

Includes unsigned series through Class A honesty, signing dry-run branch merges, PR merges `#12` `#13` `#14` (merge commits signed `G` by GitHub/user key where applicable), baseline integrity, HITL `.seq` exclusivity, deferred-control registry, security headers, evidence path hygiene.

**Notable:** branch `ci/signing-enforce-dryrun` still exists at `2e8fedb` (merge dry-run experiment).

### 2.4 2026-08-03 … 08 (grant + KT2 + RT waves)

From `c52023c` (qwen-local) through grant-rt stamp/PII/SSRF/LLM allowlist, Studio wiring, open corpora, jury packs, tracker commercial quarantine, Exp B docs, multiple Red Team closure docs under `docs/audit/` and `docs/quality/`.

**ТРЕБУЕТСЯ ПРОВЕРКА:** per-commit line-level security review of all 158 messages was inventoried; **not** every hunk was re-executed. Deep reproduction below focuses on residual defects at HEAD.

---

## 3. Thematic deep dives (required checklist)

### 3.1 Advisory egress / VLM rename / Kimi aliases / Yandex gate

| Question | Finding at `a818bfe` |
| --- | --- |
| What changed? | Kimi contour renamed to VLM (`4ad3d9b`+); Yandex kimi-k3 refuse gate in `vlm_endpoint_gate.py`; IP/unknown-host treated as Yandex when `provider=yandex*` |
| Threat closed? | Wrong response_format / silent kimi-k3 against Yandex |
| Test on real path? | Gate exercised via mentor/DI paths in prior commits; **no** `tests/test_vlm_endpoint_gate.py` |
| Bypass? | **VERIFIED:** substring `"yandex" in host` matches `not-yandex.evil` |
| Silent fallback? | Empty model on Yandex-looking endpoint → refuse (good) |
| Claim expansion? | Docs increasingly say VLM; keep “advisory only” |
| Clean Architecture? | Gate in `core/config` — OK |
| Env migration? | Old `AEROBIM_KIMI_*` aliases — **ТРЕБУЕТСЯ ПРОВЕРКА:** exhaustive alias matrix not re-run in Stage A |

### 3.2 VLM schema / cache / headers

| Question | Finding |
| --- | --- |
| Headers immutable? | **VERIFIED FAIL** on `VlmAdvisoryClient._request_headers` (see RT-20260811-01). `OpenAICompatLlmProvider` writes `Authorization` **after** extras (safer for auth), but still allows `Content-Type` override via extras |
| DI wiring today | `bootstrap._build_advisory_vlm_pipeline` constructs `VlmAdvisoryClient` **without** `extra_headers` — reduces immediate exploitability |
| Cache isolation | Prior commits added namespace fail-closed; **ТРЕБУЕТСЯ ПРОВЕРКА:** cross-tenant concurrency mutation not re-run Stage A |
| Schema validation | Response schema modules exist; rich observation must stay local-validated — spot check only |

### 3.3 CV P0–P4 / PDF vertical slice / DrawingRegion / vectors / geo / IFC matching

| Question | Finding |
| --- | --- |
| Actual capability | Heuristic region detection + PDF text-layer vertical slice + overlay smoke PNG |
| Over-claim risk | HIGH if README says “CV ready” — matrix/docs in tip keep heuristic / fixture wording |
| Overlay evidence | `docs/evidence/drawing-overlay-smoke-2026-08/` (deterministic bbox) |
| IFC matching | Domain module present; customer ambiguity path **not** re-proven Stage A |

### 3.4 OIDC PKCE 2.5 / allowlists / RBAC / HITL

| Question | Finding |
| --- | --- |
| OIDC routes | **4×** `status_code=501` in `presentation/http/routes/system.py` |
| PKCE | Stub issues CSRF+PKCE S256; **not** production session BFF |
| HITL | Sequence / `.seq` exclusivity work in 09.08 commits; N-50 audit-store CAS historically PARTIAL — **ТРЕБУЕТСЯ ПРОВЕРКА** concurrency on HEAD |
| Shared bearer | Still pilot-shaped unless enterprise OIDC lands |

### 3.5 ZIP / XML / upload / rate limit / error sanitization

Landed across earlier RT waves. **ТРЕБУЕТСЯ ПРОВЕРКА:** zip-bomb + 100-concurrent upload battery not executed in Stage A.

### 3.6 Closed-contour Docker / offline / signing / baseline

| Question | Finding |
| --- | --- |
| Docker | Digest-pinned `python:3.12-slim`; compose context `./backend` with `.dockerignore` |
| Signing | A4 ACTIVE; tip signed |
| Baseline circular lock | Soft-skip / ancestor window policies from 09.08; N43 still deferred |
| Offline SBOM | Referenced in KT2 commits; Stage A did **not** regenerate `audit/reports/sbom.json` |

### 3.7 Customer blockers / ODA / README / claims

| Question | Finding |
| --- | --- |
| ODA | Honesty / reason split eng pack — native DWG **not** product |
| Clash TZ | Fixture AABB n=5 P/R=1.0 — **must not** publish as TZ >90% |
| Checkpoint | Runtime baseline still records NO_GO until RT-001/002/003 |

---

## 4. VERIFIED findings (Stage A reproductions)

### RT-20260811-01: VLM `extra_headers` can override Authorization

- **Severity:** P1  
- **Status:** VERIFIED  
- **Category:** VLM / transport security  
- **Exact path:** `backend/src/aerobim/infrastructure/adapters/vlm_advisory_client.py`  
- **Symbol:** `VlmAdvisoryClient._request_headers` (merge order: base headers then `**self._extra_headers`)  
- **Current SHA:** `a818bfe2eeeaa2cf2b5c98cdd331887e519aacf7`  
- **Parent SHA:** `7c75155…`  
- **Observation:** Unlike `OpenAICompatLlmProvider` (Authorization applied last), VLM client allows extras to replace `Authorization`, `Content-Type`, `Accept`, `x-data-logging-enabled`, `x-folder-id`.  
- **Reproduction:**

```text
cd backend
python -c "from aerobim.infrastructure.adapters.vlm_advisory_client import VlmAdvisoryClient as C; c=C.__new__(C); c._auth_scheme='Bearer'; c._api_key='REAL'; c._folder_id='folder-real'; c._extra_headers={'Authorization':'Bearer ATTACKER','Content-Type':'text/plain','Accept':'*/*','x-data-logging-enabled':'true','x-folder-id':'folder-evil'}; h=C._request_headers(c); print(h['Authorization'], h['x-data-logging-enabled'], h['x-folder-id'])"
```

- **Expected:** security headers immutable / extras cannot override.  
- **Actual:** `Authorization=Bearer ATTACKER`, logging=`true`, folder=`folder-evil`.  
- **Security impact:** API contract allows credential/logging/folder spoof if any caller passes attacker-influenced extras.  
- **Correctness impact:** provider logging / folder routing may diverge from settings.  
- **Claim impact:** none directly.  
- **Minimal fix:** apply extras first, then force security headers; deny-list override keys; mirror LLM client order.  
- **Regression test:** unit test “immutable security headers” for VLM **and** LLM Content-Type.  
- **CI gate:** include in VLM unit job.  
- **Migration risk:** low.  
- **Owner decision:** none for fix; confirm whether any external plugin injects extras.  
- **Exploitability:** PARTIAL today (DI does not pass `extra_headers` into `VlmAdvisoryClient`), but defect is live in the class.

### RT-20260811-02: Yandex host detection is substring-based

- **Severity:** P1  
- **Status:** VERIFIED  
- **Category:** VLM endpoint gate / correctness  
- **Exact path:** `backend/src/aerobim/core/config/vlm_endpoint_gate.py`  
- **Symbol:** `endpoint_looks_like_yandex` — `if "yandex" in host`  
- **Current SHA:** `a818bfe…`  
- **Observation:** host `not-yandex.evil` evaluates `looks=True` and refuses kimi-k3 even with `provider=None`. Host `yandex.attacker.example` likewise.  
- **Reproduction:**

```text
python -c "from aerobim.core.config.vlm_endpoint_gate import endpoint_looks_like_yandex, refuse_yandex_kimi_default_model as r; u='https://not-yandex.evil/v1'; print(endpoint_looks_like_yandex(u), bool(r(base_url=u, model='kimi-k3', provider=None)))"
```

- **Expected:** exact allowlist / suffix / DNS identity — not raw substring.  
- **Actual:** substring match → false-positive Yandex classification.  
- **Security impact:** gate confusion; paired with provider=yandex unknown hosts → treat as Yandex (intentional for IP bypass) but substring creates unrelated false positives.  
- **Correctness impact:** refuse/allow decisions on odd hostnames.  
- **Minimal fix:** exact host set / publicsuffix rules; never `"yandex" in host`.  
- **Regression test:** `not-yandex.evil`, exact Yandex hosts, IP + provider=yandex, moonshot markers.  
- **CI gate:** new unit module (today **missing**).  
- **Owner decision:** whether non-Yandex IP with provider=yandex must remain refuse-closed (recommended keep).

### RT-20260811-03: No unit tests for `vlm_endpoint_gate`

- **Severity:** P2  
- **Status:** VERIFIED  
- **Category:** test gap  
- **Exact path:** `backend/src/aerobim/core/config/vlm_endpoint_gate.py`  
- **Observation:** `rg` / pytest path `tests/test_vlm_endpoint_gate.py` → absent; no test references `endpoint_looks_like_yandex`.  
- **Impact:** regressions in gate logic (incl. RT-20260811-02) not caught.  
- **Minimal fix:** add focused unit tests listed in audit brief §7.2.  
- **Owner decision:** none.

### RT-20260811-04: No automated layer-import architecture gate

- **Severity:** P2  
- **Status:** VERIFIED  
- **Category:** architecture  
- **Exact path:** expected `backend/tests/test_architecture_import_gate.py` — **absent**  
- **Observation:** `test_architecture_seams.py` covers precision/capability honesty, **not** AST import direction `domain ↛ infrastructure`.  
- **Impact:** Clean Architecture violations can land unnoticed.  
- **Minimal fix:** add import-linter / AST walk gate in CI.  
- **Owner decision:** choose tool (import-linter vs custom).

### RT-20260811-05: Dirty IFC release-benchmark evidence on workstation

- **Severity:** P3  
- **Status:** VERIFIED  
- **Category:** hygiene / provenance  
- **Exact path:** `audit/evidence/ifc-release-benchmark-2026-08.json`, `docs/evidence/ifc-release-benchmark-2026-08.md`  
- **Observation:** `git status` shows both modified vs `a818bfe`; not committed.  
- **Impact:** local evidence drift; risk of accidental commit of unreviewed metrics.  
- **Minimal fix:** regenerate intentionally + commit, or discard.  
- **Owner decision:** keep / discard / re-baseline.

### RT-20260811-06: LLM `Content-Type` still overridable via extras

- **Severity:** P2  
- **Status:** VERIFIED  
- **Category:** LLM transport  
- **Exact path:** `openai_compat_llm_provider.py` `_request_headers`  
- **Observation:** Authorization is forced last (safe), but `Content-Type: evil` survives from extras.  
- **Reproduction:** constructed `__new__` probe → `Content-Type=evil`, `Authorization=Bearer REAL`.  
- **Minimal fix:** force Content-Type/Accept after extras.  
- **Exploitability:** PARTIAL (DI builds extras from settings).

---

## 5. ACCEPTED_RISK / OWNER_DECISION (not “fixed by code alone”)

| ID | Status | Note |
| --- | --- | --- |
| RT-OIDC-BFF | ACCEPTED_RISK / OWNER | Routes remain 501; PKCE Phase 2.5 ≠ production BFF |
| RT-001/002/003 | OWNER_DECISION | Customer evidence blockers — checkpoint NO_GO |
| RT-NATIVE-DWG | OWNER_DECISION | ODA honesty only |
| RT-MEP-SYSTEM | OWNER_DECISION | Gap documented; fixture AABB ≠ MEP product |
| RT-TZ-90 | OWNER_DECISION | Never publish fixture P/R as TZ >90% |
| RT-BASELINE-N43 | ACCEPTED_RISK | Lag allowed until 2026-08-17 |
| RT-RUF100 | ACCEPTED_RISK | Deferred to 2026-08-25 |
| RT-N59-KEYS | ACCEPTED_RISK | Deferred to 2026-08-25 |
| RT-PYMU-PDF-AGPL | OWNER / LEGAL | Optional `pdf-agpl` extra; production image claims exclude it — **ТРЕБУЕТСЯ ЮРИДИЧЕСКАЯ ПРОВЕРКА** for deployment mixes |

---

## 6. NOT_REPRODUCED / HYPOTHESIS (Stage A)

| ID | Status | Why |
| --- | --- | --- |
| Cross-tenant report enumeration leak | HYPOTHESIS | Not exercised against live multi-tenant store |
| ZIP bomb / nested archive DoS | HYPOTHESIS | Limits exist in code; battery not run |
| DNS rebinding vs outbound pin | HYPOTHESIS | `outbound_url.py` has pinning; no Stage A network experiment |
| HITL multi-process CAS race | HYPOTHESIS | Unit coverage historically improved; concurrency stress not re-run |
| VLM changes `summary.passed` | NOT_REPRODUCED (spot) | Code comments + orchestrator contour separation assert advisory-only; full OFF/ON matrix **not** re-executed Stage A — mark **ТРЕБУЕТСЯ ПРОВЕРКА** before claiming closed |
| Frontend XSS on finding text | HYPOTHESIS | No browser exploit run Stage A |
| REGRESSION of closed P0 from 08–09.08 | NOT_REPRODUCED | No controlled mutation audit yet (Phase 19) |

---

## 7. REGRESSION watchlist (from diffs; not yet mutation-proven)

1. VLM rename may leave Kimi-labeled docs/telemetry — parity check pending.  
2. Baseline ancestor soft-skip can hide stale publishable evidence if abused.  
3. Fixture clash precision=1.0 may be misread as product accuracy in downstream slides.  
4. Signing ratio `0.03` over inspect window of 50 can stay green while most history is unsigned.  
5. CV P0–P4 language in plans vs README — claims lint must stay on.

---

## 8. Stage A stop board (for owner)

### Actual SHA
`a818bfe2eeeaa2cf2b5c98cdd331887e519aacf7`

### Commits in window
158 (`--all`) / 134 (first-parent `main`)

### Changed files
641 unique paths (see `_window_unique_files_2026-08-11.txt`)

### VERIFIED P0
**None confirmed in Stage A spot checks.**

### VERIFIED P1
- RT-20260811-01 (VLM header override)  
- RT-20260811-02 (Yandex substring host gate)

### VERIFIED P2
- RT-20260811-03 (missing gate tests)  
- RT-20260811-04 (missing architecture import gate)  
- RT-20260811-06 (LLM Content-Type override)

### VERIFIED P3
- RT-20260811-05 (dirty benchmark evidence)

### NOT_REPRODUCED
- VLM flips `summary.passed` (spot negative; full matrix pending)  
- Known historical P0 returns (pending mutation audit)

### REGRESSION
- **None verified** yet (Phase 19 not started)

### Owner decisions required before Stage B prioritization
1. Confirm Stage B may patch P1 header + host-gate (recommended).  
2. Confirm OIDC remains 501 through freeze (expected).  
3. Confirm fixture clash/overlay wording stays non-publishable for >90%.  
4. Decide dirty IFC benchmark files: discard vs commit.  
5. Confirm N43 lag acceptable until 17.08.

---

## 9. Explicit non-claims

Stage A does **not** assert:

- production-ready OIDC BFF  
- native DWG  
- MEP system-aware clash  
- CV / VLM engineering understanding  
- customer accuracy / TZ >90%  
- closed-contour install completeness without clean-checkout Stage C  
- that prior `docs/audit/RED_TEAM_*.md` files are still true without re-proof

---

*End Stage A. Await owner confirmation before remediation (Stage B).*

---

## 10. Stage B status (2026-08-11, post-owner OK)

Remediation log: [`RED_TEAM_REMEDIATION_PLAN_2026-08-11.md`](RED_TEAM_REMEDIATION_PLAN_2026-08-11.md).

| ID | Stage B |
| --- | --- |
| RT-20260811-01 | **FIXED** (immutable VLM headers + tests) |
| RT-20260811-02 | **FIXED** (exact/suffix Yandex host gate) |
| RT-20260811-03 | **FIXED** (gate unit tests) |
| RT-20260811-04 | **FIXED** (architecture import gate test) |
| RT-20260811-06 | **FIXED** (LLM Content-Type forced) |
| RT-20260811-05 | open (owner: dirty benchmark files) |
