---
title: "What Samolet Must Supply for Task 07 Pilot (July 2026)"
status: active
version: "1.0.0"
last_updated: "2026-07-10"
tags: [aerobim, samolet, intake, techlab]
---

# What Samolet must supply (Task 07 pilot)

English SSOT mirror of the customer ask.  
**Russian handoff version (send to Samolet):** [`SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](SAMOLET_WHAT_WE_NEED_2026_07-ru.md).

## One-screen summary

| Ask | Why | Blocked without it |
|-----|-----|--------------------|
| One agreed PD/RD + IFC + brief + calcs + 2D pack | SLA + quality measurement | No pilot KPI |
| Agreed rule set (not “all codes”) | Machine-readable acceptance (IDS) | No acceptance criteria |
| ≥20 typical-error patterns with examples | Remark calibration | Catalog stays scaffold |
| ≥2 adjudicating engineers + manual baseline hours | TP/FP and time-saved KPI | Cannot claim accuracy / −20% time |
| CDE name + BCF version + pilot project | Issue handoff loop | No Solibri/BIMcollab-class close |
| Signed scope memo | Disciplines, stages, non-goals (CV/full GOST) | Scope creep |

## Practice anchors (July 2026)

| Source | Implication for Samolet ask |
|--------|-----------------------------|
| ISO 19650 EIR + acceptance criteria (UK BIM Framework / ACCA) | Client must define checkable criteria; IDS automates structured IFC checks |
| ISO 19650 DIS 2026 (EIR→IPR draft) | Pilot uses current EIR+IDS wording; do not wait for final IM rename |
| buildingSMART IDS 1.0 + BCF loop | Provide IDS (or property table) + CDE for BCF import |
| W78 2024 IDS limits | Separate alphanumeric IDS from geometric clash; do not demand CV as MVP gate |
| VDC 2026 KPIs / clash FP noise | Measure confirmed findings (TP≥60% interim), not raw clash count |
| RU: GRC 57.5/57.7, PP 331/614, SP 333, CIM hardening 2026-03 | Real IFC export + IM requirements in brief; CIM↔PD mismatches are in-scope |
| RU expertise practice | PD↔RD consistency is a first-class Task 07 pilot case |

## Mapping to AeroBIM readiness

AeroBIM already ships the checker, review UI, upload, BCF, HITL remarks, SLA rail.  
Samolet supplies **truth boundaries**, **corpus**, and **people** — see RU doc for full checklists (blocks A–E) and week-1 copy-paste list.

## Related

- [`TECHLAB_TASK_07_READINESS_2026.md`](TECHLAB_TASK_07_READINESS_2026.md)  
- [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md)  
- [`../../audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md)

## Drawing AI posture (retained local SSOT)

July 2026: [../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
