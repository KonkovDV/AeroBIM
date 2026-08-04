---
title: "KT#2 Block I delivery report — TZ Task 07"
date: 2026-08-04
status: active
version: "1.0.0"
claim_boundary: >-
  Checkpoint remains NO_GO. No product accuracy claims. AECV is open_bench_only.
---

# Отчёт: доработка под ТЗ Задачи №7 (Блок I)

HEAD baseline в промпте: `29d66b8`. Работа поверх `733a445` + незакоммиченные research docs.

## I.1 Матрица (Finding 0)

**Файлы:** `audit/reports/TZ_RUNTIME_MATRIX.md`

| Строка | Статус | Основание |
|---|---|---|
| **27** MS Office | **PARTIAL** | `DoclingOfficeDocumentIngestor` + upload + `test_cad_office_ingest.py`; нет реального docx fixture → не VERIFIED_FIXTURE_ONLY |
| **28** Сравнение версий/типов | **MISSING** | Multi-package CDE compare отсутствует; STAGE/VERSION labels в row 12 ≠ закрытие ТЗ (footnote) |
| **19** | MISSING → **ADVISORY_ONLY** | см. I.4 |
| **21** | PARTIAL → **VERIFIED_FIXTURE_ONLY** | см. I.2 |
| **26** | FIXTURE_ONLY; gate=**p95** | см. I.3 |

Сводка пересчитана (28 строк).

## I.2 EN-замечания

**Файлы:** `backend/tests/test_remark_locale_parity.py`  
**Тесты:** паритет RU/EN по 4 категориям + EXISTS; BCF Description несёт EN body (`at least`), Title = rule_id.  
**Инвариант:** locale process-wide via `AEROBIM_REMARK_LOCALE` (per-request API не добавляли).

Строки матрицы **21** → `VERIFIED_FIXTURE_ONLY`. Строка **9** (ТЗ EN extraction) остаётся `PARTIAL` (корпус есть, CI F1 gate нет).

## I.3 SLA p95

**Файлы:** `benchmark_project_package.py` (`p95_ms`), `measure_package_sla.py` schema **1.4.0**, `test_measure_package_sla.py`  
**Доказано:** gate metric = `p95_minutes_observed`; env `llm_advisory_enabled_env` пишется в артефакт; advisory budget share поля.  
**Параллелизм overlay:** `overlay_llm_remarks(..., max_workers)` из `llm_max_concurrent` (cap 10).

Полный dual-run advisory on/off на эталоне — выполнить оператором (токены):

```text
AEROBIM_LLM_LOCAL_ENABLED=false  python -m aerobim.tools.measure_package_sla --pack ... --iterations 5
AEROBIM_LLM_LOCAL_ENABLED=true   python -m aerobim.tools.measure_package_sla --pack ... --iterations 5
```

Публиковать **p95**, не avg.

## I.4 Space efficiency → ADVISORY_ONLY

**Файлы:**  
- `domain/space_efficiency_advisory.py`  
- `infrastructure/adapters/ifc_space_inventory.py`  
- wire в `AdvisoryOrchestrator` (local IFC, без egress)  
- `determinism_gate` сохраняет `remark`  
- `tests/test_space_efficiency_advisory.py`

**Доказано:** только INFO + `origin=advisory` + `ai_generated` / expert confirmation; **нет** числовых порогов эффективности.  
**Не сделано:** live VLM crop enrichment (layout_note optional; PII-гейт без исключений при подключении).

## I.5 AECV publish

**Файлы:** evidence JSON (`mape_bench_protocol`, `publish_framing`), `docs/research/AECV_PUBLISH_FRAMING_I5_2026_08_04.md`, evidence README.  
Headline: **`macro_extended=0.4325`** (Table 1 metric), `macro_bench_protocol=0.5064` reference-only. B.5 gates listed. Forbidden: «обошли Gemini» / сравнение 4-классного mean с Table 1.

## I.6 Бюджет vs биллинг

**Файл:** `docs/architecture/LLM_BUDGET_BILLING_RECONCILE_WEEKLY_2026_08_04.md`

Снимок ledger 2026-08-04 (Europe/Moscow day_key `2026-08-03`):

| Поле | Значение |
|---|---|
| `tokens_today` | **34** |
| Billing console | **NOT_RUN this session** — оператор сверяет вручную |

Δ billing ≫ 34 ожидаема (open-bench AECV мимо ledger).

## I.7 Библиография

**Файл:** `CITATION_ERRATA_2026_08_04.md` — блок 309-ФЗ/УКЭП OVERCLAIM; DOI twin FABRICATED уже был.  
`research.md` / `представление.txt` **не в git** — scrub внешних копий.

## Инварианты перепроверены

| Тест | Результат |
|---|---|
| `test_remark_locale_parity` | pass |
| `test_space_efficiency_advisory` | pass |
| `LlmLocalOffEqualsOnTests` | pass |
| `test_advisory_remark_api_wiring` | pass |
| SLA schema/reject tests + fixture p95 evidence | pass (46 focused + evidence `samolet-sla-fixture-p95-2026-08-04.json`) |
| Honesty surface contract (RT-W-02) | pass |

Checkpoint **NO_GO**. RT-001/002/003 без изменений.

## Расход токенов

Этот проход **не** тратил Yandex токены (только unit/fixture). Dual SLA advisory on/off — отдельный операторский прогон.

## Незакрыто (честно)

| Пункт | Почему |
|---|---|
| I.3 live dual SLA artifact в evidence | Нужен операторский прогон с ключом; не поднимали бюджет |
| I.4 VLM crop на реальном плане | Отложено; IFC inventory достаточно для ADVISORY_ONLY |
| Row 9 EN extraction CI gate | Отдельный evaluate_extraction на EN corpus |
| Row 27 VERIFIED_FIXTURE_ONLY | Нет реального docx/xlsx fixture |
| Row 28 MISSING | Multi-package CDE = Блок II |
| B.5 prompt verbatim dump | Нужен diff с §3.1.2 PDF |
| Блок II–III | По плану после КТ#2 |
