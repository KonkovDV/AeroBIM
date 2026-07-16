# Remediation Plan (post-audit only)

Do **not** mass-refactor. Fix in severity order. Each slice must be atomic:

```text
problem → design → domain contract → adapter → DI → runtime test → negative test → docs → evidence
```

A finding is closed only when runtime + regression + negative test + evidence + claim wording align.

## P0 — BLOCKER (security / false pass / broken runtime)

| ID | Slice | Acceptance | Status |
|---|---|---|---|
| RT-005 | Tenant/project object ACL on report artifacts | Cross-tenant GET IFC/BCF/preview → 403 | **CLOSED** 2026-07-17 |
| RT-006 | Fix frontend vitest failures | `npm test` exit 0 | **CLOSED** (21 passed) |
| RT-004 | Pilot profile: required clash capability | Missing `ifcclash` under require_clash ⇒ FAILED | **CLOSED** |
| RT-009 | Commit or revert dirty seams; re-freeze baseline | Clean commit of audit + seams + P0 | **CLOSED** (this commit) |
| RT-013 | Revision empty/drawing identity | AMBIGUOUS when one-sided empty; drawings in scope | **CLOSED** |
| RT-014 | Raster/bSI soft-success edges | Zero OCR yield FAILED; schema policy gate | **CLOSED** |
| RT-015 | Storage fail-closed non-dev | Postgres misconfig does not silently FS-fallback | **CLOSED** |
| RT-007 | Mandatory finding provenance | Persist rejects missing evidence/source/rule | **CLOSED** |

## P1 — CRITICAL (claims / capabilities — still open)

| ID | Slice | Acceptance | Status |
|---|---|---|---|
| RT-001/002 | Claims lockdown + customer corpus/norm pack | No >90%; norms = НЕТ customer pack | OPEN (customer-blocked) |
| RT-003 | MEP wording + capability boundary | Keep NOT VERIFIED; never wire fake MEP | OPEN (honest gap) |

## P2 — HIGH (TZ gaps needing customer data or honest PARTIAL)

| ID | Slice | Acceptance |
|---|---|---|
| RT-008 | BCF independent import evidence | Saved import log/screenshot + hash |
| RT-010 | Split calculation claims in docs/API | Two labels: match results vs verify correctness |
| RT-011 | DWG/CV non-claims | Explicit MISSING in API capability surface |
| RT-012 | SLA evidence pack | package hash, sizes, machine, cold/warm, command, result JSON |

## P3 — Customer-blocked (cannot close in git alone)

1. Approved residential norm pack + approval_ref  
2. Federated MEP IFC + scope memo  
3. Labeled detection corpus + 2 adjudicators  
4. CDE BCF import confirmation  
5. Baseline manual review hours for −20% KPI  

## Explicit non-goals until P0/P1 green

- New CV/VLM features  
- Solibri-parity MEP  
- Publishing accuracy numbers  
- “Production-ready” marketing  

## Verification rails after each slice

```bash
cd backend && python -m ruff format --check . && python -m ruff check . && python -m mypy src/aerobim
cd backend && python -m pytest -q
cd frontend && npm test
python audit/tools/generate_audit_baseline.py
```

Update `CRITICAL_BLOCKERS.md` status per closed ID; never close by documentation-only edits.
