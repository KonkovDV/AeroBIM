---
title: "Red Team Master Audit — Findings Report"
date: 2026-08-08
phase: "1-2"
status: superseded
checkpoint: NO_GO
remediation: closed_engineering
superseded_by: docs/audit/RED_TEAM_CLOSURE_2026_08_08.md
---

# Red Team Master Audit — Findings Report (Phases 1–2)

> **Historical:** Pre-remediation findings registry. Engineering closure: [`RED_TEAM_CLOSURE_2026_08_08.md`](RED_TEAM_CLOSURE_2026_08_08.md); Waves 3–5: `RED_TEAM_WAVE*_CLOSURE_2026_08_08.md`.


**Audit ID:** RT-MASTER-2026-08-08  
**Snapshot:** [`RED_TEAM_SNAPSHOT_2026_08_08.md`](RED_TEAM_SNAPSHOT_2026_08_08.md)  
**Sprint 3 claims (separate):** [`audit/reports/SPRINT3_RED_TEAM_AUDIT_2026.md`](../../audit/reports/SPRINT3_RED_TEAM_AUDIT_2026.md)

**Verdict:** Engineering security posture is **materially improved** since July 2026 remediation waves. **Post-remediation closure:** [`RED_TEAM_CLOSURE_2026_08_08.md`](RED_TEAM_CLOSURE_2026_08_08.md) (2026-08-08).

**Original verdict (pre-fix):** New Sprint 3 adapters reintroduced egress-read gaps; SSRF defense-in-depth had a non-canonical IP hostname hole. **Remediated in Wave 1–2.** Customer checkpoint blockers remain open.

---

## 1. Executive summary

| Class | Count |
|---|---|
| VERIFIED (actionable) | 4 |
| PARTIAL (defense-in-depth / doc) | 6 |
| NOT_VULNERABLE / FALSE_POSITIVE | 2 |
| HYPOTHESIS (not reproduced) | 4 |
| Customer checkpoint (unchanged) | 3 (RT-001/002/003) |

**Recommended owner gate:** approve P1 remediation bundle (SSRF normalization + egress caps on new adapters + HITL lock scope) before И1 bare-metal offline investment.

---

## 2. Finding registry

Severity: **P0** = exploitable in default production config · **P1** = defense-in-depth / new-surface gap · **P2** = hygiene / ops · **CHK** = customer checkpoint (not eng-fix).

| ID | Severity | Status | Title | Production impact |
|---|---|---|---|---|
| RT-SSRF-001 | P1 | **PARTIAL** | Non-dotted IP hostnames bypass literal-IP SSRF check | Low via `safe_urlopen` (DNS fails); **Medium** on `resolve_dns=False` paths |
| RT-SSRF-002 | — | **NOT_VULNERABLE** | IPv6-mapped / NAT64 loopback literals | Blocked |
| RT-EGRESS-001 | P1 | **VERIFIED** | Unbounded `response.read()` on new LLM extraction + BCF client | DoS / memory pressure if upstream malicious |
| RT-ZIP-001 | P1 | **PARTIAL** | ZIP limits use central-directory sizes only | Theoretical zip bomb if metadata lies |
| RT-ERR-001 | P2 | **VERIFIED** | `str(exc)` returned in HTTP 400 on analyze routes | Information disclosure |
| RT-RATE-001 | P2 | **VERIFIED** | No application rate limiting | Abuse / cost amplification at edge |
| RT-HITL-001 | P2 | **PARTIAL** | HITL idempotency/sequence computed outside exclusive lock | Race under concurrent writers |
| RT-OFFLINE-001 | CHK | **CLOSED** | И1 Docker image-track verified (`closed-contour --smoke`) | — |
| RT-BLOCKERS-001 | P2 | **VERIFIED** | `CRITICAL_BLOCKERS.md` CLOSED rows vs stale BLOCKER prose | Operator confusion |
| RT-LIC-001 | — | **NOT_VULNERABLE** | PyMuPDF AGPL gated to optional extra | Engineering cleared |
| RT-UPLOAD-001 | — | **HYPOTHESIS** | Multipart buffering before quota enforcement | Not reproduced |
| RT-OIDC-001 | — | **HYPOTHESIS** | JWKS `oct` / alg confusion | JWKS bounded + PyJWT path not fuzzed |
| RT-ARCH-001 | — | **HYPOTHESIS** | Frontend ESLint / import-layer gate | Not run in this pass |
| RT-SECRET-001 | — | **HYPOTHESIS** | Git history secrets scan | Not run in this pass |
| RT-001 | CHK | **OPEN** | Customer expertise GT | Business |
| RT-002 | CHK | **OPEN** | Customer pilot evidence | Business |
| RT-003 | CHK | **OPEN** | MEP federated clash | Product |

---

## 3. Verified findings (detail)

### RT-SSRF-001 — Non-dotted IP hostname encodings (P1, PARTIAL)

**Claim:** Decimal / hex IP literals bypass `_is_blocked_ip` because `ipaddress.ip_address()` rejects them as hostnames.

**Evidence (live probe, 2026-08-08):**

```
assert_safe_outbound_url(..., resolve_dns=False):
  http://2130706433/  → ALLOWED
  http://0x7f000001/  → ALLOWED
  http://127.0.0.1/   → BLOCKED

assert_safe_outbound_url(..., resolve_dns=True) [production default for safe_urlopen]:
  http://2130706433/  → BLOCKED (DNS resolution failed)
  http://0x7f000001/  → BLOCKED (DNS resolution failed)
```

**Code:** `outbound_url.py` lines 192–207 — literal IP branch uses `ipaddress.ip_address(host)`; non-parseable hostnames fall through to DNS.

**Production `safe_urlopen`:** always `resolve_dns=True` (line 255) → decimal hostnames **fail closed** on DNS in tested environment.

**Residual risk:** `assert_safe_outbound_url(..., resolve_dns=False)` used in tests and `safe_datastore_urlopen` datastore path. Any future caller passing attacker-controlled URL with `resolve_dns=False` could reach loopback if the HTTP stack resolves decimal forms differently than `ipaddress`.

**Remediation (awaiting owner):**
1. Reject hostnames matching `^\d+$` or `^0x[0-9a-f]+$` before DNS.
2. Optional: normalize via `socket.inet_pton` / explicit decimal-to-dotted conversion then re-check `_is_blocked_ip`.
3. Add regression tests in `test_rt_remediation_post.py`.

---

### RT-SSRF-002 — IPv6-mapped literals (NOT_VULNERABLE)

**Probe:** `::ffff:127.0.0.1`, `64:ff9b::127.0.0.1`, `2002:7f00:1::` → **BLOCKED** by `_is_blocked_ip`.

**Conclusion:** Prior NAT64/6to4 bypass hypothesis **not reproduced** on current code.

---

### RT-EGRESS-001 — Unbounded outbound response reads (P1, VERIFIED)

**Affected:**

| File | Line | Pattern |
|---|---|---|
| `llm_extraction_adapters.py` | ~157 | `response.read().decode("utf-8")` |
| `http_bcf_api_client.py` | ~132 | `response.read().decode("utf-8")` |

**Contrast (bounded):**

| Adapter | Cap |
|---|---|
| `kimi_k3_advisory_client.py` | `max_response_bytes` + `read(n+1)` |
| `openai_compat_llm_provider.py` | `_MAX_RESPONSE_BYTES` |
| `oidc_token_validator.py` | `_MAX_JWKS_BYTES` |

**Impact:** Trusted-but-compromised upstream or malicious BCF endpoint could cause large memory allocation. SSRF guard still applies; this is **egress volume**, not SSRF bypass.

**Remediation:** Apply same `read(cap+1)` pattern as Kimi/OIDC; unit test oversize rejection.

---

### RT-ZIP-001 — ZIP metadata-only inspection (P1, PARTIAL)

**Code:** `zip_limits.py` `_inspect_zipfile` sums `ZipInfo.file_size` from central directory without streaming member bodies during read.

**Existing mitigations:** path traversal rejected; member count / ratio / aggregate caps on metadata.

**Gap:** If central directory lies about `file_size`, actual `extract` could exceed budget. Extraction paths should call `inspect_zip_bytes` **before** `extractall` (verify call sites in upload pipeline).

**Remediation:** Add streaming extraction budget wrapper or document reliance on metadata + post-extract size assert.

---

### RT-ERR-001 — Exception text in HTTP 400 (P2, VERIFIED)

**Code:** `analyze.py` — `except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc))` on `/v1/validate/ifc` and `/v1/analyze/project-package`.

**Impact:** Validation messages may leak internal paths or rule IDs useful for reconnaissance. 404 paths correctly use generic `"file not found"`.

**Remediation:** Map to stable error codes; log `str(exc)` server-side only.

---

### RT-RATE-001 — No application rate limiting (P2, VERIFIED)

**Evidence:** No `slowapi`, middleware, or token-bucket in `backend/src`. Only mention in `offline_bundle.py` mirror checklist.

**Impact:** Authenticated abuse (large analyze jobs, upload spam) relies entirely on reverse proxy / infra limits.

**Owner decision:** Accept infra-level limiting vs implement per-tenant quotas in app.

---

### RT-HITL-001 — Review event append TOCTOU (P2, PARTIAL)

**Code:** `filesystem_review_event_store.py` `append()`:
1. Reads full event list **without lock** (lines 42–52).
2. Computes `sequence = len(existing) + 1`.
3. `_append_exclusive` only wraps the write.

**Impact:** Concurrent appends could duplicate sequence numbers or slip past idempotency checks under multi-worker deployment. Single-worker pilot may mask.

**Mitigations present:** O_EXCL lock; idempotency keys; `previous_state` tests exist.

**Gap:** No `ThreadPoolExecutor` concurrency test.

**Remediation:** Hold lock for read-modify-write or use atomic append with post-hoc sequence validation.

---

### RT-OFFLINE-001 — Bare-metal offline DEFERRED (CHK, VERIFIED)

**Evidence:** `offline_bundle.py` `wheelhouse` → exit 2; `docs/offline-deployment-2026.md` documents Docker-only VERIFIED path.

**И1 implication:** Closed-contour bare-metal install script + hashed wheelhouse **not shipped**. Owner previously accepted Docker-only.

---

### RT-BLOCKERS-001 — Blocker doc drift (P2, VERIFIED)

**Evidence:** `CRITICAL_BLOCKERS.md` — RT-004…007 marked **CLOSED** in tables while expanded sections below still use present-tense BLOCKER narrative.

**Impact:** Operators may mis-read open vs closed state.

**Remediation:** Doc-only — collapse or banner stale sections; point to Claims Lock SSOT.

---

### RT-LIC-001 — PyMuPDF license (NOT_VULNERABLE)

**Evidence:** `test_dependency_license_gate.py`, `test_dependency_sbom_gate.py`; PyMuPDF absent from runtime lock; optional `pdf-agpl` extra.

**Status:** Aligns with LIC-001 **ENGINEERING_CLEARED_FOR_CORE_PDF**.

---

## 4. Hypotheses not reproduced (this pass)

| ID | Notes |
|---|---|
| RT-UPLOAD-001 | Upload quota + Starlette multipart ordering not traced end-to-end |
| RT-OIDC-001 | JWKS fetch bounded; no fuzz test for `oct` keys / `none` alg |
| RT-ARCH-001 | `test_export_runtime_baseline.py` checks inventory; full arch import gate not executed |
| RT-SECRET-001 | No `gitleaks` / `trufflehog` run on history |

**Recommendation:** Run RT-SECRET-001 and RT-ARCH-001 in CI hygiene sprint (low cost).

---

## 5. Sprint 3 engineering evidence (informational)

Completed in working tree (see snapshot §6):

| Item | Result |
|---|---|
| IFC4 benchmark p95 | Stabilized: p95≈24 ms (was ~568 ms spike with n=5) |
| IDS case 0017 | Upstream IfcTester edge documented; 23/24 denominator policy |
| Mumbai corpus | Downloaded to internal store; `foreign_acc_analog`; RT-001 still open |
| LLM extraction adapters | New surface → triggers RT-EGRESS-001 |

---

## 6. Owner decisions required

| # | Decision | Options | Audit recommendation |
|---|---|---|---|
| D1 | И1 bare-metal offline | A) Keep Docker-only DEFERRED · B) Implement wheelhouse + install script | **A** unless customer mandates no-Docker |
| D2 | RT-SSRF-001 | A) Normalize/reject non-dotted IPs · B) Accept DNS-fail-closed only | **A** (cheap defense-in-depth) |
| D3 | RT-EGRESS-001 | A) Cap reads in new adapters · B) Defer | **A** before enabling LLM extraction in pilot |
| D4 | RT-RATE-001 | A) Infra-only · B) App middleware | **A** for pilot; **B** before public multi-tenant |
| D5 | RT-ERR-001 | A) Stable error codes · B) Accept verbose 400 in dev | **A** for production profile |
| D6 | RT-HITL-001 | A) Fix lock scope · B) Document single-worker assumption | **A** if multi-worker planned |

---

## 7. Proposed remediation plan (post-approval only)

**Wave 1 — P1 security (est. 1–2 sessions)**

1. RT-SSRF-001: hostname normalization + tests.
2. RT-EGRESS-001: cap `llm_extraction_adapters` + `http_bcf_api_client` reads.
3. RT-ZIP-001: audit extract call sites; add streaming budget if gap confirmed.

**Wave 2 — P2 hygiene**

4. RT-ERR-001: public error code map for analyze routes.
5. RT-HITL-001: lock scope fix + concurrency test.
6. RT-BLOCKERS-001: doc cleanup in `CRITICAL_BLOCKERS.md`.

**Wave 3 — И1 (only if D1=B)**

7. `offline_bundle wheelhouse` implementation, `docs/ops/`, clean-machine verify.

**Explicitly out of scope for eng remediation:** RT-001/002/003 customer evidence.

---

## 8. Verification matrix

| Finding | Method | Result |
|---|---|---|
| RT-SSRF-001 | Live Python probe on `assert_safe_outbound_url` | PARTIAL |
| RT-SSRF-002 | Live Python probe | NOT_VULNERABLE |
| RT-EGRESS-001 | `grep response.read()` + code review | VERIFIED |
| RT-ZIP-001 | Read `zip_limits.py` | PARTIAL |
| RT-ERR-001 | Read `analyze.py` | VERIFIED |
| RT-RATE-001 | Repo grep | VERIFIED |
| RT-HITL-001 | Read `filesystem_review_event_store.py` | PARTIAL |
| RT-OFFLINE-001 | Read `offline_bundle.py` + docs | VERIFIED |
| RT-BLOCKERS-001 | Read `CRITICAL_BLOCKERS.md` | VERIFIED |
| RT-LIC-001 | License gate tests (prior CI) | NOT_VULNERABLE |
| Pytest collect | `pytest --collect-only` | 1926 tests |

---

## 9. Stop statement

Per Red Team Master Audit charter: **Phases 0–2 complete. No remediation code committed.** Await owner confirmation on §6 decisions before Wave 1 implementation.

**Next agent action after approval:** implement Wave 1 items 1–2 (SSRF normalization + egress caps) with focused tests; re-run `test_rt_remediation_post.py` + new regression cases.
