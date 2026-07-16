# Claims lock — Red Team freeze (2026-07-17)

**Status:** locked for remediation P0.  
**Checkpoint verdict:** `NO_GO` until RT-005/004/006/007/013/014/015 closed with runtime evidence.

## Forbidden public wording (until evidence exists)

- «точность >90%» / product accuracy percentages
- «утверждённый заказчиком нормативный пакет» (current: **НЕТ**)
- «MEP clash» as delivered capability
- «анализирует DWG/DXF»
- «проверяет расчёты» as independent correctness
- «production-ready» / «external academic audit»
- «BCF готов к CDE» without import artifact
- Green pass when required clash/OCR/schema checks were skipped

## Allowed wording

- Fixture extraction macro_f1 (not product accuracy)
- Generic IFC clash **when** `ifcclash` installed and capability OK
- Synthetic / draft norm packs only
- BCF ZIP export; CDE import **НЕ ДОКАЗАНО**
- Internal self-audit only

## Dirty-tree note

Remediation commit must include prior uncommitted S1–S4 seams + this audit tree, or explicitly drop them. Do not demo from dirty HEAD as “shipped”.
