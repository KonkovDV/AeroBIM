---
title: "AeroBIM Reproducibility 2026"
status: active
version: "1.2.0"
last_updated: "2026-10-20"
tags: [aerobim, reproducibility, FAIR, openBIM, academic]
---

# Reproducibility and FAIR Alignment (2026)

Single source of truth for reviewers, pilot operators, and supplementary material (ITcon / Automation in Construction class).

**Repository layout:** public GitHub = product code + TechLab jury docs; operator/debug materials stay under `.local/` (gitignored). CI dumps use `artifacts/`.

## Reference commits

| Line | Git ref | Use when |
|---|---|---|
| **CI-attested pin** | commit `c057a2e9f174` from [`evidence/runtime-baseline-latest.json`](evidence/runtime-baseline-latest.json) (`attested_by=ci`, `claim_level=fixture_engineering`, `publishable=true`) | Citing test counts, LOC and fixture extraction F1 |
| **Rolling documentation** | branch `main` (latest jury pack) | Operator-local notes under `.local/`; citeable fixtures in [`evidence/README.md`](evidence/README.md) |

The numbers in the root README come from that pin. A newer pin lands only from a CI artifact, never from a local run.

The tag `pilot-2026-pre` and its commit `1a5c03e` did not survive the history rewrite of 2026-10-01, and the remote carries no tags today. Cite the pin commit instead ([`evidence/HISTORY_REWRITE_ORPHAN_SHA_2026_10.md`](evidence/HISTORY_REWRITE_ORPHAN_SHA_2026_10.md)).

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
git checkout c057a2e9f174db7ed58a5975b7b576c7d6bd333f   # CI-attested pin; or stay on main

cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,raster]"

.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
.\.venv\Scripts\python.exe -m aerobim.tools.generate_benchmark_report --output-dir ../artifacts/benchmark
.\.venv\Scripts\python.exe -m aerobim.tools.run_ablation_study --output ../artifacts/ablation-study-report.json
```

The outputs land in `artifacts/`, which git ignores, so the tracked evidence stays as pinned.

## Minimal reproduction (bash)

```bash
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM
git checkout c057a2e9f174db7ed58a5975b7b576c7d6bd333f

cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,raster]"

python -m pytest tests -q
python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
python -m aerobim.tools.generate_benchmark_report --output-dir ../artifacts/benchmark
python -m aerobim.tools.run_ablation_study --output ../artifacts/ablation-study-report.json
```

Math, study design and the sample-size plan: [`quality/ACADEMIC_ROADMAP_2026_09.md`](quality/ACADEMIC_ROADMAP_2026_09.md).

## Evidence artifact manifest

| Artifact | Role |
|---|---|
| [`evidence/README.md`](evidence/README.md) | Citeable fixtures index |
| [`evidence/runtime-baseline-latest.json`](evidence/runtime-baseline-latest.json) | Runtime LOC / tests / F1 |
| [`evidence/benchmark-report-2026-05-21.md`](evidence/benchmark-report-2026-05-21.md) | Academic benchmark snapshot |
| [`evidence/sla-pilot-moscow-2026-05-21.json`](evidence/sla-pilot-moscow-2026-05-21.json) | Fixture SLA (not customer) |
| [`evidence/tz-matrix-status-latest.json`](evidence/tz-matrix-status-latest.json) | TZ matrix status |
| [`../audit/evidence/bcf-structural-handoff-2026-07-25.json`](../audit/evidence/bcf-structural-handoff-2026-07-25.json) | BCF structural T1 |
| [`../audit/evidence/cde-import-proof/STATUS.json`](../audit/evidence/cde-import-proof/STATUS.json) | CDE import gate (`NOT_VERIFIED`) |
| [`techlab-alignment-2026.md`](techlab-alignment-2026.md) | TechLab R1–R15 |
| [`../samples/benchmarks/typical-errors-catalog.json`](../samples/benchmarks/typical-errors-catalog.json) | Typical error catalog scaffold |
| [`../samples/benchmarks/russian-aec-ground-truth.json`](../samples/benchmarks/russian-aec-ground-truth.json) | RU extraction corpus |
| Customer SLA | `docs/evidence/internal/` / `samples/customer/` (gitignored) |

## FAIR software self-check (condensed)

| Principle | AeroBIM status | Notes |
|---|---|---|
| **Findable** | pass | Public repo, CI-attested pin commit, [`CITATION.cff`](../CITATION.cff), [`CITATION.bib`](CITATION.bib) |
| **Accessible** | pass | MIT license, documented install, no paywall on code |
| **Interoperable** | pass | Open JSON, BCF, IDS, IFC; no proprietary-only export |
| **Reusable** | pass | Frozen corpus, pip-freeze hash in benchmark report, deterministic path |
| Metadata | pass | Version, Python pin, environment block in benchmark MD |
| Tests in CI | pass | [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) |
| Claim boundary | pass | [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) |

Reference frameworks: [FAIR Software Checklist v0.2](https://fairsoftwarechecklist.net/v0.2/), CODE reusable research software (Scientific Data, 2026).

## Claims Lock — report reproducibility vs model determinism

**Report reproducibility is the deterministic core.** The language-model output is not an input to the verdict; it is stored as a provenanced annotation (prompt/response hashes, model URI, schema version, expert mark) and on re-run is **presented**, not re-generated. Vendor intra-session / across-time determinism probes measure provider behaviour; they are not a publication gate for FAIR report reproducibility.

See the advisory contour [`ai/LLM_ADVISORY_CONTOUR.md`](ai/LLM_ADVISORY_CONTOUR.md).

## Explicit limits (do not overclaim)

1. **Deterministic sign-off only** — no non-deterministic drawing adapters or trained extraction in pilot path.
2. **Fixture corpus** — 10 RU narrative documents / 50 requirements; pilot Moscow pack may differ.
3. **No customer data** in the public repository.
4. **Decision-support** — not licensed engineering sign-off or full regulatory automation.
5. Cite the CI-attested pin commit for numbers; rolling `main` may add docs without changing the pinned code.

## Citation

Prefer:

```text
Konkov, D. V. (2026). AeroBIM (commit c057a2e9f174) [Software].
https://github.com/KonkovDV/AeroBIM
```

Or BibTeX from [`CITATION.bib`](CITATION.bib). Name the commit SHA whenever a number is published.
