# Claims lock — Red Team freeze (2026-07-17)

**Status:** locked; public wording frozen for Samolet TechLab Task 07.  
**Checkpoint verdict:** `NO_GO` until RT-001/002/003 closed with customer evidence.

## Forbidden public wording (until evidence exists)

- «точность >90%» / product accuracy percentages
- «утверждённый заказчиком нормативный пакет» (current: **НЕТ**)
- «MEP clash» as delivered capability
- «анализирует DWG/DXF» / implying DWG ready because DXF parsed (mixed package must surface FAILED)
- Soft-pass when quantity/load/MEP infrastructure threw (must be capability FAILED)
- Soft-pass when `require_mep_system_clash` and MEP is NOT_VERIFIED / empty graph
- Soft-pass when audit JSONL corruption is silently ignored under pilot profile
- «проверяет расчёты» as independent correctness
- «production-ready» / «external academic audit»
- «BCF готов к CDE» without import artifact (structural ZIP ≠ CDE)
- Green pass when required clash/OCR/schema checks were skipped
- Fixture SLA as customer комплект ≤30 мин
- «I9 DONE», «GraphRAG готов», «IfcLLM в AeroBIM» — I9 is **advisory scaffold** only
- Closing RT-001/002/003 without customer evidence

## Allowed wording

- Fixture extraction macro_f1 (not product accuracy)
- Generic IFC clash **when** `ifcclash` installed and capability OK
- Synthetic / draft norm packs only
- BCF ZIP **structural** OK; CDE import **НЕ ДОКАЗАНО**
- Fixture SLA schema 1.2.0 with `claim_level=fixture_only`
- Calculation **сверка** PARTIAL; **корректность** НЕ РЕАЛИЗОВАНО
- Dual-human adjudication + Cohen’s κ / Krippendorff’s α required before publishable precision
- DXF EntityGraph via optional `[cad]` (`dwg_dxf` never OK; mixed DWG+DXF → FAILED if DWG unparsed)
- Hybrid drawing = detector **priors / future YOLO** + OCR degrade (not human-level CV)
- Relational IFC KG advisory fixture scores ≠ IfcLLM product accuracy
- Advisory ON/OFF must not change deterministic findings or `summary.passed`
- `AEROBIM_SIGNOFF_PROFILE=samolet_pilot` fail-closes required MEP/clash/BSI/audit corruption
- Checkpoint remains **NO_GO** until RT-001/002/003

## Evidence pointers (public)

- Blockers: `audit/reports/CRITICAL_BLOCKERS.md`
- Claim boundary: `docs/pilot-claim-boundary-2026.md`
- Tier-0: `docs/TIER0_INDEX.md`
- BCF T1: `audit/evidence/bcf-structural-handoff-2026-07-18.json`
- SLA fixture honesty: `audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json`
- Intake gates: `audit/evidence/customer-intake-gate.json`
- System honesty API: `GET /v1/system/capabilities`
- TZ: `docs/tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`
- Public audit index: `audit/reports/README.md`
- Red Team phase deltas: local only (`.local/engineering-docs/audit-reports/`) — not on GitHub
