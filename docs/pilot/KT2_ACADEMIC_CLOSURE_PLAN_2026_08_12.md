<!-- claims-lint: allow-file reason="Academic KT#2 plan; forbidden accuracy phrases only as non-claims / protocol bounds" -->
---
title: "КТ#2 — академический план закрытия окна (→ 20.08.2026)"
date: "2026-08-12"
status: active
version: "1.0.0"
head_at_authoring: "518c5f5"
claim_boundary: "Plan + literature alignment. Fixture GO ≠ Checkpoint GO. Not customer >90%. Not native DWG / MEP delivered / OIDC BFF production."
---

# КТ#2 academic closure plan (12–20.08.2026)

## 0. Epistemic frame

| Layer | Question | Allowed evidence |
| --- | --- | --- |
| L0 Code capability | Does the contour run fail-closed? | Tests, evidence bundles, verify gates |
| L1 Fixture evidence | Reproducible on in-repo packs? | `kt2-handoff-*`, clash/overlay STATUS |
| L2 Open benchmark | Comparable on public corpora? | Open-bench / IFC-Bench pins (not product) |
| L3 Customer evidence | Publishable precision / SLA / CDE? | **Blocked** until RT-001/002/003 |
| L4 Contract / Fund | TechLab KPIs + MIK act | Customer + Fund signatures |

**Theorem for KT#2:** intermediate version = **L0+L1 (+ L2 optional)** under Claims Lock.  
Flipping Checkpoint GO without L3 is a **protocol violation**, not an engineering win.

### External anchors (verified Aug 2026 pass)

| Practice | Source | Implication for AeroBIM |
| --- | --- | --- |
| IDS 1.0 machine-checkable requirements (approved Jun 2024; active standard) | [buildingSMART IDS](https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/) | Keep IDS fail-closed; customer pack = RT-002 |
| IDS → IFC check → BCF issue loop on CDE | Tomczak et al., *Buildings* 15(3):378 (2025) | BCF T2 in **customer CDE** remains the missing link |
| BCF 3.0 + OpenCDE Foundation API | [buildingSMART BCF](https://www.buildingsmart.org/standards/bsi-standards/bim-collaboration-format/), BCF-API 3.0 | Export ≠ CDE import proof |
| Dual-rater adjudication; Krippendorff α | Label Studio / Encord guides (2025); convention α≥0.67 tentative, ≥0.80 preferred | Matches pilot instruction κ/α gates |
| Reproducible BIM-QA evaluation + α reporting | Hellin-Fuchs et al., EC3 2026 (TUM) | Prefer published α + held-out + FN tracking before any product claim |
| Deterministic verdict ≻ LLM advisory | Industry ACC practice + ADR-001 | VLM never sets `summary.passed` |

**Skip claim:** this plan does **not** assert that web sources were exhaustively crawled; citations above are primary standards + 2025–2026 peer venues used for design alignment.

---

## 1. Tri-source requirements → KT#2 deliverable

| Source | KT#2 expectation | Repo SSOT | Closure mode by 20.08 |
| --- | --- | --- | --- |
| **Самолёт ТЗ v2** | Intermediate scenario, measurable method, honest KPI interim 0.60 | `docs/tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md` | Methodology + fixture |
| **Техлаб Task 07** | 5 pilot success criteria defined | `docs/partners/TECHLAB_TASK_07_READINESS_2026.md` | Criteria ENG_READY; numbers L3 |
| **МИК** | M3 program, M4 schedule, M5 metrics, M6 protocols | `docs/partners/MIK_PILOT_COMPLIANCE_2026.md` | M3–M6 ENG_READY; M2/M7/M8 owner |

Detailed row map: [`../tz/KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md`](../tz/KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md).

---

## 2. Work packages (implementable without inventing customer data)

| WP | Objective | Acceptance | Owner lane |
| --- | --- | --- | --- |
| **WP-A** Academic alignment pack | This plan + tri-source matrix + literature table | Files merged; Claims Lock clean | docs |
| **WP-B** Handoff verify gate | `aerobim.tools.verify_kt2_handoff` exit 0 on green fixture pack | Targeted unittest + CLI | eng |
| **WP-C** Refresh L1 evidence | Re-run wall-guid verify, vertical slice pin, clash/overlay STATUS | STATUS.json updated 2026-08-12 | eng |
| **WP-D** Red Team KT#2 | Independent recheck report; no silent GO | `docs/audit/RED_TEAM_KT2_HANDOFF_2026_08_12.md` | audit |
| **WP-E** Calendar hygiene | N43 reminder 17.08; forbid RUF100/FE lint before 19.08 | Freeze recheck pointer | gov |

**Explicitly out of scope until customer intake:** publishable precision, customer SLA, BCF-in-CDE T2 screenshots, MEP=OK, OIDC Phase 3, native DWG product.

---

## 3. Measurement protocol (academic)

For any precision number shown at KT#2:

1. State **corpus_kind** ∈ {fixture, synthetic, open, customer}.  
2. State **n**, **adjudicators**, **held_out**, **FN tracked**.  
3. Report **κ and/or α** when dual-rater; if α missing, say so.  
4. Refuse publishable gate unless protocol satisfied (`--require-publishable` exit 1 on synthetic).  
5. Prefer wording: *geometric intersection of extents / measured P/R at n* — never «коллизия по ТЗ >90%».

Fixture clash currently: AABB extents, n=5, fixture_only (L1 only).

---

## 4. Day plan 12→20.08

| Date | Action |
| --- | --- |
| **12.08** | Land WP-A…D; push signed tip |
| **13–16.08** | TZ-only: keep clash/overlay honest; if Samolet IFC arrives → start dual-blind labels (do not invent) |
| **17.08** | N43 baseline lag=1 rehearsal |
| **18–19.08** | Dry-run 30–40 min jury script from handoff cover |
| **20.08** | KT#2 meeting: fixture GO + NO_GO speech + intake ask |
| **≥19.08 evening** | Only then RUF100 / FE lint backlog |

---

## 5. Success criteria for “КТ#2 closed as intermediate version”

| # | Criterion | Gate |
| --- | --- | --- |
| 1 | Handoff pack present + verify CLI green | `verify_kt2_handoff` |
| 2 | Evidence bundle tamper-check passed | `verify_evidence_bundle` |
| 3 | Publishable gate fails on synthetic | exit 1 |
| 4 | Clash/overlay STATUS fixture_* | JSON |
| 5 | Tri-source alignment doc + academic plan | this tree |
| 6 | Red Team report says NO_GO remains | audit md |
| 7 | No Claims Lock / matrix-guard violations | CI scripts |

**Non-criteria (must remain open):** RT-001/002/003, M7 act, customer >90%, CDE T2.

---

## 6. Risks

| Risk | Mitigation |
| --- | --- |
| Jury hears fixture P/R as product | Cover note + STATUS `checkpoint_verdict=NO_GO` |
| Pressure to “close GO” | Refuse; cite CRITICAL_BLOCKERS |
| Infra thrash before 19.08 | Freeze protocol deferrals |
| Literature overclaim | Cite standards; mark unverified legal/Fund items VERIFY_WITH_OPERATOR |
