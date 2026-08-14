<!-- claims-lint: allow-file reason="Clone-to-demo verification; NO_GO; live CLI 14.08 not customer accuracy" -->
---
title: "Проверка README clone-to-demo (14.08.2026)"
date: "2026-08-14"
claim_boundary: "Path and live CLI check. Fixture demo. Checkpoint NO_GO. Not customer accuracy."
---

# Clone-to-demo (15.1 / 15.3)

README EN §Quick Start и README RU §Быстрый старт называют одну команду:

`python -m aerobim.tools.run_demo_vertical_slice`

из каталога `backend/`, после `pip install -e ".[dev,raster,pdf-agpl]"`.

## Входы на диске

| Путь | Статус |
| --- | --- |
| `backend/src/aerobim/tools/run_demo_vertical_slice.py` | есть; fail-loud; пишет `artifacts/vertical-slice-demo/` |
| `samples/demo/vertical-slice-2026-08-11/manifest.json` | есть |
| `samples/demo/vertical-slice-2026-08-11/techlab-a101-wall-thickness.pdf` | есть |
| `samples/ifc/walls-multi-entity.ifc` | есть; IfcOpenShell fixture, **не** Renga |
| `backend/tests/test_demo_vertical_slice.py` | есть: HTML `#kt2-overlay`, PNG signature, `summary.passed=false` |
| `docs/evidence/drawing-overlay-smoke-2026-08/overlay-wall-thickness.png` | committed PNG |
| `docs/evidence/kt2-handoff-2026-08-11/vertical-slice/report.html` | snapshot **11.08**, секции `#kt2-overlay` **нет** — superseded; live CLI + [`../evidence/vertical-slice-demo-live-2026-08-14.md`](../evidence/vertical-slice-demo-live-2026-08-14.md) |

## Live CLI на этой машине (14.08, после среза 1.1)

Интерпретатор: `backend/.venv` · Python **3.13.7** (CI = 3.12; 3.12 locally missing).  
Команда завершилась **exit 0**. Это успешная **генерация** артефактов, не customer PASS.

Канонический каталог: `artifacts/vertical-slice-demo/` (gitignored). Повтор в `artifacts/vertical-slice-demo-run2/`.

| Поле | Значение |
| --- | --- |
| `git_sha` | `2e6654b9da0ced35afee42819e026b2414045530` (HEAD; working tree dirty during this session) |
| `checkpoint_verdict` | **NO_GO** |
| `summary.passed` | `false` |
| `outcome` | `failed` |
| `verification_status` | `NOT_PASS_EXPERT_REQUIRED` |
| `reproducibility_hash` | `3b404e15a805c91b2b79e593374b055c9ba56721337d1f4c64345737ae867be4` (stable across two runs) |
| overlay PNG sha256 | `9826281f83a1a5608a3bd88e7d4f4f52475a702c5f3c3a5b4100d05f05f6a349` (stable) |
| `run-manifest.json` sha256 | `6ff41196340e7592d85a863dbc48a2366d1116c5a5f55932539df2e486f483a1` (stable) |
| `LIMITATIONS.json` sha256 | `78877c146bb9525b866e9c18f3605fa819615b8f8bc49628a596ffc5f20e1965` (stable) |
| `report.json` / `report.html` / `findings.bcfzip` | **дрейф** `created_at` — сравнивать hash воспроизводимости, не сырые байты |

HTML содержит: `#kt2-claim-boundary`, `#kt2-overlay`, `#kt2-text-evidence` (150 mm / WALL-01), `#kt2-capabilities`, `#kt2-release`, `finding_id` / `source_id` / `evidence_refs`, `summary.passed=false`.

Видео **не** создавалось. Человек: [`KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md), due 2026-08-19.

## Что считать DoD

| Критерий плана | Вердикт 14.08 |
| --- | --- |
| Команда в README | **PASS** |
| Входы на месте | **PASS** |
| Overlay PNG в evidence | **PASS** (smoke 12.08) |
| Live exit 0 в этом сеансе | **PASS** (генерация; вердикт не PASS) |
| Snapshot HTML = текущий CLI | **FAIL** (устарел 11.08) — для показа брать live `artifacts/` |
| Checkpoint GO | **NO_GO** |
