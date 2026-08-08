<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Kimi K3 × Самолёт (Задача №7): сценарии «от и до»"
status: study
version: "1.0.0"
last_updated: "2026-07-27"
claim_boundary: "Kimi K3 работает ТОЛЬКО в AI_ADVISORY: даёт кандидатов/черновики/объяснения, НИКОГДА не выставляет summary.passed (ТР-2/ТР-27/ТР-31). Все сценарии — advisory+HITL; вердикт у детерминированного движка и эксперта. Точность — только через harness на adjudicated-корпусе (RT-001). Checkpoint NO_GO."
tags: [aerobim, kimi-k3, samolet, scenarios, vlm, advisory, tz]
---

# Kimi K3 × требования Самолёта: полная проработка сценариев

Спутник [`KIMI_K3_INTEGRATION_STUDY_2026_07_27.md`](KIMI_K3_INTEGRATION_STUDY_2026_07_27.md)
(факты о модели) и [`VLM_OCR_COMPARISON_PROTOCOL_2026_08`](../pilot/VLM_OCR_COMPARISON_PROTOCOL_2026_08.md).
Трёхисточниковое согласование (Техлаб × МИК):
[`KIMI_K3_MIK_TECHLAB_ALIGNMENT_2026_07_27.md`](KIMI_K3_MIK_TECHLAB_ALIGNMENT_2026_07_27.md).
Здесь — разбор **каждого** сценария ТЗ (ТР-3..24) и **всех 20** типовых ошибок
(`samples/benchmarks/samolet-typical-errors-catalog.json`) в терминах: что K3
делает, где граница, tier данных, риск, вердикт.

**Инвариант (не обсуждается):** ТР-2 «только `DETERMINISTIC_VALIDATION`
выставляет `summary.passed`»; ТР-27 DeterminismGate «advisory↔engine → движок
побеждает, `DivergenceRecord`»; ТР-31 «LLM/VLM только advisory + HITL».
K3 везде ниже — **кандидат/черновик/объяснение**, не вердикт.

## 1. Размещение по контурам (от и до)

| Контур | Роль K3 | Кто владеет результатом |
|---|---|---|
| **INGESTION** | Чтение сканов/растровых листов (region+VLM, ТР-4/5/7) → **кандидатные** аннотации/регионы с `confidence` | Детерминированные экстракторы + IDS; K3-значения не авторитетны |
| **DETERMINISTIC_VALIDATION** | **НИКОГДА не входит** (ТР-2) | Движок (IFC/IDS/cross-doc/clash/quantity) |
| **AI_ADVISORY** | Дом K3: `drawing_vlm_read`, `requirement_interpret`, `norm_corpus_retrieve` (reasoning), объяснение противоречий | Advisory-issue `origin="advisory"`; не флипает `passed` |
| **EVIDENCE_REPORTING** | Черновик текста замечания RU/EN, описание BCF-топика (ТР-21) | Шаблон/эксперт (HITL); provenance обязателен (ТР-24) |

Правило: результат K3, попадая на путь вердикта, проходит DeterminismGate —
при расхождении с движком фиксируется `DivergenceRecord`, побеждает движок.

## 2. Сквозной прогон (residential AR-комплект)

Вход: ПД+РД (АР), IFC, ТЗ (нарратив), расчёт площадей, 3 скана листов (штамп+план).

1. **Ingest**: IFC → IfcOpenShell (детерм.); сканы → K3 `drawing_vlm_read`
   (tier A на открытых данных / малый Kimi-VL на NDA) → кандидатные аннотации
   размеров/марок + регионы; low-confidence → `hitl_required` (ТР-7a).
2. **Requirement extract**: ТЗ структурировано детерм.; неоднозначный нарратив →
   K3 `requirement_interpret` → кандидатные `ParsedRequirement` (не sign-off).
3. **Deterministic validation**: IDS/properties (ТР-8), cross-doc ПД↔РД↔ТЗ↔расчёт
   (ТР-9/10/12), clash (ТР-14), quantity (ТР-16) — **движок**. K3 не участвует.
4. **Advisory**: K3 объясняет найденное движком противоречие; предлагает pairing
   для неоднозначных секций (ТР-10) — как кандидат для детерм. компаратора.
5. **Evidence**: движок породил issue → K3 черновик замечания (ТР-21) с
   `finding_id/source_id/evidence_refs`; эксперт правит (HITL, ТР-22); BCF-экспорт.
6. **Verdict**: `summary.passed` — только из детерм. issues; K3 off/on → **идентичен**
   (тест advisory-OFF==ON обязателен).

## 3. Матрица по ТР

Легенда роли: **CAND** (кандидат-вход, детерм. проверяет) · **EXPLAIN** (объяснение/черновик) ·
**NONE** (K3 не нужен) · **FORBIDDEN** (запрещён как источник вердикта).

### 3.1 Графика (ТР-3,4,5,7,7a,19)

| ТР | Сценарий | Роль K3 | Граница / риск |
|---|---|---|---|
| ТР-3 | Атрибуты/геометрия IFC | NONE (IfcOpenShell) | K3 лишь NL-запрос к модели (advisory `ifc_kg_query`) |
| ТР-4 | Аннотации/размеры из 2D | CAND | native vision; paraphrase divergence → нормализация обязательна |
| ТР-5 | OCR сканов PDF | CAND | сильная сторона K3; low-conf → HITL; zero-yield ≠ pass |
| ТР-7 | Регионы (штамп/таблицы) + VLM | CAND | режим `detector_vlm`; регионы → `DrawingRegionRef` |
| ТР-7a | HITL для unmatched/low-conf | CAND | event `drawing_region_escalated`; `cv_human_level=MISSING` неизменен |
| ТР-19 | Размер чертёж↔IFC | CAND | K3 читает размер (кандидат) → детерм. сравнение выносит вердикт |

### 3.2 Документы/соответствие (ТР-9,10,11,12,13)

| ТР | Сценарий | Роль K3 | Граница / риск |
|---|---|---|---|
| ТР-9 | Извлечение требований ТЗ | CAND | неоднозначный нарратив → кандидат; детерм. re-check; не sign-off |
| ТР-10 | PD↔RD section pairing | CAND | предлагает canonical-key для неоднозначных пар; вердикт — компаратор |
| ТР-11 | Norm packs / RASE | EXPLAIN | помогает черновику RASE-правил с **цитатами**; `customer_approved` — только подпись заказчика (**RT-002**), K3 не делает pack approved |
| ТР-12 | Сверка расчётов (load/qty) | CAND | извлекает числа из расчёта (кандидат) → детерм. numeric compare |
| ТР-13 | Независимая корректность расчёта | **FORBIDDEN** | K3 ≠ solver; `calculation_correctness=NOT_IMPLEMENTED` неизменен (RT-010) |

### 3.3 Ошибки (ТР-14,15,16,17,18)

| ТР | Сценарий | Роль K3 | Граница / риск |
|---|---|---|---|
| ТР-14 | Геометрический clash | EXPLAIN | детекция — IfcClash; K3 лишь триаж/описание топика |
| ТР-15 | MEP system-aware clash | EXPLAIN (гипотеза) | **RT-003**; `geometry_verified=False`; `mep_system_clash` никогда OK; **высокий риск proactiveness** |
| ТР-16 | Площади/количества | CAND | quantity-алгебра — движок; K3 читает площади со сканов/спек |
| ТР-17 | Неэффективное пространство | OUT | P4, только если KPI согласован; иначе out-of-scope |
| ТР-18 | Несогласованность разделов | EXPLAIN | объясняет противоречие; вердикт — cross-doc движок |

### 3.4 Поддержка эксперта (ТР-20,21,22,23,24)

| ТР | Сценарий | Роль K3 | Граница / риск |
|---|---|---|---|
| ТР-20 | Подсветка `problem_zone` | CAND | зона привязана к региону/GUID; K3 не «придумывает» координаты |
| ТР-21 | Черновик замечания RU/EN | **EXPLAIN (высокая ценность)** | лучше шаблонов; HITL-редактируемо; provenance stamped; не финал |
| ТР-22 | Редактирование (HITL) | EXPLAIN | K3 черновик → эксперт правит → `edited_remark` |
| ТР-23 | Приоритизация | EXPLAIN | скор — детерм. `compute_issue_priority`; K3 лишь объясняет rationale |
| ТР-24 | Provenance | (обязательство) | вывод K3 обязан нести `evidence_refs` (`advisory_trace_record` требует) |

## 4. Матрица по каталогу типовых ошибок (SAM-TYP-001..020)

| Ошибка | Дисциплина / категория | Роль K3 | Примечание |
|---|---|---|---|
| SAM-TYP-001 огнестойкость spec↔calc↔IFC | fire / CROSS_DOC | CAND (читает значения) | вердикт HARD_CONFLICT — движок |
| SAM-TYP-002 площадь calc↔ТЗ | arch / CROSS_DOC | CAND | numeric cross-doc — движок |
| SAM-TYP-003 толщина стены < критерия | struct / IFC | NONE | property-правило детерм. |
| SAM-TYP-004 площадь помещения > лимита | fire / IFC | NONE | quantity-правило детерм. |
| SAM-TYP-005 аннотация↔IFC расхождение | arch / DRAWING | CAND | K3 читает аннотацию (кандидат) → детерм. match |
| SAM-TYP-006 отсутствует MEP-параметр | mep / IFC | NONE | IDS exists-правило; нужен customer MEP IFC |
| SAM-TYP-007..011 отсутствующие/несоотв. свойства AR | arch/fire / IFC | NONE | IDS/property детерм.; K3 лишь черновик замечания |
| SAM-TYP-012 площадь РД↔ПД | arch / CROSS_DOC | CAND/EXPLAIN | pairing-кандидат + объяснение; вердикт — компаратор |
| SAM-TYP-013 тип двери ПД без РД | arch / CROSS_DOC | EXPLAIN | STAGE_MISMATCH — движок |
| SAM-TYP-014 материал фасада РД↔ПД | arch / CROSS_DOC | CAND | строковый mismatch — детерм.; K3 нормализует синонимы (кандидат) |
| SAM-TYP-015 РД на устаревшую ревизию ПД | arch / CROSS_DOC | NONE | VERSION_MISMATCH детерм. |
| SAM-TYP-016 IFC schema pre-gate | openbim / IFC | NONE | чисто детерм. |
| SAM-TYP-017 IDS-документ некорректен | openbim / IDS | NONE | defusedxml + XSD-аудит детерм. |
| SAM-TYP-018 масштаб единиц IFC | openbim / IFC | NONE | детерм. |
| SAM-TYP-019 жёсткая геометрич. коллизия | mep / SPATIAL | EXPLAIN | IfcClash детекция; K3 триаж |
| SAM-TYP-020 системная MEP-коллизия | mep / SPATIAL | EXPLAIN (гипотеза) | **gap MEP-CLASH-001 / RT-003**; никогда OK; proactiveness-риск |

**Итог по каталогу:** K3 добавляет ценность как **CAND** там, где вход —
пиксели/нарратив (чтение сканов, извлечение чисел, нормализация синонимов) и как
**EXPLAIN** для черновиков/объяснений. Для чисто структурных проверок
(SAM-TYP-003/004/006-011/015-018) K3 **не нужен** — их владеет детерминизм.

## 5. Cross-cutting под KPI Самолёта

| Критерий пилота | Как взаимодействует K3 | Правило |
|---|---|---|
| **SLA ≤30 мин** | max-effort K3 добавляет латентность | K3 advisory **вне критического пути** вердикта: параллельно/best-effort, degrade-gracefully; таймаут+бюджет токенов; сбой K3 ≠ сбой пакета |
| **TP/(TP+FP) ≥60% interim / >90% цель** | K3 — advisory; кандидаты могут поднять recall | Измеряется **только** `evaluate_detection_precision` на adjudicated-корпусе (RT-001); precision K3 отдельно не заявляется |
| **Экономия ≥20%** | Черновики замечаний (ТР-21) + чтение сканов экономят время эксперта | Замер vs baseline-часы (intake-gate); не постулируется |
| **BCF в СОД** | K3 обогащает описания топиков | Текст grounded; T2-evidence — отдельно (RT-008) |
| **Каталог ≥20 ошибок** | K3 — CAND/EXPLAIN по 8-10 из 20 | `customer_confirmed=0` до подтверждения площадкой |

### Данные (tier — жёстко)

- **Открытые/fixture** → K3 API (tier A) через SSRF-гард. Годится для бенчей/демо.
- **NDA-комплект Самолёта** → K3 API запрещён; только малый Kimi-VL on-prem (tier C)
  или детерминизм-only. Полный K3 (2.8T, 64+ ускорителей) вне пилотного железа.
- Config-гейт: на customer-профиле tier A заблокирован; K3 включён но не
  сконфигурирован → capability `FAILED` (fail-closed, не тихий skip).

### Детерминизм и proactiveness

- `temperature=0` + пин снапшота + логи для eval; advisory-OFF==ON держится.
- **«Excessive proactiveness» (документирована Moonshot)** — главный риск для
  приёмки стройки: K3 склонен решать за пользователя. Обезврежено архитектурно
  (advisory-only, engine wins, HITL) + явные ограничения в system-prompt.

## 6. Что K3 НЕ делает НИКОГДА (forbidden)

1. Не выставляет `summary.passed` и не влияет на него (ТР-2/27/31).
2. Не делает norm pack `customer_approved` (RT-002 — только подпись заказчика).
3. Не подтверждает корректность расчёта (ТР-13 — не solver, RT-010).
4. Не делает `mep_system_clash`/`dwg_dxf`/`cv_human_level` = OK (honesty-гейт).
5. Не отправляет NDA-данные в публичный API.
6. Сырой вывод VLM не идёт в правило без нормализации и grounding.

## 7. Вердикт по сценариям (приоритет внедрения)

| Приоритет | Сценарии | Обоснование |
|---|---|---|
| **P1 (высокая ценность, низкий риск)** | ТР-21 черновики замечаний; ТР-5/7 чтение сканов как CAND | прямая экономия времени эксперта; advisory, HITL, grounded |
| **P2 (условно)** | ТР-4/19 размеры-кандидаты; ТР-9/10 interpret/pairing; ТР-11 RASE-черновик | нужны нормализация + adjudication; RT-002 для норм |
| **P3 (только гипотеза/объяснение)** | ТР-14/15/18 триаж/объяснение clash и MEP | детекция у движка; MEP — RT-003, proactiveness-риск |
| **OUT** | ТР-13 корректность расчёта; ТР-17 эффективность; полный K3 на NDA | solver/железо/scope |

**Условие любого внедрения:** победа в [протоколе VLM/OCR](../pilot/VLM_OCR_COMPARISON_PROTOCOL_2026_08.md)
(T1–T4, CI/p-values) **и** прохождение closed-contour fail-closed. До этого K3 —
исследовательский advisory-кандидат, не поставляемая возможность.

## 8. Явно НЕ заявляется

- K3 не «читает чертежи как инженер»; не заменяет эксперта; не ускоряет вердикт
  (только черновики/чтение как вход).
- Никаких чисел точности/экономии без замера на корпусе заказчика (RT-001).
- Подключение K3 **не** двигает Checkpoint (`NO_GO` до RT-001/002/003).
- Все «CAND/EXPLAIN» выше — проектные роли, не подтверждённые на данных Самолёта.
