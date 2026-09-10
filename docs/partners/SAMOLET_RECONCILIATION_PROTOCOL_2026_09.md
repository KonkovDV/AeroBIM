<!-- claims-lint: allow-file reason="Reconciliation protocol; quotes forbidden claims only as KILL; single adjudicator; NO_GO" -->
---
title: "Протокол сверки «строка требования ↔ семейство проверок» — 2026-09-09"
date: "2026-09-09"
last_updated: "2026-09-09"
status: active
version: "1.3.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  Protocol for a human crosswalk of the customer's requirement-checklist
  rows against AeroBIM check families. Not product accuracy. Not a TP/FP
  gold set. One adjudicator does not make PrecisionClaim.publishable.
  Single-expert packet review is the operational mode from the 09.09 call.
  Dual raters remain the scientific path. Checkpoint GO; customer_go false.
  LLM is not a rater (ADR-001).
---

# Протокол сверки отчёта AeroBIM с книгами проверки комплекта

Единица сравнения — **строка требования** их чек-листа приёмки
(содержание требования / лист РД + статус проверки + комментарий), а не
«замечание» и не наша находка по элементу IFC. Прямой построчный процент
«сколько из ваших замечаний мы нашли» — брак независимо от значения.

## Два режима оценки (не смешивать)

| Режим | Кто | Что измеряется | Что нельзя сказать |
|---|---|---|---|
| **Операционный пилот** (созвон 09.09) | AeroBIM отдаёт пакет → один назначенный эксперт проходит по **выданным** находкам | overlap / novel / disagreement / unresolved относительно их baseline | precision, recall, κ, «точность продукта», закрытие RT-001 |
| **Научный** (publishable) | ≥2 независимых человека, adjudication, held-out | Wilson / κ / α по протоколу измерения | не переносится на колл 15.09 без корпуса и времени |

Один эксперт, который видит только выданные системой строки, **не измеряет
recall**. Baseline стороннего checker'а — reference, не Gold Standard, пока
заказчик не утвердил документ эталона письменно.

FN-first: неуверенную находку **нельзя удалять**, чтобы «не шуметь». Статусы
`advisory` / `LOW_CONFIDENCE` / `SKIPPED` / `NOT_VERIFIED` остаются в выжимке.

## Что сверяется

| Сторона | Что входит | Что не входит |
|---|---|---|
| Заказчик | строки `review_book` с заполненным статусом; шаблоны `requirement_template` — только как каталог требований | пустые шаблоны как «найденное»; ФИО и почта; строки `stage_mismatch` (лист РД при отсутствии RD IFC) |
| AeroBIM | только `pack_finding` прогона канала (14 IFC под SPF-капом) | `coverage_note`, `service_record`, `advisory_candidate`; демо-seed overlay `999…` |

Связь 1:N: одна строка требования может ссылаться на несколько `finding_id`
колонкой `customer_remark_id`. Колонка заполняется человеком. Машинный матч
по тексту запрещён.

## Разметка `machine_verifiability`

Каждая строка требования получает ровно одно значение:

| Код | Смысл |
|---|---|
| `machine_full` | проверяемо детерминированно по IFC/IDS целиком |
| `machine_partial` | машина сужает область, вердикт за человеком |
| `needs_document` | лист, том, ИРД, не модель |
| `needs_human` | согласование или инженерное суждение |
| `out_of_scope` | вне MVP |

`assigned_by` обязан быть человеком. Черновик модели допускается; строка с
`assigned_by=llm` в знаменатель не входит.

## Согласие и FN

Согласие по статусу считается **только** на пересечении
`machine_full` ∩ покрытие `checked`. Это подписывается как «согласие по
требованию», не precision и не recall.

FN — только там, где карта покрытия зафиксирована как `checked` **до**
ингеста книг (хеш карты не меняется после загрузки). Площади, арматура и MEP
на этом канале заранее `not_checked`.

Неоднозначность из-за короткой пометки заказчика (медиана ~36 символов) →
`unresolved`, не совпадение.

## Выходы

- `.local/pack-out/requirement-crosswalk.csv` + манифест
  (`dataset_status: draft`, `adjudicators: 1`, `publishable: false`).
- `precision-recall.json` появляется только после `build_detection_labels`
  при ≥2 размётчиках и 0 `unresolved`.
- В git — агрегаты без текста замечаний, ФИО и имён файлов.

## Что нельзя произносить по итогам

| ID | Формулировка | Вердикт |
|---|---|---|
| `RT-REC-01` | их сверка = точность продукта | **KILL** (один судья) |
| `RT-REC-02` | 23 машинных записи = 23 замечания | **KILL** |
| `RT-REC-03` | замечание не найдено ⇒ наш пропуск | **KILL** (сначала карта покрытия) |
| `RT-REC-04` | мы сопоставили замечания автоматически | **KILL** |
| `RT-REC-05` | сверка на их комплекте ⇒ RT-001 CLOSED | **KILL** |
| `RT-REC-06` | в отчёте нет отклонённых ⇒ мы их удалили | **KILL** |
| `RT-REC-07` | демо-seed сверили с книгой канала | **KILL** (другой комплект) |
| `RT-REC-08` | пин распаковки 6408 = живое дерево 09.09 | **KILL** (пин устарел) |
| `RT-REC-09` | их замечание и наша находка — одна единица | **KILL** |
| `RT-REC-10` | типовые чек-листы = то, что заказчик уже нашёл | **KILL** (шаблоны пусты) |
| `RT-REC-11` | 152 строки с комментарием = 152 замечания | **KILL** (раунды и дубли) |
| `RT-REC-12` | мы закрыли их чек-лист приёмки | **KILL** |
| `RT-REC-13` | сторонний checker / «Норм Чекер» = Gold Standard | **KILL** (это baseline, пока нет письменного эталона) |
| `RT-REC-14` | один эксперт заказчика = precision продукта / κ | **KILL** |
| `RT-REC-15` | сомнительную находку лучше скрыть | **KILL** (скрытый FN) |
| `RT-REC-16` | checkpoint сейчас NO_GO | **KILL** (GO = regulatory-measurement MVP; `customer_go` false) |
| `RT-REC-17` | 90% и 30 мин уже измерены | **KILL** (цели пилота; 21.07) |
| `RT-REC-18` | молчание заказчика = согласие на сужение scope | **KILL** |
| `RT-REC-19` | ссылка на GitHub = доставка трёх отчётов | **KILL** |
| `RT-REC-20` | шаринг экрана = самостоятельная проверка | **KILL** |
| `RT-REC-21` | демо-seed = отчёт по направленному комплекту | **KILL** |
| `RT-REC-22` | колл 15.09 = сдача Самолёту / второй шанс | **KILL** (канала нет; финал 14.09 через организаторов) |

Персональные данные книг (ФИО, должность, рабочая почта) не покидают
входной парсер.

Checkpoint **GO**; `customer_go` false. RT-001/002/003 открыты.
