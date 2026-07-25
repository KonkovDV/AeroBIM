---
title: "Four-direction honesty implementation report"
status: active
version: "1.0.0"
last_updated: "2026-07-24"
claim_boundary: "Honesty/fail-closed only — does not close DWG, MEP, calc correctness, or BCF T2."
---

# Итоговый отчёт: ограниченные направления AeroBIM (2026-07-24)

**Цель:** честно зафиксировать границы, а не создать видимость закрытия четырёх направлений. Checkpoint остаётся **NO_GO**.

## 1. Найденные текущие реализации

| Контур | Реализация |
|---|---|
| CAD ingest | `EzdxfCadModelIngestor` на analyze path; `OdaCadModelIngestor` = STUB-ODA-CAD-001, не в analyze |
| DWG | Fail-closed `supported=False`, reason `native DWG parser is not implemented` |
| DXF | PARTIAL via optional `ezdxf` → `dwg_dxf=NOT_VERIFIED` (never OK) |
| Hard clash | Optional ifcclash geometric intersection |
| MEP graph | `MepSystemGraphProvider` (+ `build_graph` alias); Unconfigured / Scoped / Federated co-presence |
| Calc | Load/quantity/cross-doc/OpenRebar **сверка**; `calculation_correctness=NOT_IMPLEMENTED` |
| BCF | 2.1/3.0 ZIP export + T1 structural evidence; T2 proof dir empty |

## 2. Найденные несоответствия статусов (до фикса)

- Риск маскировки PDF/IFC как «поддержки DWG» без provenance.
- MEP co-presence / ENG_FIXTURE могли читаться как полный system-aware clash.
- Calculation match мог путаться с correctness.
- BCF structural ZIP мог путаться с CDE import (T2).
- API honesty schema отставал от единого capability contract.

## 3. Внесённые изменения

- Unified contract: `capability_contract` + `direction_contracts` в `GET /v1/system/capabilities` **1.3.0**
- `DerivedCadProvenance` + `derived_cad_provenance` helpers
- `mep_intake` + clearance matrix schema **1.1.0** + enriched template
- `CalculationEvidenceOutcome` + `independent_solver_not_implemented_payload`
- `verify_bcf_t2_evidence` tool (log + screenshot + hashes gate)
- `MepSystemGraphProvider.build_graph` alias on providers
- Honesty reasons aligned; ODA stub never returns OK
- Docs: Claims Lock, capability matrix, README/README.ru

## 4. Новые и изменённые тесты

- `backend/tests/test_four_direction_honesty.py` (DWG/ODA/derived/MEP/calc/BCF/contract)
- Updated: `test_cad_office_ingest.py`, `test_api_security.py` (schema 1.3.0)

## 5. API и capability changes

- Schema `1.3.0`: `direction_contracts`, `bcf_t2`, `mep_intake`, `forbidden_claim_phrases`
- Native DWG: `missing`; DXF: `partial`; MEP rules: `blocked_customer_data`; calc correctness: `not_implemented`; BCF T2: `not_verified`

## 6. Отчёты и Claims Lock

- `audit/reports/CLAIMS_LOCK_2026_07_17.md` — расширен forbidden/allowed
- `docs/capability-claim-matrix-2026.md` — four-direction table
- README / README.ru — honest wording

## 7. Подтверждено на unit / fixture / integration

| Уровень | Что |
|---|---|
| unit | DWG never OK; ODA stub; honesty enforce; solver payload; T2 verifier; derived provenance |
| fixture | DXF TEXT (when ezdxf); clearance matrix schema; MEP ENG_FIXTURE intake |
| integration | Existing BCF ZIP / T1 evidence ladder tests remain |

## 8. Заблокировано данными заказчика

- RT-001 accuracy corpus
- RT-002 approved norms
- RT-003 federated MEP + signed clearance matrix + geometry_verified
- BCF T2 CDE sandbox (import-log, screenshot, hashes)

## 9. Разрешённые claims

- DXF PARTIAL; native DWG MISSING
- PDF/IFC as derived inputs with provenance
- Hard geometric clash when evidenced
- Calculation **сверка** (evidence consistency only)
- BCF 2.1 / T1 structural AVAILABLE
- Shared-gate `summary.passed` per ADR-001

## 10. Запрещённые claims

- DWG поддерживается / `dwg_supported` / DWG-ready
- полный MEP clash / MEP delivered
- проверка корректности расчётов / `calculation_correctness_verified`
- BCF готов для СОД / `CDE_READY` / CDE interoperable
- fixture_only = customer; co-presence = connection

## 11. Оставшиеся блокеры

- RT-001 / RT-002 / RT-003 (CRITICAL_BLOCKERS)
- Licensed native DWG (ODA legal gate) if ever needed
- Customer CDE import environment for T2
- Independent calculation solver (explicitly out of scope)

## 12. Следующий шаг до КТ №2 (20 августа 2026)

1. Customer intake: federated MEP IFC + signed scope memo + clearance matrix (RT-003).
2. Fill T2 evidence pack against named СОД (or keep NOT_VERIFIED).
3. Parallel: expert labeling + norm pack RASE ([PARALLEL_WORKPLAN_CHECKPOINT2](PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md)).
4. Keep Claims Lock; never flip checkpoint to GO without RT evidence.
