---
title: "Red Team Master Audit — Environment Snapshot"
date: 2026-08-08
phase: 0
status: snapshot
checkpoint: NO_GO
claim_boundary: engineering_evidence_only
---

# Red Team Master Audit — Snapshot (Phase 0)

**Audit ID:** RT-MASTER-2026-08-08  
**Scope:** Full-repo security + engineering readiness inventory (Phases 0–2). **No code fixes in this pass.**  
**Related:** Sprint 3 claims audit → [`audit/reports/SPRINT3_RED_TEAM_AUDIT_2026.md`](../../audit/reports/SPRINT3_RED_TEAM_AUDIT_2026.md)  
**Findings report:** [`RED_TEAM_REPORT_2026_08_08.md`](RED_TEAM_REPORT_2026_08_08.md)

---

## 1. Repository state

| Field | Value | Evidence |
|---|---|---|
| HEAD SHA | `adbf79c34e223acd66f474d074877b524ca5e22f` | `git rev-parse HEAD` |
| Branch | `main` | `git branch --show-current` |
| Tag (pilot) | `pilot-2026-pre` | git tags |
| Working tree | **dirty** (~42 changed/untracked paths) | `git status --short` |
| Remote | `https://github.com/KonkovDV/AeroBIM` | `git remote -v` |
| Last commit | 2026-08-06 — `fix(security): close white-hat residuals on advisory egress` | `git log -1` |

**Note:** Baseline artifact [`docs/evidence/runtime-baseline-latest.json`](../evidence/runtime-baseline-latest.json) records `working_tree_clean: false` at the same HEAD.

---

## 2. Runtime baseline (frozen vs live)

| Metric | Baseline JSON (2026-08-07) | Live probe (2026-08-08) |
|---|---|---|
| Backend tests collected | 1924 | **1926** (`pytest --collect-only`) |
| Backend src LOC | 58525 | not re-counted |
| Backend test LOC | 40180 | not re-counted |
| Python | 3.13.7 / CPython | 3.13.7 |
| Platform | Windows-11-10.0.26200 | confirmed |
| Lockfile SHA256 | `7401d81b…` | not re-hashed |
| Quality gates (ruff/mypy/pytest CI) | UNKNOWN in baseline | not re-run (audit read-only) |

**Claim boundary:** fixture `extraction_macro_f1=0.86` ≠ product accuracy. Checkpoint **NO_GO** until RT-001/002/003 customer evidence.

---

## 3. Checkpoint & blocker registry

| ID | Status | Summary |
|---|---|---|
| RT-001 | **OPEN** | Customer expertise ground truth / dual adjudication |
| RT-002 | **OPEN** | Customer pilot scope / signed evidence |
| RT-003 | **OPEN** | MEP federated clash delivery |
| LIC-001 | **ENGINEERING_CLEARED_FOR_CORE_PDF** | PyMuPDF optional `pdf-agpl`; core path pypdfium2 |
| POST-05 OIDC BFF | **DESIGNED / NOT_IMPLEMENTED** | `docs/architecture/_2026_07.md` |

SSOT: [`audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md) — **RT-BLOCKERS-001:** CLOSED table rows coexist with legacy BLOCKER prose below (doc hygiene, not runtime defect).

---

## 4. Security surface inventory

### 4.1 Outbound / SSRF

| Component | Path | Guard |
|---|---|---|
| SSRF guard + DNS pin | `backend/src/aerobim/core/security/outbound_url.py` | `assert_safe_outbound_url`, `safe_urlopen`, `safe_datastore_urlopen` |
| OIDC JWKS fetch | `backend/src/aerobim/infrastructure/security/oidc_token_validator.py` | SSRF guard + **bounded** JWKS read |
| Kimi advisory VLM | `backend/src/aerobim/infrastructure/adapters/kimi_k3_advisory_client.py` | SSRF + host allowlist + **bounded** read |
| OpenAI-compat LLM | `backend/src/aerobim/infrastructure/adapters/openai_compat_llm_provider.py` | SSRF + **bounded** read |
| LLM extraction (new) | `backend/src/aerobim/infrastructure/adapters/llm_extraction_adapters.py` | SSRF via `safe_urlopen`; **unbounded** `response.read()` |
| BCF HTTP client | `backend/src/aerobim/infrastructure/adapters/http_bcf_api_client.py` | SSRF via `safe_urlopen`; **unbounded** read |
| S3 / object GET | `backend/src/aerobim/infrastructure/adapters/s3_object_store.py` | endpoint SSRF + `read_stream_capped` |
| Tests | `backend/tests/test_outbound_guard_invariant.py`, `test_rt_remediation_post.py` | invariant + regression |

### 4.2 Upload / archive limits

| Component | Path | Notes |
|---|---|---|
| ZIP bomb guard | `backend/src/aerobim/core/security/zip_limits.py` | Central-directory metadata inspect; path traversal blocked |
| XML caps | `backend/src/aerobim/core/security/xml_limits.py` | ElementTree + defusedxml |
| Object stream caps | `backend/src/aerobim/core/security/object_limits.py` | `read_stream_capped` for storage |

### 4.3 Auth / tenancy

| Component | Path |
|---|---|
| Bearer / OIDC | `backend/src/aerobim/infrastructure/security/oidc_token_validator.py` |
| Object ACL | `backend/src/aerobim/domain/object_acl.py` |
| Tenant binding | settings + bootstrap |

### 4.4 HITL / audit trail

| Component | Path | Notes |
|---|---|---|
| Review event store | `backend/src/aerobim/infrastructure/adapters/filesystem_review_event_store.py` | O_EXCL file lock on append; idempotency + sequence |
| Audit store | `backend/src/aerobim/infrastructure/adapters/filesystem_audit_store.py` | report lifecycle |

### 4.5 HTTP API error paths

| Route file | Pattern |
|---|---|
| `backend/src/aerobim/presentation/http/routes/analyze.py` | `HTTPException(400, detail=str(exc))` on `ValueError` |

### 4.6 Rate limiting

**No application-level rate-limit middleware found** (grep: only offline-bundle mirror checklist comment).

---

## 5. Offline / closed-contour (И1)

| Track | Status | Evidence |
|---|---|---|
| Docker image offline bundle | **VERIFIED** | `aerobim.tools.offline_bundle` build/verify/smoke; CI `offline-bundle-smoke` |
| Bare-metal wheelhouse | **DEFERRED** | `wheelhouse` subcommand exit 2 + `wheelhouse-DEFERRED.json` |
| Docs | **VERIFIED** | [`docs/offline-deployment-2026.md`](../offline-deployment-2026.md) |

Owner note (2026-08-01): Docker offline sufficient; bare-metal not required until owner reverses.

---

## 6. Sprint 3 engineering deltas (uncommitted working tree)

High-signal paths in dirty tree (not exhaustive):

| Area | Paths |
|---|---|
| IFC benchmark stability | `backend/src/aerobim/tools/benchmark_project_package.py`, `audit/evidence/ifc-release-benchmark-2026-08.json` |
| LLM extraction port | `backend/src/aerobim/domain/llm_extraction.py`, `llm_extraction_adapters.py`, `evaluate_llm_extraction.py` |
| IDS upstream edge 0017 | `samples/ids/buildingsmart-testcases/KNOWN_UPSTREAM_EDGES.json`, `test_ids_case_0017_upstream_edge.py` |
| Schema suite packs | `samples/benchmarks/project-package-ifc*.json` |
| Evidence / GTM docs | `docs/evidence/*`, `docs/gtm/*` |

**External (not in git):** Mumbai Building Permit corpus → `C:\plans\aerobim-internal-data\raw\expertise\mumbai-building-permit\` (666 PDFs, `claim_level=foreign_acc_analog`, does **not** close RT-001).

---

## 7. Test inventory (security-relevant)

| Suite | File | Covers |
|---|---|---|
| Outbound invariant | `test_outbound_guard_invariant.py` | no raw `urlopen` in adapters |
| Post-remediation | `test_rt_remediation_post.py` | SSRF, ZIP, ACL, signoff |
| RT full 2026-07-20 | `test_rt_full_remediation_2026_07_20.py` | CGNAT, datastore SSRF |
| Dependency license | `test_dependency_license_gate.py`, `test_dependency_sbom_gate.py` | LIC-001 |
| Kimi advisory | `test_kimi_k3_advisory.py` | SSRF, response cap, NaN JSON |
| Red team signoff | `test_red_team_signoff_remediation.py` | advisory cannot flip pass |
| Architecture baseline | `test_export_runtime_baseline.py` | README / inventory drift |

**Gap:** no concurrent HITL append stress test; no decimal-IP SSRF regression test.

---

## 8. Hypotheses queued for Phase 1–2 (see report)

| Hypothesis ID | Topic |
|---|---|
| RT-SSRF-001 | Non-dotted IP hostname encodings (decimal/hex) |
| RT-ZIP-001 | ZIP metadata-only inspect vs streaming extraction |
| RT-EGRESS-001 | Unbounded outbound response bodies |
| RT-HITL-001 | HITL append TOCTOU (read outside lock) |
| RT-ERR-001 | ValueError text echoed to clients |
| RT-RATE-001 | Missing app rate limits |
| RT-UPLOAD-001 | Multipart buffering vs quota order |
| RT-OIDC-001 | JWKS alg / `oct` key confusion |
| RT-DOC-001 | `CRITICAL_BLOCKERS.md` stale BLOCKER sections |
| RT-ARCH-001 | Layer import gate / frontend ESLint |
| RT-SECRET-001 | Git history secrets scan |

---

## 9. Audit method & stop rule

1. **Phase 0 (this doc):** snapshot + inventory.  
2. **Phase 1–2:** live probes + code review → [`RED_TEAM_REPORT_2026_08_08.md`](RED_TEAM_REPORT_2026_08_08.md).  
3. **Stop:** no remediation commits until owner confirms P0/P1 registry and И1 scope.

**Auditor:** IDE agent (Composer), 2026-08-08.  
**External-evidence skip:** local repo-fact + live Python probes only; no vendor doc delta required for snapshot.
