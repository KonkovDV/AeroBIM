<!-- claims-lint: allow-file reason="Kane IUA ledger; TZ 90%/SLA as blocked inferences; NO_GO" -->
---
title: "Interpretation/Use ledger — Самолёт × трекер × Техлаб/МИК × отрасль"
date: "2026-08-16"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >-
  Kane IUA over existing AeroBIM scores. Licensed uses stop at fixture demo, engine regression, open-bench countable subsets, gold-IDS processability, and protocol planning. Not customer precision, not TZ >90%, not customer SLA, not Checkpoint GO.
---

# Interpretation/Use ledger (КТ#2 → КТ#3)

Валидность — свойство **вывода из оценки**, не свойства программы (Messick 1995; Kane 2013). Этот файл — SSOT: что текущие цифры AeroBIM имеют право значить для Самолёта, , Техлаба, МИК и отраслевых стандартов, и чего они значить не имеют.

- Checkpoint **NO_GO**
- audited_head `375109c`
- closes_rt001/002/003: **false**
- CLI: `python -m aerobim.tools.export_interpretation_use_ledger --write-docs-evidence`

Продуктовая точность по-прежнему только через `PrecisionClaim.publishable` (corpus_kind=customer, ≥2 разметчика, κ/α). Этот ledger её не выдаёт.

| ID | Источник | Требование | Лицензированный вывод | Запрещённый вывод | licensed_use |
|---|---|---|---|---|---|
| SAM-01 | samolet | ТР-1: ассистент эксперта, не замена ГИП | HITL + Claims Lock + ADR-001: модель не ставит summary.passed | Система заменяет экспертизу / лицензированного специалиста | `fixture_demo` |
| SAM-02 | samolet | IFC + IDS / атрибуты BIM | IfcOpenShell + IfcTester на fixture и open packs; IDS 1.0 checking | Профиль приёмки Самолёта / CIM-compliance / RT-002 CLOSED | `engine_regression` |
| SAM-03 | samolet | 2D PDF + подсветка замечания | pypdfium2 overlay на fixture; finding_id / evidence_refs | CV-счёт дверей/окон; AECV-Bench как product accuracy | `fixture_demo` |
| SAM-04 | samolet | Нативный DWG в ТЗ | Fail-closed intake: dwg_native=NOT_IMPLEMENTED / FAILED | DWG-ready / тихий пропуск DWG | `not_licensed` |
| SAM-05 | samolet | Коллизии / MEP / «точность >90%» | Generic IfcClash на fixture; tiny-skip fail-closed; protocol TP/(TP+FP)≥0.60 | Customer clash precision; mep_system_clash=OK; TZ >90% | `protocol_planning` |
| SAM-06 | samolet | SLA «до 30 минут» | measure_package_sla на согласованном fixture; StageBudget sum=30 min | Customer SLA / любой комплект Самолёта | `protocol_planning` |
| SAM-07 | samolet | BCF замечания в СОД | BCF 2.1 ZIP export (структурный) | CDE import VERIFIED / T2 roundtrip | `fixture_demo` |
| TRK-01 | tracker | Задача 1: доработать продукт к КТ#2 (20.08) | IFC Acceptance Gate + HD fail-closed; live CLI; Checkpoint NO_GO | Checkpoint GO / market GO = customer GO | `fixture_demo` |
| TRK-02 | tracker | Задача 2: таблица IFC2X3 / IFC4 / IFC4X3 | Fixture kernel n=20: findings 5/4/6, passed=false, clash=skipped | Product accuracy / customer SLA по релизам IFC | `engine_regression` |
| TRK-03 | tracker | Задача 3: поиск и прогон открытых датасетов | IFC-Bench 27/1026 countable; PNST CLI skip-honest; Ishigaki XML processability | Open bench = RT-001; свежий 18/22; Harbor agent run; DrawingVQA в MIT tree | `open_bench` |
| TRK-04 | tracker | Задача 4:  / ИТ-ментор Михаил | Вопросы и демо-ссылка в репозитории | Выдуманные минуты консультаций | `operational_hygiene` |
| TRK-05 | tracker | Задача 5: KPI = назначенные демо (3–5) | Живой счёт только .local/commercial-ops/ | Назначенные демо как git-факт | `operational_hygiene` |
| TRK-06 | tracker | Задача 6: монетизация при открытом коде | Варианты A/B к обсуждению; LICENSE MIT; ADR-002 accepted | Трекер согласовал Tangl/10D/SKU | `operational_hygiene` |
| TL-01 | techlab | КТ#2 (до 20.08): этап МИК «доработка» | Предварительная версия в ЛК; GitHub прототип; видео — человек | Валидация эффективности начата; внедрение начато | `fixture_demo` |
| TL-02 | techlab | Критерии пилота 2 млн ₽ (interim ≥0.60, SLA, BCF в СОД) | Протокол измерения согласован как методика | Фактическое достижение критериев на комплекте Самолёта | `protocol_planning` |
| MIK-01 | mik | Соглашение / акт / финотчётность Фонда (M2, M7, M8) | Контур документирован; формы не сочиняем | Самодельные шаблоны Фонда; акт с fixture-цифрами | `not_licensed` |
| MIK-02 | mik | Четырёхэтапная модель: доработка → валидация → внедрение | Стадия = доработка (КТ#2) | Валидация эффективности / внедрение как текущий факт | `operational_hygiene` |
| IND-01 | industry | buildingSMART IDS 1.0 (final standard, 1 June 2024) | IDS checking (IfcTester) + IDS audit (XmlIdsDocumentAuditor / XSD 1.0) | IDS audit = checking = Samolet EIR; IDS 1.1 как approved standard | `engine_regression` |
| IND-02 | industry | ISO 19650-2:2018 cl. 5.6–5.7 (review / authorize) | summary.passed = Shared-gate technical status (ADR-001) | Automated check replaces appointing-party authorization | `fixture_demo` |
| IND-03 | industry | Solihin & Eastman 2015 rule classes | Class 1–3 inventory of in-repo rules; class 4 not claimed | SP 63 template = proof of solution | `engine_regression` |
| IND-04 | industry | ПНСТ 909-2024 (Renga publisher pack) | Aggregated 18/22 IDS runtime_clean snapshot 05.08 after ToS GO | Свежий 18/22; customer precision; эталон Самолёта | `open_bench` |
| IND-05 | industry | IFC-Bench v2 / Ishigaki-IDS-Bench (open science) | Countable 27/1026; gold XML processability 166/166; observation unit stated | Paper generation F1; 514 false-pass; product accuracy | `open_bench` |

## KT#3 (03–21.09) — что должно измениться, чтобы снять NO_GO

NO_GO снимается только при CLOSED RT-001 + RT-002 + RT-003, не этим файлом.

| ID | Условие КТ#3 |
|---|---|
| SAM-01 | Без изменения роли: эксперт остаётся уполномочивающим (ISO 19650-2 5.7) |
| SAM-02 | Подписанный EIR/IDS Самолёта + customer_pack_hash |
| SAM-03 | Размеченный 2D-корпус заказчика; VLM остаётся advisory |
| SAM-04 | ODA trial = измерение KT#3, не покупка и не product claim |
| SAM-05 | Корпус + ≥2 разметчика + κ/α; federated MEP + signed clearance (RT-003) |
| SAM-06 | Замер на customer pack с corpus_kind=customer |
| SAM-07 | Log + screenshot + hashes именованного CDE Самолёта |
| TRK-01 | КТ#3 — итоговое решение; победителей определяют заказчики |
| TRK-02 | Повтор на customer packs, не на wall-fixture |
| TRK-03 | Корпус ПД+экспертиза по-прежнему отсутствует |
| TRK-04 | Минуты только после заметок владельца |
| TRK-05 | Owner file; git не изобретает воронку |
| TRK-06 | Решение коммерции — вне кода |
| TL-01 | КТ#3 03–21.09 — итоговое решение |
| TL-02 | Замеры только после intake-gates |
| MIK-01 | VERIFY_WITH_OPERATOR до получения форм |
| MIK-02 | Следующие этапы — после решения заказчиков на КТ#3 |
| IND-01 | Customer IDS pack remains RT-002 |
| IND-02 | Организационный акт 5.7 остаётся за экспертом |
| IND-03 | Class 4 только с расчётным solver, которого нет |
| IND-04 | Полный extract + сценарии 3/18/21/22, если издатель даст IDS |
| IND-05 | Не заменяет L3 customer corpus (Mushkani et al. project-level unit) |

## Evidence pointers

- `SAM-01`: `docs/architecture/ADR-001-verdict-ownership-2026.md`
- `SAM-02`: `python -m aerobim.tools.run_demo_ifc_acceptance_gate`
- `SAM-03`: `python -m aerobim.tools.run_demo_vertical_slice`
- `SAM-04`: `docs/architecture/ADR-003-dwg-oda-trial-kt3-2026.md`
- `SAM-05`: `docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`
- `SAM-06`: `python -m aerobim.tools.measure_package_sla`
- `SAM-07`: `docs/pilot-claim-boundary-2026.md`
- `TRK-01`: `docs/partners/_2026_08_16.md`
- `TRK-02`: `docs/evidence/ifc-release-matrix-2026-08.md`
- `TRK-03`: `docs/evidence/DATASET_HUNT_LOG_2026_08.md`
- `TRK-04`: `docs/demo/CONSULTATIONS_2026_08_14.md`
- `TRK-05`: `docs/gtm/COMMERCIAL_AND_OPEN_CORE_2026_08_14.md`
- `TRK-06`: `docs/architecture/ADR-002-open-core-commercial-boundary-2026.md`
- `TL-01`: `docs/pilot/KT2_UPLOAD_PACK_2026_08_14.md`
- `TL-02`: `docs/partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md`
- `MIK-01`: `docs/partners/MIK_PILOT_COMPLIANCE_2026.md`
- `MIK-02`: `docs/docs.md`
- `IND-01`: `samples/ids-xsd/ids.xsd`
- `IND-02`: `docs/architecture/ADR-001-verdict-ownership-2026.md`
- `IND-03`: `docs/evidence/solihin-rule-classes-2026-08.md`
- `IND-04`: `docs/evidence/PNST909_22_SCENARIO_COVERAGE_AXIS_2026_08.md`
- `IND-05`: `docs/evidence/ifc-bench-v2-smoke-latest.json`
