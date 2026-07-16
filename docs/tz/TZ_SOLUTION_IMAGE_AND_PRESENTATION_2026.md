---
title: "AeroBIM TZ Solution Image and Presentation 2026"
status: active
version: "1.0.0"
last_updated: "2026-07-10"
tags: [aerobim, tz, presentation, demo]
---

# TZ Solution Image and Presentation

Fills **«Образ финального решения»** and **«Требования к презентации»**.
Score ladder companion: [`../samolet-techlab-scorecard-2026.md`](../samolet-techlab-scorecard-2026.md).

## 1. Solution image (MVP)

**One sentence:** AeroBIM is a browser-assisted, openBIM-native expert co-pilot that cross-checks IFC, IDS, TZ, calculations, and drawings, highlights problem zones, and exports BCF — with the engineer remaining accountable.

### User-visible surfaces

1. **Ingest** — project package (IFC + IDS + specs + calcs + drawings); multipart upload (P0).
2. **Analyze** — deterministic multimodal report with explicit `capabilities`.
3. **Review** — 3D IFC viewer + 2D drawing overlay + prioritized issue list + editable remarks (P0).
4. **Handoff** — JSON / HTML / BCF 2.1 (3.0 opt-in) into the customer CDE.

### What the jury should see as “done”

| Verified | Roadmap (say so) |
|----------|------------------|
| IFC + IDS + cross-doc | Full SP/GOST corpus |
| Clash capability (opt-in) | MEP-specific rule sets |
| OCR baseline on PDF/raster | True CV layout models |
| RU template remarks (+ EN P0) | LLM auto-remarks without HITL |
| ≤30 min on **agreed** pack | Universal production SLA |
| Pilot TP ≥60% protocol | Published >90% without labels |

## 2. Demo script (8–12 minutes)

| Step | Action | Success signal |
|------|--------|----------------|
| 1 | Open review shell; show auth if non-dev | `/health` + report list |
| 2 | Run or load agreed package analysis | Report `passed` / issue counts |
| 3 | Open issue with `problem_zone` | 2D overlay rectangle |
| 4 | Select clash / GUID issue | 3D isolate |
| 5 | Show generated remark; edit & save (P0) | `review-events` accepted |
| 6 | Export BCF | Download ZIP / hub push if configured |
| 7 | Show claim boundary slide | Honest non-claims |

Pack suggestion: `samples/benchmarks/project-package-pilot-moscow-v1.json` or customer pack after intake.

## 3. Slide outline (6–8)

1. **Problem** — manual review cost, risk, expert bottleneck  
2. **Solution** — AeroBIM as acceptance-criteria co-pilot  
3. **Architecture** — openBIM stack (IFC/IDS/BCF) + multimodal fusion  
4. **Live demo** — overlay + clash + remark  
5. **Evidence** — F1 gate, SLA fixture, ablation table  
6. **KPI protocol** — 60% interim → path to 90% with adjudication  
7. **Roadmap** — P0–P4 (upload, DWG, CV/LLM advisory)  
8. **Ask** — pilot corpus + CDE week-1 + engineer adjudicators  

## 4. Presentation constraints

- One language per slide deck (EN or RU) — see [`../LANGUAGE-POLICY-2026.md`](../LANGUAGE-POLICY-2026.md).
- No revenue or “replaces Solibri” claims.
- Every metric cites `docs/evidence/` or live command.
- Screenshots from `run_live_review_smoke` preferred over mockups.

## 5. Final solution checklist (MVP exit)

- [ ] Compliance matrix rows for MVP marked `done` or accepted `partial`
- [ ] P0 upload + remarks UI shipped
- [ ] SLA green on agreed pack
- [ ] Adjudication log started (even if n small)
- [ ] Claim boundary reviewed with customer
