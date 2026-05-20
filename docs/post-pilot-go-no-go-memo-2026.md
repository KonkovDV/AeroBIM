---
title: "Post-Pilot Go / No-Go Memo 2026"
status: template
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, decision]
---

# Post-Pilot Go / No-Go Memo (template)

Fill at pilot end (target: November 2026). Decision tree: [`post-pilot-fork-2026.md`](post-pilot-fork-2026.md).

## Readiness checklist (complete before November memo)

| Prerequisite | Source |
|---|---|
| Pre-pilot gates 1–4 signed | [`pilot-pre-pilot-gates-2026.md`](pilot-pre-pilot-gates-2026.md) |
| Frozen tag `pilot-2026-pre` | [`pilot-frozen-tag-protocol-2026.md`](pilot-frozen-tag-protocol-2026.md) |
| Weekly logs W1–Wn filled | [`pilot-weekly-log-2026.md`](pilot-weekly-log-2026.md) |
| Case study KPI table | [`pilot-case-study-report-2026.md`](pilot-case-study-report-2026.md) |
| Claim boundary respected | [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) |

## Summary

| Item | Value |
|---|---|
| Pilot window | YYYY-MM-DD → YYYY-MM-DD (target end: 2026-11) |
| Frozen tag | `pilot-2026-pre` @ `1a5c03e`; optional `pilot-2026-final` |
| Scope | fire + structure (pilot default) |
| Start package | [`pilot-start-package-2026.md`](pilot-start-package-2026.md) |

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
| Macro F1 ≥ 0.70 on frozen tag | pre-pilot: **0.86** | re-run on final SHA |

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
