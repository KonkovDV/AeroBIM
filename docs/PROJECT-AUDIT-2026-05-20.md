---
title: "Гиперглубокий аудит AeroBIM — 2026-05-20"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, audit, fact-check, hygiene]
---

# Гиперглубокий аудит AeroBIM (2026-05-20)

Метод: инспекция репозитория, `pytest` / `ruff` / `mypy`, `evaluate_extraction`, сопоставление README и pilot-документов с кодом, поиск следов IDE/ИИ-инструментов и рунглиша.

## Исполняемое состояние (фактчек)

| Проверка | Результат |
|---|---|
| `pytest tests -q` | **292 passed**, 2 skipped |
| `ruff check src tests` | pass |
| `mypy src/aerobim --ignore-missing-imports` | 63 files, pass |
| `evaluate_extraction --min-macro-f1 0.70` | **PASS**, macro F1 = **0.86** |
| Co-authored-by в последних 30 коммитах `main` | не найдено |
| Уникальный автор `main` | только `KonkovDV` |

## Что подтверждено как рабочее

- Детерминированное ядро IFC + IDS + cross-doc + narrative (regex).
- 2D overlay и drawing evidence в UI (`DrawingEvidencePanel`, live smoke).
- BCF 2.1/3.0, OpenRebar digest, ConflictKind, ISO 19650-lite поля.
- CI: lint, typecheck, test, benchmark-smoke, extraction-quality, openapi-contract.

## Критические находки (исправлены в этой сессии)

| ID | Проблема | Действие |
|---|---|---|
| H-01 | `backend/llm/` — FT-scaffold, не в пилотном sign-off | Удалён из репозитория |
| H-02 | `reports/aerobim_ft_scaffold_gate_report_v1.json` — пути `samolet`, артефакт FT | Удалён |
| H-03 | `docs/superpowers/` — внутренние спеки donor control-plane (`agent:preflight`) | Удалены |
| H-04 | `docs/git-hygiene-2026.md`, README — бренд IDE и «агент» | Заменено на `contributor-git-2026.md` |
| H-05 | `docs/05-fact-check-audit.md` — граница `c:\plans\samolet` | Исправлено на AeroBIM |
| H-06 | Публичные упоминания LLM/VLM/GPT/Cursor в docs | Нейтрализованы (стохастические/непрозрачные модели) |

## Оставшиеся гэпы (не ломают CI, но важны для пилота)

| ID | Гэп | Серьёзность |
|---|---|---|
| G-01 | Таблицы sign-off в `pilot-pre-pilot-gates-2026.md` | **Закрыто** 2026-05-21 |
| G-02 | Тег `pilot-2026-pre` | **Закрыто** на `1a5c03e` |
| G-03 | `docs/10-academic-audit-and-recommendations-ru.md` v0.6 (overlay/smoke shipped) | **Закрыто** |
| G-04 | Dependabot PR triage | Политика в [`evidence/ops-hygiene-2026-05-21.md`](evidence/ops-hygiene-2026-05-21.md) |
| G-05 | `gh` CLI / About/Topics | Ручной шаг; см. ops-hygiene |
| G-06 | OIDC, arq/Redis, полный Postgres hydration — post-pilot | Ожидаемо по плану |
| G-07 | Cross-doc на pilot fixture pack: 0 contradictions | Информационно — не overclaim на прод-данных |
| G-08 | `.[clash]` / `.[docling]` opt-in | **Закрыто** — [`optional-adapters-smoke-2026.md`](optional-adapters-smoke-2026.md) + weekly log |
| G-09 | FAIR/CODE reproducibility SSOT | **Закрыто** — [`REPRODUCIBILITY-2026.md`](REPRODUCIBILITY-2026.md) |

## Рунглиш (инвентарь и политика)

**Допустимо (термины отрасли):** IFC, IDS, BCF, GUID, fixture, benchmark, smoke, sign-off, overlay, endpoint, pack.

**Исправлено в RU-доках:** смешение «operator-документация», «capability framing», «One-report smoke path» — в `10-academic-audit` добавлены русские формулировки рядом с терминами.

**Frontend/UI:** пользовательские строки без следов IDE; см. `frontend/src`.

## Документация vs код (расхождения)

| Утверждение | Факт |
|---|---|
| Macro F1 ≈ 0.86 | Подтверждено `evaluate_extraction` |
| 290+ тестов | 292 passed |
| 2D overlay «planned» в старом аудите §5.1 | **Уже в коде** (май 2026) — аудит §10 нужно обновлять |
| Fine-tuning production | **Нет** — только удалённый scaffold |
| Vision-language sign-off | **Нет** — порт `VisionDrawingAnalyzer`, deterministic PDF/OCR baseline |

## Рекомендации maintainer (актуально на 2026-05-21)

1. Pre-pilot gates и тег `pilot-2026-pre` — выполнено.
2. Перед каждым push: [`evidence/pre-push-verification-2026-05-21.md`](evidence/pre-push-verification-2026-05-21.md).
3. Пилот week 1+: [`pilot-start-package-2026.md`](pilot-start-package-2026.md), [`pilot-weekly-log-2026.md`](pilot-weekly-log-2026.md).
4. Ноябрь 2026: [`post-pilot-go-no-go-memo-2026.md`](post-pilot-go-no-go-memo-2026.md).

## Команды воспроизведения

```powershell
cd AeroBIM\backend
.\.venv-pilot\Scripts\python.exe -m pytest tests -q
.\.venv-pilot\Scripts\python.exe -m ruff check src tests
.\.venv-pilot\Scripts\python.exe -m mypy src/aerobim --ignore-missing-imports
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
```
