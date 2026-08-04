# Red Team — Jury pack + IFC-Bench v2 / model-diff (2026-08-04)

**Author relationship:** self  
**Scope:** Novator/TechLab jury docs + IFC-Bench v2 smoke + thin `IfcModelDiff`  
**Checkpoint:** **`NO_GO`** (unchanged)  
**Security subagent:** [Security Review](e01b2e2d-bf36-4db4-8291-dcf21e7c910f)

## Verdict

| Lane | Result |
|---|---|
| Application security (Critical/High) | **0** |
| Integrity (Medium) | **2 found → mitigated in this commit** |
| Claims Lock / jury framing | **PASS with notes** — no new >90% / MEP delivered / CDE-ready product claims |
| Customer Checkpoint | Still **NO_GO** (RT-001/002/003) |

## Findings

| ID | Sev | Status | Finding | Mitigation |
|---|---|---|---|---|
| RT-JURY-01 | MED | **MITIGATED** | IFC-Bench smoke: CSV `project` could path-escape `dataset_root/projects` | Containment check before open |
| RT-JURY-02 | MED | **MITIGATED** | Smoke exit 0 ignored SHA pin mismatch | `main()` returns 3 if pin fails |
| RT-JURY-03 | LOW | **MITIGATED** | Sprint2 tracker contradicted itself on v2 smoke | Done/Not-done lists reconciled |
| RT-JURY-04 | LOW | **MITIGATED** | Search results still said «Next: pin v2» | Updated to measured 7/1026 |
| RT-JURY-05 | INFO | OPEN | `IfcModelDiff` not HTTP-wired — add path jail before any upload/API path | Documented; matrix row 28 still MISSING |
| RT-JURY-06 | INFO | OPEN | Economic SAM A1/D-DOM need Dom.RF primary source before contest filing | Labeled assumptions only |
| RT-JURY-07 | INFO | OPEN | Team criterion 2.6 / builder name — cannot close in docs | External |

## Claims Lock spot-check

| Invariant | Status |
|---|---|
| No product >90% | Intact |
| AECV 0.4325 / fixture 0.86 separated (pitch + docs.md) | Intact |
| NO_GO framed as customer sign-off, not «system dead» | Intact (README.ru) |
| Competitive matrix has honest lose rows | Intact |
| Economic model = labeled forecast, not proven ROI | Intact |
| Thin IFC diff ≠ CDE version compare | Intact (fn28) |
| KAAN do-not-vendor | Intact |

## Residual risks for jury

1. Cherry-picking `exact_match_rate_on_scored: 1.0` without `7/1026` denominator.  
2. Showing README EN first screen (`NO_GO` banner) instead of jury pack / README.ru.  
3. Treating LOI template as signed letter.

## Not claimed closed

RT-001, RT-002, RT-003, Rospatent filing, builder-in-team, Dom.RF figure verification.
