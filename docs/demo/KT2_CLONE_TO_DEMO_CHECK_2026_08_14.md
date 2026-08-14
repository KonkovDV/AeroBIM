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
| `git_sha` | `d809d3677492c988d35024e9e06664ae7f949b89` (`working_tree_dirty=false`) |
| `checkpoint_verdict` | **NO_GO** |
| `summary.passed` | `false` |
| `outcome` | `failed` |
| `verification_status` | `NOT_PASS_EXPERT_REQUIRED` |
| `reproducibility_hash` | `f67038c00578fae123f4ecfcbe05cc536382cb445a9f0364513590d92225fa6d` (stable across two clean runs; binds `code_version`) |
| overlay PNG sha256 | `9826281f83a1a5608a3bd88e7d4f4f52475a702c5f3c3a5b4100d05f05f6a349` (stable) |
| `run-manifest.json` sha256 | `0ff1f6d085c8306edd85469f967be87051617da622955e3724f948983edd8c56` (stable across two clean runs) |
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
