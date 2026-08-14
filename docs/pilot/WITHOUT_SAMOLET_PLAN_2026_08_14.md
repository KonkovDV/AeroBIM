<!-- claims-lint: allow-file reason="Plan of work that does not need Samolet models; NO_GO explicit" -->
---
title: "Что закрываем без «Самолёта» — план и граница"
date: "2026-08-14"
claim_boundary: "Plan only. Checkpoint NO_GO. No new ports/DI. Not customer accuracy. Not moscow_agr complete profile."
---

# Без моделей «Самолёта»

Их корпус и подписанный профиль приёмки нам не нужны, чтобы закрыть ниже. Checkpoint остаётся **NO_GO**.

## Делаем сейчас (код + тест + хеш)

| # | Что | Зачем к 20.08 | Не утверждаем |
| --- | --- | --- | --- |
| 1 | Устаревшая норма: ГОСТ Р 21.101-2020 → 2026 | Демо: ведомственный документ ссылается на заменённый ГОСТ | Не «мы заменили экспертизу» |
| 2 | Обменные проверки ЦИМ АГР класса 1: схема IFC4, ReferenceView, запрет Proxy, 5 полей имени, 500 МБ | Детерминированно, без ML, без нового порта | Не полный `moscow_agr` (нет УКЭП, СК, МССК, ведомости XML) |
| 3 | Стресс открытых IFC: `samples/ifc` 15/15 + GNI 224 header / 223 IfcOpenShell (1 oversize) | Масштаб без NDA | Не точность продукта; не 223 «как Самолёта» |
| 4 | Протокол приёмки №7: ложный пропуск первым, единица = проект | Линейка для всех финалистов | Не точность продукта |
| 5 | Перегон IFC-матрицы после fail-closed | IFC4X3 fixture теперь честно шумит | Не SLA продукта |

## Поиск 14.08 вечер — публичные замены трёх блокеров

Полная таблица: [`../datasets/RT001_002_003_WITHOUT_SAMOLET_2026_08_14.md`](../datasets/RT001_002_003_WITHOUT_SAMOLET_2026_08_14.md).

| ID | Интернет вместо «Самолёта» | CLOSED? |
| --- | --- | --- |
| RT-001 | ЕГРЗ = метаданные (ПП 878 п. 23); IFC-Bench / AECV / GNI / синтетика Rail R3–R7 | **Нет** |
| RT-002 | IDS МОГЭ + текст АГР Москвы; IDS ПИК не скачивается | **Нет** |
| RT-003 | IFC-Bench федерация + IfcClash; G55 Solibri BCF — чужие клиентские данные, не вендорить | **Нет** |

Это не «мало искали». Эталон экспертизы и подписанный профиль юридически не лежат в открытом доступе.

## Не делаем без них (и не притворяемся)

- Цифра ложных пропусков на моделях Самолёта
- Подписанный профиль приёмки
- УКЭП / ИУЛ на их файлах
- AEC-Bench Harbor 160 (нет агента) — остаётся SKIPPED
- Скачивание 726 МБ GNI **в git** (локально уже в `.local/gni-bim`, gitignored)
- Новые порты / DI
- Видео 3 мин и ЛК — человек
- Второй заказчик программы Техлаб (А101 / Галс) как замена корпусу «Самолёта» — правило AM 05.08 запрещает
- Копирование G55 / Solibri BCF из чужого клиентского дерева

## Команды

```bash
cd backend
python -m aerobim.tools.export_stale_norm_scan
python -m aerobim.tools.run_agr_exchange_fixture
python -m aerobim.tools.run_open_ifc_stress --gni-root ../.local/gni-bim --open-model
python -m aerobim.tools.export_gni_anonymization_pin
python -m aerobim.tools.run_ifc_bench_smoke --version v2 --also-docs-evidence
python -m aerobim.tools.run_moexp_on_gni_sample
python -m aerobim.tools.export_ifc_release_matrix --iterations 5 --warmup-iterations 1
python -m aerobim.tools.run_tz_proxy_rehearsal
```

Академический максимум ТЗ без корпуса: [`../evidence/tz-proxy-rehearsal-2026-08.md`](../evidence/tz-proxy-rehearsal-2026-08.md). Три блокера остаются OPEN.
