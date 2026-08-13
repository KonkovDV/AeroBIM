# AI WORK PLAN — KT#2 (for the next agent)

**Tip:** `07f2782`. **Checkpoint:** NO_GO. **Hours are calendar windows, not ideal-engineer time.**  
**Every number must come from a run** (`artifacts/` or committed `docs/evidence/`). No hand-typed metrics.

## P0 — before the tracker opens the repo (14.08, ≤60 min)

1. **Fix golden hash.** `backend/tests/test_golden_report.py` expects `62ade…8595`; code on `07f2782` yields `b243e8c9…1524` (PackageOutcome priority). Refresh the constant **and** the «fourth conscious refresh» comment. Re-run `pytest tests/test_golden_report.py -q`.
2. **Register lint bypasses.** Add `docs/demo/TRACKER_MEETING_2026_08_14.md` and `docs/pilot/KT2_7DAY_PLAN_2026_08_13.md` to `audit/claims_allow_file_registry.json`, or switch them to per-line `claims-lint: allow`. Re-run `python scripts/lint_claims.py`.
3. **Index VLM evidence.** Add one row to `docs/evidence/README.md` for `vlm-comparison-2026-08.json`.
4. **Align ADR-001.** Add the precedence order (FAILED > BLOCKED > REVIEW_REQUIRED > PASS_WITH_WARNINGS > PASS) to `docs/architecture/ADR-001-verdict-ownership-2026.md` decision #2.

Gate: `pytest` on the four files above + `ruff check` + `lint_claims.py` all green.

## P1 — vertical slice UI (15–16.08, 10 h)

- One page: PDF fragment → finding → evidence link → overlay PNG → outcome enum. Reuse existing review-shell; **no new ports**.
- e2e: `backend/tests/test_demo_vertical_slice.py` + `frontend/src/components/VerticalSliceKt2.test.tsx`.
- DoD: README «10 minutes from clone to demo» is true on a clean machine.

## P2 — honest external validation (17.08, 6 h)

- **AEC-Bench:** inventory exists (`docs/evidence/aec-bench-smoke-latest.json`). Either run the 160-task Mushkani slice with project-cluster bootstrap and **publish false-pass rate first**, or write `SKIPPED` with the reason (no agent budget / no Docker). Do **not** publish accuracy.
- **MOEXP per-pack:** extend `export_moexp_ids_coverage` with `by_kind` (attributes vs classification). Re-run, bump `content_sha256`.
- **Solihin classes:** tag each in-repo rule 1–4 in a JSON; class 4 = not claimed.

## P3 — decision, not build (17.08, 2 h)

`moscow_agr` is **not in code** (no proxy scan, no 5-field filename, no 500 MB cap, no CRS audit). Architecture freeze forbids new ports. Two options:

| Option | Cost | Say on 20.08 |
| --- | --- | --- |
| Build as **data** (JSON inventory + existing `package_completeness` + new rule-pack) | ~4 h, no new DI | «Формальная полнота комплекта по чек-листу, не проверка проектных решений» |
| Cut | 0 | «Профиль АГР не собран; есть официальные IDS МОГЭ и движок» |

**Default: cut.** Do not promise a Moscow profile that fails the freeze.

## P4 — measurement protocol + DWG ADR (18.08, 5 h)

- Extend `docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md` with: unit of independence = project; cluster bootstrap; false-pass first; selective-risk curve; Solihin split.
- DWG ADR: ODA trial 60 days = KT#3 fact-finding; buy only if ≥30% customer packs are DWG-only and DWG is in acceptance. Commercial license ≠ SaaS.

## P5 — pack, not polish (19.08, 6 h)

- Human records 3-min video (agent cannot).
- README KT#2 block: working / externally verified / experimental / customer-blocked. NO_GO on top.
- CI green. Upload to LK.

## Never do

- New ports / adapters / DI tokens (except the already-landed outcome priority).
- «>90%», «DWG-ready», «MEP delivered», «CDE-ready BCF», «соответствует ПП 87», «московский профиль готов».
- AEC-Bench numbers without a run log and hash.
- Delete adapters without the owner's written «yes».

## One-screen status for 14.08 08:00

| Show | Say |
| --- | --- |
| `run_demo_vertical_slice` | Один CLI: лист → finding + overlay + BCF. Fixture. |
| `docs/evidence/norm-pack-moexp-coverage-2026-08.md` | Движок исполняет 389/389 официальных спецификаций МОГЭ. ЦИМ по профилю МОГЭ **не замеряли**. |
| Qwen live | Advisory на штампе/spec. Не вердикт. Kimi закрыт гейтом. |
| `NO_GO` | RT-001 корпус РФ-экспертизы, RT-002 профиль «Самолёта», RT-003 MEP. Кодом не снимается. |

**Ask Samolet for:** корпус моделей + 2 разметчика + подписанный профиль приёмки. Нормы экспертизы уже в репо.
