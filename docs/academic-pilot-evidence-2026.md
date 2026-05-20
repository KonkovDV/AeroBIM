---
title: "AeroBIM Academic Pilot Evidence 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, academic, evidence, pilot, openBIM]
---

# Academic Pilot Evidence Dossier (May 2026)

## Abstract

AeroBIM implements a **deterministic, provenance-aware, multimodal BIM quality-assurance kernel** aligned with openBIM delivery practice (IFC, IDS 1.0, BCF 2.1) and emerging information-management framing (ISO/DIS 19650-1:2026). This dossier records reproducible evidence for an 8–12 week developer / design-institute pilot — not a claim of full regulatory automation.

## Theoretical grounding

| Theme | Source (May 2026 baseline) | AeroBIM instantiation |
|---|---|---|
| Automated code checking (ACC) | Alnuzha et al., ITcon 2025 SLR — hybrid rule + ML | Rule-first narrative extraction; ML/FT deferred until P/R gated |
| IFC reliability | IFC-QA benchmark — grounding failures dominate LLM-only paths | Deterministic IFC/IDS kernel; LLM outside sign-off |
| Delivery contracts | buildingSMART IDS 1.0 | First-class IDS validation via IfcTester |
| Issue handoff | BCF 2.1 (default), BCF 3.0 opt-in | Export with GUID + viewpoint metadata |
| Information management | ISO/DIS 19650-1:2026 (IM terminology) | Optional `stage`, `revision`, `doc_status`, `information_container_id` |
| LOIN | ISO 7817-1 (referenced in 19650 draft) | Documented per-check purpose/milestone/actor in pilot playbook |

## Reproducibility package

| Artifact | Command / path |
|---|---|
| Unit + integration tests | `pytest tests -q` (use `backend/.venv-pilot`) |
| Runtime evidence | `python -m aerobim.tools.export_runtime_baseline` → `var/reports/aerobim_runtime_benchmark_report_v1.json` |
| Project-package benchmark | `python -m aerobim.tools.benchmark_project_package --pack ../samples/benchmarks/project-package-pilot-moscow-v1.json` |
| Extraction P/R/F1 | `python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` |
| Ground truth | `samples/benchmarks/russian-aec-ground-truth.json` |
| Gate profile | `samples/benchmarks/benchmark-extraction-quality.json` |

### Extraction metrics (deterministic baseline)

Evaluated with `NarrativeRuleSynthesizer` + `russian_aec_narrative_patterns.py` (auditable regex inventory, no LLM).

Target gate: **macro F1 ≥ 0.70** (docs/13-academic-execution-plan-2026.md, Iteration C.4 advisory).

Observed baseline (2026-05-20, isolated venv): macro F1 ≈ **0.86** on the Russian AEC corpus (10 fixtures, 50 ground-truth requirements). CI enforces macro F1 ≥ 0.70 via `evaluate_extraction`.

## Pilot scope (narrow by design)

- **Package:** `project-package-pilot-moscow-v1` — fire-safety + structure over shared IFC fixture
- **Normative context:** RF BIM documentation pressure (PP RF №331) — pilot validates **workflow**, not entire code corpus
- **Excluded from pilot sign-off:** VLM, FT models, full CDE, autonomous agents

## Evidence claims (C2 — repository-verified)

1. Multimodal analyze path: IFC + IDS + narrative + calculation + drawing annotations.
2. ISO 19650-lite context persisted and exported in HTML when provided.
3. OpenRebar SHA-256 provenance chain with `advisory` / `enforced` policy modes.
4. Browser review: `web-ifc` + persisted `ProblemZone` overlay contract.
5. Extraction evaluation harness with published ground-truth manifest.

## Non-claims

See [pilot-claim-boundary-2026.md](pilot-claim-boundary-2026.md).

## Operational gates before customer pilot

[pilot-pre-pilot-gates-2026.md](pilot-pre-pilot-gates-2026.md) — deterministic replay, BCF roundtrip, false-positive budget.

## Post-pilot research fork

[pilot-kpi-protocol-2026.md](pilot-kpi-protocol-2026.md), [post-pilot-fork-2026.md](post-pilot-fork-2026.md).

## Suggested citation

```
AeroBIM (2026). Multimodal deterministic BIM validation kernel — pilot evidence bundle.
Repository: https://github.com/KonkovDV/AeroBIM
Evidence: aerobim_runtime_benchmark_report_v1.json, russian-aec-ground-truth.json
```
