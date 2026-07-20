# AeroBIM RT26 — Full Codebase Red Team Audit & Remediation Plan

**Freeze SHA:** `f1742bc` (2026-07-20)  
**Mode:** adversarial re-audit after RT-FULL P0/P1 (`73e8932`)  
**Checkpoint:** **NO_GO** (RT-001 / RT-002 / RT-003 — customer evidence, not code)  
**External anchors (Jul 2026):** RFC 8725 / oauth-rfc8725bis JWT BCP; OWASP ASVS v5 OAuth/OIDC V10; OWASP A10 SSRF DNS-pin guidance; SLSA + `pip --require-hashes` + image digest pins; PyMuPDF CVE-2026-3029 class (sandbox/subprocess for untrusted PDF — lock has `pymupdf==1.28.0`, patched for that CVE, isolation still required)

---

## 1. Executive verdict

| Layer | Assessment |
|---|---|
| Production `from_env` + pilot/production Shared-gate | **Largely sound** after RT-FULL |
| Auth boot / JWKS pin / kid / tenant claim / compose loopback / Docker digest | **Hold** |
| Residual HIGH | HITL state/approval integrity; clash flag desync on custom Settings; evidence HTML dual-truth; PyMuPDF process isolation; S3 boto3 pin |
| Customer blockers | **Correctly open** |

Prior RT-FULL closed the validate/ifc false-PASS, OIDC kid/tenant, DNS pin, CGNAT, Content-Disposition, quota lock, docs-off, prod loopback, etc. This pass finds **new integrity gaps** and ranks remaining work against 2026 practice.

---

## 2. Closed since RT-FULL (do not reopen)

| Prior ID | Control that holds |
|---|---|
| D01 validate/ifc policy | Settings-wired `SignOffCapabilityPolicy` |
| A02/A03 OIDC kid + tenant | Reject missing kid; no `api_tenant_id` fallback |
| A01/B01/B04 SSRF | Resolve-once + IP dial + Host/SNI; non-global/CGNAT blocked |
| A04/C01 compose + Docker | `127.0.0.1:8080`; `python:3.12-slim@sha256:…` |
| A07/A13/A15/B05–B07/B09–B10 | Docs off; sanitized disposition; MIME allowlist; object-key tenant assert; quota `reserve`; drawing symlink reject |
| D03 hard profiles | Weakening overrides ignored for pilot/production |
| C03/C05/C06 CI | Dual lock drift; dispatch path/iteration jail; academic least-privilege |

---

## 3. Open findings (post-remediation)

### 3.1 HIGH — fix in Wave R1 (1–3 days)

| ID | Finding | Practice anchor | Acceptance |
|---|---|---|---|
| **RT26-A01** | HITL `previous_state` is client-supplied → forged transitions | ASVS access-control: server is SSOT for workflow state | Derive current state from review-event store; reject client mismatch |
| **RT26-A02** | Norm-pack `proposed_by` / `customer_approved` client-forgeable | ASVS V10: identity from `iss`+`sub`; RBAC on approve | Bind actor to `principal.subject`; require role/scope for `customer_approved` |
| **RT26-D01** | Host `_clash_affects_pass` can disagree with hard policy on custom `Settings(profile=production, clash_affects_pass=False)` | Fail-closed consistency | Drive hard-clash flip from `policy.clash_affects_pass` only |
| **RT26-C01** | Evidence HTML shows ambient `summary.passed` while manifest uses enforced production PASS | Claim honesty / dual-truth ban | Render HTML + logs from enforced policy (or stamp ambient as non-authoritative badge only) |
| **RT26-B03** | Untrusted PDF → in-process PyMuPDF (DoS/hang/residual memory risk) | 2026 PDF practice: subprocess timeout + sandbox | Subprocess renderer with hard timeout/memory; optional disable PDF raster in pilot |
| **RT26-B02** | S3/boto3 still dials hostname after boot check | SSRF pin end-to-end | Allowlist endpoints or pin via custom endpoint resolver |

### 3.2 MEDIUM — Wave R2 (3–5 days)

| ID | Finding | Fix |
|---|---|---|
| RT26-A03/A09/A10 | OIDC without `sub` falls back to client actor; no scope/RBAC; shared bearer as human identity | Require `sub`; map scopes to read vs HITL; bearer = machine-only |
| RT26-A04 | `AEROBIM_CORS_ORIGINS=*` accepted | Reject `*` outside explicit break-glass |
| RT26-A06/A07/A08 | Soft env ACL-off; anon shared identity; OpenAPI in dev | ACL-on for multi-user; ephemeral anon; flag-gate docs |
| RT26-B08/B20–B24 | Full-file ZIP OOM; corrupt quota reset; no reserve rollback; flat `drawing-assets/`; unset prod quotas; job TOCTOU | Stream; fail-closed quota; compensate; tenant-prefix previews; bake quotas; atomic job create |
| RT26-B11/B12 | `.txt` allows IFC; bSI multipart raw filename | Tighten kinds; sanitize multipart name |
| RT26-D03/D05 | Cancel leaves durable PASS; job concurrency race | Tombstone/discard; atomic semaphore |
| RT26-D06 | Soft SPF → `ifc_schema=OK` | Soft → `NOT_VERIFIED` |
| RT26-C02/C03 | Hashless locks; floating pip; unpinned Playwright | `uv pip compile --generate-hashes`; pin pip/uv; lock Playwright |
| RT26-C04/C08/C09 | Stale README metrics; shared-bearer overclaim; fixture SLA naming | Sync metrics; narrow claims; `fixture-sla-*` artifacts |

### 3.3 LOW / INFO — Wave R3

Health shape; debug auto-CORS; JWKS↔issuer host bind; Vite overwrite Authorization; NTFS `:`; ZIP Unicode; HTML CSP/nosniff; local `presign_get`; compose CORS `127.0.0.1`; demo tool footguns.

### 3.4 Correctly open (out of engineering scope)

| ID | Why |
|---|---|
| RT-001 | Customer accuracy corpus |
| RT-002 | Approved customer norms |
| RT-003 | Product MEP system-aware clash |
| POST-05 | Production BFF / OIDC browser flow |

---

## 4. Remediation plan (ordered)

### Wave R0 — Claim & scope freeze (0.5 day)
1. Publish this plan + freeze SHA on `CRITICAL_BLOCKERS` residual table.
2. Mark RT-POST-09 remains **PARTIAL** until hashes land.
3. Do **not** claim GO / multi-tenant human SSO / PyMuPDF-safe until R1–R2 done.

### Wave R1 — Integrity P0 (must ship before next pilot demo)
| Step | Work | Owner surface | Tests |
|---|---|---|---|
| R1.1 | HITL state SSOT from event store (RT26-A01) | `api.py`, HITL domain | Transition forge rejected |
| R1.2 | Norm-pack actor/approve bind + role gate (RT26-A02) | `api.py`, `apply_norm_rule_hitl_event.py` | Client `proposed_by` ignored |
| R1.3 | Clash flip from policy only (RT26-D01) | `analyze_orchestrators.py` | Custom Settings production cannot soft-flip |
| R1.4 | Evidence HTML/logs from enforced policy (RT26-C01) | `export_evidence_bundle.py` | HTML matches `summary_passed_enforced` |
| R1.5 | PDF render subprocess + timeout; pin/check PyMuPDF (RT26-B03) | raster + audit_store preview | Hang/kill covered; optional disable flag |
| R1.6 | S3 endpoint pin/allowlist (RT26-B02) | `s3_object_store.py` | Custom endpoint cannot rebind |

**Exit:** focused pytest + RT26 regression file green; no dual-truth in evidence HTML.

### Wave R2 — AuthZ depth + abuse/DoS + supply chain
| Step | Work | Practice |
|---|---|---|
| R2.1 | OIDC `sub` required; scopes/roles (`read` / `hitl` / `approve`) | ASVS V10 |
| R2.2 | Reject CORS `*`; tighten soft-env ACL/docs | Browser isolation |
| R2.3 | Stream ZIP/S3; quota fail-closed + rollback; bake pilot quotas | Resource abuse |
| R2.4 | Tenant-prefix drawing-assets; atomic job limit | Tenancy + concurrency |
| R2.5 | Cancel-after-analyze tombstone | Consistency |
| R2.6 | Soft schema → NOT_VERIFIED; `.txt` text-only | Honesty |
| R2.7 | `--generate-hashes` + `--require-hashes`; pin pip/uv; Playwright in lock | SLSA/CI 2026 |
| R2.8 | README/metrics sync; fixture SLA artifact names | Claim hygiene |

**Exit:** CI installs with require-hashes; RBAC smoke tests; quota/job races covered.

### Wave R3 — Hygiene + POST-05 track
| Step | Work |
|---|---|
| R3.1 | Health `{status}`, CSP/nosniff, JWKS host=issuer, debug CORS |
| R3.2 | Design/ship BFF or OIDC code flow (POST-05) — separate epic |
| R3.3 | Optional SLSA provenance job (generator + verify) when publishing images |

### Wave R4 — Customer blockers (parallel, non-code)
RT-001 corpus · RT-002 norms · RT-003 MEP delivery — keep checkpoint **NO_GO** until evidence exists.

---

## 5. Priority matrix

```
Impact ↑
  HIGH │ A01 A02 D01 C01 B03 B02     │  RT-001/002/003
       │ (R1 code)                   │  (customer)
  MED  │ A03–A10 B08 B20–B24 D03–D06 │  C02 C03 C08 POST-05
       │ C04 C09                     │
  LOW  │ A11–A16 B11–B16 hygiene     │
       └─────────────────────────────┴──────────────────→ Effort
              Small/medium                    Large/epic
```

---

## 6. Non-goals for R1–R2

- Closing RT-001/002/003 by inventing customer data
- Full multi-IdP federation
- Claiming production-ready / >90% accuracy
- Reverting fail-closed pilot gates to get green Shared-gate

---

## 7. Verification rails

| Gate | Command / artifact |
|---|---|
| Unit/integration | `pytest tests -q` (+ new `test_rt26_*.py`) |
| Frontend | `npm test` + `npm run build` |
| Supply chain | lock drift + `--require-hashes` install (after R2.7) |
| Evidence honesty | bundle HTML `summary.passed` == enforced |
| Claim freeze | `CRITICAL_BLOCKERS.md` + Claims Lock stay NO_GO |

---

## 8. Method

Three parallel hostile passes on HEAD `f1742bc` (auth, upload/SSRF, domain/CI/claims) + independent verification of NEW highs (HITL `previous_state`, clash host desync, evidence HTML ambient status) + Jul 2026 external anchors (RFC 8725, ASVS V10, SSRF pin, SLSA/hashes, PyMuPDF CVE class).
