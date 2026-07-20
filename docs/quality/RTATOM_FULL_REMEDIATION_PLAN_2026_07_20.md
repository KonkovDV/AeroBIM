# AeroBIM RTATOM — Atomic Red Team & Remediation Plan

**Freeze SHA:** `9b610e9` (2026-07-20 RTATOM A1/A2 landing; plan baseline `f1742bc`)  
**Depth:** seams · chains · blind spots · vectors · every `/v1` route · every `summary.passed` writer · every I/O boundary · DI · frontend · CI/claims  
**Checkpoint:** **NO_GO** (RT-001 / RT-002 / RT-003)  
**Supersedes for engineering sequencing:** extends `docs/quality/RT26_FULL_REMEDIATION_PLAN_2026_07_20.md` with atomic findings  

### Status (2026-07-20)

| Wave | Status | Notes |
|---|---|---|
| A0 | DONE | Plan published; baseline `f1742bc` |
| **A1** | **DONE** | H01 I05 G01 H04 H05 G04 G11 I01 I02 I03 I04 G03 + soft SPF honesty — landed `9b610e9` |
| **A2** | **PARTIAL→A2.5 CLOSED*** | A2.1–A2.4 + A2.6 landed `9b610e9`; A2.5 hashed locks + CI/Docker `--require-hashes` (pip/uv bootstrap residual). **Deferred:** full OIDC BFF (POST-05); ADS residual; broader S3 stream OOM |
| **A3** | **PARTIAL** | CSP/nosniff; NFKC; JWKS host bind; ZIP stream inspect; TOCTOU on report get + IFC/drawing FileResponse. Residual: POST-05 design, ElementTree caps |
| A4 | PENDING | Customer RT-001/002/003 evidence only |

### External anchors (Jul 2026)
| Domain | Anchor |
|---|---|
| API IDOR/BOLA | OWASP API Security Top 10 **API1:2023** — object ownership on every ID; prefer query-level tenant filter |
| JWT/OIDC | RFC 8725 / oauth-rfc8725bis; OWASP ASVS v5 V10 |
| SSRF | OWASP A10 — DNS pin between check and connect |
| Supply chain | SLSA · `pip --require-hashes` · image digest pins |
| Untrusted PDF | Process isolation + timeout (PyMuPDF CVE class 2026; lock `1.28.0` patched for CVE-2026-3029, isolation still required) |
| Workflow integrity | Server SSOT for HITL state; never trust client previous_state |

---

## 1. Atomic coverage map

### 1.1 HTTP surface (22 routes)

| Class | Count | Status |
|---|---|---|
| `/v1/*` with bearer `Depends` | **21/21** | Auth present |
| Public | 1 (`GET /health`) | Intentional |
| Report/job ACL assert | 12 | Hold under ACL-on |
| Path-jail only (upload/validate/analyze) | 5 | Tenant jail when ACL-on |
| **Atomic gaps** | IFC/drawing **FS** branch skips tenant prefix; list loads-all-then-filters; HITL body forge; soft ACL-off global list | See H01–H05 |

### 1.2 `summary.passed` writers (closed set)

| Writer | Path |
|---|---|
| Package analyze | `EvidenceAssembler` ← `build_signoff_policy` + host clash flip |
| Validate IFC | `ValidateIfcAgainstIdsUseCase` ← settings policy |
| Evidence tool | Manifest `enforced`; HTML still **ambient** (G04) |
| Non-writers (hold) | DeterminismGate, agent, RASE, HITL, IDS assist stubs |

### 1.3 Outbound / storage

| Channel | Guard | Blind spot |
|---|---|---|
| JWKS / BCF / bSI | `safe_urlopen` pin | Hold |
| S3 boto3 | Boot assert only | **I01** rebind |
| Redis / Postgres URLs | Env only | **I09/I10** |
| Upload FS | Quarantine + tenant prefix | Promote race **I13**; ADS **I04** |
| Report JSON | Atomic commit | No hash verify on get **G11** |
| PyMuPDF | In-process | **I03** |
| ZIP upload | Inspect-only | OOM **I08**; BCF consumer **I14** |

---

## 2. Findings ranked (atomic)

### P0 — CRITICAL / HIGH (Wave A1, 2–4 days)

| ID | Seam | Attack chain (atomic) | 2026 fix |
|---|---|---|---|
| **RTATOM-H01** | IFC/drawing **FS** resolve | Own report ACL OK → poison `ifc_path` / planted path under `storage_dir` but **outside** `tenants/{caller}/` → `GET .../source/ifc` serves peer bytes (object-key branch has assert; FS branch does not) | `assert_path_under_tenant_prefix` on **every** FS artifact read; OWASP API1 ownership in data path |
| **RTATOM-I05** | `safe_storage_token` | `Tenant/A` and `Tenant_A` both map to `Tenant_A` → shared prefix → ACL merge | Collision-resistant encoding (hash or escape `/\_`) |
| **RTATOM-G01/D02** | Host ≠ policy | `Settings(profile=production, clash_affects_pass=False)` → WARNING clashes → `passed=true` | Flip hard clash **only** from `policy.clash_affects_pass` |
| **RTATOM-H04/I06** | HITL SSOT | Client `previous_state` forges transition | Derive state from event store |
| **RTATOM-H05/I07** | Norm-pack forge | Client `proposed_by` + `customer_approved` | Bind `principal.subject`; RBAC approve |
| **RTATOM-G04** | Evidence dual-truth | HTML ambient PASSED vs manifest enforced FAIL | Render from enforced only |
| **RTATOM-G11** | Report integrity | Edit `{id}.json` `"passed":true` → API green | Hash in commit manifest; verify on get |
| **RTATOM-I01** | S3 SSRF | boto3 re-resolves after boot | Pin/allowlist endpoint |
| **RTATOM-I02/I03** | Quota / PDF | Corrupt quota→0; PyMuPDF hang | Fail-closed quota; subprocess PDF |
| **RTATOM-G03** | Cancel race | Job CANCELLED, report PASS remains | Tombstone/discard |
| **RTATOM-F01/F07** | FE trust | No BFF; WASM IFC 1GiB DoS | BFF epic; worker+caps |

### P1 — MEDIUM (Wave A2, 3–5 days)

| ID | Theme | Fix |
|---|---|---|
| H02/H03 | Soft ACL-off list/path IDOR | Always tenant-filter list; ACL-on for networked soft |
| G02/G05/G06/G07/G08 | Soft Shared-gate / cross-doc WARNING / SPF OK / openrebar advisory / soft validate | Stamp non-authoritative; hard force ERROR/enforced |
| I04/I08/I11/I13–I21 | ADS, ZIP OOM, reserve rollback, symlink TOCTOU, BCF ZIP, corrupt stores, PG fallback, `.txt` IFC, bSI filename, IFC cache, quotas unset, Redis scan | As prior RT26 R2 + BCF `inspect_zip` |
| D01/D05/D08 | Soft Settings(); Unconfigured≠delivered; enterprise fallback | Constructor gates; claim ban; fail-closed URLs |
| C01/C02/C07 | Floating pip/uv/Playwright; hashless locks; fixture F1 release | Pin + hashes; fixture-only label |
| F02–F06/F08/F10 | VITE bearer; proxy overwrite; preview MIME; empty prod base | Proxy-only; Blob MIME; build fail |

### P2 — LOW / hygiene (Wave A3)

Health shape; CORS `*`; JWKS↔issuer; NFKC; ElementTree caps; clash temp jail; README token counts; runner pin; CSP/nosniff; demo stamps; orphan DI tokens docs.

### Out of engineering scope (Wave A4)

RT-001 · RT-002 · RT-003 · POST-05 full BFF (tracked epic).

---

## 3. Remediation plan (waves)

### Wave A0 — Freeze & inventory (0.5 d)
1. Publish this plan; freeze `f1742bc`.
2. Route inventory test: every `/v1` has auth (already 21/21) + **artifact FS reads call tenant prefix**.
3. `summary.passed` writer allowlist test (only EvidenceAssembler + Validate UC).

### Wave A1 — Atomic integrity (must before next pilot)
| Step | IDs | Acceptance |
|---|---|---|
| A1.1 | H01 | FS IFC + drawing resolve assert tenant prefix; cross-tenant path → 404 |
| A1.2 | I05 | Distinct tenants with `/` vs `_` never share prefix |
| A1.3 | G01/D02 | Custom production Settings cannot green hard clashes |
| A1.4 | H04/I06 | HITL transition ignores forged previous_state |
| A1.5 | H05/I07 | Norm-pack actor=subject; approve role-gated |
| A1.6 | G04 | Evidence HTML/logs use enforced pass only |
| A1.7 | G11 | Report get verifies content hash vs commit |
| A1.8 | I01–I03, G03 | S3 pin; quota fail-closed; PDF subprocess; cancel tombstone |

**Exit:** new `tests/test_rtatom_*.py`; pytest green; no dual-truth HTML.

### Wave A2 — BOLA depth + abuse + supply chain
| Step | Work | Anchor |
|---|---|---|
| A2.1 | List reports: DB/FS query **scoped by tenant** (not load-all-filter) | API1 BOLA |
| A2.2 | Soft ACL / validate / cross-doc / SPF / openrebar honesty | Claim boundary |
| A2.3 | Stream ZIP/S3; ADS; BCF inspect; reserve rollback; bake quotas; atomic jobs | DoS/tenancy |
| A2.4 | Redis/DB URL gate; PG fail-closed; corrupt report/index fail-closed | Config SSRF |
| A2.5 | `--require-hashes`; pin pip/uv/Playwright; fixture release labels | SLSA 2026 |
| A2.6 | FE: remove VITE bearer path; Blob MIME; WASM caps | Browser trust |

### Wave A3 — Hygiene + POST-05 design
CSP/nosniff; health; CORS; JWKS host; NFKC; SECURITY/README sync; BFF design spike.

### Wave A4 — Customer blockers
RT-001/002/003 evidence only.

---

## 4. Priority matrix

```
Impact ↑
 CRITICAL│ H01 I05 G11          │  RT-001/002/003
 HIGH    │ G01 H04 H05 G04 I01  │  F01 POST-05
         │ I02 I03 G03 F07      │
 MED     │ soft IDOR · ZIP · CI │  hashes · BFF
 LOW     │ hygiene              │
         └──────────────────────┴──────────────→ Effort
```

---

## 5. Verification rails

| Gate | Proof |
|---|---|
| Route auth | Static inventory: 21/21 bearer |
| BOLA FS | Two-tenant fixture: poison `ifc_path` → 404 |
| Token collision | `A/B` vs `A_B` distinct prefixes |
| Policy parity | Custom Settings production cannot soft-clash-pass |
| HITL | Client previous_state mismatch → 400 |
| Evidence | HTML `summary.passed` == enforced |
| Report hash | Tampered JSON → 409/404 |
| Supply chain | CI `--require-hashes` (after A2.5) |

---

## 6. Method

Four parallel atomic passes on HEAD `f1742bc`:
1. HTTP/ACL/BOLA — every route  
2. Shared-gate chains — every `passed` writer  
3. I/O/SSRF/races — every outbound/FS/ZIP/PDF/DB  
4. DI/frontend/CI claims  

Plus independent verification of **H01** (FS IFC without tenant prefix) and **I05** (`safe_storage_token` collision).

**Code not changed in this pass** — audit + plan only.
