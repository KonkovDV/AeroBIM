---
title: "Red Team — аудит недели 27.07–04.08.2026"
base: 518fef8
head: 29d66b8
date: 2026-08-04
status: active
version: "1.2.0"
remediation: >-
  RT-W-01/02/05 closed earlier 2026-08-04. RT-W-06/07 + Task 0 scorer validation
  closed post-733a445/f131974 wave. RT-W-03/04 remain process; Checkpoint NO_GO.
method: >-
  Operator static audit (diff, greps, selective read, secrets, licenses).
  Local remediation tests: aecv_bench_eval + honesty_surface_contract.
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

### Task 0 · scorer validation → **CLOSED**

Вынесено: [`docs/evidence/aecv-scorer-validation-2026-08-04.json`](../evidence/aecv-scorer-validation-2026-08-04.json) + [`.md`](../evidence/aecv-scorer-validation-2026-08-04.md).  
Десять моделей Table 1: max \|Δ\|≈0.020, median≈0.004 → `SCORER_EQUIVALENT_WITHIN_TOLERANCE`.  
Сверка идёт по `macro_extended` (5 полей) — так считает upstream `visualizer.mean_accuracy`.

### RT-W-06 · высокий · offline без provenance → **CLOSED**

`object_counting_offline.provenance`: `upstream_repo`, `upstream_commit` (`1c88ec2…`), path pattern, `predictions_tree_sha256`, `fetched_at`, split `paper_table1_models` (10) / `repo_only_models_not_in_paper_table1` (17).

### RT-W-07 · высокий · канонический macro занижен → **CLOSED**

В `object_counting_live.summary` рядом:
- `macro_bench_protocol` = **0.5064** (468 field-scores)
- `macro_extended` = **0.4325** (585)
- `macro_exact_match_rate` → привязан к protocol
- `comparability_gates` (B.5 + table1_vs_protocol_keys)

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
Волна после `733a445`: заявления (provenance offline, dual macro, scorer validation)
закрыты вместе с honesty/XSD/patch. Checkpoint остаётся **NO_GO**.
