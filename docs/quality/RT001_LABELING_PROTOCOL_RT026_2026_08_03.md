---
title: "RT-001 labeling protocol (RT-026) — preregistration draft"
status: draft
version: "0.1.0"
last_updated: "2026-08-03"
claim_boundary: "Protocol draft only. No corpus measured. Checkpoint NO_GO. Not a κ claim."
---

# RT-001 labeling protocol (RT-026)

**Purpose:** make RT-001 inter-rater metrics defensible **before** Samolet corpus lands.  
**Status:** draft for preregistration — freeze schema before first labeler sees cases.

## Scope

| In | Out |
|---|---|
| Customer package findings: presence / severity / category / GUID link (where claimed) | Product accuracy >90% marketing |
| Dual-rater + adjudicator on stratified sample | Whole-corpus labeling as day-1 requirement |
| Pre-registered metrics: Krippendorff α (primary), Gwet AC1 (imbalance), κ (secondary only) | κ>0.8 as sole acceptance without n / strata / CI |

## Sample size (planning)

1. Fix **minimum detectable effect** and **expected prevalence** per stratum before drawing the sample.  
2. Use Wilson / binomial planning already in WP-07 quality protocol (interim 0.60) as the volume calculator SSOT — do not invent a second planner.  
3. Record planned `n`, power assumptions, and stop rule in the run manifest **before** labeling starts.  
4. If prevalence is unknown: two-phase — pilot `n₀` (≤30) for prevalence estimate, then lock final `n`.

## Stratification (required)

| Axis | Levels (minimum) |
|---|---|
| Discipline | AR / ST / MEP (or pack-declared) |
| Criticality | error vs warning (Shared-gate relevant) |
| Modality | IFC-only / drawing / cross-doc |
| Claimed GUID | claimed present / absent / N/A |

Empty stratum → document and do not pool silently into κ.

## Schema freeze

- Label schema versioned (`schema_version`, JSON Schema path) **before** first rater opens a case.  
- Changes after start → new schema version + restart agreement on affected items (no silent remap).  
- Adjudication codes: `agree` / `rater_a` / `rater_b` / `unresolved` (align `build_detection_labels`).

## Raters & adjudication

- ≥2 independent raters; third adjudicator on disagreements only.  
- Blind to model/advisory output; deterministic report fields only.  
- Training: 5–10 gold items (not in scored sample); pass bar recorded.  
- Timing: no joint discussion of scored items until both submit.

## Metrics (report all three)

| Metric | Role | Note |
|---|---|---|
| **Krippendorff α** | Primary | Already in repo tooling (`measure_adjudicator_agreement`) |
| **Gwet AC1** | Imbalance-robust | Required when class skew high (κ paradox) |
| **Cohen/Fleiss κ** | Secondary | Never sole gate; report prevalence + CI |

Also report: raw agreement, per-stratum α, Wilson CI on prevalence, adjudication rate.

## Acceptance (eng gate, not Checkpoint GO)

Draft bar for **protocol completeness** (not product claim):

- Schema frozen + prereg file committed  
- `n` and strata filled  
- Dual-rater + adjudication path executed on pilot  
- α and AC1 reported with CI / bootstrap note  

**Customer Checkpoint** still needs RT-001 corpus delivery + this protocol executed on that corpus. This draft alone does **not** close RT-001.

## Forbidden claims

- «κ>0.8 ⇒ quality OK» without n, strata, prevalence, CI  
- Pooling unbalanced classes then citing κ only  
- Post-hoc schema edits without version bump  
- Using advisory/LLM text as rater ground truth  

## Artifacts to produce (when corpus arrives)

1. Copy/fill `samples/benchmarks/rt001-preregistration-template.json` → `artifacts/rt001/preregistration.json`  
2. Label export + agreement report (α, AC1, κ) via `measure_adjudicator_agreement` (schema 1.2+)  
3. Pointer from evidence bundle / run manifest  

## Owners

| Role | Responsibility |
|---|---|
| Eng | Tooling, schema, agreement CLI, prereg template |
| Customer | Corpus access, rater nomination, adjudication SLA |
| Claims Lock | No accuracy slide until prereg + report exist |
