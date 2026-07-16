# Claims lock — Red Team freeze (2026-07-17)

**Status:** locked; P0 closed; evidence wave honesty surfaces active; public README aligned 2026-07-17.  
**Operational freeze SHA:** `8efbef8fa5191ef8d6d68841f54fb1e415ae1a9b`.  
**Checkpoint verdict:** `NO_GO` until RT-001/002/003 closed with customer evidence.

## Forbidden public wording (until evidence exists)

- «точность >90%» / product accuracy percentages
- «утверждённый заказчиком нормативный пакет» (current: **НЕТ**)
- «MEP clash» as delivered capability
- «анализирует DWG/DXF»
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

## Evidence pointers

- BCF T1: `audit/evidence/bcf-structural-handoff-2026-07-17.json`
- SLA fixture honesty: `audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json`
- Intake gates: `audit/evidence/customer-intake-gate.json`
- System honesty API: `GET /v1/system/capabilities`
