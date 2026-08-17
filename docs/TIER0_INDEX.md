---
title: "AeroBIM Tier-0 — карта для жюри Техлаба"
status: active
version: "4.5.9"
last_updated: "2026-08-17"
tags: [aerobim, documentation, tier-0, techlab]
claim_boundary: "Jury pack only. Checkpoint NO_GO until RT-001/002/003. Eng readiness ≠ customer GO."
---

# Tier-0 — карта для жюри Техлаба

**`NO_GO`** — [реестр блокеров](../audit/reports/CRITICAL_BLOCKERS.md) · [CLAIMS_LOCK](../audit/reports/CLAIMS_LOCK_2026_07_17.md) · [граница заявлений](pilot-claim-boundary-2026.md) · [ADR-001](architecture/ADR-001-verdict-ownership-2026.md)

**Объект КТ#2.** Речь и пакет = текущий `main`. Цифры тестов = CI pin `acac02bd` ([`docs/evidence/runtime-baseline-latest.json`](evidence/runtime-baseline-latest.json), `attested_by=ci`). IUA freeze `f9389bf` (не HEAD). Прочие SHA на поверхностях — исторические. После гигиены pin может отставать (N-43); локальный pytest не публикуем.

**Kane IUA (30 s).** Сегодня можно: учебный показ, IDS с отказом при пропуске (BSI 0101), открытый бенч **27/1026**, протокол. Запрещено: точность на комплекте заказчика, ТЗ >90%, SLA заказчика, MEP delivered, импорт в СОД, Checkpoint GO. Журнал: [Interpretation/Use](quality/INTERPRETATION_USE_LEDGER_2026_08.md). IUA freeze `f9389bf` — позднейшая гигиена не переоткрывает валидность.

**Six desks (17.08).** Техлаб / МИК / трекер / ИТ-ментор / наука / венчур: [красная команда жюри × МИК](quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md) § Current pass. Форма 5/5 ≠ Checkpoint GO.

| Документ | Роль |
|---------|------|
| [Техобоснование для жюри](docs.md) | `docs.md` |
| [Инженерный статус](ENGINEERING_STATUS_2026_08.md) | Готовность ≠ Checkpoint GO |
| [Враждебный QA](demo/) | Скрипты привязаны к SSOT |
| [Видео к КТ#2](demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md) | Не записываем и не прилагаем; показ = живой CLI |
| [Карточка речи / FAQ](demo/KT2_JURY_FAQ_2026_08_12.md) | Формула стадии |
| [Тайминг на фикстуре](demo/KT2_FIXTURE_TIMING_2026_08_16.md) | Порядок величины — не SLA заказчика |
| [Сравнение решений Задачи 07](demo/KT2_TASK07_COMPARISON_2026_08.md) | Пять решений; цифры конкурентов = их claims |
| [Контракт intake 10D](demo/KT2_10D_INTAKE_CONTRACT_2026_08.md) | Предлагаемые поля; не коннектор 10D |
| [Строка корпуса](demo/KT2_CORPUS_SSOT_2026_08.md) | Заморожена до КТ#2 |
| [Запрос к Самолёту](partners/_08_15.md) | Комплект / профиль / разметчики / СОД |
| [Заморозка клина](partners/_2026_08_16.md) | Продукт = IFC Acceptance Gate |
| [Профиль приёмки v0.1](partners/SAMOLET_ACCEPTANCE_PROFILE_V0_1_2026_08_15.md) | RT-002 OPEN |
| [Протокол качества](partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md) | Метод измерения |
| [Готовность Задачи 07](partners/TECHLAB_TASK_07_READINESS_2026.md) | Форма / готовность |
| [Красная команда жюри / МИК](quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md) | Стадия = доработка |
| [Академическая честность](quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md) | Messick / Kane |
| [Разбор литературы](quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md) | Август 2026 × IUA (Harbor NOT_RUN) |
| [Атаки diligence](quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md) | Враждебные вопросы венчура |
| [Журнал Interpretation/Use](quality/INTERPRETATION_USE_LEDGER_2026_08.md) | Что цифры имеют право значить |
| [Принятые риски](quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md) | На КТ#2 |
| [Заявление о данных](evidence/DATA_STATEMENT_2026_08.md) | Что есть; открытые бенчи ≠ RT-001 |
| [Индекс доказательств](evidence/README.md) | Цитируемые фикстуры |
| [Стратегия Самолёта](samolet.md) | Контекст 10D |
| [ТЗ заказчика v2.0](tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) | ТЗ Задачи 07 |
| [Граница заявлений](pilot-claim-boundary-2026.md) | Проверено vs план |
| [ADR-001 владение вердиктом](architecture/ADR-001-verdict-ownership-2026.md) | Кто пишет `summary.passed` |
| [Целевая архитектура](architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) | Гибридный контур |
| [Матрица возможностей](capability-claim-matrix-2026.md) | Можно vs нельзя |
| [Карточка защиты QA](qa-defense-2026.md) | Ответы на 20–30 с |
| [README](../README.md) · [README (RU)](../README.ru.md) | Продуктовый README |

Операторские runbook, сессионные аудиты и коммерческие ПДн лежат в `.local/` — не на GitHub.

## Submission pack (форма приёма решения)

Пять полей формы разложены по подпапкам: [пакет подачи КТ#2](../submission/README.md). Построчное покрытие ТЗ Задачи 07: [карта требований ТЗ](../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md).

## Pre-flight (KT#2, 20.08)

Intake-form completeness = **5/5 fields**: в дереве есть сдаваемый файл по каждому полю формы (репозиторий, документация, презентация, прототип, доп. материалы). Это ≠ Checkpoint GO, не стадия 3 МИК, не измеренный эффект. Checkpoint **NO_GO**. Правки — код и тесты в этом дереве; загрузка в ЛК — человек ([итоговый вердикт красной команды](quality/RED_TEAM_FINAL_VERDICT_2026_08_16.md) §4). Ролик 2–3 мин **не записываем и не прилагаем**.

| # | Требование карточки КТ#2 | Что лежит в дереве | Гейт |
|---|---|---|---|
| 1 | Видео 2–3 мин | Не прилагаем. Показ: `run_demo_ifc_acceptance_gate` ([уведомление](demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md)) | mp4 нет; снимок HTML запрещён |
| 2 | Подход к решению | [техобоснование](docs.md) + [готовность](partners/TECHLAB_TASK_07_READINESS_2026.md) + [клин](partners/_2026_08_16.md) | детерминированный гейт; подсказка ≠ вердикт |
| 3 | Сравнение решений | [сравнение Задачи 07](demo/KT2_TASK07_COMPARISON_2026_08.md) | цифры конкурентов = их claims |
| 4 | Харденинг | [враждебный QA](demo/) §2 | формула §0; [итоговый вердикт](quality/RED_TEAM_FINAL_VERDICT_2026_08_16.md) §1 |
| 5 | Версия для проверки | [инженерный статус](ENGINEERING_STATUS_2026_08.md) → `run_demo_ifc_acceptance_gate` | отказ при пропуске; хеш воспроизводимости |

Люди: загрузка в ЛК 19–20.08. Видео не записываем. Не код.
