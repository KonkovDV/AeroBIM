<!-- claims-lint: allow-file reason="TechLab 14.08 action log; forbidden phrases as non-claims; NO_GO" -->
---
title: "Действия после обсуждения 14.08.2026"
date: "2026-08-14"
claim_boundary: "Action log. Checkpoint NO_GO. Not customer accuracy. Not DWG-ready. Not MEP delivered. Not CDE-ready. Not claimed production-ready."
---

# Действия 14.08 — шесть пунктов обсуждения

Checkpoint остаётся **NO_GO**. Журнал работ по списку трекера из командного чата (~15:26). Протокол утренней встречи 08:00 в git **нет**.

| # | Пункт | Кто | Статус 14.08 вечер | Артефакт |
|---|---|---|---|---|
| 1 | КТ#2 к 20.08 — доработать продукт | ИИ + человек (видео/ЛК) | 15.08: local pytest HEAD `005b7bc` **2259 passed / 12 skipped / 0 failed** (Windows 3.12.10 + ifcclash extra). Не заменяет CI pin 2167. Overlay HTML: `#kt2-overlay` + Not CDE import. UI: Checkpoint NO_GO. Репетиция = live CLI, не wall-guid. | [`../evidence/runtime-baseline-wave-a-windows-2026-08-15.md`](../evidence/runtime-baseline-wave-a-windows-2026-08-15.md) · [`../demo/KT2_DEMO_REHEARSAL_2026_08_12.md`](../demo/KT2_DEMO_REHEARSAL_2026_08_12.md) |
| 2 | Сводная таблица трёх релизов IFC | ИИ | **15.08 12:07 МСК:** n=20 CPython 3.12.10. Findings 5 / 4 / 6; `passed=false`. IFC4X3: `clash=failed, ids=failed` (BSI 0101). Clash failed = IfcClash `AssertionError` на крошечной стене, не silent pass. p50 ≈ 26–34 мс — **не** SLA. Tracker-paste в том же файле. | [`../evidence/ifc-release-matrix-2026-08.md`](../evidence/ifc-release-matrix-2026-08.md) |
| 3 | Датасеты: поиск, прогон скачанного, фикс ошибок | ИИ | **15.08:** `run_open_corpora_profiles --mode smoke` → `pins_ok=true` (7 regression). Harbor 160 не гнать до 17.08. RT-001/002/003 OPEN. | [`../datasets/OPEN_SOURCE_SEARCH_2026_08_14.md`](../datasets/OPEN_SOURCE_SEARCH_2026_08_14.md) · [`../datasets/RT001_002_003_WITHOUT_SAMOLET_2026_08_14.md`](../datasets/RT001_002_003_WITHOUT_SAMOLET_2026_08_14.md) |
| 4 | Вопросы + демо ядра у; созвон с Михаилом | Человек проводит; ИИ готовит пакет | Пакет готов. 12.08 слот а по календарю был; **минут в git нет**. **15.08:** вопросы 6–7 (Messick/Kane IUA; Solihin class 4). Второй слот а: ждём AM. | [`../demo/CONSULTATIONS_2026_08_14.md`](../demo/CONSULTATIONS_2026_08_14.md) |
| 5 | Коммерческий трек: KPI = назначенные демо 3–5 | Подрядчик / владелец | Бриф переформулирован. Холодный канал 50 касаний / 0 ответов — не продолжать тем же KPI. В git демо = 0. **15.08:** Funding + Academic Red Team — не просить раунд/SAFE; речь MIT+услуги. | [`../gtm/COMMERCIAL_AND_OPEN_CORE_2026_08_14.md`](../gtm/COMMERCIAL_AND_OPEN_CORE_2026_08_14.md) · [`../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md`](../quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md) · [`../quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md`](../quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md) |
| 6 | Монетизация при открытом коде — на следующей встрече | Команда | До КТ#2 речь **A (MIT + услуги)**. B не продавать как SKU. LICENSE не меняем | тот же файл, §2–3 |

## Проблемы поля, которые код не снимает

| Проблема | Факт из контура программы | Что делаем в репо | Что не делать |
|---|---|---|---|
| Корпус заказчика | Запрос приложений ТЗ 05.08; ответа нет | RT-001 открыт; публичные прокси ≠ CLOSED | Публиковать open-corpus F1 как точность продукта |
| Профиль приёмки «Самолёта» | IDS МОГЭ ≠ Samolet | RT-002 открыт | Alias IFC4X3 → IFC4 |
| Federated MEP | AABB ≠ clash | RT-003 открыт | MEP delivered |
| DWG в ТЗ | Трекер 07.08: требование остаётся | FAILED + мемо TZ-mandatory | «Вне скоупа молча» / DWG-ready |
| Второй заказчик Техлаба | AM 05.08: одна задача, один заказчик | Коммерческий бриф | Письма А101/Галс *как* второй заказчик программы |
| Холодные касания | 50 / 0 | KPI = слот в календаре | Новые 50 писем тем же текстом |
| Юрлицо | 14.08: нет | Человек / Harbor 17.08 | Обещать договор от имени юрлица |
| Оверинжиниринг | Ментор 08.08 | Freeze портов **снят оператором 14.08 вечер**; extra-method на существующих адаптерах | Новые DI/ports только atomic; не ради объёма |

## Не закрывается кодом до 20.08

RT-001 / RT-002 / RT-003, видео 3 мин (19.08, человек), загрузка в ЛК, интеграция с Tangl/10D, native DWG, ответ «Самолёта» по приложениям, тёплые контакты трекера, слот 2-й консультации а.
