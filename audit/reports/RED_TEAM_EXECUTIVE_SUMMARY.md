# RED TEAM — Executive Summary (AeroBIM × Samolet TechLab)

> **Historical freeze (pre-remediation).** Measured at SHA `c0c4b2b` with dirty tree and failing frontend tests.  
> **Operational delta (post P0 + evidence wave):** see [`RED_TEAM_DELTA_2026_07_17.md`](RED_TEAM_DELTA_2026_07_17.md) at SHA `8efbef8` (451 backend / 21 frontend).  
> **Checkpoint verdict remains `NO_GO`** (RT-001/002/003). Do not cite defect counts below as current.

**Verdict: `NO_GO`**

**Audit date (UTC):** 2026-07-16T20:59:16Z  
**Commit SHA:** `c0c4b2bdc8f0a6e18dacfe674b616b4e4e61d04f` (`main`)  
**Working tree:** DIRTY (20 uncommitted paths including S1–S4 seams + this `audit/` tree)  
**Author relationship:** self (this package is an internal Red Team inventory, not an external audit)

## One-line judgment

AeroBIM is a **real modular openBIM validation codebase** with deterministic IFC/IDS rails and honest gap docs — but it is **not checkpoint-ready** as a Samolet Task 07 deliverable that claims automated PD/RD compliance, MEP coordination, normative approval, customer accuracy, or production handoff.

## Freeze (measured, not README)

| Metric | Value | Command / source |
|---|---|---|
| Backend src LOC | 15290 / 101 files | `audit/tools/generate_audit_baseline.py` |
| Backend tests LOC | 11149 / 63 files | same |
| Backend pytest | **436 passed / 3 skipped / 0 failed** (439 collected) | `pytest -q` |
| Frontend vitest | **18 passed / 3 failed** — EXIT 1 | `npm test` |
| Extraction macro_f1 | ≈0.86 | fixture corpus only |
| `ifcclash` | **NOT importable** | optional probe |
| `rapidocr` / `boto3` / `docling` | **NOT importable** | optional probe |
| Latest CI on main | success (push at commit above) | `gh run list` |
| Customer corpus | **false** | `docs/evidence/tz-matrix-status-latest.json` |

Full freeze: [`audit/evidence/audit-baseline.json`](../evidence/audit-baseline.json)

## Critical blockers (auto → NO_GO)

1. **No customer-approved norm pack** — norms cannot be claimed for sign-off.  
2. **MEP system-aware clash NOT VERIFIED** — scaffold only; not in DI; generic clash only; clash extra missing so capability often SKIPPED without blocking pass.  
3. **Customer / product accuracy NOT publishable** — no customer corpus + ≥2 adjudicators.  
4. **Frontend review shell tests FAIL** — reproducibility of UI path broken in this environment.  
5. **Object access is report-ID + shared bearer**, not tenant/project isolation — knowing an ID is enough to fetch IFC/preview/BCF.  
6. **Independent BCF CDE import evidence missing** — ZIP export ≠ proven interoperability.  
7. **Finding contract incomplete** — `ValidationIssue` lacks required `finding_id` / `evidence_refs` / `document_identity` / capability binding.  
8. **Dirty tree vs published SHA** — revision-merge guard and several seams exist only as uncommitted work; checkpoint must not assume they are shipped.

## Contour answers (forced)

| Question | Answer |
|---|---|
| Can AI change `summary.passed`? | **No** (tests assert advisory OFF==ON for pass flag) |
| Can adapter failure become empty success? | **Risk: yes for clash SKIPPED** (missing `ifcclash` → empty clashes, pass not blocked) |
| Can frontend invent findings? | **Not observed** (display-only); UI tests currently red |
| Can report lose provenance? | **Yes structurally** — optional provenance fields, not mandatory finding contract |
| Can revisions silently merge? | **Risk on committed HEAD**; guard present in dirty tree but `DocumentIdentity` still incomplete |

## What is actually strong

- Layering: no `domain → infrastructure` imports found.  
- Fail-closed for **FAILED** capabilities and failed norm packs affecting `summary.passed`.  
- Pilot claim-boundary docs that already forbid >90%, Solibri replacement, DWG, MEP overclaim.  
- Synthetic IFC/IDS/cross-doc/quantity paths with substantial automated tests.

## What must never be said at the checkpoint

- «точность >90%»  
- «полная проверка норм» / утверждённый пакет норм  
- «MEP clash detection» as delivered  
- «анализирует DWG»  
- «проверяет расчёты» (independent correctness)  
- «production-ready» / «external academic audit»  
- «BCF готов к CDE» without import proof  

## Norm pack final line

```text
Есть ли утверждённый заказчиком нормативный пакет: НЕТ
```

## Next action (after this report only)

Do **not** start feature work. Remediate blockers in order in [`REMEDIATION_PLAN.md`](REMEDIATION_PLAN.md): security/isolation → clash policy honesty → finding provenance contract → commit or discard dirty seams → green frontend → customer intake blockers (data from Samolet).
