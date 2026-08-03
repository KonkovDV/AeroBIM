---
title: "Red Team — AeroBIM vs world practices (A1–A8)"
status: active
version: "1.0.0"
last_updated: "2026-08-04"
claim_boundary: "Claims-justification audit only. Checkpoint remains NO_GO. No new product metrics invented. ADR-001 / claim boundary unchanged."
---

# Red Team: AeroBIM против мировых практик (2025 — авг 2026)

**Роль:** рецензент-скептик жюри Техлаба.  
**Объект:** разрыв между документацией репозитория (`main`) и защитимым перед читавшим литературу.  
**Не объект:** баги кода (закрывались отдельными волнами).  
**Checkpoint:** **NO_GO** (RT-001/002/003) — не меняется этим отчётом.

Проверка внешних якорей: 2026-08-04 (arXiv / GitHub / mediaTUM / ScienceDirect abstracts).

---

## Находки

### A1 — Открытые бенчмарки не прогнаны при известности литературы

| Поле | Содержание |
|---|---|
| **Критичность** | **высокая** |
| **Что заявлено** | RT-001 блокирует точность без корпуса заказчика: `audit/reports/CRITICAL_BLOCKERS.md` §RT-001 («Product HOLD — RT-001 still OPEN until customer corpus»). Open corpora явно не дают product accuracy: `samples/benchmarks/open-corpora/README.md` L28–28 («never product accuracy»); `docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md` L18–24 (fixture/open ≠ publishable product accuracy). |
| **Чем опровергается** | **AEC-Bench** (arXiv:2603.29199; github.com/nomic-ai/aec-bench; **Apache 2.0**) — датасет + agent harness + evaluation code. **AECV-Bench** (arXiv:2601.04819; github.com/AECFoundry/AECV-Bench) — 120 планов + 192 QA. Оба доступны без байта от Самолёта. В репозитории бенчи **цитируются** как литература (`docs/docs.md` L295, L411; `docs/architecture/KIMI_K3_MIK_TECHLAB_ALIGNMENT_2026_07_27.md` L24), но в `docs/evidence/` **нет** артефакта прогона AeroBIM/его VLM-контура на этих харнессах. Нет записанного решения «сознательно не прогоняем и почему». |
| **Почему риск на защите** | Вопрос «почему нет числа на открытом бенче?» больше не закрывается фразой «нет корпуса заказчика» — это звучит как нежелание измеряться. |
| **Минимальное исправление** | (1) Одностраничный decision record: *customer KPI* vs *external open-bench baseline*. (2) Smoke-прогон **одного** открытого контура (предпочтительно AECV counting exact-match **или** узкий IFC-Bench retrieval через детерминированное ядро) → артефакт в `docs/evidence/` с `claim_level=open_bench_only`, `≠ RT-001`. (3) На слайд «видит ≠ проверяет» — цитата AECV-Bench capability gradient (OCR силён / символы слабы), явно как *чужой* результат, не ваш KPI. |
| **Что нельзя делать** | Публиковать open-bench score как «точность AeroBIM» / «>90%» / закрытие RT-001. |

**Нюанс (обновление 2026-08-04 вечер):** L1 decision record + IFC-Bench v1 smoke (**7/7** countable) + **live AECV counting** on Yandex `qwen3.6-35b-a3b` (120/117/3; macro exact-match **0.4325**; Door/Window/Space weak, Bedroom/Toilet strong) → `docs/evidence/aecv-bench-eval-latest.json`, Red Team note `RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md`. AECV **QA** LLM-judge path and AEC-Bench **agentic** Harbor trial still deferred. Checkpoint remains **NO_GO**; `closes_rt001=false`.

---

### A2 — Агрегат «точность» vs оси Recognition / Reasoning / Judging

| Поле | Содержание |
|---|---|
| **Критичность** | **средняя** |
| **Что заявлено** | ТЗ / Claims: единый порог «>90%» как evaluation target (`docs/pilot-claim-boundary-2026.md` L27; `docs/docs.md` L299). Interim KPI — одно число TP/(TP+FP) ≥ 0.60 (`QUALITY_MEASUREMENT_PROTOCOL` L99–101). Стратификация есть, но по **discipline × criticality × finding_class × modality** (`QUALITY_MEASUREMENT_PROTOCOL` L28–36), не по осям восприятия/рассуждения/суждения. |
| **Чем опровергается** | **MechVQA** (arXiv:2605.30794, ICML 2026) — Recognition / Reasoning / Judging как раздельные оси. **AECV-Bench** — отдельные категории OCR / counting / spatial / comparative. **BRAVO** — четыре диагностических слоя (perception → compliance reasoning) + non-compensatory CRS. Смешение в один процент методологически устарело. |
| **Почему риск на защите** | Вопрос «а по каким классам ошибок?» обнажит, что протокол готовит страты finding_class, но публичная риторика и ТЗ-порог остаются одним числом. |
| **Минимальное исправление** | В WP-07 добавить mapping: finding_class → (Recognition \| Reasoning \| Judging \| Formal-check) и запрет публиковать только macro без per-axis / per-class Wilson. MechVQA/BRAVO — в bibliography `docs.md`. |
| **Что нельзя делать** | Заявлять «мы уже измеряем как MechVQA» без артефакта; подгонять strata post-hoc под удобный процент. |

---

### A3 — Протокол оценки vs гибрид LLM-as-a-judge

| Поле | Содержание |
|---|---|
| **Критичность** | **средняя** |
| **Что заявлено** | Dual-blind эксперты + κ/α + Wilson (`QUALITY_MEASUREMENT_PROTOCOL` L56–58, L111–117). В VLM-протоколе LLM-judge **отвергнут** для выбора модели: ChartMuseum маскирует перцептивные ошибки (`docs/pilot/VLM_OCR_COMPARISON_PROTOCOL_2026_08.md` L22–23). |
| **Чем опровергается** | AECV-Bench QA scoring: automatic match + **LLM-as-a-judge** + human adjudication **только** edge cases. Практический выигрыш — человеко-часы при том же качестве; адъюдикаторы — заявленный дефицит (grant docs). |
| **Почему риск на защите** | «Мы отвергли LLM-judge» защищает качество метки, но не отвечает, почему не используете гибрид как *pre-filter* очереди экспертов. |
| **Минимальное исправление** | Decision note в WP-07: LLM-judge **разрешён** только как triage/queue-ranker (не как publishable truth); human на disagreement + critical strata; ссылка AECV-Bench + ChartMuseum как границы. |
| **Что нельзя делать** | Подменять dual adjudication LLM-judge для publishable precision; публиковать judge-score как κ. |

---

### A4 — Библиография: `research.md` и DOI-близнецы

| Поле | Содержание |
|---|---|
| **Критичность** | **высокая** (процесс / доверие), **с оговоркой по локальному git** |
| **Что заявлено** | Errata прямо: «there is no `research.md` at repo root; apply fixes wherever mirrored (ClickUp doc, decks…)» — `docs/research/CITATION_ERRATA_2026_08_03.md` L3–4. Жюри-пак `docs/docs.md` L409–420 содержит список DOI/arXiv. |
| **Чем опровергается / статус проверки** | Пара `10.1016/j.aei.2025.103676` / `…2026.103676` **в локальном git не найдена** (grep по репо = 0). Внешне: **2025.103676 подтверждён** (Shi/Solihin/Yeoh, AEI 68, BuildThemis — ScienceDirect abstract). **2026.103676** при поиске 2026-08-04 **не индексируется** как статья с этим номером (подозрительный «близнец»). В `docs.md` стоит Zentgraf `…2026.104735` (отдельный DOI; fetch Elsevier 406 в этой среде — оставить в группе «неподтверждённые online в этой сессии», ранее errata помечала VERIFIED 2026-08-03). `docs/AeroBIM.pdf` — бинарный/без извлечённых DOI-строк в этой проверке. |
| **Почему риск на защите** | Одна вымышленная ссылка в ClickUp/слайде обнуляет доверие ко всему корпусу; смешанный корпус хуже полностью фейкового. |
| **Минимальное исправление** | Полный inventory внешних зеркал (ClickUp Task 07 `research.md`, презентация): три колонки confirmed / unverified / false. Удалить или пометить `2026.103676`, если встречается. Добавить в git SSOT research index (чтобы не жить только в ClickUp). |
| **Что нельзя делать** | «Чинить» DOI угадыванием года; оставлять неподтверждённые ссылки в публичном паке без пометки. |

#### Локальная библиография `docs/docs.md` (частичный аудит)

| Ссылка | Статус этой сессии |
|---|---|
| AECV-Bench arXiv:2601.04819 | **подтверждена** (arXiv abstract) |
| BRAVO mediaTUM 1854636 | **подтверждена** (mediaTUM + PDF) |
| AEC-Bench arXiv:2603.29199 | **подтверждена** внешне; **отсутствует** в списке `docs.md` L409–420 (есть в Kimi alignment) |
| MechVQA arXiv:2605.30794 | **подтверждена** внешне (arXiv + ICML poster); **отсутствует** в `docs.md` |
| Arch-Eval (Wu et al., Sci Rep 2025) | **подтверждена** внешне; **отсутствует** в корпусе research |
| IFC-Bench-v1 (Hellin et al., EC3 2025) | **подтверждена** внешне (mediaTUM/HF); **отсутствует** в корпусе |
| Perov ICDM DOI 10.1109/icdmw69685.2025.00203 | **неподтверждена online** (HTTP 406 в этой сессии); есть в errata |
| Madireddy electronics14112146 | **неподтверждена online** (HTTP 406); цитируется в literature refresh |
| Zentgraf aei.2026.104735 | **неподтверждена online** в этой сессии (timeout/406); errata: VERIFIED 2026-08-03 |

---

### A5 — Мультимодальность: приём ≠ распознавание

| Поле | Содержание |
|---|---|
| **Критичность** | **средняя** (частично уже закрыто в grant-доках) |
| **Что заявлено (осторожно)** | Grant: «Vision: endpoint **accepts** Base64 images (HTTP 200); **recognition quality NOT_MEASURED**» — `docs/architecture/YANDEX_AI_STUDIO_GRANT_KT2_2026_08_03.md` L61; claim_boundary того же файла L6. |
| **Что заявлено (риск)** | Claim boundary «Verified»: «**Multimodal** project-package analysis» — `docs/pilot-claim-boundary-2026.md` L34. Жюри-текст опирается на AECV/BRAVO для «распознать ≠ решить» (`docs/docs.md` L295) — это хорошо, но слово *Multimodal* в verified-таблице легко читается как доказанная vision-способность. |
| **Чем опровергается** | AECV-Bench: OCR до ~0.95, symbol counting часто 0.40–0.55 — «принимает картинку» ≠ «понимает чертёж». |
| **Почему риск на защите** | Один неточный термин в verified-таблице перевешивает осторожные grant footnotes. |
| **Минимальное исправление** | Переименовать verified-строку: «Multi-**source** package analysis (IFC+PDF+drawings)» / «Vision endpoint accepts images; recognition NOT_MEASURED». |
| **Что нельзя делать** | «Мультимодальность подтверждена» / «VLM читает штамп» без crop-with-known-content артефакта. |

---

### A6 — Cross-sheet / project coordination не сопоставлены с бенчмарком

| Поле | Содержание |
|---|---|
| **Критичность** | **средняя** |
| **Что заявлено** | Cross-doc в матрице как часть deterministic Shared-gate / calculation match (`docs/capability-claim-matrix-2026.md` L27, L61). Отдельной строки «cross-sheet reasoning» / «project-level coordination» в терминах AEC-Bench **нет**. Измерение отдельно от внутрилистовых проверок **не** описано. |
| **Чем опровергается** | AEC-Bench taxonomy: drawing understanding, **cross-sheet reasoning**, project-level coordination — самостоятельные семейства задач. |
| **Почему риск на защите** | «У нас есть междокументная сверка» без сопоставимой метрики выглядит как category error. |
| **Минимальное исправление** | Строка в capability matrix: `cross_document_consistency` = fixture-verified / customer NOT_MEASURED; явно ≠ AEC-Bench agentic cross-sheet score. Опционально: 1–2 synthetic cross-sheet fixtures с отдельным отчётом. |
| **Что нельзя делать** | Заявлять «закрыли AEC-Bench cross-sheet» прогоном IDS/cross-doc на одном IFC. |

---

### A7 — «Обвязка важнее модели» — упущенная формулировка

| Поле | Содержание |
|---|---|
| **Критичность** | **низкая** |
| **Что заявлено** | Архитектура: deterministic core + advisory model (`docs/docs.md` L291–297; ADR-001). AEC-Bench цитируется лишь для калибровки ожиданий agentic-фронта (`KIMI_K3_MIK_TECHLAB_ALIGNMENT` L24), **не** как внешнее подтверждение выбора harness. |
| **Чем опровергается** | AEC-Bench (arXiv abstract / Nomic): domain tools & harness techniques **равномерно** улучшают разные base models. |
| **Почему риск на защите** | Сильную сторону придётся импровизировать устно; письменно она не «прибита» к внешнему результату. |
| **Минимальное исправление** | 3–5 предложений в `docs.md` §10 / literature refresh: «наш split verdict/advisory совпадает с выводом AEC-Bench о роли harness; это literature alignment, не наш score». |
| **Что нельзя делать** | Приписывать себе числа AEC-Bench baselines. |

---

### A8 — «Нет цифры сильнее чужой 90%» для не-инженера

| Поле | Содержание |
|---|---|
| **Критичность** | **средняя** |
| **Что заявлено** | FAQ: «Где >90%?» → нужны клиентский корпус, adjudicators, CI (`docs/samolet.md` L545–547). Claims Lock запрещает >90% без evidence. Нет короткого **не-инженерного** абзаца вида: «конкурент без методики = несопоставимо; мы публикуем только воспроизводимое; open-bench baseline ≠ customer KPI». |
| **Чем опровергается** | Практика жюри / закупок: при отсутствии методики чужие «90% / 15 пилотов» выигрывают нарратив, если ваш «нет цифры» звучит как уклонение (см. A1). |
| **Почему риск на защите** | Аргумент «только в голове команды» не сработает под вопросом организатора. |
| **Минимальное исправление** | Один слайд / § в `docs.md` или TECHLAB readiness: три уровня чисел (1) open-bench baseline, (2) fixture regression, (3) customer adjudicated — и почему (3) ещё NO_GO, а (1) можно показать честно. Без имён конкурентов. |
| **Что нельзя делать** | Критиковать соседей по потоку по именам в артефактах для организатора; выдумывать свои %. |

---

### A9 (новая) — Корпус литературы неполон относительно доступных бенчмарков

| Поле | Содержание |
|---|---|
| **Критичность** | **средняя** |
| **Что заявлено** | `docs.md` §бенчмарки (L409–420) + literature refresh 2026-07-28 — без MechVQA, Arch-Eval, IFC-Bench; AEC-Bench не в жюри-библиографии. |
| **Чем опровергается** | Все четыре работы существуют и релевантны (проверено 2026-08-04). |
| **Минимальное исправление** | Дописать в research SSOT + `docs.md` с пометкой «literature only». |
| **Что нельзя делать** | Добавлять ссылки без проверки DOI/arXiv. |

---

## 1. Что можно закрыть до 20 августа (окно КТ#2)

| Действие | Трудозатраты (оценка) | Закрывает |
|---|---|---|
| Decision record: customer KPI ≠ open-bench baseline | 0.5 дн | A1, A8 |
| Smoke AECV counting **или** IFC-Bench retrieval через свой контур → `docs/evidence/*-open-bench-*.json` + claim_level | 2–4 дн | A1 |
| Слайд «видит ≠ проверяет» с AECV-Bench citation | 0.5 дн | A1, A5, A7 |
| Переименовать «Multimodal» в claim boundary | 0.5 ч | A5 |
| WP-07: оси Recognition/Reasoning/Judging + LLM-judge triage note | 1 дн | A2, A3 |
| Inventory ClickUp/`research.md`/deck DOIs; purge twin 2026.103676 | 1–2 дн | A4 |
| Дописать MechVQA / AEC-Bench / Arch-Eval / IFC-Bench в `docs.md` | 0.5 дн | A9, A7 |
| Матрица: строка cross_document vs AEC-Bench cross-sheet | 0.5 дн | A6 |
| Не-инженерный абзац «три уровня чисел» | 0.5 дн | A8 |

**Итого порядка 6–10 человеко-дней** без закрытия Checkpoint.

## 2. Что требует данных заказчика (остаётся открытым честно)

- RT-001 publishable precision / «>90%»
- RT-002 approved norm pack
- RT-003 customer MEP federated evidence
- Customer SLA ≤30 мин как product claim
- κ/α на реальном корпусе Самолёта

Open-bench числа **не** заменяют этот список.

## 3. Что не удалось проверить и почему

| Объект | Почему |
|---|---|
| ClickUp `research.md` и слайды вне git | Нет файла в репозитории; errata указывает на внешние зеркала |
| Пара DOI `…2025.103676` / `…2026.103676` **внутри** git | Не найдена; близнец 2026.103676 не подтверждён индексом, но исходник пары вне репо |
| Полный текст `docs/AeroBIM.pdf` | DOI-строки не извлеклись из бинарника в этой среде |
| Elsevier DOI (Zentgraf, Madireddy, Perov IEEE) | HTTP 406 / timeout к publisher в этой сессии |
| Фактический прогон AEC-Bench/AECV на инфраструктуре AeroBIM | AECV **object counting live** на Yandex Qwen — артефакт есть (`aecv-bench-eval-latest.json`); AEC-Bench agent + AECV QA — по-прежнему без прогона |
| Имена/методики конкурентов потока | Сознательно не разбирались (ограничение промпта §5) |

---

## Вердикт для жюри (одно предложение)

Документация AeroBIM **честна по RT-001 customer KPI**, но **устарела как линия защиты «нет никаких цифр»**: открытые AEC-бенчмарки уже в литературе проекта, не в evidence; до 20 августа дешёвый путь — decision record + один open-bench артефакт + чистка внешних ссылок, без движения Checkpoint.
