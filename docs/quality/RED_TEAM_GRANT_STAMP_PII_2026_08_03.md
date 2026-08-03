---
title: "Red Team — Studio grant stamp/PII gate (2026-08-03)"
status: active
version: "1.0.0"
last_updated: "2026-08-03"
claim_boundary: "Self red-team. Checkpoint NO_GO. Not external audit. Not DPA."
---

# Red Team — Yandex Studio stamp/PII + claims (2026-08-03)

**Author relationship:** self  
**Scope:** region-restricted VLM stamp exclude · grant≠RT-001 Claims Lock · report reproducibility wording  
**Checkpoint:** **NO_GO**  
**Security review subagent:** no medium+ on diff; residuals below hardened or left OPEN

## Attack surface

| Threat | Path | Control |
|---|---|---|
| Signatory PII (ФИО) reaches Studio C0/C1 | region-crop of stamp → Base64 VLM | `exclude_stamp_regions=True` default; dual gate `layout_role=stamp` **or** ≥50% overlap with normalized stamp prior |
| Detector omits `layout_role` | future/alternate detector | bbox prior gate (`is_stamp_like_region`) |
| Operator flips exclude off via env | settings | **no env knob**; only constructor (tests / explicit DI) |
| Constructor False in DI | bootstrap | DI does not pass `exclude_stamp_regions=False` |
| Whole-sheet smoke bypass | `KimiVlmDrawingPipeline` | unchanged; fail-closed on pilot/production via `kimi_advisory_ready()`; not verdict path |
| Vendor log as sole audit | Studio request history not retrievable | adapter `prompt_sha256` / `response_sha256` + `x-client-request-id` (prior wave); AeroBIM audit is primary |
| Overclaim Checkpoint via grant | tracker / pitch | Claims Lock forbids «quota increase = RT-001 progress»; grant doc bottleneck table |

## Findings

| ID | Surface | Verdict |
|---|---|---|
| RT-STAMP-01 | Role-only exclude bypassed if `layout_role` missing | **MITIGATED** — dual gate + unit test unlabeled stamp bbox |
| RT-STAMP-02 | Content band false-positive exclude | **MITIGATED** — ≥50% area overlap with stamp prior; content (0,0)–(1,0.85) kept |
| RT-STAMP-03 | Page-pixel bbox mis-classified by prior | **MITIGATED** — prior applies only to normalized 0..1 boxes; pixel crops need explicit `layout_role=stamp` |
| RT-STAMP-04 | Exclude count invisible in result | **MITIGATED** — `SheetReadResult.stamp_regions_excluded` |
| RT-STAMP-05 | Title-block FIO still on C0/C1 | **OPEN** — title_block not excluded (needed for marks); treat as INTERNAL only / DPA or C2 for customer sheets with names in title block |
| RT-STAMP-06 | Heuristic prior ≠ customer sheet geometry | **OPEN** — validate on customer corpus before CONFIDENTIAL claims; until then PUBLIC/INTERNAL fixtures only |
| RT-CLAIM-01 | Grant tokens sold as RT-001 progress | **MITIGATED** — Claims Lock + grant bottleneck section |
| RT-CLAIM-02 | Model non-determinism blocks FAIR report | **MITIGATED** — Claims Lock / REPRO: verdict = deterministic core; annotation presented from provenance |
| RT-CLAIM-03 | Scenario 5.3 implies Checkpoint GO | **MITIGATED** — ENGINEERING_STATUS Checkpoint NO_GO; RT-001/002/003 external |

## Still open (external)

RT-001 / RT-002 / RT-003 · customer stamp-geometry validation · title_block PII policy · D-7 batch mode · live Studio multimodal 5.3 wiring · DPA for CONFIDENTIAL

## Verdict

Stamp/PII eng-gate **acceptable under Claims Lock** for PUBLIC/INTERNAL fixture crops. Checkpoint **NO_GO**. Do not claim RESTRICTED-safe Studio VLM without C2 or validated stamp+title PII controls.
