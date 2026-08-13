<!-- claims-lint: allow-file reason="Tracker 14.08 one-pager; NO_GO and forbidden phrases as non-claims" -->
---
title: "Встреча с трекером 14.08.2026 08:00"
date: "2026-08-14"
claim_boundary: "Fixture demo. Checkpoint NO_GO. Not customer accuracy. Not DWG-ready. Not MEP delivered."
---

# Трекеру, 14 августа 08:00 — одна страница

## Главное за 30 секунд

Мы нашли тихий пропуск в своём же fail-closed и закрыли его **до** заказчика.

IfcTester считает `ifcVersion` метаданными (официальный кейс buildingSMART **0101**). IDS для IFC2X3 на модели IFC4 мог выглядеть чистым. Теперь `AEROBIM-IDS-IFC-VERSION` и SKIPPED в IDS-контуре = FAILED под pilot/production, `summary.passed` падает. Доказательство: [`docs/evidence/ids-fail-closed-2026-08.md`](../evidence/ids-fail-closed-2026-08.md) · `content_sha256=94db20d230714159177828f7d4f8fd25b152c9577c9f1a5da40056e1043b3162` (прогон, не цифра продукта).

Следствие для стека заказчика: официальные IDS МОГЭ имеют `ifcVersion="IFC4"`. Выгрузка Renga с `FILE_SCHEMA(('IFC4X3'))` **не** проходит молча — это fail-closed, не баг. Токен `IFC4X3` ≠ `IFC4X3_ADD2` тоже не алиасим.

Это не «ещё один слой архитектуры». Это единственная архитектурная правка, без которой заявление fail-closed было бы ложным.

## Что показать за 3 минуты

1. Команда: `cd backend && python -m aerobim.tools.run_demo_vertical_slice`
2. Открыть `artifacts/vertical-slice-demo/report.html` — лист, замечание, `finding_id` / `evidence_refs`, вердикт **не PASS**.
3. Рядом PNG оверлея и `findings.bcfzip` (структурный ZIP, **не** CDE-ready).

Сценарий: **штамп / экспликация / толщина стены на текстовом слое PDF**. Не счёт дверей и окон (AECV-Bench, обновление 11.08.2026: двери ~39%, окна ~34%).

Демо-IFC должны быть выгрузкой **Renga**, не Revit: стек заказчика Renga + Tangl (вебинар Tangl × «Самолёт», кластер Пушкино; дирекция ИМ — А. Панькин).

## Честный статус (открытые данные, не молчание заказчика)

| Вопрос Сигиневича | Ответ |
| --- | --- |
| Checkpoint | **NO_GO**. Не перекрашиваем. |
| «Нет норм?» | **Ложь.** IDS Мособлгосэкспертизы публичны: [moexp.ru ТИМ](https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/). Engine coverage: [`../evidence/norm-pack-moexp-coverage-2026-08.md`](../evidence/norm-pack-moexp-coverage-2026-08.md). Нет **подписанного профиля приёмки Самолёта** и нет **корпуса моделей Самолёта** — это две другие вещи |
| «Нет корпуса?» | Открытые: AEC-Bench ([arXiv:2603.29199](https://arxiv.org/abs/2603.29199)), IFC-Bench V2, GNI BIM ([Zenodo 10.5281/zenodo.19722012](https://doi.org/10.5281/zenodo.19722012)). Не использовали для цифры ложных пропусков. **Не существует** публичного «ПД РФ + заключение экспертизы». Атрибуция: [`../DATASETS.md`](../DATASETS.md) |
| MEP | Публичные многодисциплинарные IFC есть (west_riverside, sixty5, duplex…). **Замера у нас нет.** Не MEP delivered. Не цитировать «~0.5 с на учебном пакете» |
| IDS fail-open | Найден и закрыт. Кейс 0101 теперь FAILED у нас сознательно |
| Kimi vs Qwen | **LIVE на Qwen** (fixture). Kimi на Yandex Studio **закрыт гейтом**. Advisory, не проверка норм |
| DWG | Жёсткий **FAILED**. ODA trial 60 дней = КТ#3, не покупка. [`../architecture/ADR-003-dwg-oda-trial-kt3-2026.md`](../architecture/ADR-003-dwg-oda-trial-kt3-2026.md) |
| Московский АГР | **Не собран** (архитектура заморожена). Не обещаем |
| CV | Heuristic регионы + text layer. Это не обученный CV |
| 1980 проверок / 656 тестов | Регрессия кода, **не** доля ложных пропусков ([arXiv:2607.29058](https://arxiv.org/abs/2607.29058): fail-closed ≠ низкий false-pass) |

## Что сознательно не делаем до 20.08

Новые порты/DI, Iteration B.x, демо «посчитай двери», перекрас GO, GPLv3-модели IFC-Bench в репозиторий.

План 7 дней: [`../pilot/KT2_7DAY_PLAN_2026_08_13.md`](../pilot/KT2_7DAY_PLAN_2026_08_13.md)
