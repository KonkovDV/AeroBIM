---
title: "Samolet Pilot Protocol 2026"
status: active
version: "1.0.0"
last_updated: "2026-07-19"
claim_boundary: "Protocol only. Thresholds are parameters for customer agreement. Checkpoint NO_GO until RT-001/002/003."
---

# Pilot Protocol — ГК «Самолёт» × AeroBIM TechLab Task 07

## Goal

Evidence-driven bounded pilot: measure whether AeroBIM reduces expert verification effort on an agreed package **without false-green Shared-gate** and with full finding provenance.

## Non-goals

- Replace licensed engineer.
- Claim >90% / customer SLA / MEP delivered / native DWG / calc solver / CDE-ready BCF without artifacts.

## Agreed inputs (Phase 0 — blocking)

| Input | Owner | Notes |
|---|---|---|
| NDA + scope memo | Samolet + AeroBIM | Disciplines, stage П/Р, in/out of auto-check |
| Customer package (IFC/PDF/ТЗ/calc) | Samolet | `samples/customer/` local only — never git |
| Approved norm/IDS pack + approval object | Samolet | RT-002 |
| Federated MEP pack + clearance rules (if MEP in scope) | Samolet | RT-003 |
| ≥2 named adjudicators | Samolet | Dual-independent |
| Manual baseline hours | Samolet | Same package |

Intake gate: `aerobim-validate-customer-intake-gate` · [`../audit/evidence/customer-intake-gate.json`](../audit/evidence/customer-intake-gate.json).

## Threshold parameters (agree in writing — do not invent GO)

| Parameter | Suggested starting point | Binding? |
|---|---|---|
| Interim precision TP/(TP+FP) | ≥ 0.60 | Agree with Samolet |
| Critical-error recall | Agree per class | Agree |
| Cohen’s κ / Krippendorff’s α | ≥ 0.60 suggested | Agree |
| Package wall-clock | ≤ 30 min on **agreed** pack | Measure, then claim |
| Review-time reduction | ≥ 20% vs baseline | Measure |
| Max false-positive burden | Agree | Agree |

## Phases

```text
Phase 0  Agree corpus + rules + thresholds + frozen split
Phase 1  Manual baseline (hours, findings, cycles)
Phase 2  AeroBIM run offline (no production workflow influence)
Phase 3  Dual adjudication TP/FP/FN + κ/α
Phase 4  Controlled BCF handoff + import evidence (if in scope)
Phase 5  Expand / narrow / stop decision
```

### Phase 2 runtime

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/customer/<agreed-pack>.json \
  --output ../artifacts/pilot-evidence/<run-id>
```

Bundle must include: file hashes, report JSON/HTML, findings, capability coverage, timings, code version, reproduction README.

### Stop / narrow rules

Stop or narrow if: expert distrust; critical misses above threshold; unstable mandatory checks; missing provenance; time not scaling; no effect vs baseline; customer cannot supply corpus/rules.

## Roles

| Role | Responsibility |
|---|---|
| Tech lead | Runtime, evidence bundle, fail-closed profile |
| openBIM lead | IFC/IDS/clash/BCF |
| Adjudicators (≥2) | TP/FP labels; no LLM-as-adjudicator |
| Samolet sponsor | Scope memo; CDE import proof owner |
| Security | Closed-contour review before production data |

## Success / expansion

Expand only if: mandatory checks stable; findings have source+evidence; quality measured on frozen set; critical classes meet agreed recall; time measured on real pack; effect vs baseline documented.

Product checkpoint remains **NO_GO** until RT-001/002/003 close with evidence — engineering remediations do not flip checkpoint.
