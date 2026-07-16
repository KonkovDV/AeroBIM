# AeroBIM — Academic Deep Audit (End-to-End) — internal self-audit

**Date:** 2026-07-10  
**Object:** `c:\plans\AeroBIM`  
**Author relationship:** self (internal self-audit — not an independent/external audit)  
**Method:** Integrity scan + architecture/DI audit + security/correctness hunt + live pytest/extraction + standards check  
**Companion:** [`FULL_AUDIT_FACTCHECK_2026_07_10.md`](FULL_AUDIT_FACTCHECK_2026_07_10.md)  
**Prior:** `docs/archive/05-fact-check-audit.md` (2026-04-12), `docs/evidence/public-surface-factcheck-2026-05-21.md`

---

## 0. Epistemic frame (academic)

| Layer | Question | Method |
|-------|----------|--------|
| L0 Integrity | Are sources/data intact after crash? | Encoding, AST, JSON, IFC trailer, conflict markers |
| L1 Architecture | Does Clean Architecture hold? | Layer tests, import graph, DI inventory |
| L2 Correctness | Do validators tell the truth? | Code paths for silent skip / false pass |
| L3 Security | Is the deployment threat model sound? | Auth defaults, path resolution, DoS |
| L4 Claims | Do public docs match implementation? | README vs enum/adapters/LOC |
| L5 Reproducibility | Can results be replayed? | F1 gate, hash stability, optional deps |

**Overall academic verdict:** AeroBIM is a **substantive openBIM validation system** with real IFC/IDS/BCF rails and strong automated tests. It is **not** free of material defects: several paths produce **silent false negatives**, default deployment auth is **fail-open**, and public taxonomy/metrics **overclaim**. Integrity of the executable tree is good; one RU README was encoding-damaged (repaired this session).

---

## 1. Integrity (corruption / crash debris)

| Category | Verdict | Evidence |
|----------|---------|----------|
| Python AST / compileall (`src`+`tests`) | **PASS** | 66 + 41 files parse |
| JSON (samples + 418 report payloads) | **PASS** | 0 parse errors |
| IFC fixtures (488 files) | **PASS** | `ISO-10303-21` … `END-ISO-10303-21` |
| Git conflict markers | **PASS** | none |
| Frontend lockfile / entry | **PASS** | lockfile v3, `main.tsx` chain |
| `pyproject.toml` / compose / LICENSE | **PASS** | parse OK |
| **`README.ru.md` encoding** | **FAIL → FIXED** | Was CP1251 + `| ? |` status cells; converted to UTF-8, glyphs restored |
| Temp debris | **WARN** | `_tmp10.md`, `backend/.tmp_api_venv/` leftover |

**Conclusion:** No evidence of crash-corrupted **code or IFC/JSON data**. Damage was documentation encoding + session temp artifacts.

---

## 2. Live verification (this session)

| Check | Result |
|-------|--------|
| `pytest tests -q` | **299 passed, 2 skipped** (5.50s) |
| Extraction gate `--min-macro-f1 0.70` | **PASS**, macro F1 ≈ **0.86** |
| Test defs | **303** |
| LOC (non-empty) | src ≈ **7 630**, tests ≈ **7 032** |

---

## 3. Architecture inventory (corrected)

| Metric | README claim | Live | Verdict |
|--------|--------------|------|---------|
| Layers | 5 | 5 | **PASS** |
| Domain ports | 9 | **13** (12 in `ports.py` + `StructuredLogger`) | **FAIL (stale)** |
| DI tokens | 13 | **18** | **FAIL (stale)** |
| Adapters | 12 | **~17** wired classes | **FAIL (stale)** |
| LOC | ~1.9K / ~1.8K | ~7.6K / ~7.0K | **FAIL (stale)** |

**Domain purity:** PASS (guarded by `test_layer_boundaries.py`).  
**Composition root:** PASS with exceptions (`OpenRebarEvidenceVerifier` hard-wired; OpenAPI export mini-container; presentation imports BCF exporters).

---

## 4. Finding register (severity-ranked)

### CRITICAL

| ID | Title | Evidence | Impact |
|----|-------|----------|--------|
| **C1** | `/v1/*` open when `AEROBIM_API_BEARER_TOKEN` unset | `api.py:125-128`; docker-compose binds `0.0.0.0` without token | Unauthenticated validation, report download, BCF/IFC export, async jobs |
| **C2** | Symlink escape under storage root | `api.py:117-123`, `local_object_store.py:42-47` — `resolve()` + `is_relative_to` without symlink rejection | If attacker can plant symlink in storage, path can resolve outside jail |

### HIGH

| ID | Title | Evidence | Impact |
|----|-------|----------|--------|
| **H1** | Frontend never sends Bearer | `frontend/src/lib/api.ts:11-16` | Secured backend breaks UI → operators disable auth |
| **H2** | Clash detector silent failure → `[]` | `ifc_clash_detector.py:27-35` bare `except Exception` | False “no clashes”; coordination safety lie |
| **H3** | Clashes excluded from `summary.passed` | `analyze_project_package.py:167-202` | Report **PASS** with hard spatial clashes |
| **H4** | Unbounded IFC memory loads | `filesystem_audit_store.py:110-114`, `s3_object_store.py:45-48`, viewer full buffer | DoS / OOM on large models |
| **H5** | IFC validator silently skips incomplete rules | `ifc_open_shell_validator.py:107-108` | False pass when `property_set`/`property_name` missing |
| **H6** | Unit-scale failure falls back to `1.0` | `ifc_open_shell_validator.py:224-233` | Wrong SI normalization → false pass/fail |
| **H7** | Async jobs stuck `queued` after restart | in-memory job store + no replay | 202 Accepted forever without worker |
| **H8** | `asyncio.run()` inside Postgres `save()` | `postgres_audit_store.py:72-77` | Nested-loop / concurrency fragility |

### MEDIUM

| ID | Title | Evidence | Impact |
|----|-------|----------|--------|
| **M1** | `ConflictKind` 6 values; only 3 assigned | `models.py:48-78` vs `analyze_project_package.py:436-480` | STAGE/VERSION/SOFT never produced — taxonomy overclaim |
| **M2** | OpenRebar “enforced” drops issue metadata | `analyze_project_package.py:248-265` | Lost priority/conflict_kind/evidence fields |
| **M3** | Drawing compare without unit normalization | `analyze_project_package.py:664-693` | `3000 mm` vs `3 m` false errors |
| **M4** | `ExternalEvidenceVerifier` bypasses DI | `bootstrap.py:132` | Non-swappable; atomic-delivery smell |
| **M5** | TTL does not prune Postgres index | filesystem TTL only | Orphan enterprise index rows |
| **M6** | S3 misconfig silently → LocalObjectStore | `bootstrap.py:162-175` | Split-brain in multi-instance prod |
| **M7** | Job store lacks CAS state machine | `mark_running` unconditional | Duplicate/re-entrant job races |
| **M8** | `Content-Disposition` unsanitized filenames | `api.py:560-588` | Header injection risk |
| **M9** | WebP analyzed but not in drawing assets | suffix lists diverge | No 2D preview for WebP-only inputs |
| **M10** | Presentation imports infra exporters | `api.py` BCF/OpenRebar | Layer coupling |
| **M11** | Frontend absent from main CI | `ci.yml` | Viewer regressions undetected |
| **M12** | README metrics / ConflictKind / raster row drift | README vs live | Publication integrity |

### LOW

| ID | Title | Impact |
|----|-------|--------|
| **L1** | `hash()` annotation IDs | Non-reproducible across PYTHONHASHSEED |
| **L2** | Postgres `list_reports` write-only | “Enterprise index” does not serve listing |
| **L3** | Corrupt JSON silently skipped in listings | Hidden integrity loss |
| **L4** | Reinforcement digest returns absolute path | Info disclosure |
| **L5** | Docs imply Bearer on `/health`; health always public | Ops confusion |
| **L6** | Temp debris `_tmp10.md`, `.tmp_api_venv/` | Hygiene |

---

## 5. Correctness theory (why silent failures matter)

In validation systems, **soundness** requires: if the system reports PASS, no material requirement was violated *and* no capability required for that judgment was unavailable.

AeroBIM currently violates soundness in at least three ways:

1. **Capability absence ≡ empty result** (clash ImportError/Exception → `[]`).
2. **Incomplete rule ≡ no issue** (missing property metadata → `continue`).
3. **Spatial findings outside pass predicate** (clashes stored but `passed = error_count == 0` on issues only).

This is the academic core defect class: **fail-open validation under degraded dependencies**.

Recommended invariant:

```text
Report.capabilities.clash ∈ {ok, skipped, failed}
Report.passed ⇒ (no ERROR issues) ∧ (capabilities.required all ok)
```

---

## 6. Security threat model (deployment)

| Threat | Current posture | Required posture |
|--------|-----------------|------------------|
| Anonymous API on Docker `0.0.0.0` | Fail-open if token unset | Fail-closed outside `development` |
| Path traversal `../` | Blocked | Keep + tests |
| Symlink jailbreak | Not blocked | Reject symlinks |
| Large IFC DoS | Unbounded read | Size caps + streaming |
| Zip-slip on BCF | N/A (export-only) | — |
| SSRF | Not observed | Keep filesystem-bound |

---

## 7. Claim boundary (publication hygiene)

| Claim class | Status |
|-------------|--------|
| IFC/IDS/BCF pipeline exists and is tested | **Supported** |
| IDS 1.0 as buildingSMART final standard | **Supported** (external, Jun 2024) |
| Russian AEC F1 ≥ 0.70 | **Supported** (live ≈ 0.86) |
| Full 6-kind ConflictKind policy engine | **Overclaim** (3 kinds computed) |
| Enterprise Postgres “index” as query surface | **Overclaim** (write-mostly) |
| Clash as coordination signal affecting pass/fail | **Under-specified / misleading** |
| Advanced non-deterministic raster | **Correctly planned**; deterministic OCR already live |
| Full ISO 19650 / 12006-3 certification | **Not claimed; do not imply** |

---

## 8. Test gap matrix (high-risk)

| Risk | Covered? | Gap |
|------|----------|-----|
| Auth fail-open default | Partial | No “prod must require token” test |
| Symlink escape | **No** | Critical missing |
| Clash failure visibility | Happy path only | No failed-engine assertion |
| Clashes vs `passed` | Weak | No fail-on-clash contract |
| Frontend + Bearer | **No** | — |
| Job restart recovery | Snapshot only | No QUEUED replay |
| Drawing unit compare | Cross-doc only | Drawing path untested |
| WebP assets | **No** | Suffix mismatch |
| ConflictKind stage/version/soft | **No** | Enum dead values |

---

## 9. Remediation roadmap (priority)

### P0 (security / soundness)

1. Fail-closed auth outside development; set token in docker-compose.  
2. Reject symlinks in `_resolve_safe_path` / ObjectStore.  
3. Clash: never silent `[]` — emit capability status + optional ERROR.  
4. Include clashes in pass criteria or document exclusion explicitly in API contract.  
5. Frontend Bearer support.

### P1 (correctness / reliability)

6. Incomplete IFC rules → WARNING/ERROR, not skip.  
7. Unit-scale failure → visible warning, not silent `1.0`.  
8. Job replay or durable queue; CAS state machine.  
9. Replace `asyncio.run` in Postgres adapter.  
10. Drawing validation reuse SI quantity pipeline.  
11. Implement or delete unused ConflictKind values.

### P2 (hygiene / claims)

12. Refresh README ports/LOC/ConflictKind/raster rows.  
13. Cap IFC size; stream S3/local reads.  
14. WebP in drawing assets; sanitize Content-Disposition.  
15. Delete `_tmp10.md`, `.tmp_api_venv/`.  
16. Frontend smoke in CI or explicit release-only label.

---

## 10. What was repaired this session

| Item | Action |
|------|--------|
| `README.ru.md` | CP1251 → UTF-8; restored status glyphs (`| ? |` → ✅/🔜) |

---

## 11. Final academic statement

AeroBIM demonstrates a **credible research/engineering artifact** for cross-modal BIM validation: Clean Architecture, IDS/IFC/BCF integration, reproducible extraction benchmarks, and a large automated test suite. The deepest problems are not “missing features” but **epistemic failures of the validator under degradation** (silent empty clash results, silent rule skips, pass/fail decoupling) and **deployment fail-open security**. Until P0 items are closed, publication and pilot claims must explicitly bound: *clash optional*, *auth required for non-dev*, *ConflictKind subset implemented*, *metrics refreshed*.

---

## Related

- Fact-check companion: `FULL_AUDIT_FACTCHECK_2026_07_10.md`  
- Architecture SSOT: `docs/06-architecture-reference.md`  
- Pilot claim boundary: `docs/pilot-claim-boundary-2026.md`
