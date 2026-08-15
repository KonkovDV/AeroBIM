<!-- claims-lint: allow-file reason="KT#2 work plan; forbidden phrases as non-claims; NO_GO explicit" -->
---
title: "План работ: решаемые затыки КТ#2 (14.08.2026, после среза 1.1)"
date: "2026-08-14"
claim_boundary: "План работ. Код в этом документе не меняется. Checkpoint NO_GO. Не customer accuracy. Не DWG-ready. Не MEP delivered. Не CDE-ready."
---

# План работ — решаемые затыки КТ#2

**Состояние на 14.08 ~14:00:** вертикальный срез 1.1 живой (exit 0, `summary.passed=false`, NO_GO, hashes стабильны). HEAD `2e6654b`, рабочее дерево **грязное** (срез не закоммичен).

**Закрыто 14.08 ~14:40:** A1 закоммичен (`d809d3677492c988d35024e9e06664ae7f949b89`). Повтор CLI: `working_tree_dirty=false`, overlay PNG без дрейфа. Checkpoint **NO_GO**.

**Жёсткие рамки для исполнителя:**

- Checkpoint остаётся **NO_GO**. Не перекрашивать.
- Архитектура заморожена: **нет** новых domain ports, DI tokens, adapters, Iteration B.x, knowledge graph, BCF API, полноценного CV.
- Не заявлять: точность >90%, SLA ≤30 мин, DWG-ready, MEP delivered, CDE-ready BCF, независимую корректность расчётов, fixture GO = customer GO.
- 654 AABB overlap pairs ≠ коллизии. IDS МОГЭ ≠ профиль Самолёта. Qwen/Kimi ≠ сравнительное исследование (`comparison_not_run`). GNI/AEC-Bench/IFC-Bench ≠ корпус заказчика. DXF ≠ подтверждённая поддержка. Docker ≠ bare-metal.
- Видео не генерировать: `human_required`, due 2026-08-19.
- Каждый шаг: сначала воспроизвести, потом чинить; после правки — focused pytest + ruff + mypy на затронутых файлах; не раздувать diff.

---

## A. Репо-локальные затыки (решает ИИ, без заказчика)

### A1. Закоммитить срез 1.1 — **блокер для всего остального**

- **Затык:** 18 изменённых/новых файлов висят в working tree; `git_sha` в артефактах ссылается на `2e6654b` при `working_tree_dirty=true`.
- **Действие:** `git add` только файлы среза (backend 8 файлов, docs 7 файлов, `audit/claims_allow_file_registry.json`, новый `docs/evidence/vertical-slice-demo-live-2026-08-14.md`). Не добавлять `artifacts/` (gitignore). Коммит: `feat(kt2): vertical slice 1.1 — run manifest, output hashes, NO_GO banner`.
- **DoD:** `git status` чист по срезу; повторный прогон CLI даёт `working_tree_dirty=false` и новый SHA.
- **Эскалация:** коммит/push — только по явной команде владельца.

### A2. Четыре pre-existing падения pytest

Полный прогон 14.08: **2147 passed, 4 failed**. Все четыре старше среза, но блокируют «pytest проходит».

| # | Тест | Причина | Путь решения |
|---|---|---|---|
| A2.1 | `test_docs_metadata_integrity` | `last_updated` у `docs/tz/TZ_COMPLIANCE_MATRIX_2026.md` и `docs/capability-claim-matrix-2026.md` старше последнего коммита | Обновить `last_updated` в двух файлах (docs-only) |
| A2.2 | `test_golden_report` | Дрейф golden reproducibility hash baseline | Воспроизвести, зафиксировать новый golden с записью обоснования (почему hash сменился) |
| A2.3 | `test_injected_ifc_defects_level_b` LB007 | class swap = vacuous pass на IDS-only | Разобрать кейс LB007; чинить тест или gate, не удаляя проверку |
| A2.4 | `test_samples_manifest_gate` | 10 файлов `samples/` не в `DATASET_MANIFEST.json` (moexp pack, agr fixture, norm-citation configs) | Дописать файлы в манифест с sha256 |

- **DoD:** `pytest tests -q` → 0 failed. Каждое исправление — отдельным логическим коммитом или одним `fix(ci):` с перечнем.
- **Граница:** не «чинить» тесты удалением assertions.

### A3. mypy `src/aerobim` — 48 ошибок в 10 файлах

- **Факт 14.08:** `mypy src/aerobim --strict --ignore-missing-imports` → **48 errors / 10 files** (было 58/13; 4 модуля среза уже чисты). Остаток — в `tools/` (union-attr на `.get`, assignment None→Path и т.п.).
- **Действие:** точечные типизации в `tools/`, без новых абстракций. Паттерны: сужение `dict` после `isinstance`, `Optional` guard, `cast` только с комментарием-причиной.
- **DoD:** `mypy src/aerobim --strict --ignore-missing-imports` → 0 errors. Не ослаблять `strict`, не добавлять глобальные `type: ignore`.

### A4. ruff repo-wide — 12 errors + 32 файла форматирования

- **Факт 14.08:** `ruff check src tests` → 12 errors (6 auto-fixable); `ruff format --check` → 32 файла.
- **Действие:** `ruff check --fix` только для безопасных правил; `ruff format` по всем 32; ручной разбор остатка (E501/I001 в `settings.py`, `openai_compat_llm_provider.py`, `region_restricted_vlm_pipeline.py` и др.).
- **DoD:** `ruff check src tests` и `ruff format --check src tests` → PASS.
- **Граница:** форматирование не смешивать со смысловыми правками в одном коммите.

### A5. claims-lint `--full-docs` и CI-гейты

- **Затык (было):** `--full-docs` / `wall_guid_verify exit=1`.  
- **Закрыто 14.08 вечер:** snapshot `wall-guid` был с CRLF-хешами; Linux `eol=lf` валил verifier. Снимок нормализован в LF, exporter пишет `newline="\n"`. Runtime baseline README drift (env + LOC) обновлён. N43 lag=1 **не** включали.  
- **DoD локально:** `verify_evidence_bundle` wall-guid OK; `--check-readme` OK; `lint_claims.py` OK. Зелёный CI — после push.

### A6. Паритет интерпретатора: локальный 3.13 vs CI 3.12 — **закрыто 14.08 вечер**

- **Факт (было):** venv собран на Python **3.13.7**; `pyproject` требует `>=3.12`; CI гоняет 3.12. Хеши среза на 3.13 подтверждены, на 3.12 — нет.
- **Сделано:** установлен CPython **3.12.10** (`winget` `Python.Python.3.12`); venv `backend/.venv-3.12` (`.venv` 3.13.7 не снесён); extras по README (`hashed lock` на Windows падает на `uvloop`); два прогона CLI; `.python-version` = `3.12`.
- **DoD:** overlay PNG и `LIMITATIONS.json` **совпали** с пином 3.13.7. `reproducibility_hash` / `run-manifest.json` **отличаются** из‑за `code_version=f380354` + dirty tree vs `d809d36` clean — не 3.12 vs 3.13. Пин: `docs/evidence/vertical-slice-demo-live-2026-08-14.md`.

### A7. Устаревший handoff-снапшот 11.08

- **Затык:** `docs/evidence/kt2-handoff-2026-08-11/vertical-slice/report.html` не содержит `#kt2-overlay`; риск показать старое на демо.
- **Действие:** не перезаписывать снапшот (это исторический evidence). Добавить в его README строку «superseded by live CLI; см. `vertical-slice-demo-live-2026-08-14.md`».
- **DoD:** любой путь из docs к демо-HTML ведёт на свежий `artifacts/`, а не на снапшот.

### A8. BCF 2.1 — структурная валидация по vendored XSD

- **Факт:** в репо есть `samples/bcf-xsd/release_2_1`; экспorter пишет без namespace под официальные XSD. Проверка `findings.bcfzip` против XSD локально возможна без CDE.
- **Действие:** прогнать XSD-валидацию `markup.bcf` из свежего `findings.bcfzip`; результат — строкой в пин live-CLI.
- **DoD:** «BCF ZIP проходит vendored XSD 2.1» или честный FAIL с причиной. Импорт в CDE не заявлять.

### A9. Frontend vitest — разовое подтверждение

- **Факт:** frontend не тронут, vitest в этой сессии не запускался.
- **Действие:** `cd frontend && npm ci && npm run test` (или repo-стандарт). Если зелёно — записать в release report. Если падает — не чинить молча, вынести в блокеры.
- **DoD:** verdict по vitest зафиксирован фактом, не «не затронут».

### A10. N43 runtime baseline (после 17.08, не раньше)

- **Факт:** baseline SHA `3489cad` отстаёт на 62 коммита при политике `max_commits_behind=50`; активация отложена до 17.08.
- **Действие (только после 17.08):** обновить runtime baseline, прогнать N43 lag=1, зафиксировать результат.
- **Граница:** до 17.08 не активировать.

---

## B. Требует человека (не ИИ)

| # | Задача | Срок |
|---|---|---|
| B1 | Записать 3-мин видео по `docs/demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md` на свежем `artifacts/vertical-slice-demo/report.html` | 19.08 |
| B2 | Решение о коммите/push среза и фиксов A2–A5 | до 18.08 |
| B3 | Загрузка пакета в ЛК по `docs/pilot/KT2_UPLOAD_PACK_2026_08_14.md` | 19–20.08 |
| B4 | Парный VLM-прогон (Qwen vs Kimi, одинаковые input/prompt/schema) — нужен не-Yandex endpoint Kimi или решение владельца; до этого статус `comparison_not_run` не трогать | по решению |

## C. Заблокировано заказчиком (не решается в репо)

| # | Блокер | Что нужно |
|---|---|---|
| C1 | RT-001: корпус «ПД РФ + заключение экспертизы» | публично не существует; нужен корпус заказчика |
| C2 | RT-002: подписанный профиль приёмки Самолёта | документ заказчика (IDS МОГЭ — не он) |
| C3 | RT-003: federated MEP IFC + верифицированный clash | модели заказчика + scope memo; AABB pairs ≠ clash |
| C4 | Выгрузка Renga IFC Самолёта вместо IfcOpenShell fixture | письмо-запрос готово: `docs/partners/SAMOLET_RENGA_IFC_REQUEST_2026_08_14.md`. **14.08:** публичный образец издателя (ПНСТ 909, Renga 8.7, `FILE_SCHEMA=IFC4`) измерен командой `run_renga_export_probe`; демо-IFC **не** подменён; Самолёт по-прежнему intake |
| C5 | ODA trial (native DWG) | задача КТ#3; CADSoftTools не принято |
| C6 | Импорт BCF в CDE заказчика | доступ к CDE; до проверки — «не CDE-ready» |

---

## Порядок выполнения

1. **A1** (коммит среза) — по команде владельца.
2. **A2.1 → A2.4** (pytest green) — каждый с focused-тестом.
3. **A4** (ruff) — отдельным коммитом форматирования.
4. **A3** (mypy) — итерации по 10 файлам.
5. **A5** (claims + wall_guid) → push → смотреть CI.
6. **A6, A7, A8, A9** — пины и подтверждения.
7. **A10** — только после 17.08.
8. Финальный release report: что сделано / не сделано / заблокировано заказчиком; NO_GO неизменен.

**Стоп-условия:** любая задача, требующая нового порта/DI/adapter, заявки GO, или данных заказчика — стоп и эскалация, не обходить.
