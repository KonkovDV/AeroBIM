# KAAN Architecten IFC license — honesty record

**Date:** 2026-08-04  
**Status:** **PARTIAL — do not vendor**  
**Claim level:** inventory only; `closes_rt001=false`

## What was checked

| Source | Finding |
|---|---|
| BatchPlan paper (CAADRIA 2024 / TU Delft PDF) | Dev/test used **6** KAAN Architecten residential projects (not a redistributed «800+ open IFC» corpus) |
| BatchPlan tool (`github.com/byildiz/BatchPlan`) | **MIT** — software only |
| KAAN project IFC / plans themselves | **No primary open-content license URL found** in paper, GitHub README, or PyPI packaging; firm copyright applies unless KAAN publishes otherwise |

## Decision

- Do **not** copy KAAN project IFC into `samples/` or public evidence.  
- Treat «KAAN residential» as **research citation / contact path**, not open corpus.  
- Prefer redistributable IFC (IFC-Bench non-GPL subset, OSArch examples after license read) for planted-defect pipelines.

## Primary URLs (for re-check)

- https://github.com/byildiz/BatchPlan  
- https://papers.cumincad.org/data/works/att/caadria2024_514.pdf  
- https://repository.tudelft.nl/record/uuid:2899ea54-d769-4154-bb04-3c95b018a194  

Re-open only if KAAN publishes an explicit open license for the project files.
