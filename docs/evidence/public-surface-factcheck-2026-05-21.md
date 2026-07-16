---
title: "Public Surface Fact-Check 2026-05-21"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
---

# Public surface fact-check (2026-05-21)

Verification after language hygiene sweep: no AI vendor branding in active docs; `RasterDrawingAnalyzer` port rename; runglish split EN/RU.

## Commands (Windows, `backend/.venv-pilot`)

| Check | Command | Result |
|-------|---------|--------|
| Tests | `python -m pytest tests -q` | **299 passed**, 2 skipped |
| Lint | `python -m ruff check src tests` | pass (after `--fix`) |
| Extraction | `python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` | **PASS**, macro F1 ≈ **0.86** |

## Content sweep (active `docs/` root, not `archive/`)

| Pattern | Active docs hits |
|---------|------------------|
| `LLM`, `VLM`, `GPT`, `Cursor`, `Copilot` | 0 |
| `VisionDrawingAnalyzer`, `vision_drawing_analyzer` | 0 (code + docs aligned on `RasterDrawingAnalyzer`) |
| Marketing «AI product» | 0 (policy mentions avoidance only) |
| `learned-model` / `stochastic vision` in pilot SSOT | 0 (replaced with **non-deterministic**) |
| PyPI extra `vision` | 0 (renamed to **`raster`**) |

## Code rename

- Domain port: `RasterDrawingAnalyzer`
- DI token: `raster_drawing_analyzer`
- Adapter: `RasterDrawingAnalyzer` in `raster_drawing_analyzer.py`

## Language

- EN pilot/SSOT docs: English only
- RU: `README.ru.md`, `contributor-git-ru.md`, `pilot-case-study-report-ru.md`, `archive/10-academic-audit-and-recommendations-ru.md`
- Customer remark strings in `template_remark_generator.py`: Russian (locale output, not documentation)

## Frozen tag

`pilot-2026-pre` unchanged (`1a5c03e`).
