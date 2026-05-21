---
title: "Samolet Compliance Scorecard 2026 (10/10 closure)"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, samolet, compliance, scorecard]
---

# Samolet compliance scorecard — closure SSOT

**Rule:** overall **10.0** only when every row is **≥ 9** with linked evidence and sign-off.

| ID | Requirement | Score | Evidence path | Sign-off |
|----|-------------|------:|---------------|----------|
| R1 | 2D drawings | 7 | overlay smoke; customer PDF TBD | [ ] |
| R2 | BIM models | 9 | pytest, IDS/IFC | [x] repo |
| R3 | TZ + calculations | 8 | F1 evidence | [x] repo |
| R4 | Norms | 6 | `samolet-*-rules.txt` | [ ] customer |
| R5 | Collisions | 7 | clash policy doc | [ ] week1 |
| R6 | Areas/dimensions | 8 | cross-doc engine | [ ] pilot |
| R7 | Logic/missing | 8 | IDS operators | [x] repo |
| R8 | Problem zones | 8 | 2D overlay | [x] repo |
| R9 | Prioritization | 8 | `AEROBIM_PRIORITY_PROFILE=samolet` | [x] repo |
| R10 | Comments | 7 | remark + BCF | [x] repo |
| R11 | Faster review | 6 | KPI memo TBD | [ ] customer |
| R12 | Expert in loop | 10 | claim boundary | [x] |
| R13 | MVP + reports | 9 | API/BCF/HTML | [x] repo |
| R14 | Typical errors | 4 | catalog + `map_typical_errors` | [ ] customer |
| R15 | SLA ≤ 30 min | 7 | fixture SLA JSON | [ ] customer pack |
| CDE | BCF roundtrip | 5 | [`pilot-cde-handoff-2026.md`](pilot-cde-handoff-2026.md) | [ ] week1 |

## KPI gates (Wave 2)

| KPI | Target | Value | Pass |
|-----|--------|------:|------|
| Confirmed findings | ≥ 60% | TBD | [ ] |
| Review time saved | ≥ 20% | TBD | [ ] |
| Traceability | ≥ 90% | TBD | `audit_issue_traceability` |
| Package SLA | ≤ 30 min | TBD | `measure_package_sla` |

## Signed artifacts (fill at closure)

- [ ] KPI memo (PDF/MD, joint sign)
- [ ] `docs/evidence/internal/samolet-sla-customer-*.json` (gitignored)
- [ ] `docs/evidence/internal/cde-import-proof/` (gitignored)
- [ ] Case study: [`pilot-case-study-report-2026.md`](pilot-case-study-report-2026.md)
- [ ] Demo-day deck (external)

## Overall

| Metric | Value |
|--------|------:|
| **Weighted score today** | **7,6** |
| **Target at demo-day** | **10,0** |

Update scores in this file after each pilot week; do not move tag `pilot-2026-pre` without material-change protocol.
