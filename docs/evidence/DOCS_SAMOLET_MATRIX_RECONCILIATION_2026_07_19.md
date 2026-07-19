---
title: "docs.md §3.1 matrix reconciliation + TECHLAB partners diff"
status: active
version: "1.0.0"
last_updated: "2026-07-19"
checkpoint: NO_GO
tags: [aerobim, docs, samolet, claims, reconciliation]
---

# Reconciliation — 2026-07-19

**Sources:** `docs/docs.md` §3.1 · `docs/samolet.md` · `docs/partners/TECHLAB_*` · current code (branch tip at write time).  
**Checkpoint:** **NO_GO** (RT-001/002/003).

---

## 1. docs.md §3.1 ↔ code

| # | Claim | Docs | Code | Verdict |
|---|---|---|---|---|
| 1 | IFC2x3 / IFC4 / IFC4x3 | covered scenarios | `basic_ifc_schema_validator` + `ifc-compatibility-matrix.md` | ALIGNED |
| 2 | IFC props / quantities | covered rules | IfcOpenShell validator + quantity adapter | ALIGNED |
| 3 | IDS | covered scenarios | IfcTester adapter + e2e tests | ALIGNED |
| 4 | Cross-source compare | base mechanism | section pairing / cross-doc contour | ALIGNED |
| 5 | PDF / OCR | base contour | PyMuPDF / RapidOCR (raster extra) | ALIGNED |
| 6 | Geometric clash | analyzer + required profile | clash detector; **`require_clash` SSOT = `capability_policy.py`** | ALIGNED after path fix (was STALE → `signoff_policy.py`) |
| 7 | Finding provenance | model-level | `finding_provenance.py` | ALIGNED |
| 8 | BCF 2.1 export | export | primary 2.1 exporter; **3.0 experimental also exists** | ALIGNED (+ clarified in docs.md) |
| 9 | >90% | pilot goal | RT-001 / precision harness | ALIGNED |
| 10 | ≤30 min | pilot goal | `measure_package_sla.py` (fixture ≠ customer) | ALIGNED |
| 11 | MEP system clash | not confirmed | unconfigured provider / NOT_VERIFIED | ALIGNED |
| 12 | Native DWG | not confirmed | ODA stub / MISSING | ALIGNED |
| 13 | Independent calc | not separate path | `calculation_correctness` NOT_IMPLEMENTED | ALIGNED |
| 14 | BCF → CDE import | not confirmed | structural verify / push ≠ import | ALIGNED |

`CRITICAL_BLOCKERS.md` — **exists** (source link in docs.md is valid).

---

## 2. Document roles (no ownership conflict)

| Doc | Audience | Owns |
|---|---|---|
| `docs.md` | Jury / TechLab | Narrative + claims matrix for defense |
| `samolet.md` | Internal strategy | Why Samolet, wedge, Q&A, GO-for-pilot |
| `partners/TECHLAB_TASK_07_READINESS_2026.md` | Ops / application pack | Requirement → status vocabulary |
| `partners/TECHLAB_SAMOLET_APPLICATION_2026.md` | Form copy | Short EN/RU blurbs + pilot criteria |
| `partners/AEROBIM_STRATEGIC_ASSESSMENT_2026_07.md` | Positioning | Canonical / forbidden claims |

---

## 3. Diff vs `partners/TECHLAB_*` (duplicates & drift)

### Aligned (keep both; different depth)

| Theme | docs.md / samolet.md | TECHLAB_* |
|---|---|---|
| Expert remains accountable | Central | Central + sponsor quote |
| Fail-closed / AI not owner of pass | docs §5.1, samolet §3.4 | readiness §2 |
| NO_GO / RT blockers | Implicit + sources | Explicit checkpoint header |
| File-first wedge before 10D API | samolet §6 | readiness “demo path” |
| MEP / DWG / >90% honesty | Matrix + limitations | Form field “Подходы” + Claims Lock |

### Duplicates (intentional, not merge)

- “Не заменяем инженера / 10D” — repeated in docs.md, samolet.md, readiness, application, strategic assessment.
- Pilot asks (corpus, 2 adjudicators, norms, BCF import) — samolet §6.3 ≈ readiness §3 “Needs Samolet”.
- Competitor framing (Solibri / Navisworks / BIMcollab) — docs §7 ≈ samolet §5 ≈ strategic assessment.

**Policy:** jury narrative stays in `docs.md`; ops vocabulary stays in readiness; do not collapse into one file.

### Drift to fix later (not silent)

| Item | Where | Issue | Action |
|---|---|---|---|
| Clash default for pilot | `TECHLAB_TASK_07_READINESS` § Pilot env | Says “defaults keep clash optional”; after RT-POST-01 non-dev/production defaults **fail-closed production signoff** | Update readiness env note to: unset `AEROBIM_SIGNOFF_PROFILE` under `AEROBIM_ENV=production` ⇒ production profile; use `development`/`fixture` only for local soft gates |
| Interim precision ≥60% | readiness / application success criteria | docs.md / samolet.md emphasize methodology, not the 60% interim number | Keep 60% as **pilot contract interim** only; never promote to public accuracy claim |
| Architecture layers | docs.md “five levels” | TARGET hybrid also describes four contours | Layers (clean arch) ≠ contours (runtime); both valid — add cross-link if jury asks |
| BCF versions | readiness “2.1/3.0 export” | docs.md historically “2.1” only | Clarified in docs.md §3.1 |
| Prize / 2M ₽ | TECHLAB only | Absent from docs.md / samolet.md | Correct for jury technical memo (commercial detail stays in partners) |

### Stale in TECHLAB readiness (recommend edit)

```bash
# OLD (misleading after production signoff default):
# "Defaults keep clash optional so fixture/dev installs without .[clash] stay green."

# PREFERRED wording:
# Development/fixture profiles keep soft gates for local installs.
# AEROBIM_ENV=production (or SIGNOFF_PROFILE=samolet_pilot|production) forces
# require_clash / require_bsi_schema / require_mep_system_clash fail-closed.
```

---

## 4. Verdict

- **docs.md §3.1:** claim statuses match code; one path stale fixed (`capability_policy`).
- **SSOT index:** `docs.md` + `samolet.md` registered in `docs/README.md` and `TIER0_INDEX.md`.
- **TECHLAB_*:** no contradictory overclaim vs docs/samolet; residual drift is env-profile wording and interim 60% metric ownership.
- Overall product checkpoint remains **NO_GO**.
