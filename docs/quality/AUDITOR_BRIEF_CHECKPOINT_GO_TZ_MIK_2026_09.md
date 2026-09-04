<!-- claims-lint: allow-file reason="Standalone auditor corpus; TZ/MIK criteria and forbidden phrases as non-claims; Checkpoint GO; customer_go false; closes_rt false" -->
---
title: "Самодостаточный аудиторский корпус — Checkpoint GO × ТЗ Самолёта × Техлаб/МИК"
date: "2026-09-04"
last_updated: "2026-09-05"
status: active
version: "2.1.0"
standalone: true
repo_required: false
distribution: internal_auditor_pack_channel_derivatives_minimized
audit_disposition_date: "2026-09-05"
checkpoint: GO
go_kind: regulatory_measurement_mvp
customer_go: false
market_go: false
deployment_go: false
closes_rt001: false
closes_rt002: false
closes_rt003: false
precision_claim_publishable: false
mep_delivered: false
cde_import: NOT_VERIFIED
independent_human_raters: 0
llm_counts_as_rater: false
predicted_aerobim_total: null
claim_level: audit_corpus_not_score
claim_boundary: >
  Этот файл — полный корпус для аудитора без доступа к репозиторию.
  Не прогноз балла МИК. Не PrecisionClaim.publishable. Не MEP delivered.
  Не CDE-ready. Checkpoint GO (regulatory_measurement_mvp). customer_go false.
  closes_rt001/002/003 остаются false. Симулированные разметчики — не люди.
---

# Самодостаточный аудиторский корпус

Дата заморозки состояния: **2026-09-04**. Аудитор **не имеет** репозитория. Этот файл — единственный SSOT. Не запрашивать пути, не предполагать содержимое git, не «дочитывать» отсутствующие документы. Если позднее приложены фрагменты чужого текста — классифицировать их **против онтологии этого файла**. Не изобретать людей, подписи, федеративный IFC заказчика, импорт в СОД, κ на корпусе Самолёта.

Стиль отчёта аудитора: сухой, сжатый, академический. Вердиктная лексика только из §0.3.

---

## 0. Протокол аудита без репозитория

### 0.1 Задача аудитора

Выдать структурированный отчёт (схема §23) о согласованности **заявленного состояния продукта AeroBIM** с (а) ТЗ Самолёта × ТехЛаб задача верификации ПД/РД, (б) критериями отбора/финала МИК, (в) онтологией Checkpoint после рескоупа 04.09.2026. Источник фактов внутреннего аудита — **только этот файл**. Внешний контур (OSINT) — только §0.6; он **не** основание менять §3.1. Гипотезы без опоры на числа/формулировки ниже = `UNVERIFIABLE`.

### 0.2 Что этот файл не является

Не акт экспертизы. Не оценка комиссии. Не `customer_go`. Не прогноз приза. Не лицензия перекрасить OPEN-тома в CLOSED. Не заявление «ТЗ закрыто». Не заявление «можно в прод Самолёта».

### 0.3 Вердиктная лексика (обязательна)

| Код | Когда |
|---|---|
| `CONSISTENT` | Утверждение совпадает с онтологией и числами этого файла |
| `DRIFT` | Внутреннее противоречие корпуса или устаревшая формула «Checkpoint NO_GO» на **живом** продуктовом слое после 04.09 при сохранённом `customer_go=false` |
| `OVERCLAIM` | Утверждение сильнее доказанного: `customer_go=true`; недифференцированное `closes_rt001/002/003=true`; `PrecisionClaim.publishable=true` без `corpus_kind=customer` и ≥2 **человеческих** разметчиков; `mep_system_clash=OK`; CDE T2 `claim_allowed=true`; точность продукта >90%; SLA заказчика ≤30 мин; native DWG/RVT/NWD готов; LLM пишет `summary.passed`; симуляция = люди; городской IDS = подпись Самолёта; посаженный IfcClash = MEP delivered |
| `UNVERIFIABLE` | Факт вне корпуса (ФИО заявки, PDF приказа Фонда, часы партнёра, хеш живого пакета) |
| `HISTORICAL_PIN` | Датированная заморозка (КТ#2 handoff 11.08, CLAIMS_LOCK июля, JSON августа с `"checkpoint":"NO_GO"`). Не переписывать как текущий SSOT. Не трактовать как опровержение GO 04.09 |

### 0.4 Messick: два разных закрытия

| Слой | Что закрыто | Что не закрыто |
|---|---|---|
| **Content / substantive** (измерение) | Публичные IDS экспертизы; каталоги типовых ошибок РФ; учебный комплект; инъекция; симуляция протокола dual-rater; текст EIR v4 на канале; посаженный геометрический clash; HVAC `IfcSystem` rehearsal; три NWD как носитель | Публикуемая точность продукта |
| **Criterion** (приёмка у назначающей стороны) | Ничего из residual volumes | Двое людей; корпус Самолёта в git; подписанный IDS/`customer_approved`; system-aware MEP; федеративный IFC заказчика; CDE T2 |

Документация TBD ТЗ (архитектура, сборка, образ, презентация, сопр. доки) заполнена в git. Это **не** `customer_go`. Checkpoint `GO` = регуляторно-измерительный MVP (content). `customer_go` рисует **заказчик**, не текст.

### 0.5 Жёсткие запреты аудитору

1. Не ставить `closes_rt001` / `closes_rt002` / `closes_rt003` = true без дифференциации a/b/c.
2. Не считать `independent_human_raters` > 0. В корпусе = **0**.
3. Не считать LLM разметчиком.
4. Не считать автора фикстуры двумя разметчиками.
5. Не двойной счёт: `moscow_agr_2026` = **RT-002a**, не RT-002c.
6. Не считать signed OOS (шаблоны out-of-scope) закрытием RT-003.
7. Не прогнозировать `predicted_aerobim_total`. В машине это `None`.
8. Не переносить 52,6 как «наш балл». Это тождественность верхней кромки К1-low + нижней кромки rest-high.
9. Не путать Checkpoint `GO` с Customer GO / market GO / deployment GO.
10. Исторический КТ#2 handoff **обязан** остаться `NO_GO` как pin 11.08.2026.
11. Не произносить «RT-001b CLOSED». Речевая литера RT-001b = `b2_criterion_dual_rater` (люди, OPEN). Протокол симуляции = `b1_protocol_rehearsal`.

### 0.6 OSINT-контур (внешний, не SSOT; не меняет §3.1)

Классификация прохода 05.09.2026. Внешние факты не основание для `customer_go` / closes_rt / PRECISION / MEP / CDE.

| Утверждение корпуса | Внешний контур | Дисп. |
|---|---|---|
| МСФО 6м2026 выручка / убыток | Отчётность эмитента: выручка **117 448 млн ₽** (−31,3% к 170 967), чистый убыток **22,3 млрд ₽** vs прибыль 1,84 млрд годом ранее. Пресса округляет 117,4. | CONSISTENT по существу. Внутренний SSOT дальше пишет **117,4 млрд** (117 448 млн), не 117,5 |
| «Инвестируйте»/CAPEX мёртв | Пресса: сжатие EBITDA и штата | Усиливает тезис К4; не выручка AeroBIM; не SSOT |
| Стадия «доработка»; внедрение не начато | Публичное описание Техлаба: витрина запросов бизнеса; отбор по готовности к внедрению | CONSISTENT с календарём. Тактический риск К3/Б3: публичный критерий «готовность к внедрению» vs `customer_go=false`. Формула: «готовность к пилоту на согласованном пакете», не «внедрено» |
| Приз 2 млн ≠ i.moscow/pilot | Публичный акт пилотов Москвы: **ПП 631-ПП** (27.05.2020). Совпадение суммы 2 млн — источник путаницы | CONSISTENT разведение призов. Идентификатор **449-ПП** в старых текстах — UNVERIFIABLE как публичный акт этого прохода; не приравнивать ни 631-ПП, ни 449-ПП к призу задачи №6 |
| ГОСТ Р 72514/72515-2026 | Каталог стандартов: оба обозначения существуют | Существование CONSISTENT. Номера приказов 64-ст/65-ст — in-repo pin карточки фонда; этот OSINT-проход их не подтвердил (UNVERIFIABLE внешне). Смежный 66-ст той же даты не доказательство |
| Законопроект Минцифры, текст 18.03.2026 | Публикация проекта 18.03.2026 | Дата CONSISTENT. ID 166424 и вступление 01.09.2027 — UNVERIFIABLE этим проходом |
| Соседние задачи потока | ДГП Москвы — иная задача Техлаба | Не переносить лексику «пилот у ДГП» на задачу Самолёта |
| Состав комиссии №7, приказ П-01-ОД-52-1/26, цитата спонсора, ЛЭТИ 30.04, ComNews 46 команд / 200 млн, IDS MOEXP/CGE/AGR | Публично не найдены этим проходом | UNVERIFIABLE. ФИО комиссии не изобретать. Гендиректор МИК (публичное имя) **не** заявлен корпусом как член комиссии №7 |

Вывод OSINT: **ни один внешний факт не меняет §3.1.**

---

## 1. Идентичность продукта

**Имя:** AeroBIM.  
**Класс:** открытый проверяльщик комплекта строительной документации: IFC + IDS + листы/ведомости/ТЗ/расчёты.  
**Лицензия публичного дерева:** MIT. Репозиторий: https://github.com/KonkovDV/AeroBIM.  
**Не является:** SynAPS, GridPlan, MobiRoute, Tangl, 10D, CDE, просмотрщиком модели как продукта, заменой эксперта/ГИП, решателем ЛИРА/SCAD, валидатором buildingSMART Validation Service.  
**Рабочие корни владельца (не путать):** `C:\AeroBIM` — этот продукт. `C:\SynAPS`, `C:\SynAPS-GridPlan`, `C:\SynAPS-MobiRoute` — другие. Каталог `C:\plans` не используется.

**Роль:** decision-support эксперта. Человек остаётся ответственным за итог. HITL подтверждает/отклоняет **находки**; HITL **сам по себе** не переписывает `summary.passed` (ADR-001).

**Слой рынка (три колонки, интеграции нет и не обещаем):**

| Вопрос | Tangl (их контур) | 10D СОД (их контур) | AeroBIM |
|---|---|---|---|
| Что проверяет | Модель / наполнение / коллизии / EIR по **модели** | Наличие файла, маршрут, ЭЦП, комплектность пакета | Согласованность **содержимого**: модель ↔ лист ↔ ТЭП/ведомость ↔ ТЗ ↔ записка ↔ смежный раздел |
| Native RVT/NWD | их authoring | — | жёсткий отказ; обмен IFC + PDF/A |
| Вердикт комплекта | отчёты модели | статус документа | `summary.passed` только детерминированный движок |
| Импорт замечания в их СОД | их среда | маршруты СОД | BCF ZIP; импорт **NOT_VERIFIED** |

Одна фраза: 10D проверяет наличие и маршрут; Tangl — модель; AeroBIM — что факты в разных файлах не противоречат друг другу, с пунктом нормы и GUID.

**ISO 19650:** `summary.passed` = Shared-gate по сконфигурированным правилам. Не Shared→Published. Не контрактная годность к строительству.

**УГТ (самооценка, не независимая ОГТ):** ГОСТ Р 58048-2017, приказ 2128-ст. Программный пол К2 Техлаба — не ниже УГТ 3. AeroBIM: **УГТ 4** (лаборатория: CI, CLI, открытые пакеты, фикстура). **Не** УГТ 5 (окружение, близкое к эксплуатации = комплект партнёра в контуре измерения; нет dual-rater на комплекте партнёра). **Не** УГТ 6+ (пилот/штатная эксплуатация; i.moscow/pilot — другой инструмент). Pytest и показ жюри — доводы УГТ 4, не «внедрено». Независимая команда ОГТ по п. 5.1.2 **не** проводилась.

---

## 2. Программа: календарь, нумерация, приз

**Конкурс:** ТехЛаб Московского инновационного кластера, задача Самолёта — система автоматизированной верификации проектной и рабочей документации.

**Приз формата задачи:** платное пилотное тестирование **2 000 000 ₽** (соглашение Партнёр↔Фонд). Не городской грант пилотов (**ПП Москвы 631-ПП** от 27.05.2020 — другой инструмент; совпадение суммы 2 млн — источник путаницы). Идентификатор 449-ПП в старых текстах — UNVERIFIABLE как публичный акт (OSINT §0.6); не вход в Техлаб. Не «фонд 20 млн» как наш приз. Не i.moscow/pilot. Не вход «сначала ИП/юрлицо»: FAQ i.moscow 26.08 — физлица или команда 1–10, возраст 18+. Как Самолёт перечислит 2 млн при победе — соглашение Партнёра и Фонда, не карточка входа.

**Нумерация (не схлопывать):**

| Контур | Число | Смысл |
|---|---|---|
| Витрина i.moscow | заголовок несёт **07** | историческая этикетка раздачи / имена файлов |
| Приложение 4 Положения (публичная сверка ЛЭТИ 30.04.2026) | **строка 6** | задача Самолёта, приз 2 млн |
| Комиссия в приказе | **№7** | не путать со строкой 7 другого партнёра |
| Произнесение | запрещено | говорить «07» как номер статьи Положения |

Соседняя задача того же потока (Газпромбанк) публично: 46 команд (ComNews, 24.08.2026). Четыре карточки каталога задачи Самолёта — **уже отфильтрованные выжившие**, не полный вход. `catalog_four_are_all_applicants = false`. Первый поток: до 50 команд, 10 победителей на десять задач = **одно место на задачу**, не прогноз победы.

**Окна:**

| Окно | Даты | Смысл |
|---|---|---|
| КТ#2 | исторически 20.08.2026 | пакет `submission/`; handoff 11.08 pin `checkpoint_verdict=NO_GO` |
| КТ#3 | 03–21.09.2026 | feature freeze 18.09; delivery 19–21.09; финал 29–30.09 (SberCity) |
| Стадия программы | **доработка** | валидация эффективности и внедрение у назначающей стороны **не начались** |
| Канал заказчика | получен **25.08.2026** | хеш-пакет **не** в публичном git; фраза «нет данных заказчика» **запрещена** |
| Запрос данных | исходящий пакет вопросов датирован **04.09**; срок ответа **08.09**; план Б с **09.09** | git почту не отправляет |
| Письменный режим данных на 04.09 | **нет** (запрос 28.08; ответ — нет данных) | самоограничение ADR-005 не ждёт ответа |

**Трекеры (не смешивать):** шесть задач 14.08; восемь SIG-задач 29.08; семь задач сравнения ТехЛаба (картография, Uncertain) — не шесть.

**Элитность:** программа допускает команду до десяти человек из НИИ/вузов/лабораторий. Объект К1 — **состав заявки** (роль → человек → чем подтверждена → вклад), не HEAD git и не устные консультанты. ЛЭТИ: от 1 до 10; **два класса** компетенций (наука + инженерия). Десять фамилий не требуются.

---

## 3. Онтология Checkpoint (рескоуп 2026-09-04)

### 3.1 Машинные константы (живые)

```
CHECKPOINT                  = "GO"
GO_KIND                     = "regulatory_measurement_mvp"
GO_RE_SCOPE_DATE            = "2026-09-04"
CUSTOMER_GO                 = False
MARKET_GO                   = False
DEPLOYMENT_GO               = False
PRECISION_PUBLISHABLE       = False
MEP_DELIVERED               = False
CDE_IMPORT                  = "NOT_VERIFIED"
```

Недифференцированные `closes_rt001` / `closes_rt002` / `closes_rt003` = **false**.

### 3.2 Смысл флагов

| Флаг | Значение | Смысл |
|---|---|---|
| product `CHECKPOINT` | GO | Регуляторно-измерительный MVP |
| `go_kind` | regulatory_measurement_mvp | Публичные IDS экспертизы, учебное золото, посаженный clash, HVAC IfcSystem rehearsal, git-безопасные носители канала (EIR v4 текст, NWD-федерации) |
| `customer_go` | false | Нет двух человеческих разметчиков на pack-specific корпусе; нет именной подписи назначающей стороны на профиле **внедрения**; нет system MEP / федеративного IFC заказчика; нет CDE T2 |
| `market_go` | false | Не рыночное утверждение |
| `deployment_go` | false | Не внедрён у назначающей стороны |
| `PrecisionClaim.publishable` | false | Требует `corpus_kind=customer` и ≥2 человеческих adjudicators + agreement |
| `MEP_DELIVERED` | false | `mep_system_clash` остаётся NOT_VERIFIED |
| CDE import | NOT_VERIFIED | Структурный BCF ZIP T1 ≠ журнал импорта T2 |

### 3.3 Граница утверждения (verbatim, EN)

Checkpoint GO is the regulatory-measurement MVP: public examination IDS (MOEXP/CGE/AGR), fixture gold, planted geometric clash, HVAC IfcSystem graph rehearsal, and git-safe channel carriers (EIR v4 text, NWD federations). customer_go stays false. Not two human raters. Not a named appointing-party signed IDS. Not mep_system_clash=OK. Not CDE import. Not product accuracy. Not customer SLA. closes_rt001/002/003 stay false.

### 3.4 Честность живых снимков

Функция `require_honest_checkpoint`: ошибка, если `checkpoint ≠ GO`, если `go_kind` задан и ≠ `regulatory_measurement_mvp`, если любой из `customer_go` / `market_go` / `deployment_go` = true.

Intake-снимок `BLOCKED_NO_CUSTOMER_DATA` **не** есть продуктовый checkpoint. Overlay capabilities выставляет `checkpoint=GO` при всех gates=false.

### 3.5 Исторический pin (обязан остаться NO_GO)

КТ#2 handoff 11.08.2026: `checkpoint_verdict = "NO_GO"`. Инструмент `verify_kt2_handoff` обязан требовать NO_GO. Переворот этого pin в GO = уничтожение исторической заморозки = `OVERCLAIM` относительно аудита истории, даже если живой продукт GO.

CLAIMS_LOCK июля 2026 — историческая заморозка формулировок. Живой SSOT запрещённых фраз — список §5.

---

## 4. Замок речи

### 4.1 Формула RU (дословно, без изменений)

Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

Маркеры (все должны присутствовать на поверхностях жюри):

1. Мы на стадии доработки контура заказчика
2. Одна команда показывает находку с доказательствами на учебном комплекте
3. Валидация эффективности и внедрение у назначающей стороны ещё не начались
4. Checkpoint `GO` — регуляторно-измерительный MVP
5. `customer_go` остаётся false, пока нет независимого размеченного корпуса

Поверхности, обязанные нести RU verbatim: README.ru, docs.md, TIER0_INDEX, KT2_JURY_FAQ, pilot-claim-boundary, submission README и README папок 01–05, slides.md.

### 4.2 Формула EN (дословно)

We are in *refinement* on the customer contour. One command shows a fail-closed finding on a fixture. Effectiveness validation and deployment have not started. Checkpoint `GO` is the regulatory-measurement MVP. `customer_go` stays false until an independent labeled pack, two raters, a signed appointing-party profile, and CDE proof.

Поверхность: README.md.

### 4.3 30 секунд жюри (дословно)

AeroBIM ловит шов комплекта — площадь в ведомости против IFC, отметка в ПД против РД — на публичных машиночитаемых требованиях экспертизы. Это ассистент эксперта, не замена экспертизы, не СОД и не внедрение у Самолёта. Tangl — слой модели; AeroBIM — шов (требования ↔ IFC ↔ листы ↔ ревизии). Профиль *измерения* — городской IDS. Подпись / СТО Самолёта — строка «внедрено» (RT-002c OPEN). Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` false.

### 4.4 Три формулировки, валидные на отборе и финале

1. **УГТ.** Самооценка УГТ 4 по ГОСТ Р 58048. УГТ 5 = комплект заказчика в контуре измерения; не заявляем. Не подменять УГТ 4 словом «внедрено».
2. **Профиль измерения.** Публичный IDS городской экспертизы с 02.04.2026 (ЦИМ/IDS, RT-002a). На канале EIR v4 / BIM-стандарт v4 как текст (RT-002b носитель). Подпись / `customer_approved` — RT-002c OPEN. Не говорить «профиль заказчика закрыт».
3. **Recall / precision.** Recall — генератор `inject_defects`, seed **20260824**; на синтетике mutation-kill 0/6 и 1/8, публикуются нижние границы Уилсона **0,000** и **0,022** (`synthetic_only`). Precision — два независимых **человека**. На данных Самолёта не измерялось.

### 4.5 Стоп-лист КТ#3 (32 пункта; нарушение = OVERCLAIM или DRIFT)

1. Точность >90% / «по ТЗ коллизии закрыты».
2. SLA ≤30 мин на комплекте Самолёта.
3. Native DWG / RVT / NWD готов.
4. MEP system-aware clash сдан.
5. BCF CDE-ready / импорт в 10D доказан.
6. Customer GO / «можно принимать в проде Самолёта».
7. «RT-002 CLOSED» без split a/b/c.
8. «RT-001 CLOSED» / «RT-003 CLOSED» без split; «потому что файлы на диске»; «MEP сдан, потому что IfcClash на фикстуре дал hit»; «два разметчика закрыты, потому что симуляция».
9. Self-check ЦИМ АГР как наш канал (с 29.06 это бесплатный городской сервис).
10. «Стек заказчика = Renga» без квалификатора ИЖС.
11. «Неопределённый прогноз НКР» (снят 20.03.2026).
12. Номер задачи: витрина 07 vs приложение 4 строка 6; не спорить с сайтом; не произносить 07 как номер Положения.
13. «Фонд 20 млн» как наш приз.
14. «Для участия / приза обязательно ИП или юрлицо».
15. «Площади / огнестойкость на IFC заказчика уже измерены». Coverage map: IfcSpace без NetFloorArea; FireRating редкий и не класс ТЗ. Не акт дефекта.
16. «Нет данных заказчика» после канала 25.08. Канал получен; хеш-пакет не в git; RT-001 OPEN.
17. «Облако с логином готово» / ближайшее пересечение осей. OIDC BFF = 501; ось только `IfcGridAxis.AxisTag`.
18. Прогноз балла комиссии / «порог 50 у нас в кармане». Отбор — среднее; финал — сумма невиденной таблицы.
19. ГОСТ Р 72514/72515 как сертификат; законопроект Минцифры ID 166424 как действующий закон.
20. Fixture p95 / «30 минут на комплект Самолёта». Пакет обложки не representative. Система B ≠ pytest. Приложение 3 к Положению не видано.
21. ГОСТ Р ИСО/МЭК 42001 как сертифицированная СМИИ; i.moscow/pilot / грант 631-ПП / 449-ПП как приз 2 млн. Карта критерий→git не прогноз балла.
22. Состав команды из git / вымышленные ФИО в шаблоне К1. Объект К1 — заявка i.moscow.
23. «Нужно десять человек». УГТ 5 / независимая ОГТ. К3 как pytest.
24. 10,1 млрд ₽ рынка BIM как наши продажи; −72% как наш эффект; ПНСТ 841 как сертификат SQuaRE.
25. «52,6 у нас в кармане» / цитата спонсора задачи = председатель / 25,1 млрд к 2030 как наша выручка.
26. «Инвестируйте» / CAPEX / «мы закроем убыток МСФО». РСБУ +31% как картина группы. Четыре карточки = все, кто пришёл. «15 пилотов» соседа как факт.
27. Поднять SPF cap IFC до 1,5 ГБ / «мы SPF-открываем 1,5 ГБ» / native DWG к КТ#3 / 8,3% как текущая доля КР (headline 16,7%). 1,5 ГБ — ingest + RocksDB; WASM и SPF остаются 256 МиБ.
28. Fixture AABB precision/recall = 1,0 при n=6 — жюри не показывать: Wilson 95% lower ≈ 0,61. Вопрос о коллизиях — на протокол (двое людей, ~100 находок).
29. «Неэффективное использование пространства реализовано» / «это не нужно заказчику». Заказчик назвал пункт 25.08 (норматив продаваемой площади, МОП, коридоры). Честная строка: advisory по внутреннему нормативу; решение «в скоупе / вне MVP» — владелец (OA-14).
30. «ODA Sustaining 7 500 $ = native RVT/NWD» / «CADSoftTools от 1 660 $». Прайс 30.08: BimRv/BimNv — отдельные 6 250 $; CAD .NET — от 765 USD. ODA Sustaining ≠ BimRv.
31. «Фронт сдан» / матрица ТЗ «Web UI done» / Vite как показ на чужом ноутбуке жюри / «две находки огнестойкости = точность». Review shell — трек ИТ-ментора. Показ жюри = CLI. Seed — git-фикстура.
32. «Мы лучше Iversen» / их F1 как наша цифра / «LLM выбирает проверки на Shared-gate». Гибрид: черновик замечания и IDS — да; `call_tool` / `change_verdict` / generated checker на маршруте вердикта — нет без journal + hashed/`approval_ref` pack.

### 4.6 Бейджи README

Зелёный: `checkpoint-GO`. Красный: `customer_sign-off-NO_GO`. UI: «Checkpoint GO; customer_go false». UI **не** пишет `summary.passed`.

---

## 5. Запрещённые утвердительные фразы (CI)

Каждая фраза запрещена как **утвердительное** продуктовое заявление. Отрицание на той же строке или маркер заголовка «Нельзя» / «запрещено» на последующие пункты списка (HDS-SUB-02) — допустимо.

Запрещённые фразы: `accuracy >90%`; `dwg-ready`; `native dwg`; `cde-ready`; `cde interoperable`; `human-level cv`; `production-ready`; `mep delivered`; `mep system clash delivered`; `полностью российский стек`; `qwen3.8-max ready`; `customer go`; `market go`; `deployment go`; `sla ≤30`; `sla ≤30 минут`; `экономия ≥20%`; `точность >90%`; `ии понимает чертёж как инженер`; `интегрированы с tangl`; `закрыли тз самолёта`; `пакет заказчика проверен`; `43 ГБ обработаны`; `режим данных согласован`; `соглашение о конфиденциальности подписано`; `первые в России сравниваем версии документации`; `точнее городского нормоконтроля`; `заменяем зарубежные проверяльщики моделей`; `поддерживаем машиночитаемые требования лучше рынка`; `интегрированы с платформой заказчика`; `заменяем валидатор buildingsmart`; `шаблон сп 63 утверждён заказчиком`; `aerobim replaces the bsi validation service`.

После рескоупа 04.09: фраза `checkpoint go` **снята** с запрета (продукт имеет право говорить Checkpoint GO). Добавлены `customer go` / `market go` / `deployment go`.

Маркеры отрицания (неполный список): not claimed; forbidden; until evidenced; until t2; missing; not implemented; not verified; not_verified; blocked; ≠; out of scope; no_go; customer_go; not wired; not a ; do not claim; not measured; запрещено; нельзя; не заявляется; не утвержд; не реализовано; не проверено; не измерено; вне scope; до доказательств.

Заблокированный вывод IUA (корректный как запрет, не как запрет произносить Checkpoint GO): «Checkpoint GO / market GO = customer GO». Не удалять. Не трактовать как stop-list против речи Checkpoint GO.

---

## 6. ТЗ Самолёта × ТехЛаб — полное тело требований

**Конкурсный бриф v1** (PDF «ТЗ Техлаб 2026», ~6 стр.) — не семь задач сравнения и не проектное ТЗ домов. «Точность >90%» в v1 — цель оценивания, не замер AeroBIM. Канон ответа — **ТЗ v2**. **0,60** — порог пилота из ТЗ v2 (ТР-37 / таблица §9), собственный интерим-порог **методики**; целевая >0,90 не снята; критерий заказчика письмом **не согласован**. Не говорить «в акт МИК внесён согласованный 0,60».

**Конфликты v1 → v2 (обязательная переформулировка):**

1. «точность >90%» → только после размеченного корпуса + κ/α + `PrecisionClaim.publishable` (ТР-48).
2. «анализ DWG» → DXF / конвертация / ODA с лицензией; native DWG = missing.
3. «ошибки расчёта» → **сверка** заявленных величин, не независимый solver (`calculation_correctness=NOT_IMPLEMENTED`).
4. «пересечения инженерных систем» как system-aware → `not_verified` до federated IFC + провайдера.

**Позиционирование ТР-1.** Интеллектуальный ассистент эксперта, не замена ГИП. Критерий: в UI и отчёте decision support / HITL; Claims Lock не нарушен. Статус: **done**.

**Концепция.** Пакет: IFC + IDS/нормы + ТЗ + расчёты + 2D. Детерминированная валидация. Замечания с provenance. Браузерный review. Экспорт HTML/JSON/BCF 2.1. LLM/VLM — только advisory; при расхождении — `DivergenceRecord`, вердикт движка сохраняется.

**ТР-2.** Только контур DETERMINISTIC_VALIDATION (семантически) выставляет `summary.passed`. Физический писатель — EvidenceAssembler. Критерий: AI-путь не пишет `passed=true` в обход DeterminismGate. Статус: **done**.

### 6.1 Термины (границы честности)

| Термин | Определение (задача Самолёта; прил. 4 стр. 6; витринная этикетка 07) | Граница |
|---|---|---|
| OCR | Извлечение текста из растра/скана/PDF | Baseline RapidOCR/PyMuPDF; ≠ понимание чертежа |
| CV | Детекция регионов/символов | Advisory; `cv_human_level=MISSING` до корпуса |
| VLM | Модель на **регионе** листа | Не whole-sheet sign-off |
| NLP | Извлечение требований; текст замечаний | Sign-off: regex/шаблоны; LLM advisory + HITL |
| BIM | IFC 2x3 / 4 / 4x3 | openBIM; не Revit-runtime |
| IDS | Information Delivery Specification 1.0 | Машиночитаемые требования к IFC |
| BCF | 2.1 export; 3.0 experimental | Export ≠ доказанный CDE-import |
| RASE | Requirement / Applicability / Selection / Exception | Прозрачность норма→замечание |
| DeterminismGate | AI не может переписать `summary.passed` | Инвариант |
| сверка расчёта | Сопоставление ожидаемых/наблюдаемых величин | ≠ solver |

### 6.2 Графика (ТР-3…ТР-7a)

| ID | Требование | Фаза | Статус | Честность |
|---|---|---|---|---|
| ТР-3 | Атрибуты/геометрия BIM (IFC) | MVP | done | IfcOpenShell / IDS |
| ТР-4 | Текст/аннотации векторных/структурированных 2D | MVP | partial | Не CAD entities |
| ТР-5 | OCR сканов PDF/растр | MVP | partial | Синтетический скан; не сканы заказчика |
| ТР-6 | DXF (ezdxf) / DWG через конвертацию или ODA | P2 | missing / not_verified | Native DWG never OK |
| ТР-7 | Детектор регионов → OCR/VLM на регионе | P2/I8a | partial | `cv_human_level=MISSING` (AECV-Bench: OCR силён, подсчёт символов слаб) |
| ТР-7a | HITL unmatched/low-confidence регионов | I8c | partial | event `drawing_region_escalated` |

### 6.3 Соответствие (ТР-8…ТР-13)

| ID | Требование | Фаза | Статус | Честность |
|---|---|---|---|---|
| ТР-8 | IDS / properties IFC | MVP | done | Fail-closed missing IDS |
| ТР-9 | Соответствие ТЗ (извлечение) | MVP | done | Детерминированное |
| ТР-10 | PD↔RD section pairing | P1 | partial | Scaffold; customer pair TBD |
| ТР-11 | Norm packs, утверждённые заказчиком | P1 | partial | Synthetic + публичные IDS; **RT-002c OPEN** |
| ТР-12 | Сверка расчётных величин | MVP | partial | Load/quantity match; не solver |
| ТР-13 | Независимая корректность расчёта | — | **not implemented** | Вне MVP |

### 6.4 Ошибки (ТР-14…ТР-19)

| ID | Требование | Фаза | Статус | Честность |
|---|---|---|---|---|
| ТР-14 | Геометрические коллизии BIM (IfcClash) | MVP | partial | Optional extra; посаженный federated; n=6 AABB не для жюри |
| ТР-15 | MEP system-aware clash | P1+ | **not_verified** | MEP-CLASH-001, RT-003 residual |
| ТР-16 | Некорректные площади / количества | MVP | partial | Space area + quantity algebra |
| ТР-17 | Неэффективное использование пространства | P4 | missing | Только если KPI согласован; OA-14 OPEN |
| ТР-18 | Несогласованность разделов / отсутствующие элементы | MVP/P1 | partial | Cross-doc + IDS exists |
| ТР-19 | Расхождения размеров чертёж↔IFC | MVP | partial | Drawing↔IFC compare |

### 6.5 Поддержка эксперта (ТР-20…ТР-24)

| ID | Требование | Фаза | Статус |
|---|---|---|---|
| ТР-20 | Подсветка problem_zone / регионов | MVP | done |
| ТР-21 | Генерация замечаний RU/EN (шаблоны) | MVP/P0 | done |
| ТР-22 | Редактирование замечаний (HITL) | P0 | done |
| ТР-23 | Приоритизация Critical/Warning/Info | MVP | done |
| ТР-24 | Provenance: finding_id, source_id, evidence_refs, norm_clause, RASE | MVP/I8b | partial |

Локация замечания: этаж/ось из `IfcSpatialIndex` / `IfcGridAxis.AxisTag`, если GUID попал; иначе явно «нет в индексе»; **не** OCR.

### 6.6 Архитектура (ТР-25…ТР-33)

**Слои (ТР-25).** presentation → application → domain ← infrastructure; core (DI, settings, path jail). Domain не импортирует Infrastructure. Constructor injection. Статус: **done**.

**Atomic Delivery (ТР-26).** Новый domain port = Protocol + adapter + DI token + wiring + тест в одном PR. Статус: **done**.

**Четыре контура:**

| Контур | Назначение | Пишет `summary.passed`? |
|---|---|---|
| INGESTION | Загрузка, CAD/Office/OCR | Нет |
| DETERMINISTIC_VALIDATION | IFC/IDS/cross-doc/clash/match | **Семантический владелец** |
| AI_ADVISORY | LLM/VLM/агент/GraphRAG query | **Нет** |
| EVIDENCE_REPORTING | Отчёт, BCF, HITL | Физический писатель `passed` как чистая функция детерминированных входов + политики |

**ТР-27 DeterminismGate.** Advisory vs engine → DivergenceRecord, engine wins. Статус: **done**.

**ТР-28. Семь стадий пайплайна:** (1) Schema/SPF pre-gate; (2) IDS document audit; (3) IFC+IDS validation; (4) Cross-doc / section / norms; (5) Clash / spatial (capability-gated); (6) Drawings / OCR / region detector; (7) Remarks + report + BCF. При `require_clash` / обязательном OCR skipped→FAILED → `passed=false`. Статус: **done**.

**ТР-29.** Опциональный модуль отдаёт `ok | skipped | failed | missing | not_verified | not_implemented`. Тишина ≠ успех.

**ТР-30.** `GET /v1/system/capabilities` отражает honesty-поля (dwg_dxf, cv_human_level, mep_system_clash, calculation_correctness).

**Запрещённые OK-состояния runtime (`enforce_honesty_capabilities`):**

| Capability | Разрешённые состояния | Запрещено |
|---|---|---|
| `mep_system_clash` | NOT_VERIFIED, MISSING, FAILED | OK |
| `dwg_dxf` | MISSING, FAILED, NOT_VERIFIED, SKIPPED | OK |
| `calculation_correctness` | NOT_IMPLEMENTED, MISSING, FAILED | OK |

**Research-aligned порты (не product GraphRAG):** DrawingRegionDetector — partial; RASE — partial; RequirementToIdsCompiler + HITL — partial; IfcKnowledgeGraphPort — **advisory scaffold** (port+DI+fixture QA; GraphRAG not shipped); MepSystemGraphProvider — not_verified.

**ТР-31.** LLM/VLM/GraphRAG только advisory + HITL; запрещены как единственный источник sign-off.

**ТР-32.** Fail-closed auth (Bearer/OIDC вне dev), tenant/object ACL, path jail, лимит IFC SPF 256 MiB.

**ТР-33.** FS по умолчанию; S3/Postgres/Redis — enterprise extras.

**Non-goals архитектуры:** полноценный CDE; Revit-runtime; автономная сертификация; обучение ML в sign-off-пути; полное покрытие всех СП/ГОСТ.

### 6.7 Код и сборка (ТР-34…ТР-42)

ТР-34: Python 3.12+, Node 20+, Vite. ТР-35: ruff format/check, mypy src, pytest. ТР-36: extraction gate `--min-macro-f1 0.70` на **fixture** corpus. ТР-37: detection harness порог пилота ≥0,6 interim; publishable только с agreement. ТР-38: vitest; не заявлять «всегда в CI», если не wired. ТР-39: docker-compose + live OpenAPI + semver. ТР-40: frozen tags, reproducibility. ТР-41: SECURITY.md; лицензии совместимы с MIT. ТР-42: anti-stub `@sota-stub` + KNOWN_BUGS. Статус кластера: **done** (локальный quality gate). Публикуемые числа тестов — только CI pin `runtime-baseline-latest.json` (`attested_by=ci`, `corpus_kind=fixture`). Локальный pytest ≠ CI pin. Не копировать `tests_passed` в речь.

### 6.8 Образ решения и презентация (ТР-43…ТР-47)

End-to-end: загрузка → автоанализ на **согласованном** эталонном пакете (цель ≤30 мин — ТР-49, не любой проект) → review IFC+2D+панель → severity → provenance → HTML/JSON/BCF 2.1 → передача проектировщику; эксперт ответственен.

ТР-43: demo-path по README + samples. Критерий: 8–12 мин без Claims Lock. Статус: **partial**.

Готово vs roadmap (§7.2 ТЗ): IFC+IDS+cross-doc vs полный СП/ГОСТ; clash optional vs MEP system-aware; OCR baseline vs YOLO/VLM product CV; шаблоны+HITL vs LLM remarks без HITL; SLA на согласованном пакете vs универсальный SLA; protocol TP≥60% vs published >90%.

ТР-44: слайды problem → assistant → 4 контура → живое демо → метрики с границами → roadmap → запрос к заказчику. ТР-45: ни один слайд не нарушает Claims Lock. ТР-46: один язык на колоду. ТР-47: каждая цифра — на evidence или команду. Статус: **partial**. Колода: PPTX — текстовый контракт; PDF может отставать.

### 6.9 Критерии оценивания ТЗ §9 (критерии **заказчика**, не замеры AeroBIM)

#### Точность (ТР-48, ТР-51)

| Уровень | Метрика | Порог | Условие |
|---|---|---|---|
| Пилот interim | TP/(TP+FP) на adjudicated findings | ≥ **0,60** | Dual-**human** labels |
| Publishable product | Precision / Recall / F1 | целевая **>0,90** | Только после P4 + корпус заказчика + `PrecisionClaim.publishable` |
| Согласованность 2 экспертов | Cohen κ | tooling ≥0,60; целевой протокол >0,80 | `measure_adjudicator_agreement` |
| ≥3 разметчика | Krippendorff α | tooling ≥0,67 | schema 1.1.0 |
| Ранжирование | nDCG graded 0/1/2 | согласовать на пилоте | fixture-only до корпуса |

**ТР-48.** Запрещено публиковать «точность >90%» без `PrecisionClaim.publishable=true` (customer + ≥2 adjudicators + agreement). В корпусе publishable = **false**.

**ТР-51.** Коллизии и несоответствия — **тем же протоколом разметки**, не отдельной «магической» >90% без корпуса.

Числа ТЗ >90% и время **не упомянуты** в ответах 25.08 — не подтверждены, не уточнены, не сняты. Не принимать их как согласованный контракт измерения, пока нет письма.

#### SLA (ТР-49)

≤30 минут — на **согласованном эталонном пакете** с `corpus-kind` customer|fixture. Fixture SLA ≠ customer SLA. Ответы 25.08 критерий времени не подтверждают. 5–10 комплектов/день — формулировка заказчика, не замер.

#### Качество замечаний (ТР-50)

Kill-критерий: доля замечаний, принятых без правки или с минимальной правкой (лог HITL `edited_remark`). Не часы A1–A8.

#### Прочие KPI §9.4

Покрытие каталога типовых ошибок: ≥20 паттернов scaffold; `customer_confirmed_patterns = 0`. FP-rate по дисциплинам — не измерен на заказчике. Время до первой подтверждённой находки — журнал HITL. Снижение часов vs baseline недели 1 — нет данных партнёра (A1–A8 пустые). Стабильность: CI + capability honesty.

### 6.10 Сопроводительная документация (ТР-52)

Обязательный пакет: README RU/EN; docker-compose + runbook; OpenAPI; руководство эксперта; матрица соответствия; ТЗ v2; KPI + annotation protocol; reproducibility; SECURITY.md; KNOWN_BUGS + capabilities; Claims Lock / CRITICAL_BLOCKERS. Статус: **done** как наличие путей; не `customer_go`.

### 6.11 Фазность (ТР-53)

| Фаза | Содержание | Конкурс |
|---|---|---|
| MVP | IFC/IDS/cross-doc/clash opt/OCR baseline/templates/review/BCF export | конкурсный минимум |
| P0 | Upload, панель, EN | done (eng) |
| P1 | Norm packs, section pairing, precision harness | scaffolds; корпуса нет |
| P2 | DXF/DWG thin, OCR, region detector | I8a partial |
| P3 | LLM remarks/IDS assist + HITL | stub/advisory |
| P4 | Customer corpus → publishable; space-efficiency optional | **blocked RT-001** |

**ТР-53.** В конкурсном MVP **не входят как done:** native DWG, MEP system-aware, publishable >90%, CDE-import proof, полный СП/ГОСТ.

### 6.12 Claims Lock ТЗ §12 (ТР-54)

До evidence запрещено утверждать: точность >90%; утверждённый заказчиком нормативный пакет (если его нет); MEP clash delivered; «анализирует DWG/DXF» как полноценный CAD; «проверяет корректность расчётов»; production-ready / external academic audit; BCF готов к CDE; fixture SLA = customer ≤30 мин; green pass при silent skip обязательных capability.

### 6.13 Матрица зависимостей от заказчика §11

| # | Поставка заказчика | Разблокирует |
|---|---|---|
| 1 | Согласованный комплект ПД/РД+IFC+ТЗ+расчёты+2D *(формулировка ТЗ; режим данных не согласован; `nda_signed=false`; не публиковать как подписанный NDA)* | SLA, precision |
| 2 | Approved norm pack + `approval_ref` | RT-002c / vs norms |
| 3 | ≥20 typical errors `customer_confirmed` | Каталог KPI |
| 4 | ≥2 разметчика + labeled corpus | RT-001 criterion / путь >90% |
| 5 | Baseline часов ручной проверки | −% review time (A1–A8) |
| 6 | CDE для BCF import week-1 | CDE claim T2 |
| 7 | Signed scope memo (CV/ГОСТ/MEP границы) | Scope |

Без п.1–4 **customer_go** остаётся false. (Исторический текст ТЗ v2: «без п.1–4 checkpoint остаётся NO_GO» — это **дорескоупная** формула; после 04.09 читать: checkpoint GO измерительный, customer_go false. Класс: `DRIFT` формулировки источника ТЗ vs живая онтология.)

### 6.14 Протокол оценки (ТР-55…ТР-56)

ТР-55: двойная слепая разметка → adjudication CSV → labels.json → agreement → `evaluate_detection_precision --require-publishable --agreement-json`.  
ТР-56: intake gate с evidence `{path, sha256}`. Tooling **done**; измерение на Самолёте **нет**.

### 6.15 AI-безопасность (ТР-57…ТР-62)

ТР-57 severity triage — обязателен (done). ТР-58 provenance/deep-link (**partial**). ТР-59 HITL для advisory accept (done). ТР-60 DeterminismGate + DivergenceRecord (done). ТР-61 CoVe — roadmap advisory, не sign-off. ТР-62 региональный VLM, не whole-sheet — требование к P2/P3.

### 6.16 Дополнения 28.08 (ТР-63…ТР-68)

| ID | Требование | Статус | Честность |
|---|---|---|---|
| ТР-63 | Сравнение версий и типов документации | **partial** | Fixture identity compare; не CDE versioning; не продавать как отличие: в СОД заказчика наложение версий уже есть |
| ТР-64 | Загрузка MS Office | done (fixture) | Native docx/xlsx; legacy .doc/.xls fail-closed |
| ТР-65 | Снижение когнитивной нагрузки | scaffold | Три метрики HITL: время до первого подтверждения; доля без правки; переключения лист↔модель (третья требует UI-событий — не закрыто) |
| ТР-66 | Извлечение инженерных сетей из 2D | **missing** | 470 DWG пакета — именно сети; DWG не читается |
| ТР-67 | Сверка объёмов спецификации с графикой/BIM | **partial** | У заказчика «логические коллизии» п. 2.1.3; **не** объёмы модели в смету (это у них закрыто BIM-платформой). Declared triples; без ingest комплекта |
| ТР-68 | Замечание цитирует пункт нормы **или СТО** | partial | Не только СП. Термины СП 63: «класс бетона/стали», не «марка» |

### 6.17 Остаток критического издания ответов 25.08 (не отдельные ТР)

- п. 1.2.3: база типовых узлов в тех же двух папках, форматы PDF/DWG, узлов в IFC нет; DWG не читается (RT-TYP-NODES).
- п. 3.1.1: облако допустимо; развёртывание в контуре заказчика не требуется; нужна изоляция **по проектам** (модель доступа, не шифрование) (RT-CLOUD-ISO). HTTPS ≠ изоляция.
- п. 3.1.2: заказчик сам записал «обезличенные комплекты в рамках NDA»; фактическая передача этому не соответствует (RT-NDA-STATED). Не наш доп. запрос.
- п. 3.2.2: горизонтальное масштабирование заложить архитектурно, не реализовывать на MVP; на защите — точки расширения, не нагрузочные цифры (RT-SCALE-MVP).
- п. 2.2.2: прямая интеграция с СОД на MVP **не требуется**; файловый обмен через веб UI достаточен.

### 6.18 Источник сверки расчётов (ответы 25.08)

Сверка — с **расчётными записками PDF/Excel**, не с бинарными файлами комплекса. Объекты сверки: нагрузки и площади. Сводная модель существует **в NWD**. Соответствие внутренним стандартам **обязательно**; перечень выдан 25.08 двумя ссылками в 1.2.1 (внутренние пути СОД; нужна публикация тем же способом, что датасет). Native `.lir` не разбирается. MATCH объявленных полей xlsx/docx ≠ `calculation_correctness`.

Четыре проверки заявленное vs записка (методика, не solver):

| ID | Проверка | Заявлено | Записка | MVP |
|---|---|---|---|---|
| CC-1 | Площадь армирования As | КР PDF текст; не IFC, пока нет IfcReinforcingBar | записка PDF/таблицы | выборочно |
| CC-2 | Класс бетона / стали | IFC IfcMaterial.Name (токены B25/B35); текст КР ПЗ | записка / спецификация | да, если есть записка |
| CC-3 | Прогибы | РД часто не заявляет | записка vs СП 20 | выборочно; часто «записка vs норма» |
| CC-4 | Нагрузки (и площади) | сбор нагрузок Office; ТЭП; load cases текстом | записка / комбинации | да, declared-field compare |

Ожидаемый частичный GO **методики**: CC-2 и CC-4 при наличии записки; CC-1 и CC-3 — выборка. Не «конструкции пересчитаны».

---

## 7. Матрица соответствия ТЗ (честные статусы)

Легенда: `done` | `partial` | `missing` | `blocked` (нужен Самолёт). Fixture-bounded, пока не customer.

| Кластер | Статус | Примечание |
|---|---|---|
| IFC 2x3/4/4x3 + IDS 1.0 | done / VERIFIED_FIXTURE_ONLY | Fail-closed missing IDS |
| Cross-doc / PD↔RD scaffold | partial | Customer pair TBD |
| Clash AABB / planted federated | partial | n=6 fixture P/R не для жюри; Wilson широк |
| MEP system-aware | not_verified | Runtime `mep_system_clash`; TZ-строка «missing» была синонимом отсутствия поставки. Код состояния SSOT: **not_verified** |
| Native DWG/RVT/NWD | missing | тот же класс честности; `validate_native_autodesk_toolchain` |
| Office docx/xlsx | done | legacy .doc/.xls fail-closed |
| OCR RapidOCR | partial | synthetic scan |
| CV «как человек» | missing / out of acceptance | |
| LLM remarks/IDS | advisory | DeterminismGate |
| Web UI | partial | review shell; восемь IA-экранов все `partial`; ноутбук жюри = CLI |
| BCF export T1 | partial | T2 NOT_VERIFIED |
| Spec vs BIM volumes (ТР-67) | partial | declared triples; не QTO estimate |
| Inefficient space | missing | advisory_unsigned inventory |
| Calc correctness | NOT_IMPLEMENTED | OpenRebar provenance сверка only |
| Typical-errors catalog | partial | ≥20 pattern scaffold; customer_confirmed=0 |
| Upload PDF | partial | path + raster + POST /v1/uploads |
| Version/doc-type compare | partial | fixture identity; не CDE versioning |
| Coverage map 4 states | partial | HTML+PDF+UI |

Строки, заблокированные Самолётом (корпус, approved norm pack, MEP federated, CDE BCF, dual adjudication), остаются `partial/missing/blocked`. Переименовать в `done` без customer evidence = OVERCLAIM.

Alignment R1–R15 (страница задачи → продукт):

| # | Требование страницы | Статус | Предел |
|---|---|---|---|
| R1 | 2D drawings | fixture | Vision-heavy не pilot sign-off |
| R2 | BIM models | done | pytest, packs |
| R3 | TZ + calculations | done (det.) | F1 gate ≥0,70 **fixture** |
| R4 | Match docs + norms | partial | customer approval required |
| R5 | Collisions | opt-in clash + cross-doc | уточнить 3D vs логика |
| R6 | Calc/dimension/area | partial | не solver |
| R7 | Logic / missing | done | IDS exists/bounds |
| R8 | Highlight zones | done | overlay |
| R9 | Prioritize | done | профиль samolet |
| R10 | Designer comments | done | RU/EN + HITL + BCF |
| R11 | Faster review | measure | SLA tool; customer OPEN |
| R12 | Expert accountable | done | claim boundary |
| R13 | MVP + viz + reports | done (fixture) | API+HTML+JSON+BCF+shell |
| R14 | Typical error catalog | partial scaffold | confirmation=0; MEP gap |
| R15 | ≤30 min | fixture rail | customer pack required for contract |

Clash policy R5: «коллизии» = IfcClash (opt-in extra); «логические расхождения» = CROSS_DOCUMENT (core); «расхождения размеров/площадей» = quantity algebra (core).

---

## 8. Ответы Самолёта 25.08 и шесть вопросов 04.09

### 8.1 Что можно говорить про данные

Канал 25.08 **получен**. В публичном git файлов заказчика нет. `share_ingested_in_git=false`. `samples/customer/` — blocked README. Не коммитить customer files. Не говорить «данных нет». Не говорить «пакет обработан» / «43 ГБ обработаны». SIG-01 дозволенная фраза: «объём находок на канале получен». `publishable_finding_count=0` на канальном инвентаре.

Owner-disk rehearsal 26.08: `detected_count=0`; fixture IDS; 14 IFC under cap, 1 inventory-only over cap; не закрывает RT-001.

Seam coverage 26.08 (не detection): 6 AR IfcSpace без NetFloorArea; FireRating sparse EI45 ≠ design-TZ class II/C0.

### 8.2 Intake gate (полный смысл JSON)

`status = BLOCKED_NO_CUSTOMER_DATA`. `claim_level = not_ready`. Все gates **false**: nda_signed; scope_memo_signed; customer_package_in_samples_customer; customer_approved_norm_pack_with_approval_ref; ids_or_property_table_present; dual_human_adjudicators_named; cohens_kappa_or_krippendorff_alpha_reported; confusion_matrix_reported; zero_unresolved_labels; precision_claim_publishable; cde_bcf_import_evidence; customer_sla_pack_measured; mep_federated_scope.

Правила: LLM не adjudicator; synthetic F1 не product accuracy; fixture SLA не customer SLA; `customer_approved` без `approval_ref` недействителен.

`share_url_received=true` (25.08); `share_url=null` в публичном JSON (ценз). `closes_rt*=false`.

`next_actions` содержит устаревшую строку «Keep checkpoint NO_GO until RT-001/002/003 evidenced» — **DRIFT** относительно живого CHECKPOINT=GO; не лицензия customer_go.

### 8.3 Шесть вопросов-блокеров ТЗ (отправка владельцем 04.09; срок 08.09)

Не спрашивать: native DWG/RVT; пороги «неэффективного пространства»; снижение цели ТЗ >90% до 0,60 в акте без их письма; импорт BCF в 10D как данное.

1. Эталонный корпус и каноническая пара ревизий ПД/РД — иначе 30 мин и сравнение версий неизмеримы на их манифесте.
2. Два специалиста, суммарно **2–4 ч** (минимум два часа эксперта) на разметку TP/FP + утверждённый перечень (книга замечаний) — иначе >90% неизмерима.
3. 1–2 утверждённые расчётные записки PDF/Excel (армирование, сечения, нагрузки, прогибы) — сверка, не пересчёт.
4. IFC типового этажа ОВ/ВК **или** письменное: NWD — визуальный референс, автопроверка сетей на MVP не входит.
5. QTO NetFloorArea если заполнен, иначе отдельная capability «площадь по геометрии»; ось только IfcGridAxis, иначе «нет в индексе».
6. Состав машиночитаемого профиля по СП 63 (IDS) и **должность подписанта**.

### 8.4 План Б (активация 09.09, не обсуждается 14.09)

1. Учебный манифест; t_tool локально; 30 мин не SLA.
2. Методика на публичном корпусе; интервалы Уилсона; вслух: на данных заказчика точность вслепую не измеряется никем.
3. Сценарий КР на учебных таблицах; подпись «результат на учебном комплекте».
4. `mep_system_clash=not_verified`; «сети в IFC не переданы»; вердикт не зелёный.
5. QTO/ось как в коде; погрешность геометрии — только фикстура.
6. Публичные IDS МГЭ / СПб ЦГЭ; UI: «профиль публичный, заказчиком не согласован».

Recall на синтетических инъекциях — пилот методики при отсутствии ground truth; **не** измерение точности продукта. Первым предложением, если тему подняли. План Б **не** перекрашивает residuals и **не** делает customer_go.

### 8.5 Профиль приёмки v0.1 (unsigned)

`profile_owner=null`. `approval_date=null`. `profile_hash=null`. Это шаблон, не подпись. Definition of Done RT-002c: `customer_pack_hash ≠ null` AND `profile_owner ≠ null` AND `approval_date ≠ null` AND scope memo signed AND norm edition/clause/jurisdiction complete.

Черновик полей: один завершённый раздел, одна ревизия; IFC как в HEADER заказчика без алиаса IFC4↔IFC4X3; IDS заказчика (`pack_hash`); МОГЭ IDS = reference only; native DWG/RVT/NWD вне MVP; MEP generic ≠ system-aware; расчёты = сверка; исходы PASS / PASS_WITH_WARNINGS / REVIEW_REQUIRED / BLOCKED.

Ask к назначающей стороне: один-ревизионный ПД/РД+IFC+2D+TZ/EIR fragment; signed IDS/`approval_ref`/`pack_hash`; два инженера-разметчика; целевая СОД для журнала импорта BCF.

---

## 9. Техлаб / МИК — полная арифметика

PDF приказа Фонда **в git нет**. Веса — IUA над брифингом владельца 30.08.2026 приказа **П-01-ОД-52-1/26** от **17.06.2026**. Не `attested_by=ci`. `predicted_aerobim_total() is None`.

Пункт 2 приказа разводит **две** математики. Обе таблицы живут в **Положении**, не в приказе.

| Слой | Отбор (п. 2.1) | Финал (п. 2.2) |
|---|---|---|
| Где критерии | Приложение **2** к Положению | Приложение **3** к Положению |
| Как в этом корпусе | К1–К5 из формы протокола к приказу | таблица Положения **не видели** (`regulation_appendix_3_in_git = false`) |
| Как считают | **среднее арифметическое** оценок членов | **итоговая сумма баллов** |
| Кто | комиссия | комиссия **плюс** представители Партнёра и Организатора |
| Зачем | допуск | победа и приз |
| Тай-брейк | система A: **К3, затем К4** (К2 не участвует) | брифинг Б1–Б5: только **Б1**; это не Приложение 3 |
| Кворум отбора | ≥ половины состава и **≥3** | при трёх голосах вес каждого = 1/3 |
| Шире пяти кресел | нет (номинал 5) | да (`FINAL_ROUND_WIDER_THAN_NOMINAL`) |

Порог приза: не менее **50**. В Порядке встречается «менее 50». Рабочий порог **50**; неоднозначность — аргумент на границе, не лицензия округлить вверх. Знаменатель финала неизвестен (`prize_floor_denominator_known = false`), если итог — сумма невиденной таблицы.

Шкала от максимума критерия: 0–20 очень низкий; 21–40 низкий; 41–60 средний; 61–80 высокий; 81–100 очень высокий.

### 9.1 Система A (отбор), макс. 100

| Код | Критерий | Макс | Доля |
|---|---|---|---|
| К1 | Компетентность и сбалансированность состава команды | 40 | 40% |
| К2 | Научно-техническая новизна и технологическая готовность | 20 | 20% |
| К3 | Соответствие задачам партнёров программы | 15 | 15% |
| К4 | Потенциал коммерциализации и масштабирования | 15 | 15% |
| К5 | Реализуемость плана работ | 10 | 10% |

К1 больше К2 вдвое и больше К3+К4 вместе. К2+К5 = 30. Качество кода и честность метрик в этой шкале — в основном К2 и К5.

Номинальная атрибуция кресел (не прогноз): партнёрские кресла номинально К1+К3+К5; кресла Фонда номинально К2+К4. Три кресла партнёра внесены **по согласованию** — участие не гарантировано приказом. Два кресла Фонда — штатные.

Кресла (роли, не ФИО): председатель Фонда (центр пилотирования); эксперт Фонда (центр внедрений и спроса); эксперт партнёра — дирекция технологического заказчика; проектный офис; информационное моделирование. Цитата спонсора задачи (Artsrun Gevorkyan: автоматическая проверка не заменяет инженера, а не пускает очевидную ошибку на стройку) **≠** засвидетельствованный председатель комиссии.

Оптика кресла:

| Кресло | Ожидаемый вопрос | Чем закрываем без overclaim |
|---|---|---|
| Пилотирование Фонда | Где пилот, если пакета нет в git | Третий путь КТ#3; канал ≠ хеш-пакет |
| Спрос Фонда | Кто ещё купит | Не витрина заказчиков; протокол измерения |
| Техзаказчик | Как в процесс, кто владелец | Эксперт/пользователь; веб без интеграции на MVP |
| Проектный офис | Что будет к КТ#3 без данных | План с альтернативой = К5, не «успеем всё» |
| Информационное моделирование | Чем не Tangl / 10D / городской нормоконтроль | Честная карта покрытия; IDS как гигиена |

Завышенное утверждение по модели, СОД или NWD бьёт сразу К2 и К3.

### 9.2 Идентичность 52,6 (не балл)

Если К1 в полосе «низкий» (21–40% от 40) → 8,4–16 баллов. Если остальные 60 на «высоком» (61–80%) → 36,6–48. Итог **45–64**. Порог 50 **не проходится автоматически** (`prize_floor_automatic_in_low_k1_high_rest = false`).

Верх К1-low (16) + низ rest-high (36,6) = **52,6 ≥ 50**. `reachable_inside_low_k1_if_rest_high = true`. К1 не обязан выходить из низкой полосы, если не сидит на её дне. Десять человек не требуются.

Другие сценарии (не прогноз): низ К1-low + низ rest-high = 45,0 < 50; К1-low-hi + rest medium-lo 41% = 40,6 < 50.

### 9.3 Что git может показать vs что не закрывает (находимость, не оценка)

| Код | Комиссия должна увидеть | Что корпус не закрывает |
|---|---|---|
| К1 | Научная + инженерная компетенция (оба класса ЛЭТИ) | ФИО, степени, патенты — **только заявка**; шаблон ролей с пустыми ячейками человека |
| К2 | Прототип не ниже TRL 3; ИС; нацстандарты ИИ | Сертификат 42001; патентный забор п. 6.3; сертификация ПНСТ 841; УГТ 5 |
| К3 | Адаптация под партнёра; измеримость | Подпись профиля; замер на их комплекте |
| К4 | Тираж; нулевой вход; не CAPEX | Выручка; второй контракт; 10,1 млрд как SAM; −72% как наш эффект; «инвестируйте»; МСФО как наш эффект |
| К5 | План и риск | Соглашение площадки |
| Б1 | Функционал + ограничения | KPI партнёра письмом; ODA BimRv не куплен |
| Б2 | Протоколы **и** подтверждённые метрики валидации | Dual-rater на партнёре; синтетика ≠ корпус Самолёта; `confirmed_partner_validation_metrics = false` |
| Б3 | Импорт/экспорт MVP | SSO; SPF-open 1,5 ГБ |
| Б4 | До/после | Часы партнёра; A1–A8 пустые |
| Б5 | Поставка + прозрачность | Передача исключительных прав |

### 9.4 Система B (брифинг, не Приложение 3), сумма

| Код | Критерий | Макс |
|---|---|---|
| Б1 | Соответствие задаче и требованиям партнёра | 30 |
| Б2 | Качество прототипа и результаты тестирования/валидации | 20 |
| Б3 | Готовность к интеграции и внедрению | 20 |
| Б4 | Измеримый эффект для партнёра | 20 |
| Б5 | Полнота документации и передача результата | 10 |

`finalist_weights_are_regulation_appendix_3 = false`. Pytest и fixture SLA **не** поднимают Б2 в «высокий». Система B не берёт порог 50 при отсутствии метрик партнёра как «высокий Б2».

### 9.5 К2 новизна (клин = методика, не 90%)

Отличимы: ADR-001 (LLM не пишет passed); протокол классов + dual-rater + κ; слой шов файлов; ablation A0–A3 на фикстуре; CI pin `attested_by=ci`. Витрина сверстников: «>90%» без корпуса. Цифры сверстников не переносить. `peer_card_claims_externally_verified = false`. Заявленные «15 пилотов», «600+ норм», «живой прототип на данных заказчика», геометрический DWG — не проверены извне. Честный проигрыш: корпус норм и живой DWG у части сверстников сильнее **заявлены**. Не «лучше Solibri глобально». Четыре пункта сравнения у всех решений: (1) корпус цифры; (2) два оценщика; (3) согласие; (4) условие несостоятельности результата.

Iversen & Huang: *Leveraging large language models for BIM-based automated compliance checking*, Automation in Construction **182** (2026) art. **106707**, DOI `10.1016/j.autcon.2025.106707` (PII S0926580525007472) — **VERIFIED** внутренним обзором (`ACADEMIC_LIT_REVIEW_2026_09`). Fuchs, Hellin & Borrmann: EC3 2026, mediaTUM **1854862** — **VERIFIED** тем же обзором. Они закрывают оцифровку нормы. AeroBIM закрывает **кто имеет право сказать pass**. Не говорить «мы лучше Iversen». Их F1 остаётся их. Перед слайдами К2: неверная библиография бьёт по К1/К2 сильнее, чем её отсутствие. EGCC / Mushkani et al. arXiv:2607.29058 — in-repo pin (четыре статуса + HITL); OSINT-проход 05.09 ID не подтвердил (UNVERIFIABLE внешне).

### 9.6 К4 коммерческий путь (контекст, не выручка)

`k4_revenue_claimed = false`. `k4_asks_customer_capex = false`. `k4_offsets_partner_ifrs_loss = false`. Аргумент «инвестируйте» мёртв после МСФО группы 1П2026.

МСФО группы 6m2026 (отчётность эмитента): выручка **117,4 млрд ₽** (117 448 млн; −31,3% к 170 967 млн); убыток **22,3 млрд ₽**. Пресса иногда пишет 117,5 — микроокругление, не SSOT. РСБУ головной за то же полугодие: выручка 8,56 млрд ₽, **+31,2%**. Знаки разные. Путать МСФО и РСБУ = потеря доверия.

Программа ИИ партнёра: публично ~200 млн ₽/год (ComNews 21.05.2026) — **их** контур. 200 млн vs убыток 22,3 млрд — меньше процента.

Три слоя рынка: TAM BIM РФ 10,1 млрд ₽ (2022, ГидМаркет/TAdviser) — **не** SAM. Горизонт 25,1 млрд к 2030 (СПбПУ) — не наша выручка. SOM = приз 2 млн. Аналог −72,1% трудозатрат (модель 5240 м²) — **их** корпус, не наш эффект.

Речь К4: нулевой вход на MVP; не CAPEX; веб + файловый обмен (п. 2.2.2); просить данные и **2–4 ч** разметки (минимум два часа эксперта), не бюджет.

### 9.7 П. 6.3 и IP

Соглашение может передать исключительные права без доплаты к призу. LICENSE остаётся MIT. Не обещать патентный забор. ADR-004: приз IP vs п. 6.3; не менять LICENSE в этом аудите.

### 9.8 Национальный стек ИИ (карта, не сертификат)

| Обозначение | Приказ / введение | Зачем К2 | Чего это не значит |
|---|---|---|---|
| ГОСТ Р 71476-2024 (ИСО/МЭК 22989) | 1550-ст 28.10.2024 / 01.01.2025 | Термины: система ИИ ≠ вердикт эксперта | «стандартизовали отрасль» |
| ГОСТ Р ИСО/МЭК 42001-2024 | 1549-ст / 01.01.2025 | СМИИ: HITL, роли | Сертифицированная СМИИ |
| ГОСТ Р 72514-2026 (42005:2025) | **64-ст** 30.01.2026 / 01.05.2026 | Оценка воздействия | Декларация соответствия |
| ГОСТ Р 72515-2026 (12792:2025) | **65-ст** 30.01.2026 / 01.05.2026 | Таксономия прозрачности | Сертификат прозрачности |
| ГОСТ Р 71752-2024 | 1548-ст / 01.01.2025 | Содержание ТЗ на ИИ | Наше ТЗ заменяет ТЗ партнёра |
| ГОСТ Р 71539-2024 (5338:2023) | 1539-ст / 01.01.2025 | Жизненный цикл | Lifecycle-сертификат |

Номер 64-ст для 72514 — in-repo pin карточки фонда; OSINT-проход 05.09 не подтвердил (UNVERIFIABLE внешне). Не снимать pin без замены источником. Совместимость ≠ сертификация.

Законопроект Минцифры ID 166424: не внесён в ГД; текст на 18.03.2026; планируемое вступление 01.09.2027. Аргумент К2 как совпадение с будущей логикой, не действующий закон.

ПНСТ 841-2023 — карта на протокол измерения, не SQuaRE-сертификат.

Постановление 2204 (пилот внедрения, УГТ ≥5) и грант площадок — другие инструменты, не оценка К2 этой комиссии.

---

## 10. RT-001 / RT-002 / RT-003 — тома измерения vs остаток

Недифференцированные closes остаются **false**. Схема объёмов **1.5.0**. Дата рескоупа томов: 2026-09-04. `claim_level = measurement_proxy_not_customer`.

Речевые литеры vs машинные ключи (запрет омонимии «b CLOSED»):

| Речь жюри | Машинный ключ 1.5.0 | Статус |
|---|---|---|
| RT-001a | `a_content_pairing` | CLOSED |
| — | `b1_protocol_rehearsal` (legacy `b_protocol_rehearsal`) | CLOSED; **не** RT-001b |
| **RT-001b** | `b2_criterion_dual_rater` | **OPEN** |
| RT-001c | `c_customer_corpus` | OPEN |
| RT-002a | `a_regulatory` | CLOSED |
| RT-002b | `b_eir_carrier` | CLOSED (носитель) |
| RT-002c | `c_corporate_signed` | OPEN |
| RT-003a | `a_federated_geometric_rehearsal` | CLOSED |
| — | `b1_navis_federation_carrier` | CLOSED |
| **RT-003b** | `b2_ifc_system_graph_rehearsal` | CLOSED (HVAC graph) |
| **RT-003c** | `b3_mep_system_clash` | **OPEN** |
| — | `c_customer_federated_ifc` | OPEN |

Запрещено: «RT-001b CLOSED»; недифференцированное «RT-001/002/003 CLOSED».

### 10.1 Замена (контур измерения) — CLOSED как тома, не как RT целиком

| ID | Том | Статус | Чем заменили отсутствие Самолёта |
|---|---|---|---|
| RT-001 | `a_content_pairing` | CLOSED | Типовые замечания экспертизы РФ (Эксп. Б) + публичные IDS + учебный комплект / инъекция / синтетические labels. Content (Messick), не criterion |
| RT-001 | `b1_protocol_rehearsal` | CLOSED | Два независимых **симулированных** прохода `sim-rater-a` / `sim-rater-b` на тех же 28 единицах. Не люди, не LLM. Не речевая литера RT-001b |
| RT-002 | `a_regulatory` | CLOSED | Публичные IDS: Мособлгосэкспертиза **24** `.ids`; СПб ГАУ ЦГЭ **22** `.ids` (`signed_by_customer=false`, `samolet_alias=false`, provenance OFFICIAL_PUBLISHED); ЦИМ АГР Москвы **4** `.ids` + pack `moscow_agr_2026` (city as publisher). Машинный порог: ≥20 MOEXP + ≥15 CGE + ≥3 AGR. Линейка измерения, не EIR Самолёта |
| RT-002 | `b_eir_carrier` | CLOSED | EIR v4.0 + BIM-стандарт v4.0 на канальном комплекте как **текст** (deep-study 30.08; имён в git нет). Носитель EIR, не `customer_approved`. `eir_lod_mep_disciplines_named=true` (ОВ/ВК/ИТП/ЭОМ/СС LOD названы; модели отсутствуют) |
| RT-003 | `a_federated_geometric_rehearsal` | CLOSED | Посаженный IfcClash: `clash-federated-box-{a,b}.ifc` и pipe vs wall. Оба прогона RUN, ≥1 hit. Не system-aware. В пине planted: `mep_system_clash=NOT_VERIFIED`, `closes_rt003` не true |
| RT-003 | `b2_ifc_system_graph_rehearsal` (речь RT-003b) | CLOSED | Учебная HVAC: 2× `IfcSystem` + `IfcRelAssignsToGroup`. Граф систем, не труба≠стенка. `geometry_verified=false`, `synthetic=true` |
| RT-003 | `b1_navis_federation_carrier` | CLOSED | Три NWD-федерации на канале. Нативный NWD не читаем. Не граф IfcSystem заказчика |

Исторические строки 24.08, где «RT-002b = подпись», читать как **RT-002c**.

### 10.2 Остаток (OPEN; подменой не закрывается)

| ID | Том | Статус | Почему нельзя закрыть подменой |
|---|---|---|---|
| RT-001 | `b2_criterion_dual_rater` (речь **RT-001b**) | OPEN | Двое независимых людей; κ/α; заключение экспертизы на тот же том. Симуляция ≠ люди. Инъекция и один автор фикстуры ≠ два разметчика. LLM ≠ разметчик. `independent_human_raters=0` |
| RT-001 | `c_customer_corpus` | OPEN | Хеш-пакет Самолёта не в git |
| RT-002 | `c_corporate_signed` (`b_corporate`) | OPEN | Подпись Самолёта / `customer_approved`. Текст EIR и город-издатель ≠ подпись. СТО Самолёта unsigned |
| RT-003 | `b3_mep_system_clash` (речь **RT-003c**) | OPEN | `mep_system_clash=NOT_VERIFIED`. 0 duct/pipe/cable в IFC комплекта. `IfcFlowTerminal` на АР — не граф заказчика. Репетиция HVAC ≠ координация инженерки. `parse_rvt_nwd_lira=false` |
| RT-003 | `c_customer_federated_ifc` | OPEN | Нет выгрузки NWD→IFC заказчика и signed clearance. Запрос 28.08: штатный пакетный экспорт NWD→IFC по одному корпусу (уже куплен), не «дайте федеративный IFC с нуля» |
| CDE T2 | импорт BCF | NOT_VERIFIED | T1 ≠ журнал импорта. `present_files=[]`. `claim_allowed=false` |

Open benches (AEC-Bench, IFC-Bench, GNI) — **другой контур**, чем RT-001b: они не пары «российский том ПД ↔ заключение экспертизы». IFC-Bench: 27/1026 countable; Harbor agent NOT_RUN; Ishigaki processability. GPLv3 IFC из IFC-Bench **вне** MIT-дерева. Frozen corpus SSOT КТ#2: `frozen_until: 2026-08-20`. IUA freeze SHA `f9389bf` ≠ HEAD.

Публичный duplex ARC vs MEP IfcClash RUN, 837 hits — engine rehearsal, не customer federated IFC, не coordinator BCF gold.

### 10.3 Dual-rater simulation (протокол, не люди)

- `independent_human_raters`: **0**
- `llm_counts_as_rater`: **false**
- `b1_protocol_rehearsal`: CLOSED
- `b2_criterion_dual_rater` (речь RT-001b): OPEN
- n: **28** (пилот протокола ≤30)
- Cohen κ: **0.705263** (порог tooling 0,60). n=28, симуляция; приблизительный 95% интервал широк (~±0,25). На слайде: «κ≈0,70, n=28, симуляция, интервал широк». Не «два эксперта»
- Krippendorff α: **0.706927** (порог 0,67)
- Gwet AC1: **0.869413** (порог 0,60)
- raw agreement: **0.8929**
- расхождений: **3**

Проход A (`sim-rater-a`): strict planted-gold — TP если frozen contract говорит дефект реален; FP если excluded/control; FN если unresolved/known miss.  
Проход B (`sim-rater-b`): conservative evidence — TP только с машиночитаемым evidence (GUID / IDS / canonical LOAD / inventory rule); geometric pipe-vs-wall не system MEP; free-text narrative вне сверки.

Ожидаемые расхождения (иначе κ=1.0 не независимость): `SYNTHETIC-AR-001-01`, `planted_federated_pipe_vs_wall`, `LB-004-freetext-area-mutation`.

Таблица A/B: FN/FN=2; FN/FP=1; FP/FP=2; TP/FP=2; TP/TP=21.

Когда появятся двое живых разметчиков на комплекте заказчика, этот CSV **не подменяется**: заводится новый журнал с человеческими `adjudicator_id`. Любой payload с `independent_human_raters>0` без человеческих `adjudicator_id` = OVERCLAIM.

Цитировать fixture κ как «два эксперта согласились» = OVERCLAIM.

### 10.4 Эксперимент Б — coverage_map_only, не точность продукта

Порядок анти-cherry-pick: сначала КР (худшее совпадение области применения: типовые КР ≈ расчёт; AeroBIM не solver).

**Headline КР ≈16,7%** (4/24 «обнаруживается») после LOGIC_ABSENT. Waypoint Task 3 ≈8,3% (2/24) — **не** текущая доля. Не цитировать 8,3% как текущую долю КР.

Сопоставимость: КР — Киров, другой орган/формат, чем АР и ВК (Мордовия, один PDF). Разница долей частично может быть методикой перечня, не только разделом.

| Раздел | n | вес 1 стр. | обнаруживается | условно | вне области | не обнаруживается |
|---|---:|---:|---:|---:|---:|---:|
| КР Киров | 24 | ≈4,2 п.п. | **≈16,7%** (4) | ≈25% (6) | 33% (8) | 25% (6) |
| АР Мордовия | 12 | ≈8,3 п.п. | **17%** (2) | 25% (3) | 42% (5) | 17% (2) |
| ВК Мордовия | 16 | ≈6,3 п.п. | **25%** (4) | 50% (8) | 13% (2) | 13% (2) |

КР «обнаруживается» четыре строки: #2 ТЧ topics полов/перегородок (inventory, не OCR обоснованности); #3 ТЧ≠значения раздела PD↔RD на synthetic KZH (не native graphics); #4 расчёты необоснованно в ПД (inventory, не корректность расчёта); #24 наличие разделов КР↔АР в комплекте (не геометрическая увязка листов).

Условно КР: 4 строки = norm-pack (≈17 п.п., RT-002); 2 = MISSING_ATTRIBUTE роли листа #9/#10 (≈8,3 п.п., не подтверждено чтением листа).

ВК условно включает RT-003 федеративную модель: 2 строки = 13 п.п. (#5 совместимость решений; #14 расстояния между сетями).

Не подавать 25% ВК как «лучшую точность». Не говорить «закрыли 25 пунктов полноты» — закрыли **четыре строки** класса полноты по КР.

Критерий статусов Эксп. Б: **обнаруживается** = проверка есть и срабатывает на типичном или open/synthetic пакете того же класса без customer-approved pack; **условно** = назван конкретный артефакт; **вне области** = суждение эксперта; **не обнаруживается** = нет runtime-пути.

### 10.5 Инъекция дефектов (синтетика)

Генератор: `inject_defects`, seed **20260824**. Одинаковый seed → одинаковые мутации. Инъекция **ниже** валидатора: не вызывает analyze API и не пишет `summary.passed`. Классы: AREA_MISMATCH, LEVEL_MISMATCH, PD_RD_DIVERGENCE, TZ_UNSATISFIED, MISSING_ELEMENT, UNIT_MISMATCH, CALC_INCONSISTENCY, IDS_VIOLATION, CONTROL. CONTROL вне знаменателя recall. Городские примеры АГР запрещены как source. `samples/customer` генератор отвергает.

Прокси детекции прогона 03.09: мутант **убит**, если мультимножество находок отличается от CONTROL. Исчезнувший сигнал = сокрытие, не подтверждение целевого дефекта. `claim_level=synthetic_only`. Не переносится на Самолёта.

**Контур 1 — канальный IFC (не в git; режим данных не согласован; не внешняя репродукция):** CONTROL/applied = 6, убито **0/6**, Wilson 95% lower **0.000**. Второй прогон: CONTROL=97, applied=6, убито **0/6**, lower **0.000**. Интервал 0/6: [0.000; 0.390]. Публикуется нижняя граница. Размеры файлов, шифры объектов и метка «NDA» в публичном тексте не ставятся (`nda_signed=false`). Классы sidecar контур не читает; MISSING_ELEMENT/IDS_VIOLATION не applied. AREA_MISMATCH бьёт в заголовок STEP `5.02` (версия EDM), не в площадь.

**Контур 2 mini-IFC (git-воспроизводим):** 8 классов applied; убит только MISSING_ELEMENT (снята IFCWALL). Mutation-kill **1/8** = 0.125; Wilson 95% [0.022; 0.471]; публикуется нижняя **0.022**. CONTROL=9; детерминизм pass. Площадь 12.5→15.513 контур не читает (demo-правила смотрят IfcSpace.NetFloorArea, не IFCQUANTITYAREA GrossFloorArea).

Это не «движок не работает». Это слепота пары инжектор↔контур на этом IDS/rule pack. Поверх этих цифр пороги не двигаем.

План precision: ~100 находок, двое людей, κ/α, evaluate_detection_precision. Не κ без n. Не >90%. Не корпус партнёра. Привлечение двух разметчиков — строка владельца, не факт корпуса.

---

## 11. ADR-001 и вердикт

Семантический владелец `summary.passed` = детерминированные выходы (ERROR count + blocking capabilities под активным sign-off профилем). Физический писатель = EvidenceAssembler — чистая функция. Advisory / AI / OCR никогда не поставляют входы, которые **одни** могут перевернуть `passed`.

Precedence `summary.outcome` (EGCC / Mushkani et al., arXiv:2607.29058 — in-repo pin; OSINT 05.09 ID UNVERIFIABLE):

1. confirmed finding failures / hard clashes → `FAILED`
2. intake blocked или required capability not OK → `BLOCKED`
3. HITL / missing source / low confidence → `REVIEW_REQUIRED`
4. warnings only → `PASS_WITH_WARNINGS`
5. else `PASS`

`REVIEW_REQUIRED` никогда не переписывает нарушение в pass. Неполное evidence никогда не становится `PASS`. `summary.passed` истинно только для PASS и PASS_WITH_WARNINGS.

Запрещённые действия провайдера: `call_tool`, `change_verdict`. `FORBIDDEN_LLM_ACTIONS`. `LLM_SELECTS_CHECK_ON_VERDICT_PATH=false`. `LLM_GENERATED_FUNCTION_WRITES_SUMMARY_PASSED=false`. Generated checkers не входят в sign-off без human-approved hashed pack с `approval_ref`. Overlay меняет только `remark`, не severity/origin. Реестр инструментов: `can_change_verdict=false`, иначе `validate_invocation` бросает.

Исключение честности: **llm_advisory не в списке блокеров pass** — иначе падение модели красило бы комплект. Clash/IDS — в списке блокеров.

Гибрид RT-E: advisory ON vs OFF → идентичные детерминированные findings и идентичный `summary.passed`; различаться могут только advisory remarks/warnings.

Fail-closed: capability failed / required-not-OK роняет вердикт. `require_clash` + SKIPPED clash ⇒ FAILED + `passed=false`. Raster requested+analyzer+zero annotations ⇒ FAILED. Norm pack load error если запрошен ⇒ failed ⇒ passed=false; не запрошен ⇒ skipped (не блокер). Unexpected exceptions в quantity/load/MEP probe ⇒ FAILED + traceback (не soft WARNING). Unparsed `.dwg` при успешном `.dxf` ⇒ `dwg_dxf=FAILED` (DXF не маскирует DWG).

Идемпотентность: одинаковый вход → одинаковый `passed`. Находка без `finding_id` / `source_id` / `evidence_refs` в персистенс не проходит.

Публичная формулировка: «deterministic Shared-gate applied at evidence assembly» — не «AI ставит pass» и не «нет автоматического статуса». Автоматический **технический** статус есть.

Аналогия: детерминированные правила = основа скоринга; LLM = advisory-слой текста; решение Shared-gate не у модели.

---

## 12. IFC: четыре числа, четыре смысла

| Число | Байты | Единица | Чем управляет |
|---|---:|---|---|
| SPF in-memory | 268 435 456 | 256 **MiB** | `ifcopenshell.open(.ifc)`; `AEROBIM_MAX_IFC_BYTES` |
| bSI Validation Service | 256 000 000 | 256 **MB** | Публичная загрузка uncompressed .ifc |
| WASM viewer | 268 435 456 | 256 **MiB** | web-ifc MEMORY_LIMIT |
| Disk analyze / ingest | 1 500 000 000 | 1,5 **GB** decimal | HTTP 413 выше; RocksDB convert затем `open(rdb)` под `samolet_pilot`/`production` |

256 MiB − 256 MB = 12 435 456 байт. Файл может пройти AeroBIM SPF analyze и провалить bSI. FAQ bSI «250 MB» vs user guide **256 MB** — не одно число с нашими 256 **MiB**.

Почему SPF default не поднимается: IfcOpenShell #7116 — SPF parse ~275–300 MB ≈ 10× disk RAM; Riverside 275 MB → 2,19 GiB RSS (~8×). Планировочный множитель в git = **10**, литература, не наш RSS на файле Самолёта. `measured_rss_delta_bytes` null. 1,5 ГБ SPF-opened ≈ 15 GiB литературы. Поэтому 1,5 ГБ идёт через RocksDB (upstream ~11 MiB vs 2,19 GiB SPF на том же ~275 MB). Convert failure → HTTP **503** `IFC disk backend unavailable`. Над ingest → HTTP **413** `ifc_over_ingest_cap`, сообщение `IFC exceeds analyze size limit` (без byte oracle). WASM и object-store get_bytes остаются 256 MiB. Не буферизовать 1,5 ГБ для preview. Development HTTP без Samolet caps: `max_model_bytes=256 MiB`.

1,5 ГБ скорее потолок authoring-экспорта Revit toolkit, не обещание SPF-open. Industry thumb: держать IFC ~250 MB или сплит.

`raises_default_cap = false`. `rocksdb_backend = wired_over_spf_cap`. Не парсит RVT/NWD/LIRA. Upload: один XHR с progress/cancel; resumable protocol **не** реализован.

Классификация байт: `analyze_ok` (SPF) / `analyze_disk` (RocksDB) / `over_ingest`.

---

## 13. Auth, HITL, изоляция

Default `GET /v1/auth/bff` = **501** / `auth_bff=NOT_IMPLEMENTED`. Vite loopback Authorization inject — только development. Phase 2 stubs login/callback/logout с CSRF — не production session. Phase 2.5 PKCE S256 — всё ещё 501. Phase 3 lab: код за `oidc_bff_phase3_ready` (token URL + client secret + cookie secret + redirect allowlist). Default остаётся NOT_IMPLEMENTED. Lab 200 LAB ≠ customer SSO.

Переключатель роли в шапке — **макет экрана, не RBAC**. Shared bearer = транспортная аутентификация пилота; **не** создаёт expert HITL события (`is_service_token` denied). Cookie в браузере права эксперта не выдаёт. Unverified BFF cookies never authorize. Verified lab cookie может bind AuthPrincipal; viewer/user expert HITL writes остаются 403.

HITL reviewer-role gate **включён только** при `signoff_profile ∈ {samolet_pilot, production}`. Development / fixture / default demo **не** требуют reviewer roles (static bearer всё равно blocked на HITL write). Не демонстрировать ролевую модель под non-pilot профилем и утверждать, что gate живой.

Non-dev: `AEROBIM_ENV != development` + empty bearer + no OIDC → Settings/bootstrap отказывается стартовать. Soft clash env flags игнорируются под pilot/production. Non-dev default `signoff_profile=production`.

ACL: cross-tenant → **404** (не 403). Object enumeration избегается. SSRF guard на JWKS / bSI / OpenCDE. OIDC tenant только из `AEROBIM_OIDC_TENANT_CLAIM` (default `tenant_id`). Upload response опускает `object_key`.

Изоляция по проектам (п. 3.1.1 ответов) — модель доступа, не on-prem и не «HTTPS = изоляция».

---

## 14. BCF лестница T0–T4

| Tier | Имя | Что доказывает | Статус |
|---|---|---|---|
| T0 | Export surface | HTTP/API может выдать BCF ZIP (2.1 default; 3.0 experimental) | AVAILABLE |
| T1 | Structural + dual-consumer | ZIP schema members parse; ≥2 независимых consumer согласны по GUID/title/viewpoint | EVIDENCED |
| T2 | Independent CDE import | СОД заказчика импортировала ZIP с log + screenshot + hashes | **NOT_VERIFIED**; `present_files=[]`; `claim_allowed=false` |
| T3 | Round-trip fidelity | Topics/comments/viewpoints переживают CDE → re-export | NOT_STARTED (блок T2) |
| T4 | Production handoff | Повторные импорты под signed scope | NOT_STARTED |

Целевая СОД идентифицирована 28.08 на уровне адреса: **10D** (samolet10d.ru); confirmation = origin share-link; содержимое папок не читалось; тип доступа неизвестен. Путь закрытия без файлов заказчика: vendor public Swagger + developer demo license + synthetic BCF в demo-tenant — это **engineering evidence**, не proof реестра заказчика. `claim_allowed` остаётся false до реального импорта.

Запрещено до T2+: BCF ready for CDE; CDE interoperable; production BCF handoff; integrated with customer CDE. OpenCDE BCF API push = Foundation, не T2.

Не изобретать скриншоты СОД.

---

## 15. ADR-005 — данные заказчика vs публичный MIT

Публикация в git необратима без переписывания истории. Письменного режима данных на 04.09.2026 нет.

В публичный git **не** кладём: имена объектов, шифры комплектов, пути шары, кадастр, хеши живых файлов, пофайловые реестры, дефекты конкретной выгрузки как «их косяк», цитаты внутренних регламентов.

Исходящие письма с цензом живут вне публичного дерева. Git почту не отправляет.

Самоограничение не ждёт ответа. Уже закоммиченные исторические пины не удаляются скрытой переписью истории без явной команды владельца. Новый текст не добавляет фактов канала.

Речь: «данные — критический путь; запрос от 04.09; план Б работает с 09.09». Не «ответственность полностью на стороне заказчика». Демо: локальный стенд и шаринг экрана.

---

## 16. Прочие инварианты честности

**PrecisionClaim:** typed claim; render withheld unless `corpus_kind=customer` и ≥2 adjudicators.

**Runtime baseline:** `export_runtime_baseline --run-gates --require-clean-tree`; `publishable: true` только на clean tree; `attested_by=ci`. Исторические blocker-file figures SHA `019962141606` — prior pin, не текущий SSOT. Operational freeze SHA `f2615e7` (2026-07-21) не HEAD. Red Team freeze `c0c4b2b` / `8efbef8` — не трактовать defect prose архива как open, если ID в CLOSED tables.

**Attestation:** нельзя подделать локально `--attested-by ci` (N-18 CLOSED 09.08; attestation только из `GITHUB_ACTIONS`).

**PDF лицензии:** production path pypdfium2 + pdfminer.six. PyMuPDF optional `pdf-agpl` only, отсутствует в runtime lock/Docker. Не судебное мнение.

**Detached signature (WP-03):** presence/hash/roles; `qualified_signature` ENG_PARTIAL; trust_chain always NOT_VERIFIED.

**I9 IFC KG:** port + DI + fixture QA — advisory scaffold. Multi-hop GraphRAG не shipped.

**Hybrid AI:** HybridRouteGate mandatory before Analyze advisory observations; domain-pure, verdict-neutral, fail-closed; never sets `summary.passed`. PUBLIC VLM egress + PrivacyGuard salt-on-egress — residual; masking ≠ anonymity.

**Redis/jobs:** Redis job store required outside development; in-memory dev/test only; arq workers post-pilot.

**IFC streaming / disk R-tree:** designed, not implemented. JSON sidecar IfcSpatialIndex ≠ disk R-tree и не wired в analyze.

**Bare-metal offline:** DEFERRED; Docker track only.

**Annotation GUID (P2-04):** presence confirm via spatial index only; не adjudicated.

**MEP edge provenance + AABB:** `geometry_verified=False`; capability stays NOT_VERIFIED. Naive 7-discipline federation ~44k elements может OOM (~30 GB); bbox pre-broadphase обязателен до цитирования runtime. Fixture «~0.5 s» не tracker SLA.

**MinStroy XSD:** intake format, не remark corpus.

**SPb GAU CGE profile:** OFFICIAL_PUBLISHED, не customer-signed, не закрывает RT-001/002, не акт экспертизы.

**Москва AGR CIM IFC с 02.04.2026** (17-ПП + приказ DIT/DGP) — **городское правило подачи**, линейка RT-002a, не профиль приёмки Самолёта.

**Renga:** не стек Самолёта без квалификатора ИЖС.

**Fixture extraction:** RU macro F1 на фикстуре ≈0,86 в alignment-доке — **не** customer accuracy. EN structured corpus macro F1 1.0 на structured fixtures — не продукт.

**Synthetic detection harness:** контракт 4 TP / 2 FP / 2 FN — harness-only.

**Vision/AECV:** open-bench Yandex Qwen macro exact-match 0.4325, `open_bench_only` — не product / RT-001.

**POST /v1/demo/seed-fixture:** development-only; копирует git samples walls+IDS; **не** в опубликованном OpenAPI; две fire-rating находки ≠ точность продукта.

**UI:** не грузит Google Fonts. Не delivered full-cycle workplace. Восемь IA screens все `partial`.

**Priority profile:** `AEROBIM_PRIORITY_PROFILE=samolet` (fire/structure/cross-doc boost) — приоритизация, не accuracy.

**ISO 19650-lite поля** на отчётах — metadata Shared-gate, не CDE.

**LOIN** на issues: geometry/alphanumeric/documentation.

**Spatial predicates** отделены от IDS: FindingCategory.SPATIAL.

**Revit thin-client:** helper script export_and_open_report — не native RVT parser.

---

## 17. Объект жюри (КТ#3 без пакета заказчика)

Команда на чужом ноутбуке: `python -m aerobim.tools.run_kt3_jury` (или `run_demo_ifc_acceptance_gate` + `run_kt3_without_customer`). Ожидаемо `summary.passed=false` на defect fixture. Показать finding с GUID (FireRating REI60 vs REI30), не пустой-GUID area row. Не открывать `wall-guid/report.html` или снимок HTML 11.08 как live. Native RVT/NWD: показать **отказ**. BCF: структурный T1; импорт NOT_VERIFIED.

`kt3-without-customer` schema 1.6.0; `plan_b_decision: re-scope`; `customer_files_expected: false`.

Сценарий 8–12 мин: формула стадии → шов файлов → четыре контура → живой CLI → acceptance-gate.json + одна находка HTML → BCF T1 → split томов RT → ask: два разметчика + IFC инженерии/арматуры или письменный OOS. Не просить «закройте GO сегодня». 5–10 комплектов/день — формулировка 25.08, не SLA.

Если покажут PDF ТЗ v1 на 6 страницах: это бриф конкурса; канон — ТЗ v2; >90% — цель оценивания.

Если спросят про 1,5 ГБ: приём и разбор через RocksDB до 1,5 ГБ; SPF в RAM и WASM — 256 МиБ; первый файл >1,5 ГБ — отказ analyze, не по норме; RSS на файле Самолёта не замерен.

Вопрос №1 комиссии про разграничение доступа — дословно §4.5 стоп-лист не покрывает, ответ: «Переключатель в шапке — макет экрана, не RBAC. GET `/v1/auth/bff` = 501, это не OIDC. HITL-запись на сервере: shared Bearer и роль viewer/user под pilot/production → 403. Cookie в браузере права эксперта не выдаёт. Production SSO в этом окне не обещаем.»

Jury clone contract: 0 failed на документированных extras; skips allowed. Не публиковать локальные counts как CI pin.

Vertical slice: overlay = deterministic bbox, не CV.

Unsigned OOS templates существуют как шаблоны; подписи назначающей стороны нет. Signed OOS ≠ RT-003 CLOSED.

Eng readiness ≠ customer GO. Form 5/5 submission fields ≠ customer_go.

---

## 18. ADR-002 / ADR-003 / ADR-004 (кратко)

ADR-002: open-core discussion; LICENSE остаётся MIT. Нулевой вход К4 согласован с MIT.

ADR-003: DWG/ODA trial — native DWG не продукт КТ#3.

ADR-004: prize IP vs п. 6.3; MIT fork honesty; не обещать exclusive-rights fence.

---

## 19. Инженерные блокеры: что OPEN для customer sign-off

Живые residual volumes: RT-001b dual **human** raters; RT-001c customer corpus; RT-002c Samolet signature; RT-003b `mep_system_clash`; RT-003c customer federated IFC; CDE T2; production OIDC BFF DESIGNED/NOT_IMPLEMENTED.

Закрытые remediation (не переоткрывать как open, если нет регрессии): RT-004 clash SKIPPED blocks pass; RT-005 tenant ACL; RT-006 frontend tests in CI; RT-007 finding provenance contract; RT-008 PARTIAL (T1 yes, T2 no); RT-010 calculation_correctness=NOT_IMPLEMENTED honesty; RT-011 capabilities API; RT-012 SLA claim gate schema (customer SLA всё ещё не доказан); N-18 attestation forgery; LIC-001 core PDF Option B; POST-01..04, 06..11 security/fail-closed wave; RTATOM wave A1/A2 hygiene.

Архивный prose с заголовками BLOCKER под CLOSED tables — **не** open items.

---

## 20. Текстовые симптомы дрейфа (аудитор без grep)

Живой SSOT после 04.09: Checkpoint **GO** + `customer_go` false. Ниже — формулировки, которые в живых (не исторических) документах означают DRIFT. Исторические pin августа/июля с NO_GO = HISTORICAL_PIN, если помечены датой ≤ рескоупа и не выдаются как текущий статус продукта.

| Симптом в тексте | Класс | Правильная формула |
|---|---|---|
| «Нельзя: Checkpoint GO» / «Не говорить \| Checkpoint GO» как stop-list продукта | DRIFT | Stop-list = **Customer GO** |
| «Checkpoint продукта NO_GO до RT-001/002/003» на ТЗ v2 YAML / readiness memo как **текущий** статус | DRIFT | GO измерительный; residuals OPEN; customer_go false |
| «Keep checkpoint NO_GO until RT-001/002/003 evidenced» в intake next_actions | **remediated 05.09** в live JSON; копии текста = DRIFT | Keep checkpoint GO; customer_go false until residuals |
| «Not Checkpoint GO» в claim_boundary скоринга МИК | DRIFT docs | Not **customer_go**; Checkpoint GO |
| «УГТ 6+: Нет. Checkpoint GO» без пояснения | DRIFT/ambiguous | УГТ 6+ нет; Checkpoint GO — другой флаг |
| CLAIM_BOUNDARY модуля скоринга: «Checkpoint stays NO_GO» | **remediated 05.09** в Python | Checkpoint GO; customer_go false |
| «Не перекрашивает NO_GO» в конце пакета вопросов 04.09 | DRIFT лексики | не перекрашивает **customer_go** / undifferentiated RT |
| Dated JSON `"checkpoint":"NO_GO"` августа без qualifier historical | HISTORICAL_PIN если generator мёртв; DRIFT если live renderer всё ещё эмитит |
| PPTX речь обновлена, PDF колоды нет | DRIFT носителя | текстовый контракт = PPTX |
| IUA «Checkpoint GO = customer GO» как **blocked inference** | CONSISTENT | не удалять |
| Red-team аудиты с Checkpoint NO_GO на дату аудита | HISTORICAL_PIN | |
| КТ#2 STATUS.json `checkpoint_verdict=NO_GO` | HISTORICAL_PIN обязательный | |
| `independent_human_raters>0` без human adjudicator_id | OVERCLAIM | |
| `closes_rt001: true` без a/b/c | OVERCLAIM | |
| `agr_pack` как закрытие подписи Самолёта | OVERCLAIM | RT-002a only |
| κ=0.705 как «два эксперта» | OVERCLAIM | sim-rater |
| 16,7% как product accuracy / Samolet KPI | OVERCLAIM | coverage_map_only |
| 1/8 mutation-kill как recall продукта | OVERCLAIM | synthetic_only |
| n=6 AABB P=R=1.0 как метрика коллизий | OVERCLAIM | Wilson lower ≈0.61; не жюри |
| Form 5/5 или «документы TBD заполнены» = customer_go | OVERCLAIM | |
| «RT-001b CLOSED» | OVERCLAIM / омонимия | RT-001b = люди OPEN; протокол = b1 |

---

## 21. Таблица решений аудитора

| Гипотеза | Если истинна | Disposition |
|---|---|---|
| Product checkpoint GO без `go_kind=regulatory_measurement_mvp` или с `customer_go=true` | онтология сломана | OVERCLAIM |
| Residual labeled CLOSED из-за moscow_agr / sim-raters / planted clash / signed OOS | double-count / category error | OVERCLAIM |
| Речевая формула сдвинулась на locked-поверхности | claims lock fail | DRIFT |
| КТ#2 STATUS.json перевернут в GO | historical pin destroyed | OVERCLAIM |
| Строка матрицы ТЗ `blocked` переименована в `done` без customer evidence | honesty fail | OVERCLAIM |
| Итоговый балл МИК предсказан из git | forbidden IUA | OVERCLAIM |
| «RT-002 CLOSED» без a/b/c | forbidden | OVERCLAIM |
| «RT-001b CLOSED» | speech омонимия | OVERCLAIM |
| Канал 25.08 описан как «нет данных» | speech fail | DRIFT |
| Checkpoint GO произнесён как «можно в прод Самолёта» | Customer GO leak | OVERCLAIM |
| Stale NO_GO на живом SSOT (константы, README, формула FAQ) | incomplete re-scope | DRIFT |
| Stale NO_GO на July CLAIMS_LOCK / КТ#2 handoff | expected | HISTORICAL_PIN |
| ТЗ v2 YAML всё ещё пишет Checkpoint NO_GO | source TZ vs ontology | DRIFT (не OVERCLAIM продукта, если речь жюри уже GO) |
| predicted_aerobim_total число | forbidden | OVERCLAIM |
| mep_system_clash=OK | forbidden | OVERCLAIM |
| CDE T2 VERIFIED при present_files=[] | invention | OVERCLAIM |
| PrecisionClaim.publishable при corpus_kind≠customer | forbidden | OVERCLAIM |

---

## 22. Жёсткий список non-claims (полный)

Не утверждать:

1. Точность продукта >90%; product accuracy %; Experiment B % как detection rate.
2. Customer SLA ≤30 мин; 5–10 packs/day как измеренный SLA; fixture p95 как представительный.
3. Native DWG/RVT/NWD product-ready; ODA Sustaining = BimRv; DXF success = DWG support.
4. MEP delivered; mep_system_clash=OK; pipe vs wall = system-aware; HVAC fixture = координация ИОС заказчика; IfcFlowTerminal на АР = граф заказчика.
5. CDE-ready BCF; 10D import proven; Tangl/10D integration; «интегрированы с платформой заказчика».
6. Production-ready; fully Russian stack; Qwen ready as product; OIDC live / облако с логином; SPF-open 1,5 ГБ; WASM 1,5 ГБ.
7. «Закрыли ТЗ Самолёта»; «пакет заказчика проверен»; 43 ГБ обработаны; NDA подписан; режим данных согласован.
8. First-in-Russia version compare; точнее городского нормоконтроля; замена bSI validator / зарубежных проверяльщиков; SP 63 template customer-approved.
9. Приз в кармане; 52,6 как наш балл; порог 50 автоматический; УГТ 5; независимая ОГТ; 42001 сертификат; 72514/72515 сертификат; ПНСТ 841 SQuaRE; законопроект 166424 как закон.
10. 10,1 млрд как SAM; 25,1 млрд как наша выручка; −72% как наш эффект; «спасём МСФО»; CAPEX-запрос; РСБУ +31% как группа.
11. Iversen F1 как наш; «мы лучше Iversen»; LLM выбирает проверки на Shared-gate.
12. Fixture n=6 AABB как метрика коллизий для жюри.
13. Симулированные разметчики = люди; LLM = rater; автор фикстуры дважды.
14. Городской IDS / AGR = подпись Самолёта; текст EIR = customer_approved; СТО unsigned = deployed.
15. Signed OOS = RT-003 CLOSED; Form 5/5 = customer_go; eng readiness = customer GO; Checkpoint GO = можно в прод.
16. Недифференцированное RT-001/002/003 CLOSED.
17. QTO/MATCH Office = calculation_correctness / LIRA solver.
18. IfcSpatialIndex JSON dump = disk R-tree / streaming parser.
19. GraphRAG / IfcLLM product; CV human-level; VLM whole-sheet sign-off; inefficient space delivered.
20. Четыре карточки каталога = все заявители; 15 пилотов соседа как факт; цитата спонсора = председатель.
21. i.moscow/pilot или грант 631-ПП / 449-ПП = приз задачи №6.
22. Self-assessment как external/independent audit.
23. Mutation-kill 0/6 или 1/8 как customer recall.
24. Coverage map площадей/огнестойкости заказчика как акт дефекта / уже измеренная точность.
25. «Неэффективное пространство не нужно заказчику» — заказчик пункт назвал.

---

## 23. Схема выходного отчёта аудитора (обязательна)

Аудитор выдаёт **один** текст со следующими разделами. Без репозитория все «проверки файлов» заменяются проверкой **внутренней согласованности этого корпуса** и любых приложенных позднее фрагментов.

```
A. Identity check
   - CHECKPOINT, GO_KIND, CUSTOMER_GO, closes_rt*, PRECISION, MEP, CDE
   - Вердикт: CONSISTENT | DRIFT | OVERCLAIM

B. Speech lock
   - Наличие пяти маркеров RU
   - Нарушения стоп-листа 1–32 в приложенных текстах (если есть)
   - Вердикт по каждому нарушению

C. TZ coverage (ТР-1…ТР-68)
   Таблица: ID | заявленный статус в корпусе | критерий приёмки | residual?
   Итог: сколько done / partial / missing / blocked
   Не суммировать в «ТЗ закрыто»

D. TZ §9 vs actual measurement
   - 0.60 dual-human: не измерено на Самолёте; sim κ не заменяет
   - >0.90: publishable false
   - 30 min: fixture only; 25.08 не подтвердил
   - HITL accept rate: протокол есть, партнёрских часов нет

E. MIK
   - predicted_aerobim_total must be null
   - Система A mean vs система B sum
   - Приложение 3 не видано
   - 52.6 identity ≠ score
   - УГТ 4 ≠ 5
   - К1 объект = заявка, не git
   - Б2 confirmed_partner_validation_metrics = false

F. RT volume ledger
   Для каждого тома §10: статус, substitute, residual reason
   Явный запрет undifferentiated CLOSED

G. Architecture / ADR-001
   - LLM не пишет passed
   - Forbidden OK states
   - Hybrid ON==OFF

H. Data / intake / ADR-005
   - Канал получен; pack not in git
   - Все gates false
   - Не «нет данных»

I. Jury object honesty
   - passed=false ожидаем
   - GUID finding
   - Native refuse
   - BCF T1≠T2

J. Drift register
   Список симптомов §20, найденных в этом корпусе самом (самопротиворечия)
   и в приложенных текстах

K. Residual volumes (must remain OPEN)
   RT-001b humans (`b2`); RT-001c corpus; RT-002c signature; RT-003c mep (`b3`);
   `c_customer_federated_ifc`; CDE T2; OIDC BFF production

L. Non-claims attestation
   Подтвердить, что отчёт аудитора сам не нарушает §22

M. Final
   Одна фраза: Checkpoint GO (regulatory_measurement_mvp); customer_go false;
   undifferentiated RT OPEN; not a MIK score.
```

### 23.1 Самопротиворечия, уже лежащие внутри источников (аудитор обязан зафиксировать как DRIFT источников, не как право customer_go)

1. ТЗ v2 front-matter и §13/§20: «Checkpoint продукта NO_GO» vs живые константы GO 04.09.
2. Матрица соответствия §8 P0: «Checkpoint NO_GO».
3. Alignment R-док claim_boundary смешивает старую формулу.
4. Intake `next_actions`: **remediated 05.09** (live JSON: Keep checkpoint GO; customer_go false).
5. BCF ladder prose: «Checkpoint remains NO_GO» при front-matter GO.
6. Pilot claim-boundary verified-table строка «IFC+IDS evidence layer … Checkpoint NO_GO» vs шапка того же файла GO.
7. MIK levers claim_boundary: «Not Checkpoint GO» рядом с «Checkpoint GO».
8. `mik_commission_scoring.CLAIM_BOUNDARY`: **remediated 05.09** (Python: Checkpoint GO; customer_go false).
9. Вопросы 04.09 финальная строка: «Не перекрашивает NO_GO».
10. TRL таблица УГТ 6+: «Нет. Checkpoint GO» — двусмысленно.

Корпус аудитора v2.1 (05.09) закрыл внутри себя: §32→§23; done/partial; ТР-63 vs матрица; ТР-15 not_verified; литеры b1/b2/b3; метка NDA; квалификатор 0,60; 117,4 млрд; библиография К2 с DOI; κ n=28 интервал. Остальное в §23.1 — DRIFT **источников**, не онтологии.

---

## 24. Краткая карта «что считать выполненным для жюри vs заказчика»

| Слой | Для жюри / измерения | Для Самолёта / customer_go |
|---|---|---|
| IFC+IDS fail-closed | да, фикстура | их pack_hash + signed IDS |
| Замечание с GUID и нормой | да, учебный комплект | цитата СТО из их папок 1.2.1 |
| Dual-rater протокол | симуляция κ≈0,70 n=28 (интервал широк) | двое людей на их томе |
| Коллизии | посаженный geometric + HVAC graph rehearsal | IFC ОВ/ВК или письменный OOS |
| EIR | текст v4 на канале | customer_approved |
| BCF | ZIP T1 | журнал импорта 10D |
| SLA 30 мин | инструмент + fixture | согласованный эталон + corpus-kind customer |
| Точность >90% | запрещено говорить | P4 + publishable |
| UI | review shell / CLI жюри | не «рабочее место сдано» |
| Auth | 501 honesty | не SSO |

Короткий ответ на «почему customer_go false, если ТЗ закрыто документацией?»: ТЗ v2 закрывает *содержание* проверки на учебном комплекте (Messick content). Оно не закрывает *критерий* «пилотировать на комплектах Самолёта». Документы TBD заполнены; `customer_go` рисует заказчик. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` false — статус **приёмки**, не статус «команда не готова измерять». Публичный критерий Техлаба «готовность к внедрению» переводить в «готовность к пилоту на согласованном пакете», не в «внедрено».

---

## 25. Disposition внутреннего аудита 2026-09-05

Метод: внутренний аудит корпуса; OSINT в §0.6; флаги §3.1 не изменены.

| Код | Итог |
|---|---|
| A Identity | CONSISTENT |
| B Speech | CONSISTENT (витрина 07 ≠ номер Положения) |
| C TZ | Content закрыт документально; criterion открыт; статусы унифицированы в v2.1 |
| D §9 | CONSISTENT; 0,60 = методика, не письмо заказчика |
| E MIK | `predicted_aerobim_total=null`; 52,6 = тождество полос |
| F RT | undifferentiated CLOSED отсутствует; схема **1.5.0** b1/b2/b3 |
| G ADR-001 | CONSISTENT |
| H Intake | CONSISTENT; NDA-метка снята |
| I Jury | CONSISTENT |
| K Residuals | все OPEN |

Приоритеты freeze 18.09, ещё открытые **вне** этого корпуса: YAML ТЗ v2 «Checkpoint NO_GO»; BCF ladder prose; TRL УГТ 6+; «Не перекрашивает NO_GO» в вопросах 04.09.

Конец корпуса. Нет подразумеваемого балла МИК. Нет подразумеваемого `customer_go`. Нет подразумеваемого undifferentiated RT CLOSED. Аудитор работает только с этим текстом, пока не приложены дополнительные фрагменты.
