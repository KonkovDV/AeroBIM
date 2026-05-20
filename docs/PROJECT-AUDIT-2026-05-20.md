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
| G-02 | Тег `pilot-2026-pre` не создан | Средняя — воспроизводимость |
| G-03 | `docs/10-academic-audit-and-recommendations-ru.md` частично устарел (апрель): R1 overlay уже в коде | Низкая — обновить статус |
| G-04 | 8 открытых Dependabot PR на GitHub | Низкая — зависимости |
| G-05 | `gh` CLI не в CI; About/Topics вручную | Низкая — публикация |
| G-06 | OIDC, arq/Redis, полный Postgres hydration — post-pilot | Ожидаемо по плану |
| G-07 | Cross-doc на pilot fixture pack: 0 contradictions | Информационно — не overclaim на прод-данных |
| G-08 | `.[clash]` / `.[docling]` opt-in — нужна явная ops-документация у заказчика | Средняя |

## Рунглиш (инвентарь и политика)

**Допустимо (термины отрасли):** IFC, IDS, BCF, GUID, fixture, benchmark, smoke, sign-off, overlay, endpoint, pack.

**Исправлено в RU-доках:** смешение «operator-документация», «capability framing», «One-report smoke path» — в `10-academic-audit` добавлены русские формулировки рядом с терминами.

**Frontend/UI:** пользовательские строки без следов IDE; см. `frontend/src`.

## Документация vs код (расхождения)

| Утверждение | Факт |
|---|---|
| Macro F1 ≈ 0.86 | Подтверждено `evaluate_extraction` |
| 290+ тестов | 294 passed |
| 2D overlay «planned» в старом аудите §5.1 | **Уже в коде** (май 2026) — аудит §10 нужно обновлять |
| Fine-tuning production | **Нет** — только удалённый scaffold |
| Vision-language sign-off | **Нет** — порт `VisionDrawingAnalyzer`, deterministic PDF/OCR baseline |

## Рекомендации maintainer (после этой очистки)

1. Закоммитить изменения через `scripts/git_commit.ps1`.
2. Заполнить pre-pilot gate sign-off и создать тег `pilot-2026-pre`.
3. Обновить `docs/10-academic-audit-and-recommendations-ru.md` (статус overlay/smoke).
4. Триаж Dependabot PR.

## Команды воспроизведения

```powershell
cd AeroBIM\backend
.\.venv-pilot\Scripts\python.exe -m pytest tests -q
.\.venv-pilot\Scripts\python.exe -m ruff check src tests
.\.venv-pilot\Scripts\python.exe -m mypy src/aerobim --ignore-missing-imports
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
```
