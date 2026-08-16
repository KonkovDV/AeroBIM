---
title: "Red Team Hyper-Deep synthesis — five-round engineering culture score"
status: active
version: "1.0.0"
last_updated: "2026-08-16"
claim_boundary: >-
  Auditor opinion after HD rounds 1–5. Scores are culture/process grades, not
  product accuracy, SLA, MEP delivered, CDE-ready, or Checkpoint GO.
  Checkpoint stays NO_GO (RT-001 / RT-002 / RT-003 OPEN).
audited_head: "working tree 2026-08-16 after HD1–HD5 remediations"
auditor: "ZCode autonomous triage, synthesis (solo)"
---

# Итоговая оценка AeroBIM (синтез HD1–HD5)

**Общий вердикт аудитора: 8/10 по инженерной культуре** — не оценка точности продукта и не коммерческий GO. Балл снимается не за то, что сделано плохо, а за то, что ещё не проверено реальной эксплуатацией. Checkpoint **`NO_GO`**.

Раунд 5 добавил **0 MEDIUM**: SQL параметризован, VLM-egress/HTML/PDF периметр OK. Residual: полный `ifc_open_shell_validator.py`, VLM-пайплайны целиком, `App.tsx`, ~290 тестов.

## 1. Измерения (снимок пяти раундов)

53 находки HD-серии, **ноль CRITICAL / ноль HIGH**. Оценки — мнение аудитора по культуре кода, не claim_level продукта.

| Измерение | Оценка | Основание (аудит) | Дельта remediation (working tree) |
|---|---|---|---|
| Архитектура и чистота кода | 9/10 | Hexagonal-дисциплина, DI, порты/адаптеры | без смены |
| Честность и методология | 9.5/10 | Verdict-путь перечислен; Wilson n=111; errata DOI | регресс n=111; DOI-twin lint |
| Безопасность | 8/10 | SSRF-pin, path_jail, XML/ZIP caps, OIDC; остатки задокументированы | HD1–HD3 perimeter + HD5 SQL/VLM/HTML/PDF confirm |
| Тестирование | 8.5/10 | Baseline `tests_collected=2271`; живые mutation tests | `tests_unaccounted=93` объяснён в baseline |
| Конкурентность и надёжность | 6/10 | Слабейшее место: DI, JWKS, quota-race, stale-локи | часть закрыта (RLock, kid-refetch, reserve-ahead); класс остаётся |
| Ресурсная эффективность | 5.5/10 (снимок) | Вечные кэши на фикстурах не видны | IFC LRU(8); TokenVault LRU(4096); in-process limiter всё ещё без жёсткого cap на все пути |
| Документация: содержание | 8/10 | Богатая и честная | без смены |
| Документация: управляемость | 6/10 (снимок) | Drift чисел; guard казался README-only | claims-forbidden scan: README + README.ru + TIER0 + ENGINEERING; DOI-twin lint. Поверхность документов по-прежнему широкая |

## 2. Три факта (с оговорками)

1. **Честность проверяема.** Центральные заявления («advisory не пишет ERROR», «n=111 воспроизводится», «fabricated DOI удалён вне errata») выдержали перечисление писателей, численный прогон и библиографический аудит. Это оценка *заявлений кода о себе*, не точности на корпусе заказчика.

2. **Реальная уязвимость — незаявленное.** Серьёзные находки — память, гонки, дрейф форматов внешних движков — fixture-режим их не показывает. Часть уже закрыта (IDS missing `status`, clash malformed → failed, LRU). Класс «болезни первого продакшена» не исчез: процессный рост, мульти-реплика, квоты после crash (HD2-UP-02 OPEN).

3. **Риск масштаба процесса.** 100+ CLI, десятки honesty-доков, CI-гейты. Drift SSOT — симптом. Remediation сузил *один* канал drift (claims scan + DOI twins); не заменяет второго инженера и не сокращает поверхность сама по себе.

## 3. Самолёту / КТ#2

Проект сам держит **NO_GO**, аудит это подтверждает **по evidentiary причине**, не потому что «код сырой»:

| Блокер | Статус | Не путать с |
|---|---|---|
| RT-001 | OPEN | нет корпуса ПД РФ + экспертизы; open benches ≠ этот корпус |
| RT-002 | OPEN | нет подписанного профиля приёмки; public MOEXP IDS ≠ Samolet |
| RT-003 | OPEN | clash NOT_VERIFIED; не MEP delivered |

Инженерная готовность к показу КТ#2 (IFC Acceptance Gate, wedge freeze) **не равна** коммерческому GO. Аудитор не поднимает Checkpoint.

## 4. Ограничения оценки

Аудит соло, без суб-агентов. VLM-пайплайны, postgres SQL-слой и ~290 тест-файлов — grep-уровень, не построчное чтение. Оценка security/reliability может сдвинуться на ±1 после пятого прохода. Ничего из прочитанного не указывает на скрытый fail-open вердикта; паттерны fail-closed равномерны по дереву *на конструктивных путях*.

## 5. Одна фраза

Исключительно дисциплинированный, академически честный, инженерно зрелый код, которому до продакшена не хватает не таланта, а шрамов — пределов ресурсов, конкурентных гонок и встречи с реальными данными заказчика; часть пределов уже поставлена в working tree, Checkpoint всё равно **NO_GO**.
