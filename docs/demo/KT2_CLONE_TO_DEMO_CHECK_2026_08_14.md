<!-- claims-lint: allow-file reason="Clone-to-demo verification; NO_GO; not live pytest on this machine" -->
---
title: "Проверка README clone-to-demo (14.08.2026)"
date: "2026-08-14"
claim_boundary: "Path and contract check. Live CLI not re-run here (no backend/.venv). Checkpoint NO_GO."
---

# Clone-to-demo (15.1 / 15.3)

README EN §Quick Start и README RU §Быстрый старт называют одну команду:

`python -m aerobim.tools.run_demo_vertical_slice`

из каталога `backend/`, после `pip install -e ".[dev,raster,pdf-agpl]"`.

## Входы на диске (проверено 14.08)

| Путь | Статус |
| --- | --- |
| `backend/src/aerobim/tools/run_demo_vertical_slice.py` | есть; fail-loud; пишет `artifacts/vertical-slice-demo/` |
| `samples/demo/vertical-slice-2026-08-11/manifest.json` | есть |
| `samples/demo/vertical-slice-2026-08-11/techlab-a101-wall-thickness.pdf` | есть |
| `samples/ifc/walls-multi-entity.ifc` | есть; IfcOpenShell fixture, **не** Renga |
| `backend/tests/test_demo_vertical_slice.py` | есть: HTML `#kt2-overlay`, PNG signature, `summary.passed=false` |
| `docs/evidence/drawing-overlay-smoke-2026-08/overlay-wall-thickness.png` | committed PNG |
| `docs/evidence/kt2-handoff-2026-08-11/vertical-slice/report.html` | snapshot **11.08**, секции `#kt2-overlay` **нет** |

## Live CLI на этой машине

`backend/.venv` **отсутствует**. Повторный `run_demo_vertical_slice` здесь **не запускался**.  
Контракт e2e закрыт тестом на `main` (после `3341553`). Для видео 19.08 человек обязан прогнать команду на машине с venv.

## Что считать DoD

| Критерий плана | Вердикт 14.08 |
| --- | --- |
| Команда в README | **PASS** |
| Входы на месте | **PASS** |
| Overlay PNG в evidence | **PASS** (smoke 12.08) |
| Live exit 0 в этом сеансе | **SKIPPED** (нет venv) |
| Snapshot HTML = текущий CLI | **FAIL** (устарел) — для показа брать live `artifacts/` |
