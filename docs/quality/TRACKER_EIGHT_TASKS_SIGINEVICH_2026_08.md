<!-- claims-lint: allow-file reason="Tracker eight-task SSOT; OIDC 501; volume≠accuracy; NO_GO" -->
---
title: "Eight tracker tasks (Siginevich 29.08) — git SSOT for KT#3"
date: "2026-08-30"
last_updated: "2026-08-31"
status: active
version: "1.1.6"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Operational plan for eight tracker tasks. SIG-01 report phrase:
  объём находок на канале получен. Not product accuracy. Not pack
  processed. Not 43 GB processed. Not production SSO. SPF stays 256 MiB.
  Checkpoint NO_GO.
---

# Восемь задач трекера (29.08.2026)

Машина: `python -c "from aerobim.domain.tracker_eight_tasks import tracker_eight_snapshot"`.

Это **не** шесть задач от 14.08 ([карточка](../demo/KT3_TRACKER_DMITRY_2026_08.md)). Окно КТ#3: **3–21.09**. Фича-фриз внешнего контура: **18.09**. Задача Самолёта в приложении 4 — **№6**; отборочная комиссия в приказе — **№7**. Не произносить «07» как номер Положения.

Checkpoint **`NO_GO`**. Пакет канала **не** в git. Локатор share **не** публикуется.

**SIG-01 — граница заявления.** Формулировка для отчёта: «объём находок на канале получен». Сырой счётчик записей машины — не точность, не «пакет обработан», не дефекты заказчика. Разложение классов, `unrestricted_eq_sample`, overlap unsigned-пакетов и два фикса движка (`target_ref=ALL`, GUID≠Name): [`FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md`](FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md). Триаж канала: [`SIG01_CHANNEL_TRIAGE_2026_08.md`](SIG01_CHANNEL_TRIAGE_2026_08.md).

Локально 31.08 (не закрывает задачи у владельца): максимум на unpack-дереве — [`CHANNEL_SAMOLET_MAX_PASS_2026_08.md`](CHANNEL_SAMOLET_MAX_PASS_2026_08.md) · триаж семейств [`CHANNEL_PACK_TRIAGE_2026_08.md`](CHANNEL_PACK_TRIAGE_2026_08.md) · пин [`../evidence/pack-family-facts-2026-08.md`](../evidence/pack-family-facts-2026-08.md). Хэшированный TSV — только `.local/`. `publishable_finding_count=0`. Несжатые байт-итоги в git нет.

Локально 30.08 вечер (не закрывает SIG-02 у владельца): recensus wrapper **2552** + unpack **6408** (утро 2618/6467 включало оболочки архивов; исходники удалены после member-coverage). Глубина носителей: [`../evidence/deep-study-carrier-facts-2026-08.md`](../evidence/deep-study-carrier-facts-2026-08.md). Это не обработка пакета.

## Что git уже умеет vs что должен сделать владелец

| ID | Задача трекера | В git | Владелец | Не говорить |
|---|---|---|---|---|
| SIG-01 | Прогон IFC/PDF, число находок + типы | Форма таблицы: `run_finding_volume --findings-lite-dir`; классы [`FINDING_VOLUME_CLAIM_BOUNDARY_2026_08`](FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md); триаж [`SIG01_CHANNEL_TRIAGE_2026_08`](SIG01_CHANNEL_TRIAGE_2026_08.md); максимум на копии [`CHANNEL_SAMOLET_MAX_PASS_2026_08`](CHANNEL_SAMOLET_MAX_PASS_2026_08.md) | Прогон на канале после OA-9; тоталы в `.local/` | Находки = точность продукта; «пакет обработан»; список дефектов заказчика |
| SIG-02 | Инвентаризация 43 ГБ | `pack_probe` + `pack_archive_overlap` + пины census / deep-study / [`pack-family-facts`](../evidence/pack-family-facts-2026-08.md); hashed TSV в `.local/` | Реестр в чат до 02.09 (после OA-9); не коммитить имена | **нельзя** говорить, что пакет обработан. «43 ГБ» — формулировка задачи, не замер |
| SIG-03 | Внешний контур, две роли | `expert`/`user` в API; `GET /v1/auth/bff` **501** | Production IdP; фриз 18.09 | Lab cookie = SSO |
| SIG-04 | Два критерия точности + классификатор | Каталог ≥20 классов; `customer_confirmed_patterns=0`; наблюдения носителей в каталоге (не confirmation) | Два разметчика; сверка с их набором | Смешать F1 фикстур с объёмом канала |
| SIG-05 | Пакет вопросов | Черновик [`../partners/SAMOLET_QUESTION_PACK_KT3_2026_08.md`](../partners/SAMOLET_QUESTION_PACK_KT3_2026_08.md) | Отправить 31.08 через организаторов | «заполните TBD с нуля» |
| SIG-06 | ЛИРА к КТ#3 | Четыре проверки; shortlist 6 docx / 46 xlsx (не MATCH) | Каноничная записка | «конструкции пересчитаны»; токен = MATCH |
| SIG-07 | RVT/NWD + CV | [одностраничник](../demo/KT3_RVT_NWD_CV_ONEPAGER_2026_08.md) | Юрлицо / закупка SDK | Sustaining = BimRv; CADSoftTools 1660 $ |
| SIG-08 | РУТ (МИИТ) | OA-10 | Письмо до 01.09 | Учебный комплект закрывает RT-001 |

## Правки к плану Team Space (GigaChat без git)

1. **Не** «поднять SPF 256 МиБ до 1,5 ГБ». SPF in-memory остаётся 256 МиБ. До 1,5 ГБ — RocksDB. WASM 256 МиБ.
2. CADSoftTools на 30.08 — **от 765 USD**, не 1 660.
3. RT-002 **split**: 002a CLOSED (городские IDS + `pack_hash`); 002b OPEN (нет подписи Самолёта). Не «норм нет».
4. Задача 3 упирается в **OIDC BFF 501**, не в отсутствие HTML. Откат к 21.09: API + ссылки на отчёты.
5. «Неэффективное пространство»: в git **`advisory_unsigned`** — inventory IfcSpace, пороги не подписаны, не delivered. Не оставлять строку без позиции.
6. Fixture clash n=6 / P=1,0 **не показывать** (Wilson lower ≈ 0,61).
7. Спринт C в копии Team Space **повреждён** (склейка текста). Этот файл — SSOT.

## Четыре спринта (окно 03–21.09; финал 29–30.09)

Трек-встречи пятницы 08:00 (04.09, 11.09, 18.09, 25.09). После каждой — текст в чат трекера. Спринт C из копии Team Space **не** использовать: там склейка строк.

| Спринт | Даты | В git / владелец |
|---|---|---|
| A | 31.08–04.09 | SIG-02 реестр **вне git** до 02.09; SIG-05 отправка 31.08; SIG-06 вердикт ЛИРА к 04.09; SIG-08 письмо РУТ 01.09; SIG-03 старт (роли уже в API, BFF остаётся 501) |
| B | 05.09–11.09 | SIG-01 объём находок (не %) на IFC/PDF; SIG-07 одностраничник к 08.09; SIG-04 каталог ≥20, класс «пространство» = `advisory_unsigned` |
| C | 12.09–21.09 | SIG-03 фича-фриз **18.09** (не формальность); откат = API + ссылки на отчёты; SIG-04 протокол измерения без смешения F1 фикстур; сдача 19–21.09 |
| D | 22.09–30.09 | Репетиция вопросов, не слайдов; `run_demo_vertical_slice` и `run_demo_ifc_acceptance_gate` с чистой машины |

Последовательность: 2 → 1 → 4. Задача 3 параллельна с дня 1. Задачи 5–8 не конкурируют с кодом. **Не** поднимать `AEROBIM_MAX_IFC_BYTES` (SPF 256 МиБ); 1,5 ГБ — ingest + RocksDB.

## Блокер №1

До письменного режима данных (OA-9, ответ нужен к 03.09) производные канала в git не кладём. Инвентарь и прогон — локально, агрегат без имён — только после ответа юрслужбы.

## Сдача 19–21.09 (честный состав)

Реестр вне git · объём находок (не %) · классификатор ≥20 · стенд двух ролей **если** BFF не 501 · записка ЛИРА · одностраничник RVT/NWD · журнал писем. Если эталона нет — **NO_GO** с работающим ядром, не перекрашивать.

Связанные: [`KT3_WINDOW_CRITICAL_PATH_2026_09.md`](KT3_WINDOW_CRITICAL_PATH_2026_09.md) · [`OWNER_ACTIONS_2026_09.md`](../OWNER_ACTIONS_2026_09.md).
