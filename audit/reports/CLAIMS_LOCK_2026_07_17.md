# Claims lock — Red Team freeze

**Status:** locked for Samolet TechLab Task 07 public wording.  
**Checkpoint verdict:** `NO_GO` until RT-001/002/003 closed with customer evidence.  
**Last Red Team docs pass:** 2026-07-19 (`main` @ post-remediation + jury-pack trim).

## Forbidden public wording (until evidence exists)

- «точность >90%» / product accuracy percentages
- «утверждённый заказчиком нормативный пакет» (current: **НЕТ**)
- «MEP clash» as delivered capability
- «полный MEP clash» / full MEP system-aware as AVAILABLE without customer federated IFC + signed matrix (RT-003)
- «анализирует DWG/DXF» / implying DWG ready because DXF parsed (mixed package must surface FAILED)
- «DWG поддерживается» / `dwg_supported` / DWG-ready (native DWG = MISSING; PDF/IFC = derived input only)
- Soft-pass when quantity/load/MEP infrastructure threw (must be capability FAILED)
- Soft-pass when `require_mep_system_clash` and MEP is NOT_VERIFIED / empty graph
- Soft-pass when audit JSONL corruption is silently ignored under pilot/production profile
- Soft `AEROBIM_CLASH_AFFECTS_PASS=false` under pilot/production (env soft flags are ignored; profile forces fail-closed)
- «проверяет расчёты» as independent correctness / `calculation_correctness_verified`
- «production-ready» / «external academic audit»
- «BCF готов к CDE» / «BCF готов для СОД» / `CDE_READY` / «CDE interoperable» without T2 import-log + screenshot + hashes
- Green pass when required clash/OCR/schema checks were skipped
- Fixture SLA as customer комплект ≤30 мин
- «I9 DONE», «GraphRAG готов», «IfcLLM в AeroBIM» — I9 is **advisory scaffold** only
- Closing RT-001/002/003 without customer evidence
- «нет автоматического вердикта» without clarifying Shared-gate `summary.passed` (see ADR-001)
- Treating co-presence MEP graph edges as connection / system-membership proof
- Treating fixture_only / ENG_FIXTURE as customer-validated MEP

## Allowed wording

- Fixture extraction macro_f1 (not product accuracy)
- Generic IFC clash **when** `ifcclash` installed and capability OK
- Synthetic / draft norm packs only
- BCF ZIP **structural** OK; CDE import **НЕ ДОКАЗАНО**
- Fixture SLA schema 1.2.0 with `claim_level=fixture_only`
- Calculation **сверка** PARTIAL; **корректность** НЕ РЕАЛИЗОВАНО (`evidence_consistency_only`)
- Dual-human adjudication + Cohen’s κ / Krippendorff’s α required before publishable precision
- DXF EntityGraph via optional `[cad]` (`dwg_dxf` never OK; mixed DWG+DXF → FAILED if DWG unparsed)
- PDF/IFC/DXF as **derived** substitutes with provenance (`available_as_derived_input`) — not native DWG support
- Hybrid drawing = detector **priors / future YOLO** + OCR degrade (not human-level CV)
- Relational IFC KG advisory fixture scores ≠ IfcLLM product accuracy
- Advisory ON/OFF must not change deterministic findings or `summary.passed`
- `summary.passed` = automatic **Shared-gate** from deterministic engine + blocking capabilities (ADR-001); **not** Shared→Published / contractual fitness; OCR/LLM cannot flip it; expert confirms findings for handoff
- Non-dev `AEROBIM_ENV` defaults `AEROBIM_SIGNOFF_PROFILE=production` (fail-closed clash/MEP/bSI/unit_scale)
- Explicit `AEROBIM_SIGNOFF_PROFILE=samolet_pilot` likewise fail-closes required MEP/clash/BSI/audit corruption
- Cross-tenant ACL denial returns **404** (not 403) to avoid object enumeration
- Outbound JWKS / bSI / OpenCDE fetches pass SSRF URL guard
- Hard geometric IFC clash **when** evidenced — separate from MEP system-aware (RT-003 OPEN)
- `GET /v1/system/capabilities` schema **1.3.0** `direction_contracts` for four gap directions
- Checkpoint remains **NO_GO** until RT-001/002/003

## Evidence pointers (public)

- Blockers: `audit/reports/CRITICAL_BLOCKERS.md`
- Claim boundary: `docs/pilot-claim-boundary-2026.md`
- Verdict ownership: `docs/architecture/ADR-001-verdict-ownership-2026.md`
- Tier-0: `docs/TIER0_INDEX.md`
- Jury memo: `docs/docs.md`
- BCF T1: `audit/evidence/bcf-structural-handoff-2026-07-18.json`
- SLA fixture honesty: `audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json`
- Intake gates: `audit/evidence/customer-intake-gate.json`
- System honesty API: `GET /v1/system/capabilities`
- TZ: `docs/tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`
- Public audit index: `audit/reports/README.md`
- Red Team phase deltas: local only (`.local/engineering-docs/`) — not on GitHub
