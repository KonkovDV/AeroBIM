---
title: "Post-Pilot Go / No-Go Memo 2026"
status: template
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, decision]
---

# Post-Pilot Go / No-Go Memo (template)

Fill at pilot end (target: November 2026). Decision tree: [`post-pilot-fork-2026.md`](post-pilot-fork-2026.md).

## Summary

| Item | Value |
|---|---|
| Pilot window | YYYY-MM-DD → YYYY-MM-DD |
| Frozen tag | `pilot-2026-…` |
| Scope | fire + structure / other |

## KPI outcomes

| KPI | Target | Actual | Pass? |
|---|---|---:|---|
| Confirmed findings (TP rate) | ≥ 60% | | |
| Review time savings | ≥ 20% | | |
| Traceability (GUID + provenance) | ≥ 90% | | |
| Deterministic replay | pass | | |
| Engineer BCF adoption | qualitative go | | |

## Technical health

| Check | Status | Notes |
|---|---|---|
| Gates 1–3 held through pilot | | |
| No evidence rail regressions on frozen tag | | |
| 2D overlay smoke (`run_live_review_smoke`) | | |
| Macro F1 ≥ 0.70 on frozen tag | | |

## Decision

- [ ] **Go** — Branch A (enterprise rollout)
- [ ] **Partial** — narrow scope + spatial/quantity hardening
- [ ] **No-go** — Branch C (archive, keep open kernel)

## Rationale (5–10 sentences)



## Next 90 days (if Go)



## Next 90 days (if No-go)



## Sign-off

| Role | Name / org | Date |
|---|---|---|
| Engineering lead | | |
| Customer sponsor | | |
