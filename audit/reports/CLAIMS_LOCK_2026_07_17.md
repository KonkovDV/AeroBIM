# Claims lock — Red Team freeze (2026-07-17)

**Status:** locked; P0 closed; evidence wave honesty surfaces active; public README aligned 2026-07-17.  
**Operational freeze SHA:** `8efbef8fa5191ef8d6d68841f54fb1e415ae1a9b`.  
**Checkpoint verdict:** `NO_GO` until RT-001/002/003 closed with customer evidence.

## Forbidden public wording (until evidence exists)

- «точность >90%» / product accuracy percentages
- «утверждённый заказчиком нормативный пакет» (current: **НЕТ**)
- «MEP clash» as delivered capability
- «анализирует DWG/DXF» / implying DWG ready because DXF parsed (mixed package must surface FAILED)
- Soft-pass when quantity/load/MEP infrastructure threw (must be capability FAILED)
- «проверяет расчёты» as independent correctness
- «production-ready» / «external academic audit»
- «BCF готов к CDE» without import artifact (structural ZIP ≠ CDE)
- Green pass when required clash/OCR/schema checks were skipped
- Fixture SLA as customer комплект ≤30 мин

## Allowed wording

- Fixture extraction macro_f1 (not product accuracy)
- Generic IFC clash **when** `ifcclash` installed and capability OK
- Synthetic / draft norm packs only
- BCF ZIP **structural** OK; CDE import **НЕ ДОКАЗАНО**
- Fixture SLA schema 1.2.0 with `claim_level=fixture_only`
- Calculation **сверка** PARTIAL; **корректность** НЕ РЕАЛИЗОВАНО
- Internal self-audit only
- Dual-human adjudication + Cohen’s κ / Krippendorff’s α required before publishable precision
- DXF EntityGraph via optional `[cad]` (capability never OK for `dwg_dxf`; mixed DWG+DXF → FAILED if DWG unparsed)
- Hybrid drawing = detector **priors / future YOLO** + OCR degrade (not human-level CV)
- Relational IFC KG advisory fixture scores ≠ IfcLLM product accuracy
- **Forbidden in prompts/decks:** «I9 DONE», «GraphRAG готов», «IfcLLM в AeroBIM» — only **advisory scaffold** (port + allowlisted query + fixture QA)
- Advisory ON/OFF must not change deterministic findings or `summary.passed` (RT-E)
- Contour orchestrators under Analyze UC (RT-A) — public `execute()` contract unchanged
- Post–I0–I7 deltas: `RED_TEAM_DELTA_I0_I7_2026_07_17.md` (+ PASS2 / PASS3); checkpoint **NO_GO**
- Combat backends: `AUDIT_COMBAT_BACKENDS_I1_I9_2026_07_17.md`
- Sign-off remediations RT-A…H: `AUDIT_RED_TEAM_RT_A_H_2026_07_17.md`
- Forbidden: citing IfcLLM 93–100% or AECV-Bench model scores as AeroBIM product accuracy
- Forbidden: calling heuristic layout regions «YOLO» (priors / future YOLO only)

## Evidence pointers

- BCF T1: `audit/evidence/bcf-structural-handoff-2026-07-17.json`
- SLA fixture honesty: `audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json`
- Intake gates: `audit/evidence/customer-intake-gate.json`
- System honesty API: `GET /v1/system/capabilities`
- Red Team current: `audit/reports/RED_TEAM_DELTA_I0_I7_PASS3_2026_07_17.md`
- RT-A…H remediations: `audit/reports/AUDIT_RED_TEAM_RT_A_H_2026_07_17.md`
- Claim boundary: `docs/pilot-claim-boundary-2026.md` · Tier-0: `docs/TIER0_INDEX.md`
