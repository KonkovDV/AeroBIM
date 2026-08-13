<!-- claims-lint: allow-file reason="KT#2 AI work plan; quotes forbidden phrases as Never-do list; NO_GO explicit" -->
# AI WORK PLAN — KT#2 (for the next agent)

**Tip:** current `main` after this delivery. **Checkpoint:** NO_GO. **Hours are calendar windows, not ideal-engineer time.**  
**Every number must come from a run** (`artifacts/` or committed `docs/evidence/`). No hand-typed metrics.

## P0 — before the tracker opens the repo (14.08, ≤60 min) — DONE 13.08

1. Golden hash refreshed (`b243e8c9…1524`); outcome assertion `failed` (violation outranks missing data).
2. Tracker/plan paths in `audit/claims_allow_file_registry.json`.
3. VLM evidence indexed in `docs/evidence/README.md`.
4. ADR-001 precedence aligned with Mushkani et al. arXiv:2607.29058.

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

**Default: cut — done 13.08.** Do not promise a Moscow profile that fails the freeze.

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
