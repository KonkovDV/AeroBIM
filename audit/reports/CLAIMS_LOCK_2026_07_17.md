# Claims lock — Red Team freeze

**Status:** locked for Samolet TechLab Task 07 public wording.  
**Checkpoint verdict:** `NO_GO` until RT-001/002/003 closed with customer evidence.  
**Last Red Team docs pass:** 2026-07-19 (`main` @ post-remediation + jury-pack trim).  
**Claims Lock v2 sync (2026-07-30, `main` @ `98c6701`):** coverage / revision diff / geometry core wording added (P1 features shipped 2026-07-29).

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
- «geometry core анализирует DWG/DXF» — `domain/geometry.py` measures already-extracted primitives only (not a CAD/DWG/DXF parser)
- Treating an INVALID / INCOMPLETE / UNIT_UNKNOWN geometry measurement as «0 violations» (no silent zero)
- «coverage подтверждает корректность документации» — coverage is checked-scope evidence only, not proof of correctness
- Claiming coverage changes or is read by `summary.passed` (coverage is verdict-neutral, read-only)
- «revision diff показывает исправленные замечания» — `no_longer_reported` ≠ resolved (the check may not have re-run)
- «AeroBIM целиком под MIT» / MIT without third-party license disclosure (PyMuPDF is AGPL-3.0/commercial **dual**, mandatory core; IfcOpenShell/IfcTester LGPL-3.0+) — see `audit/dependency_license_inventory.json`
- «интеграция с 10D» / «integrated with 10D» / «S.Project integration» before ladder **T5** (production integration approved by customer); T0–T5 ladder applies
- «в реестре российского ПО» / «российское ПО» as status — until a legal gap analysis exists
- «УКЭП проверена» / «подпись документа проверена» — QUALIFIED_SIGNATURE_VALIDATION is **missing** (no cryptographic adapter/tests); hash-provenance ≠ signature validation
- «маскирование = анонимизация» / hybrid contour makes the public API safe for customer data (masking reduces disclosure, not anonymity; contour NOT wired to verdict / live egress)
- «точность продукта выше 90%» as Sprint 2.1 baseline result
- «подтверждено на реальных проектах Самолёта» without RT-001 customer corpus + adjudication
- «SLA ≤30 минут для любого комплекта» (fixture/scoped ≠ customer)
- «полная проверка проектной документации»
- «проверка корректности расчётов» / independent calculation correctness
- «готовая интеграция с CDE» / CDE_READY from BCF alone
- «LLM понимает чертёж как инженер»
- «облачный API безопасен для customer data» without written policy + DPA evidence
- «заказчики заинтересованы» if no verified contact occurred

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
- Deterministic 2D geometry core over **already-extracted** primitives with explicit trust states (OK / INCOMPLETE / UNIT_UNKNOWN / INVALID); verdict-neutral (`domain/geometry.py`)
- Per-source check-coverage map (CHECKED_OK / NOT_CHECKED / INSUFFICIENT_DATA by processing evidence); verdict-neutral, ACL-scoped, read-only `GET /v1/reports/{id}/coverage`; not persisted in the report
- Verdict-neutral revision diff (newly / no-longer / still reported findings, delimiter-proof keys); does NOT set `summary.passed`
- «MIT for AeroBIM's own code; third-party components under their own licenses» (with inventory pointer)
- BCF integration ladder **T0–T5**: T0 structural ZIP · T1 dual-consumer · T2 customer test-env import · T3 IFC GUID/viewpoint binding · T4 round-trip lifecycle · T5 production integration approved — each tier claimable only with its evidence
- Signal-level extraction-integrity core (`domain/extraction_integrity.py`): 'text not extracted' != 'text absent'; hidden/invisible text never trusted unmarked; verdict-neutral; **NOT** a render-vs-extract product capability; signal production NOT wired into ingestion (verdict gate wired 2026-07-31: FAILED blocks pass)
- IDS pass на пакете без entity-presence требований не эквивалентен «элементы присутствуют и соответствуют»: пустая applicability даёт vacuous pass (LB-007); пилот-паки сочетают IDS с requirement-ожиданием сущностей
- Дубликат GlobalId детектируется как **WARNING** (`AEROBIM-GUID-DUPLICATE`, schema pre-gate; LB-011 закрыт 2026-07-31); проверка warning-level и verdict-neutral — «блокирующая проверка уникальности GUID» не заявляется
- `extraction_integrity` capability wired (default **NOT_VERIFIED**: сигналы ingestion-слоем ещё не производятся; FAILED блокирует pass) — «render-vs-extract проверка PDF реализована» по-прежнему НЕ заявляется
- `extraction_integrity` PDF text-layer producer wired on analyze path (2026-07-31 evening): clean PDF → OK; hidden/zero-size → NOT_VERIFIED; FAILED still blocks pass — still **not** a full render-vs-extract product claim
- «Offline install+runtime bundle пройден» (образ восстановлен из tar через docker load после удаления тега и обслужен при --network none; evidence 2026-07-31) — допустимо для контура С Docker; «bare-metal установка без Docker подтверждена» — НЕТ (wheelhouse NOT VERIFIED)
- Checkpoint remains **NO_GO** until RT-001/002/003
- Sprint 2.1: инженерный baseline на public/synthetic package (reproducible on declared commit + manifest)
- Sprint 2.1: система фиксирует deterministic findings и capability statuses
- Sprint 2.1: LLM только как advisory layer; model comparison на synthetic/public (mock in CI)
- Sprint 2.1 claims boundary: `audit/sprint-2-1-claims-boundary.md`

## Evidence pointers (public)

- Blockers: `audit/reports/CRITICAL_BLOCKERS.md`
- Claim boundary: `docs/pilot-claim-boundary-2026.md`
- Verdict ownership: `docs/architecture/ADR-001-verdict-ownership-2026.md`
- Tier-0: `docs/TIER0_INDEX.md`
- Jury memo: `docs/docs.md`
- BCF T1: `audit/evidence/bcf-structural-handoff-2026-07-25.json` (канон; 2026-07-18 superseded — без XSD-прогона)
- SLA fixture honesty: `audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json`
- Intake gates: `audit/evidence/customer-intake-gate.json`
- System honesty API: `GET /v1/system/capabilities`
- TZ: `docs/tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`
- Public audit index: `audit/reports/README.md`
- Red Team phase deltas: local only (`.local/engineering-docs/`) — not on GitHub
