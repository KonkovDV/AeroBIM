# RED TEAM — 13.08.2026 (post-prompt)

**Status:** written on `main` tip **07f2782**. Checkpoint stays **NO_GO**. This is engineering honesty, not customer evidence.  
**Scope:** what tracker will see 14.08 08:00 + brief parts 0–5. Evidence: focused pytest 47+4 passed, ruff, claims-lint, live `main` diff.

## Must fix before the tracker sees it

| Sev | Finding | Evidence | Fix |
| --- | --- | --- | --- |
| **B** | `test_golden_report.py` **broken** on `07f2782` | `b243…1524` ≠ golden `62ade…8595`. Cause: `compute_package_outcome` priority changed in `5c73c95` (FAILED outranks BLOCKED). `README.md` and `capability-claim-matrix-2026.md` both advertise «fixture reproducibility hash». | Refresh golden **after** owner says outcome change is intended. New hash = measured: `b243e8c9eb1244ff8a2b60ccd7033ae12773d8cb21a2e59f1292b09ac01c1524`. |
| **A** | MOEXP coverage lacks **per-pack** split | `coverage.json` has per-domain, not «attributes (20+10) vs classification (20+8)». Brief asks «сколько спецификаций из официального пакета исполняем чисто». | 10 min: group by file-name prefix (`Требования` vs `Проверка_КСИ`). Add `by_kind`. |
| **A** | Coverage metric is **engine-only**; pass rate is 0/389 on wall fixture | Tracker may read «389/389» as «we satisfy MOGE». | Markdown already says it; tracker one-pager **must open with** «валидация ЦИМ по профилю МОГЭ не замерялась». |
| **A** | **Claims-lint bypass:** `docs/demo/TRACKER_MEETING_2026_08_14.md` and `docs/pilot/KT2_7DAY_PLAN_2026_08_13.md` use `allow-file` headers but are **not** in `audit/claims_allow_file_registry.json` | `scripts/lint_claims.py` line 5: header alone is not amnesty (N-29). The pre-push lint passed only because the linter did not enforce the registry (or silently skipped). | Add both paths to the registry **or** use per-line `allow reason=…`. |
| **A** | `vlm-comparison-2026-08.json` is in `docs/evidence/` but **not** in `docs/evidence/README.md` index | Read-only check | One row. |
| **M** | VLM comparison is `LIVE` but coverage: 1/389 specs use it; **not** run against official pack | `run_vlm_stamp_comparison.py` runs on fixture title/spec crops | Do not present Qwen result as norm-checking. Phrase: «advisory on title/spec fixture only». |

## Real gaps the tracker should not pay for (but should know)

| Sev | Finding | Evidence | Fix |
| --- | --- | --- | --- |
| **A** | **`moscow_agr` profile does not exist.** No `BuildingElementProxy` scan, no 5-field filename parser, no 500 MB file cap, no `IfcMapConversion`/EPSG audit, no УКЭП XML presence, no rounding-rules check | Code search: no `IfcBuildingElementProxy`, no Moscow filename policy, no file-size rule on package, no CRS audit. Only `domain.package_completeness` inventory exists (PD/RD pairing, `DEFAULT_RESIDENTIAL_MANDATORY_PD=("PZ","AR","KZH")`). | **Brief overpromises a rule pack that is not in code.** Either build it 17.08 (frozen architecture allows rules in an existing JSON pack? No — still new domain code) or **cut from plan and say so.** |
| **A** | Package completeness is **fixture-grade**, not ПП РФ 87 §3(1)/3(2) | `CLAIM_BOUNDARY` in `package_completeness.py` says exactly that | Do not tell Siginevich «мы совпадаем с ЕГРЗ». Say: «structural inventory, not statutory completeness». |
| **A** | **`PackageOutcome` exception is not an enum change.** It is a priority flip in `compute_package_outcome` (application service). ADR-001 is not edited | ADR-001 still says verdict = deterministic + policy. The priority change is defensible (arXiv:2607.29058), but the ADR now lags the code. | Update ADR-001 decision #2 with the precedence order. |
| **M** | `docs/evidence/norm-pack-moexp-coverage-2026-08.json` ≈ 59 KB and duplicates `docs/evidence/…` into `artifacts/` | Convention in repo is committed snapshot + gitignored artifact; fine, but payload is heavy | Keep; do not double-commit. |
| **M** | Golden hash comment says «fourth conscious refresh 2026-08-11». Today would be fifth | Comment in `test_golden_report.py` | Bump the comment when refreshing. |
| **L** | `test_package_outcome.py::test_intake_blocked_cannot_yield_pass` now asserts *not-pass* instead of *BLOCKED* | Correct under new priority, but weaker than before | Acceptable; note in plan that intake-blocked with no findings is still BLOCKED (covered by `test_missing_data_outranks_uncertainty`). |

## What is actually true and can be shown

- IfcTester executes **389/389** official MOEXP specs on an open wall fixture (`843800f1…0885c`). This is **engine coverage**, not CIM compliance.
- IFC2x3 / IFC4 / IFC4x3 kernel matrix exists (`docs/evidence/ifc-release-matrix-2026-08.md`), fixture-scoped.
- Qwen live roundtrip on title/spec fixture; Kimi gate-refused on Yandex Studio. **VLM is advisory, 1 crop, not 389 specs.**
- Vertical slice CLI `run_demo_vertical_slice` exits 0 on fixture and fails loud on bad input.
- RT-002 wording is fixed: public IDS exist; Samolet-approved profile does not.

## Do not say on 14.08

- «Мы проверяем комплект по требованиям Мособлгосэкспертизы» — **false**. We execute the official IDS; we do not validate a customer CIM against them.
- «Есть московский профиль АГР» — **false**. Not in code.
- «AEC-Bench прогнан» — **false**. Inventory only; false-pass rate **not measured**.
- «Полнота по ПП 87» — **false**. Structural inventory only.

## Numbers to quote

| Claim | Number | Boundary |
| --- | --- | --- |
| Official IDS executed | 389/389, 0 unsupported | engine coverage, wall fixture |
| IFC schema matrix | IFC2x3 / IFC4 / IFC4x3 | fixture kernel timing |
| Qwen roundtrip | ~1.6 s, 1 region | advisory fixture, not accuracy |
| Vertical slice | 1 command → HTML/JSON/BCF/overlay | fixture pack |
| Checkpoint | NO_GO | RT-001 RF corpus, RT-002 Samolet profile, RT-003 MEP |

**Rule for the room:** any sentence with a percent, «соответствует», or «полнота» gets a one-line boundary after it. No exceptions.
