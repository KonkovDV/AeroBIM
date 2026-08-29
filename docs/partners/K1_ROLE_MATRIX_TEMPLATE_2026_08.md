<!-- claims-lint: allow-file reason="K1 role matrix template; empty names; not a scored roster; NO_GO" -->
---
title: "K1 role matrix template — fill on the application, not as a git roster"
date: "2026-08-29"
last_updated: "2026-08-29"
status: active
version: "1.1.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Empty template. Person cells stay blank in git. Public LETI text requires
  both scientific and engineering competencies. Checkpoint NO_GO.
---

# Шаблон матрицы К1

Публичный текст программы (ЛЭТИ / МИК): команда 1–10; нужны **научно-исследовательские**
и **инженерно-технические** (IT / ML / данные) компетенции. Источник той же
страницы, что таблица приложения 4.

Объект К1 — **заявка на i.moscow**, не этот файл. Ячейки «кто» в git **пустые**.
Устные консультанты сюда не вписываются.

| Роль (задача) | Класс компетенции | Кто (только заявка) | Чем подтверждена | Что сделал в git (модуль/док) |
|---|---|---|---|---|
| Научный лидер / постановка измерения | научная | | степень / публикации / патент — в заявке | Протокол 0,60; IUA ledger |
| BIM / openBIM | инженерная | | | IfcOpenShell / IfcTester; IDS 1.0 |
| Нормы / экспертиза (ассистент, не ГИП) | научная+отрасль | | | HITL; ADR-001 |
| Backend | инженерная | | | FastAPI analyze |
| Frontend / замечание | инженерная | | | review shell |
| QA / воспроизводимость | инженерная | | | pytest pin `attested_by=ci` |
| ML / VLM | инженерная | | | Advisory only; не `summary.passed` |
| Расчётчик (сверка, не solver) | отраслевая | | | Сверка чисел; `.lir` закрыт |

Пока «кто» пусто, комиссия имеет право держать К1 в полосе **низкий**.
Заполнение шаблона в git вымышленными ФИО **запрещено**.

Десять человек — **потолок**, не норматив. ЛЭТИ: **от 1 до 10**. К1 ставит
два **класса** (наука + инженерия). Один капитан с дипломом/публикацией и
с git/CI закрывает оба класса в **заявке**. Это не «команда из десяти».
Идентичность 16+36,6=52,6 — арифметика полос, не прогноз балла. См.
[`../quality/MIK_A_LEVERS_PAST_50_2026_08.md`](../quality/MIK_A_LEVERS_PAST_50_2026_08.md).

Научный класс без новой фамилии в git: протокол 0,60; IUA; самооценка 72514;
инструкция двойной разметки. Инженерный: CI pin, IfcOpenShell, IDS, fail-closed
Autodesk. Консультанты по-прежнему не балл.
