<!-- claims-lint: allow-file reason="Kane IUA ledger; TZ 90%/SLA as blocked inferences; NO_GO" -->
---
title: "Interpretation/Use ledger — Самолёт × трекер × Техлаб/МИК × отрасль"
date: "2026-08-26"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >-
  Kane IUA over existing AeroBIM scores. Licensed uses stop at fixture demo, engine regression, open-bench countable subsets, gold-IDS processability, and protocol planning. Not customer precision, not TZ >90%, not customer SLA, not Checkpoint GO.
---

# Interpretation/Use ledger (КТ#2 → КТ#3)

Валидность — свойство **вывода из оценки**, не свойства программы (Messick 1995; Kane 2013). Этот файл — SSOT: что текущие цифры AeroBIM имеют право значить для Самолёта, трекера проекта, Техлаба, МИК и отраслевых стандартов, и чего они значить не имеют.

- Checkpoint **NO_GO**
- IUA freeze (construct-validity object, not HEAD): `f9389bf`
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
| SAM-08 | samolet | ТР-16/19: площади помещений / чертёж↔IFC | 6 AR IFC: 10599 IfcSpace, 0 NetFloorArea; coverage_map_only | Площади квартир сверены с ТЭП; RT-001 CLOSED | `engine_regression` |
| SAM-09 | samolet | ТР-8: огнестойкость стены vs ТЗ (класс II / C0) | 62033 walls; FireRating 5.7% EI45 only; not TZ II/C0 | Fire check delivered; fixture REI60 = customer finding | `engine_regression` |
| TRK-01 | tracker | Задача 1: доработать продукт к КТ#2 (20.08) | IFC Acceptance Gate + HD fail-closed; live CLI; Checkpoint NO_GO | Checkpoint GO / market GO = customer GO | `fixture_demo` |
| TRK-02 | tracker | Задача 2: таблица IFC2X3 / IFC4 / IFC4X3 | Fixture kernel n=20: findings 5/4/6, passed=false, clash=skipped | Product accuracy / customer SLA по релизам IFC | `engine_regression` |
| TRK-03 | tracker | Задача 3: поиск и прогон открытых датасетов | IFC-Bench 27/1026 countable; PNST CLI skip-honest; Ishigaki XML processability | Open bench = RT-001; свежий 18/22; Harbor agent run; DrawingVQA в MIT tree | `open_bench` |
| TRK-04 | tracker | Задача 4: научный консультант / ИТ-ментор | Вопросы и демо-ссылка в репозитории | Выдуманные минуты консультаций | `operational_hygiene` |
| TRK-05 | tracker | Задача 5: KPI = назначенные демо (3–5) | Живой счёт только в локальном операторском слое (не в git) | Назначенные демо как git-факт | `operational_hygiene` |
| TRK-06 | tracker | Задача 6: монетизация при открытом коде | Варианты A/B к обсуждению; LICENSE MIT; ADR-002 accepted | Трекер согласовал Tangl/10D/SKU | `operational_hygiene` |
| TL-01 | techlab | КТ#2 (до 20.08): этап МИК «доработка» | Предварительная версия в ЛК; GitHub прототип; видео не прилагаем, показ = живой CLI | Валидация эффективности начата; внедрение начато | `fixture_demo` |
| TL-02 | techlab | Критерии пилота 2 млн ₽ (interim ≥0.60, SLA, BCF в СОД) | Протокол измерения согласован как методика | Фактическое достижение критериев на комплекте Самолёта | `protocol_planning` |
| TL-03 | techlab | Участие в «Техлаб Москва»: физлица или команда 1–10 (FAQ i.moscow/techlab) | ИП/ООО не условие входа; приз — платный пилот 2 млн ₽ | Без юрлица нельзя участвовать / нельзя принять приз — как факт Положения | `operational_hygiene` |
| TL-04 | techlab | Сравнение 1: ПД/РД ↔ АГО/АГР (листы, фасады, ТЭП) | Filename coindex on coverage map; overlay remains fixture-only | АГР/QTO сданы; задача 1 закрыта | `engine_regression` |
| TL-05 | techlab | Сравнение 2: ПД ↔ каталоги / EIR LOD | Catalog and EIR workbooks as carriers; not customer_approved IDS | IDS Самолёта утверждён из Стандарта | `protocol_planning` |
| TL-06 | techlab | Сравнение 3: планировки ОПР/ПД/РД (оси, помещения, двери) | IfcSpace/IfcDoor presence is coverage_map_only; QTO absent is Missing | Планировки сверены по стадиям; площади проверены | `engine_regression` |
| TL-07 | techlab | Сравнение 4: планировки ↔ ИРД / проектное ТЗ | II/C0, wall EI, door EI, fixture REI60 are different constructs | Планировки соответствуют ТЗ; огнестойкость сертифицирована | `engine_regression` |
| TL-08 | techlab | Сравнение 5: АР/КР/ПБ/ТХ/ИОС между собой | AR+KR IFC; other disciplines PDF; IfcFlowTerminal in AR ≠ IOS model | MEP delivered; federated clash delivered | `protocol_planning` |
| TL-09 | techlab | Сравнение 6: повторная проверка ↔ выданные замечания | After-tree thicker than before is coverage_map_only; OEP is not gold | Замечания закрыты; книга ОЭП = gold | `protocol_planning` |
| TL-10 | techlab | Сравнение 7: армирование ↔ расчётные карты (Solihin 4) | No IfcReinforcingBar; wall pitch pset ≠ class 4; .lir not parsed | Арматура сверена с расчётом; LIRA solved | `engine_regression` |
| MIK-01 | mik | Соглашение / акт / финотчётность Фонда (M2, M7, M8) | Контур документирован; формы не сочиняем; 449-ПП ≠ вход в Техлаб | Самодельные шаблоны Фонда; акт с fixture-цифрами; ИП как вход | `not_licensed` |
| MIK-02 | mik | Четырёхэтапная модель: доработка → валидация → внедрение | Стадия = доработка (КТ#2) | Валидация эффективности / внедрение как текущий факт | `operational_hygiene` |
| IND-01 | industry | buildingSMART IDS 1.0 (final standard, 1 June 2024) | IDS checking (IfcTester) + IDS audit (XmlIdsDocumentAuditor / XSD 1.0) | IDS audit = checking = Samolet EIR; IDS 1.1 как approved standard | `engine_regression` |
| IND-02 | industry | ISO 19650-2:2018 cl. 5.6–5.7 (review / authorize) | summary.passed = Shared-gate technical status (ADR-001) | Automated check replaces appointing-party authorization | `fixture_demo` |
| IND-03 | industry | Solihin & Eastman 2015 rule classes | Class 1–3 inventory of in-repo rules; class 4 not claimed | SP 63 template = proof of solution | `engine_regression` |
| IND-04 | industry | ПНСТ 909-2024 (Renga publisher pack) | Aggregated 18/22 IDS runtime_clean snapshot 05.08 after ToS GO | Свежий 18/22; customer precision; эталон Самолёта | `open_bench` |
| IND-05 | industry | IFC-Bench v2 / Ishigaki-IDS-Bench (open science) | Countable 27/1026; gold XML processability 166/166; observation unit stated | Paper generation F1; 514 false-pass; product accuracy | `open_bench` |
| IND-06 | industry | AEC-Bench (Mankodiya et al. 2026, arXiv:2603.29199) | Inventory 196 tasks / 9 families; Harbor agent NOT_RUN; authors: coding agents fail visual grounding | AEC-Bench run as product drawing literacy / RT-001 CLOSED | `open_bench` |
| IND-07 | industry | LLM-as-judge 2026 (arXiv:2606.19544; 2509.20293; 2604.15224) | VLM remains advisory candidate; TP/FP require dual human raters and κ | Model confirms findings / judges precision / stakes-framed verdict | `protocol_planning` |
| IND-08 | industry | Clash management 2026 (Buildings 16(13):2623) + Mehrbod/Hu/Lin | Geometric overlap on fixture; mep_system_clash=NOT_VERIFIED | MEP delivered; AABB inventory as coordination-complete | `protocol_planning` |
| IND-09 | industry | ISO 19650-6:2025 health and safety information | Not implemented; Shared-gate is 5.6-like control only (ADR-001) | ISO 19650 compliant / Part 6 delivered / 5.7 automated | `not_licensed` |
| IND-10 | industry | buildingSMART IDS 1.1 (feedback 2026, not final) | IDS 1.0 remains the approved standard (1 June 2024) | IDS 1.1 as current standard / certified profile | `engine_regression` |
| IND-11 | industry | EGCC 2026 (arXiv:2607.29058) constraint checking | False-pass 41-52%; authors: not for autonomous approval | EGCC % = AeroBIM on customer PD; autonomous approve | `open_bench` |
| IND-12 | industry | DrawingVQA 2026 (arXiv:2607.15418) issued-for-construction sheets | Pros 94.9% vs Gemini-2.5-pro 71.7%; QTO weak | DrawingVQA as AeroBIM product accuracy / TZ task 1 done | `open_bench` |
| IND-13 | industry | Jurisdiction IFC pre-check 2026 (CORENET X, RAVA3.5.3, city AGR) | City-as-publisher pattern = RT-002a analog; not appointing-party EIR | Public permit IDS = Samolet-signed profile / Task 07 delivered | `open_bench` |

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
| SAM-08 | QTO area only after export with quantities or signed OOS |
| SAM-09 | Customer IDS for fire class, not demo REI60 |
| TRK-01 | КТ#3 — итоговое решение; победителей определяют заказчики |
| TRK-02 | Повтор на customer packs, не на wall-fixture |
| TRK-03 | Корпус ПД+экспертиза по-прежнему отсутствует |
| TRK-04 | Минуты только после заметок владельца |
| TRK-05 | Owner file; git не изобретает воронку |
| TRK-06 | Решение коммерции — вне кода |
| TL-01 | КТ#3 03–21.09 — итоговое решение |
| TL-02 | Замеры только после intake-gates |
| TL-03 | Оплату приза уточнять только по соглашению Партнёра и Фонда |
| TL-04 | Sheet gold + dual raters; VLM stays advisory |
| TL-05 | Appointing-party IDS with pack_hash (RT-002b) |
| TL-06 | QTO export or signed OOS; RD IFC if stage compare is in scope |
| TL-07 | Customer fire IDS, not demo REI60 |
| TL-08 | Federated MEP IFC or written MEP-OOS (RT-003) |
| TL-09 | Dual named raters + κ on a frozen remark set (RT-001) |
| TL-10 | Bar entities in IFC or written OOS of task 7 |
| MIK-01 | VERIFY_WITH_OPERATOR до получения форм |
| MIK-02 | Следующие этапы — после решения заказчиков на КТ#3 |
| IND-01 | Customer IDS pack remains RT-002 |
| IND-02 | Организационный акт 5.7 остаётся за экспертом |
| IND-03 | Class 4 только с расчётным solver, которого нет |
| IND-04 | Полный extract + сценарии 3/18/21/22, если издатель даст IDS |
| IND-05 | Не заменяет L3 customer corpus (Mushkani et al. project-level unit) |
| IND-06 | Harbor only as labeled open-bench, never as Samolet PD |
| IND-07 | PrecisionClaim.publishable remains the only accuracy gate |
| IND-08 | Signed clearance + federated customer IFC (RT-003) |
| IND-09 | Do not claim Part 6; 5.7 stays human |
| IND-10 | Stay on IDS 1.0 checking + audit split until 1.1 is final |
| IND-11 | Four-state Meets/Missing/Uncertain; expert stays in the loop |
| IND-12 | VLM advisory only; no sheet-level sign-off |
| IND-13 | Keep RT-002a and RT-002b unmixed |

## Evidence pointers

- `SAM-01`: [ADR-001-verdict-ownership-2026.md](../architecture/ADR-001-verdict-ownership-2026.md)
- `SAM-02`: `python -m aerobim.tools.run_demo_ifc_acceptance_gate`
- `SAM-03`: `python -m aerobim.tools.run_demo_vertical_slice`
- `SAM-04`: [ADR-003-dwg-oda-trial-kt3-2026.md](../architecture/ADR-003-dwg-oda-trial-kt3-2026.md)
- `SAM-05`: [QUALITY_MEASUREMENT_PROTOCOL_2026_08.md](../pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md)
- `SAM-06`: `python -m aerobim.tools.measure_package_sla`
- `SAM-07`: [pilot-claim-boundary-2026.md](../pilot-claim-boundary-2026.md)
- `SAM-08`: [TZ_SEAM_COVERAGE_MAP_2026_08.md](TZ_SEAM_COVERAGE_MAP_2026_08.md)
- `SAM-09`: [TZ_SEAM_COVERAGE_MAP_2026_08.md](TZ_SEAM_COVERAGE_MAP_2026_08.md)
- `TRK-01`: [pilot-claim-boundary-2026.md](../pilot-claim-boundary-2026.md)
- `TRK-02`: [ifc-release-matrix-2026-08.md](../evidence/ifc-release-matrix-2026-08.md)
- `TRK-03`: [KT2_CORPUS_SSOT_2026_08.md](../demo/KT2_CORPUS_SSOT_2026_08.md)
- `TRK-04`: [KT3_JURY_FAQ_2026_08_25.md](../demo/KT3_JURY_FAQ_2026_08_25.md)
- `TRK-05`: [ADR-002-open-core-commercial-boundary-2026.md](../architecture/ADR-002-open-core-commercial-boundary-2026.md)
- `TRK-06`: [ADR-002-open-core-commercial-boundary-2026.md](../architecture/ADR-002-open-core-commercial-boundary-2026.md)
- `TL-01`: [docs.md](../docs.md)
- `TL-02`: [PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md](../partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md)
- `TL-03`: [TECHLAB_TASK_07_READINESS_2026.md](../partners/TECHLAB_TASK_07_READINESS_2026.md)
- `TL-04`: [TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md](TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md)
- `TL-05`: [TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md](TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md)
- `TL-06`: [TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md](TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md)
- `TL-07`: [TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md](TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md)
- `TL-08`: [TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md](TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md)
- `TL-09`: [TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md](TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md)
- `TL-10`: [TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md](TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md)
- `MIK-01`: [MIK_PILOT_COMPLIANCE_2026.md](../partners/MIK_PILOT_COMPLIANCE_2026.md)
- `MIK-02`: [docs.md](../docs.md)
- `IND-01`: [ids.xsd](../../samples/ids-xsd/ids.xsd)
- `IND-02`: [ADR-001-verdict-ownership-2026.md](../architecture/ADR-001-verdict-ownership-2026.md)
- `IND-03`: [solihin-rule-classes-2026-08.md](../evidence/solihin-rule-classes-2026-08.md)
- `IND-04`: [PNST909_22_SCENARIO_COVERAGE_AXIS_2026_08.md](../evidence/PNST909_22_SCENARIO_COVERAGE_AXIS_2026_08.md)
- `IND-05`: [ifc-bench-v2-smoke-latest.json](../evidence/ifc-bench-v2-smoke-latest.json)
- `IND-06`: [aec-bench-false-pass-2026-08.md](../evidence/aec-bench-false-pass-2026-08.md)
- `IND-07`: [ADR-001-verdict-ownership-2026.md](../architecture/ADR-001-verdict-ownership-2026.md)
- `IND-08`: [federated-clash-planted-2026-08.md](../evidence/federated-clash-planted-2026-08.md)
- `IND-09`: [ADR-001-verdict-ownership-2026.md](../architecture/ADR-001-verdict-ownership-2026.md)
- `IND-10`: [ids.xsd](../../samples/ids-xsd/ids.xsd)
- `IND-11`: [TZ_SEAM_COVERAGE_MAP_2026_08.md](TZ_SEAM_COVERAGE_MAP_2026_08.md)
- `IND-12`: [TZ_SEAM_COVERAGE_MAP_2026_08.md](TZ_SEAM_COVERAGE_MAP_2026_08.md)
- `IND-13`: [TZ_SEAM_COVERAGE_MAP_2026_08.md](TZ_SEAM_COVERAGE_MAP_2026_08.md)
