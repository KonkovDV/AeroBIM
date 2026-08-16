<!-- claims-lint: allow-file reason="Proposed 10D file/API boundary; not CDE-ready; NO_GO" -->
---
title: "КТ#2 — минимальный intake-контракт к 10D / СОД"
date: "2026-08-16"
status: active
claim_boundary: >
  Proposed file/API boundary. Not implemented as a 10D connector.
  Not CDE-ready. Not Tangl integration. Checkpoint NO_GO.
---

# Intake-контракт (одна страница)

10D хранит и ведёт документ. AeroBIM **не** заменяет 10D. Граница: СОД отдаёт пакет → AeroBIM проверяет → JSON/HTML/BCF возвращается эксперту / обратно в СОД как файл.

Текущий `docs/openapi.json` — ручки AeroBIM (`/v1/uploads`, analyze, reports). Это **не** контракт 10D. Ниже — предлагаемые поля, когда граница согласована.

## Вход (от 10D / оператора)

| Поле | Смысл | Обязательно |
|---|---|---|
| `project_id` | Проект в контуре заказчика | да |
| `package_id` | Комплект одной ревизии | да |
| `document_id` | Документ внутри комплекта (optional per file) | нет |
| `revision` | Идентификатор ревизии (строка заказчика) | да |
| `discipline` | AR / KR / MEP / … | да |
| `stage` | ПД / РД / … | да |
| `source_uri` или `upload` | Где лежат IFC/PDF/IDS | да (один из) |
| `rule_pack_id` | IDS / JSON pack + `pack_hash` | да для Shared-gate |
| `required_capabilities` | какие проверки обязательны (fail-closed) | да |

## Выход (в 10D / эксперту)

| Поле | Смысл |
|---|---|
| `run_id` | Идентификатор прогона |
| `report_id` | Отчёт |
| `outcome` / `passed` | ADR-001: `passed` следует `PackageOutcome` |
| `finding_count` / `blocking_finding_count` | IFC/IDS проекция Acceptance Gate |
| `blocking_outside_projection_count` | ERROR вне IFC/IDS (schema 1.1.0) |
| URIs | `report.html`, `report.json`, `findings.bcfzip` |
| hashes | `input_hash`, `rule_pack_hash`, `reproducibility_hash` |

Пилот до SSO: **одна ВМ + Docker + `AEROBIM_API_BEARER_TOKEN`**. `auth_bff=NOT_IMPLEMENTED` в проде. Pentest заказчика — в профиль приёмки, если согласуют (сами просим).

IFC LRU: не более **8** моделей в процессе; потолок размера файла **256 MiB** (`max_upload_bytes`). Верхняя граница кэша **8 × 256 MiB = 2 GiB** IFC, если каждый слот заполнен максимумом. RAM на федеративном пакете **не замерена**.

Checkpoint **NO_GO**. Импорт BCF в 10D = NOT_VERIFIED, пока нет лога/скрина заказчика.
