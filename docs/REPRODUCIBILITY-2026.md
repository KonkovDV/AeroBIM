---
title: "AeroBIM Reproducibility 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, reproducibility, FAIR, openBIM, academic]
---

# Reproducibility and FAIR Alignment (2026)

Single source of truth for reviewers, pilot operators, and supplementary material (ITcon / Automation in Construction class).

**Repository layout:** [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md) — committed vs gitignored vs CI `artifacts/`.

## Frozen vs rolling references

| Line | Git ref | Use when |
|---|---|---|
| **Frozen pre-pilot baseline** | tag `pilot-2026-pre` → commit `1a5c03e` | Citing metrics locked at pilot kickoff; comparing pilot weeks |
| **Rolling documentation** | branch `main` @ `078769a` (academic release, 2026-05-21); newer doc-only commits on `main` | Operator docs, weekly logs, [`evidence/pre-push-verification-2026-05-21.md`](evidence/pre-push-verification-2026-05-21.md) |

Metrics in [`pilot-start-package-2026.md`](pilot-start-package-2026.md) for extraction F1 and test counts refer to the **frozen** line unless a weekly log records a re-run on a newer SHA.

## Standards alignment (May 2026)

| Standard | Role in AeroBIM |
|---|---|
| [IDS 1.0](https://github.com/buildingSMART/IDS/releases/tag/v1.0.0) | Machine-readable exchange requirements (IfcTester) |
| BCF 2.1 (default) / 3.0 (opt-in) | Issue handoff to coordination tools |
| IFC2x3 / IFC4 / IFC4x3 | Validation substrate — [`ifc-compatibility-matrix.md`](ifc-compatibility-matrix.md) |
| ISO 19650-lite fields | Optional stage, revision, container on reports |

## Minimal reproduction (PowerShell)

```powershell
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM
git checkout pilot-2026-pre   # frozen baseline; or main for latest docs

cd backend
python -m venv .venv-pilot
.\.venv-pilot\Scripts\pip install -e ".[dev,raster]"

.\.venv-pilot\Scripts\python.exe -m pytest tests -q
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.run_ablation_study --output ../docs/evidence/ablation-study-report.json
```

## Minimal reproduction (bash)

```bash
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM
git checkout pilot-2026-pre

cd backend
python3 -m venv .venv-pilot
source .venv-pilot/bin/activate
pip install -e ".[dev,raster]"

python -m pytest tests -q
python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
python -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence
python -m aerobim.tools.run_ablation_study --output ../docs/evidence/ablation-study-report.json
```

Full publication rail: [`academic-publication-evidence-2026.md`](REPRODUCIBILITY-2026.md).

## Evidence artifact manifest

| File | Content |
|---|---|
| [`evidence/pre-pilot-gates-evidence-2026-05-21.md`](evidence/pre-pilot-gates-evidence-2026-05-21.md) | Gates 1–4 sign-off |
| [`evidence/pre-pilot-extraction-2026-05-21.json`](evidence/pre-pilot-extraction-2026-05-21.json) | Extraction P/R/F1 snapshot |
| [`evidence/pre-pilot-runtime-baseline-2026-05-21.json`](evidence/pre-pilot-runtime-baseline-2026-05-21.json) | Runtime APPROVED bundle |
| [`evidence/pre-pilot-conflict-breakdown-2026-05-21.json`](evidence/pre-pilot-conflict-breakdown-2026-05-21.json) | Pilot fixture ConflictKind |
| [`evidence/pre-pilot-bcf-handoff-2026-05-21.json`](evidence/pre-pilot-bcf-handoff-2026-05-21.json) | BCF repository verification |
| [`evidence/benchmark-report-2026-05-20.md`](evidence/benchmark-report-2026-05-20.md) | Frozen-line benchmark (pre-pilot tag era) |
| [`evidence/benchmark-report-2026-05-21.md`](evidence/benchmark-report-2026-05-21.md) | Rolling-line benchmark refresh |
| [`evidence/ablation-study-report.json`](evidence/ablation-study-report.json) | Multimodal ablation A0–A3 |
| [`evidence/pre-push-verification-2026-05-21.md`](evidence/pre-push-verification-2026-05-21.md) | Pre-commit verification lane |
| [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md) | Samolet TechLab traceability matrix |
| [`../samples/benchmarks/samolet-typical-errors-catalog.json`](../samples/benchmarks/samolet-typical-errors-catalog.json) | Typical error catalog scaffold |
| [`samolet-techlab-scorecard-2026.md`](samolet-techlab-scorecard-2026.md) | Score ladder 7.6 → 10 |
| [`samolet-compliance-scorecard-2026.md`](samolet-compliance-scorecard-2026.md) | Closure SSOT (sign-off) |
| [`evidence/samolet-sla-pilot-moscow-2026-05-21.json`](evidence/samolet-sla-pilot-moscow-2026-05-21.json) | Fixture SLA evidence |
| Customer SLA | `docs/evidence/internal/samolet-sla-customer-*.json` (gitignored) |

Corpus SSOT: [`annotation-protocol-2026.md`](annotation-protocol-2026.md), [`../samples/benchmarks/russian-aec-ground-truth.json`](../samples/benchmarks/russian-aec-ground-truth.json).

## FAIR software self-check (condensed)

| Principle | AeroBIM status | Notes |
|---|---|---|
| **Findable** | pass | Public repo, tag `pilot-2026-pre`, [`CITATION.cff`](../CITATION.cff), [`CITATION.bib`](CITATION.bib) |
| **Accessible** | pass | MIT license, documented install, no paywall on code |
| **Interoperable** | pass | Open JSON, BCF, IDS, IFC; no proprietary-only export |
| **Reusable** | pass | Frozen corpus, pip-freeze hash in benchmark report, deterministic path |
| Metadata | pass | Version, Python pin, environment block in benchmark MD |
| Tests in CI | pass | [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) |
| Claim boundary | pass | [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) |

Reference frameworks: [FAIR Software Checklist v0.2](https://fairsoftwarechecklist.net/v0.2/), CODE reusable research software (Scientific Data, 2026).

## Explicit limits (do not overclaim)

1. **Deterministic sign-off only** — no non-deterministic drawing adapters or trained extraction in pilot path.
2. **Fixture corpus** — 10 RU narrative documents / 50 requirements; pilot Moscow pack may differ.
3. **No customer data** in the public repository.
4. **Decision-support** — not licensed engineering sign-off or full regulatory automation.
5. Tag `pilot-2026-pre` must be cited for frozen metrics; rolling `main` may add docs without changing frozen code.

## Citation

Prefer:

```text
Konkov, D. V. (2026). AeroBIM (version pilot-2026-pre) [Software].
https://github.com/KonkovDV/AeroBIM
```

Or BibTeX from [`CITATION.bib`](CITATION.bib). Include commit SHA when publishing numerical results.
