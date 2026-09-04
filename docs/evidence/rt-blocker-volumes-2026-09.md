<!-- claims-lint: allow-file reason="RT volume split; substitutes close measurement only; undifferentiated closes stay false; customer_go false" -->
---
title: "RT-001 / RT-002 / RT-003 — measurement substitutes vs residuals"
date: "2026-09-04"
last_updated: "2026-09-05"
status: active
version: "1.3.1"
checkpoint: GO
go_kind: regulatory_measurement_mvp
customer_go: false
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: measurement_proxy_not_customer
claim_boundary: >
  Public/synthetic proxies and git-safe channel-pack carriers close measurement
  volumes. Undifferentiated RT-001/002/003 stay OPEN. Not product accuracy. Not MEP
  delivered. Not a Samolet signature. Checkpoint GO; customer_go false.
---

# Блокеры RT: чем заменили Самолёта, что осталось

Машинный SSOT: `python -m aerobim.tools.export_rt_blocker_volumes`  
Домен: `aerobim.domain.rt_blocker_volumes`.

Недифференцированные `closes_rt001` / `closes_rt002` / `closes_rt003` остаются **false**. Checkpoint **`GO`** (`regulatory_measurement_mvp`). `customer_go` **false**. Схема объёмов **1.5.0**: машинные ключи `b1`/`b2`/`b3` однозначны. Речевая литера **RT-001b** = только `b2_criterion_dual_rater` (люди, OPEN). Запрещено произносить «RT-001b CLOSED». `PrecisionClaim.publishable` по-прежнему требует `corpus_kind=customer` и ≥2 разметчиков. Это не перекраска `customer_go`.

## Замена (контур измерения)

| ID | Том | Статус | Чем заменили отсутствие Самолёта |
|---|---|---|---|
| **RT-001** | `a_content_pairing` | **CLOSED** | Типовые замечания экспертизы РФ (Эксп. Б: Киров КР n=24, 4 «обнаруживается») + публичные IDS экспертизы + учебный комплект / инъекция / синтетические labels. Это **content** (Messick), не criterion |
| **RT-001** | `b1_protocol_rehearsal` (`b_protocol_rehearsal`) | **CLOSED** | Два независимых симулированных прохода (`sim-rater-a` / `sim-rater-b`) на тех же 28 единицах учебного комплекта. Живые κ≈0.70, α≈0.71, AC1≈0.87. Не люди, не LLM. Не речевая литера RT-001b |
| **RT-002** | `a_regulatory` | **CLOSED** | Публичные IDS Мособлгосэкспертизы (**24** `.ids`), СПб ГАУ ЦГЭ (**22** `.ids`, `signed_by_customer=false`), ЦИМ АГР Москвы (**4** `.ids` + pack `moscow_agr_2026`, city as publisher). Линейка измерения, не EIR Самолёта. Машинный порог: ≥20 MOEXP + ≥15 CGE + ≥3 AGR |
| **RT-002** | `b_eir_carrier` | **CLOSED** | EIR v4.0 + BIM-стандарт v4.0 на канальном комплекте как **текст** (deep-study 30.08; имён в git нет). Это носитель EIR назначающей стороны, не `customer_approved` IDS |
| **RT-003** | `a_federated_geometric_rehearsal` | **CLOSED** | Посаженный IfcClash в git: `clash-federated-box-{a,b}.ifc` и pipe vs wall. Оба прогона **RUN**, ≥1 hit. Не system-aware MEP |
| **RT-003** | `b2_ifc_system_graph_rehearsal` (речь RT-003b) | **CLOSED** | Учебная HVAC-фикстура: 2× `IfcSystem` + `IfcRelAssignsToGroup`. Это граф систем, не труба≠стенка. `geometry_verified=false`, `synthetic=true` |
| **RT-003** | `b1_navis_federation_carrier` | **CLOSED** | Три NWD-федерации на канальном комплекте (по одной на дом). Нативный NWD не читаем. Не граф `IfcSystem` заказчика |

## Остаток (не подменяется)

| ID | Том | Статус | Почему нельзя закрыть подменой |
|---|---|---|---|
| **RT-001** | `b2_criterion_dual_rater` (речь **RT-001b**) | **OPEN** | Два независимых человека; κ/α; заключение экспертизы **на тот же том**. Симуляция протокола — не двое людей. Инъекция и один автор фикстуры — не два разметчика. LLM не разметчик |
| **RT-001** | `c_customer_corpus` | **OPEN** | Хеш-пакет Самолёта не в git |
| **RT-002** | `c_corporate_signed` (`b_corporate`) | **OPEN** | Подпись Самолёта на профиле приёмки / `customer_approved`. Текст EIR и город-издатель ≠ подпись |
| **RT-003** | `b3_mep_system_clash` (речь **RT-003c**) | **OPEN** | `mep_system_clash=NOT_VERIFIED`. 0 duct/pipe/cable в IFC комплекта. `IfcFlowTerminal` на АР — не граф заказчика. Репетиция HVAC ≠ координация инженерки на пакете |
| **RT-003** | `c_customer_federated_ifc` | **OPEN** | Нет выгрузки NWD→IFC заказчика и signed clearance |
| **CDE T2** | импорт BCF | **NOT_VERIFIED** | Структурный ZIP (T1) ≠ журнал импорта в СОД |

Open benches (AEC-Bench, IFC-Bench, GNI) по-прежнему **другой контур**, чем RT-001b: они не пары «российский том ПД ↔ заключение экспертизы».

Речь: измерение ведём на публичных IDS, тексте EIR/стандарта с канала и учебных комплектах; подпись Самолёта, граф ИОС в IFC и публикуемая точность — отдельные тома.
