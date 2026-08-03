---
title: "Red Team — аудит недели 27.07–04.08.2026"
base: 518fef8
head: 29d66b8
date: 2026-08-04
status: active
version: "1.1.0"
remediation: >-
  RT-W-01/02/05 closed 2026-08-04 on working tree (post-29d66b8).
  RT-W-03/04 remain process; Checkpoint NO_GO unchanged.
method: >-
  Operator static audit (diff, greps, selective read, secrets, licenses).
  Tests were not run in the auditor sandbox; local remediation tests ran for RT-W-02.
---

# Red Team: неделя 27 июля — 4 августа

## 0. Профиль недели

| Метрика | Значение | Комментарий |
|---|---|---|
| Коммитов | 227 | пик 94 за 28 июля |
| Файлов изменено | 1007 | — |
| Вставок / удалений | 72 001 / 551 | **соотношение 131:1** |
| Только Python | +30 533 / −274 | удалено 0,9% |
| Markdown-файлов в репо | 151 | — |
| Код / тесты | 53 312 / 38 425 строк | здоровое соотношение 0,72 |

Соотношение вставок к удалениям — главный структурный сигнал недели. Почти чистое
наращивание без рефакторинга означает, что ни одно решение за неделю не было
пересмотрено настолько, чтобы что-то убрать.

---

## 1. Что проверено и чисто

| Проверка | Результат |
|---|---|
| Секреты в истории и рабочем дереве | Совпадений нет |
| `.env` в коммитах | Не найден |
| Опасные конструкции | `eval`/`exec`/`pickle`/`os.system`/`shell=True`/`yaml.load` — не найдены |
| Отключение TLS | не найдено |
| Утечка ключа в инструментах | 7 сетевых инструментов — ключ не печатают |
| LIC-001 | Закрыт (pymupdf → optional) |
| CC BY-ND TestCases | Корректно (NOTICE + unmodified tree) |
| Инъекция через содержимое | Регрессионный тест есть |
| Запись `summary.passed` | Новых путей вне тестов/фикстур нет |

---

## 2. Находки и remediation

### RT-W-01 · высокий · buildingSMART XSD `review_pending` → **CLOSED**

**Было:** 11 файлов BCF/IDS XSD в `DATASET_MANIFEST.json` со статусом `review_pending`.

**Сделано (2026-08-04):**
- Upstream LICENSE verified: BCF-XML `release_3_0` и IDS — **CC BY-ND 4.0**
- Добавлены `samples/bcf-xsd/LICENSE_CC_BY_ND_4.0.txt` + `NOTICE`, то же для `ids-xsd/`
- README обновлены; манифест: `license_status=cc_by_nd_4.0`, `pending_left=0`
- Инструмент: `python -m aerobim.tools.update_buildingsmart_schema_licenses`

### RT-W-02 · высокий · honesty keys без регрессии → **CLOSED**

**Было:** `pii_gate`, `effectiveness_on_customer_sheets`, `token_budget_*`, `bcf_*`, `http_remark_field` — 0 явных упоминаний в тестах.

**Сделано:** `backend/tests/test_honesty_surface_contract.py` — фиксирует текст/значения; смена `NOT_MEASURED` → fail. Локально: **2 passed**.

### RT-W-03 · средний · рост без пересмотра → **PROCESS**

См. [`ADR_DROPPED_APPROACHES_2026_08_04.md`](../architecture/ADR_DROPPED_APPROACHES_2026_08_04.md). Отказы фиксировать в ADR, не только в git history. Примечание: `gwet_ac1` **сохранён** в `domain/eval_statistics.py` (RT-026); имя `gwet_ac` в диффе недели — промежуточное.

### RT-W-04 · средний · плотность без ревью → **PROCESS**

До 20.08 — день сведения без новых функций (см. операторский план).

### RT-W-05 · низкий · устаревший patch → **CLOSED**

Удалён `docs/review/aerobim-kt2-text.patch` (5116 строк, расходился с README).

---

## 3. Чего аудит не проверил

1. Тесты в песочнице аудитора не запускались (кроме локальной remediation RT-W-02).
2. Логика +30k строк не прочитана целиком.
3. Нагрузка / гонки не проверялись.
4. Фронтенд не аудировался.
5. Корректность доменных проверок на реальной ПД — только RT-001.

---

## 4. Итог

Неделя без находок первого класса по секретам/опасным конструкциям/LIC-001.
Две высокие находки объединялись тем, что **заявления защищены слабее кода** —
обе закрыты remediation выше до КТ#2.

Checkpoint остаётся **NO_GO**.
