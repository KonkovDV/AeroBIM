---
title: "Мастер-план дальнейшей работы: Самолёт × Техлаб × МИК → КТ2 → КТ3"
status: active
version: "1.0.0"
last_updated: "2026-07-27"
claim_boundary: "План не повышает статусы: fixture ≠ customer; Checkpoint NO_GO до RT-001/002/003. Внешние анкоры — методологические ориентиры, не capability claims."
tags: [aerobim, samolet, techlab, mik, workplan, checkpoints, roadmap]
---

# Мастер-план дальнейшей работы (составлен 2026-07-27)

Синтез трёх источников требований
([`TRI_SOURCE_REQUIREMENTS_MATRIX_2026.md`](../tz/TRI_SOURCE_REQUIREMENTS_MATRIX_2026.md)),
календаря Checkpoint #2
([`PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md`](../pilot/PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md)),
kickoff ASK ([`SAMOLET_KT2_ASK_2026_08_15.md`](../partners/SAMOLET_KT2_ASK_2026_08_15.md))
и контура МИК ([`MIK_PILOT_COMPLIANCE_2026.md`](../partners/MIK_PILOT_COMPLIANCE_2026.md)).
Этот файл — операционный план исполнителя на 28.07–21.09; он **не** заменяет
перечисленные SSOT и не ослабляет Claims Lock.

## 0. Исходное состояние (проверено 2026-07-27)

| Факт | Источник |
|---|---|
| Checkpoint **NO_GO**: RT-001 / RT-002 / RT-003 открыты, все заблокированы данными заказчика | [`CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md) |
| DoD Checkpoint #2 (методология) закрыт: протокол, инструкция экспертов, harness, evidence-бандл, TZ-матрица | Workplan КТ2 §Definition of Done |
| Все intake-ворота `customer-intake-gate.json` = false | Kickoff-карта §1 |
| Инженерные хвосты: POST-05 OIDC BFF (DESIGNED / NOT_IMPLEMENTED), DWG conversion MVP (вариант A+B), BCF T2 | RTATOM / gap-анализ |
| Последний зелёный гейт: ruff + mypy + pytest 1057 passed (2026-07-26) | Wave O |

## 1. Контрольные точки (жёсткие даты)

| Дата | Событие | Владелец формы |
|---|---|---|
| **до 3 авг** | NDA + signed scope memo Самолёта; запрос форм Фонда МИК (соглашение M2, программа M3, план-график M4, акт M7, финотчётность M8) | Tech lead / проектный офис |
| **4–10 авг** | Intake: комплект ПД/РД/IFC, нормо-пак, каталог ≥20 ошибок, 2 эксперта, baseline-часы | Самолёт (блокирует RT-001/002) |
| **4–20 авг** | **КТ2** — промежуточная версия на согласованном сценарии | Календарь Самолёта |
| **до 20 авг** | Sandbox СОД + BCF T2 evidence (log + screenshot + hashes) | Самолёт / RT-008 |
| **21 авг – 2 сен** | Оценка на размеченном срезе; BCF в контуре заказчика | Корпус + adjudication |
| **3–21 сен** | **КТ3** — пилотный отчёт, метрики, акт МИК | Подписанты обеих сторон |

Правило конфликтов: контент — календарь Самолёта; форма/сроки отчётности —
план-график Фонда; при расхождении побеждает более ранний дедлайн.

## 2. Окно 28–31 июля (текущее) — исполняется сейчас

| # | Задача | Критерий готовности | Статус |
|---|---|---|---|
| 1 | Верификация baseline: `ruff format/check`, `mypy src`, `pytest tests -q` зелёные на текущем tip | Гейт-лог в этом документе (§6) | **DONE 2026-07-27** |
| 2 | Отправка пакета Самолёту: [`SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md) + протокол + инструкция экспертов на sign-off | Письмо ушло; подтверждение получения | ВНЕ РЕПО (owner: Tech lead) |
| 3 | Запрос форм у менеджера МИК (M2/M3/M4/M7/M8) | Формы получены или зафиксирован срок | ВНЕ РЕПО (owner: проектный офис) |
| 4 | Refresh владельцев потока 5 (TZ-матрица) — по backlog «refresh owners 28–31 Jul» | Матрица без устаревших owner | PENDING |
| 5 | Стабилизация ядра на открытых данных: редкие сценарии, критические ошибки (kickoff-карта §3) | Новые негативные тесты при находках | CONTINUOUS |

## 3. Инженерные треки без данных заказчика (параллельно, приоритетный порядок)

| Приоритет | Трек | Объём до 21.09 | Ограничение |
|---|---|---|---|
| P1 | **DWG conversion MVP** (вариант A + opt-in B из [gap-анализа](../pilot/FOUR_DIRECTION_GAP_ANALYSIS_2026_07_24.md) §1.3): ingest `.dwg` как артефакт + hash, регистрация `source_dwg_sha256↔derived_*`, loss report, fail-closed при отсутствии derived. **Шаги 3–6 закрыты 2026-07-27**: hash-верификация sidecar + conversion-loss QA (пороги §1.4) + analyze-интеграция + CLI `aerobim-register-dwg-conversion`; осталось: согласованные инвентари листов/слоёв и конвертер от Самолёта | Только если Самолёт даёт DWG + согласованный конвертер; иначе фиксируется как ограничение | `dwg_dxf=ok` запрещён honesty-гейтом |
| P1 | **BCF T2 готовность**: прогон [`BCF_T2_IMPORT_RUNBOOK_2026.md`](../pilot/BCF_T2_IMPORT_RUNBOOK_2026.md) на доступном внешнем инструменте до sandbox СОД | Т2-пакет собран за ≤1 день после доступа к СОД | Т2 засчитывается только в СОД заказчика |
| P2 | **POST-05 OIDC BFF**: реализация по [`POST05_OIDC_BFF_DESIGN_2026_07.md`](../architecture/POST05_OIDC_BFF_DESIGN_2026_07.md) | До начала работы с customer-данными в общем контуре (идеал — до 10.08) | Residual security hardening |
| P2 | **VLM/OCR сравнение** Qwen/Kimi/Gemma по [`VLM_OCR_COMPARISON_PROTOCOL_2026_08.md`](../pilot/VLM_OCR_COMPARISON_PROTOCOL_2026_08.md), окно 4–20.08 | Отчёт с CI/p-values (инструментарий Wave L/M готов) | Вспомогательный, не критерий приёмки |
| P3 | MEP: подготовка к RT-003 — только приём federated IFC + signed matrix; ничего не изобретать | По факту данных | `mep_system_clash` никогда OK до evidence |

## 4. Сверка с мировыми практиками (июль 2026, проверено заново)

Позиция AeroBIM подтверждается свежей литературой — курс не менять:

| Практика | Внешний анкор (2025–2026) | Наше состояние |
|---|---|---|
| Гибрид: детерминизм ≻ LLM; LLM-центричные ACC — исследовательский фронт, не production-вердикт | Iversen 2026 (Automation in Construction, LLM-centric ACC framework — explicit research prototype); Madireddy 2025 (Electronics 14:2146) | ADR-001: вердикт только у детерминированного контура — соответствует |
| IDS 1.0 как machine-checkable якорь требований; ACC через IDS | de Mendonça, W78-2024 (IDS-based ACC); buildingSMART IDS software registry | IDS 1.0 fail-closed + официальный XSD-аудит (Wave 2026-07-25) — соответствует |
| BCF 2.1/3.0 + доказанный импорт, а не «export работает» | buildingSMART BCF implementations registry | T0/T1 done, T2 через СОД заказчика — честнее рынка |
| Чертежи: region-restricted OCR (title block) + VLM только advisory; counting/семантика не решены | Blueprint (arXiv 2602.13345); eDOCr2 (Machines 13:254); bridge-drawing digitization (2026) | OCR baseline + VLM-протокол сравнения — соответствует |
| Статистическая строгость оценок: paired permutation, TOST, anytime-valid e-values, κ/α | Dror 2018; Vovk & Wang 2021; Ramdas 2023 SAVI; arXiv 2501.03982 | Waves K–R реализованы — впереди типичной индустрии |
| Двойная слепая разметка + adjudication до публикации точности | Krippendorff α ≥ 0.67 конвенция; protocol в repo | EXPERT_LABELING_INSTRUCTION + publishable-гейты — соответствует |

Вывод: разрыв с лучшими практиками не инженерный, а **data-bound** (корпус,
нормо-пак, СОД). Академическая новизна репо (e-value regression monitoring
для eval-пайплайна) опережает публикуемую практику — кандидат в препринт
после пилота (не раньше акта МИК, Claims Lock ревью обязательно).

## 5. Риски и правила

1. Просрочка intake 4–10.08 сжимает окно adjudication → эскалация Самолёту
   на 3-й день молчания; КТ2 остаётся достижимой на fixture-сценарии.
2. Формы МИК могут прийти с более ранними сроками отчётности → двойной
   дедлайн-трекинг (контент vs форма) в kickoff-карте.
3. Любой публичный текст (включая этот план при публикации) — через Claims
   Lock ревью; запрещённые формулировки перечислены в workplan КТ2 §Claims Lock.
4. Ни одна строка акта МИК не может быть сильнее intake-gates —
   fail-closed инструменты (publishable-гейт, `claim_level`) это блокируют.

## 6. Гейт-лог исполнения плана

| Дата | Гейт | Результат |
|---|---|---|
| 2026-07-27 | `ruff format --check` + `ruff check` (src, tests) | PASS (347 files formatted, all checks passed) |
| 2026-07-27 | `mypy src` (mypy 1.20.2, запуск через `python -m mypy`) | PASS (205 files, no issues) |
| 2026-07-27 | `pytest tests -q` | **1129 passed, 7 skipped** (20.9s) |
| 2026-07-27 | Wave S (DWG derived-provenance + conversion QA): ruff + mypy (207 files) + pytest | PASS · **1149 passed, 7 skipped** |

Примечание: Windows `.venv\Scripts\mypy.exe` can return empty exit 1; canonical run is `python -m mypy src`.
