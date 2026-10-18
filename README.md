<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock" -->
<p align="center">
  <img src="AeroBIM.png" alt="AeroBIM" width="420">
  <br><br>
  <b>Presentation · 7 slides</b>
  <br><br>
  <a href="submission/03-presentation/AeroBIM.pptx"><img src="https://img.shields.io/badge/PowerPoint-.pptx-D24726?style=for-the-badge&logo=microsoftpowerpoint&logoColor=white" alt="PowerPoint"></a>
  &nbsp;
  <a href="submission/03-presentation/AeroBIM.pdf"><img src="https://img.shields.io/badge/PDF-.pdf-B30B00?style=for-the-badge&logo=adobeacrobatreader&logoColor=white" alt="PDF"></a>
  <br><br>
  <a href="submission/03-presentation/demo_day_slides.md"><b>Slide text</b></a>
  <br><br>
  <b>Full deck · 43 slides</b>
  <br><br>
  <a href="submission/03-presentation/AeroBIM-full.pptx"><img src="https://img.shields.io/badge/PowerPoint-full-D24726?style=for-the-badge&logo=microsoftpowerpoint&logoColor=white" alt="PowerPoint full"></a>
  &nbsp;
  <a href="submission/03-presentation/AeroBIM-full.pdf"><img src="https://img.shields.io/badge/PDF-full-B30B00?style=for-the-badge&logo=adobeacrobatreader&logoColor=white" alt="PDF full"></a>
  <br><br>
  <a href="submission/03-presentation/AeroBIM-full.md"><b>Full deck text</b></a>
</p>

# AeroBIM

[Русская версия](README.ru.md)

[![CI](https://img.shields.io/github/actions/workflow/status/KonkovDV/AeroBIM/ci.yml?branch=main&event=push&label=CI)](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml?query=branch%3Amain)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**AeroBIM** is automated verification of design and working documentation. It is a standalone open-source project under the MIT licence.

It checks a design/working pack against itself: model, sheet, schedule, brief and calculation. Each file can open cleanly on its own. The defect lives in the seam and usually surfaces on site.

A finding carries a clause, a storey or grid, and a GUID. An expert records the decision on a finding. The `summary.passed` flag is set by the deterministic gate: a person does not write it, and a language model does not write it. Output is HTML, JSON, PDF, and a BCF file.

Three shelves in the process.

| Shelf | What it does | Boundary |
|---|---|---|
| CDE (10D, Pilot-BIM, Sarex) | Presence, route, versions | Does not cross-check file contents |
| Model checker (Tangl, Solibri) | Model, attributes, clashes in the authoring environment | Does not compare the model with the schedule, note and calculation |
| **Pack gateway (AeroBIM)** | Cross-file consistency; acceptance profile is IDS | Does not replace the two shelves above |

It operates on the **seam between files**.

**What a finding looks like.** Demo case: cover 30 mm in the model, 40 mm on the sheet — 10 mm gap. The deterministic layer does the compare. The card traces to the requirement, GUID and sheet row. A person decides. Export is a BCF 2.1/3.0 file.

## Contents

- [What AeroBIM accepts](#what-aerobim-accepts)
- [Stage](#stage)
- [Try it](#try-it)
- [What a run does](#what-a-run-does)
- [Numbers, marks, stamps and calculations](#numbers-marks-stamps-and-calculations)
- [Why the checker is built this way](#why-the-checker-is-built-this-way)
- [Capabilities](#capabilities)
- [HTTP API](#http-api)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Repository](#repository)
- [Documentation](#documentation)
- [Cite](#cite)
- [Stack](#stack)
- [License](#license)

## What AeroBIM accepts

| | |
|---|---|
| Ingest | IFC 2x3 / 4 / 4x3, IDS 1.0, PDF vector/raster, specification text |
| Cross-check | IFC, IDS and the other files in the pack. The tolerance on a number is decimal |
| Workplace | Review shell (Vite): IFC model, saved sheet preview and zone from the report, RU/EN templates, HITL. Not a drawing editor |
| Report | HTML + JSON + PDF + structural BCF 2.1 / 3.0 ZIP |
| Verdict | `summary.passed` is a Shared-gate. LLM/VLM never write it ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)) |

An unfinished mandatory check cannot yield a positive pack result.

## Stage

Regulatory-measurement MVP. The code and the fixture packs in `samples/` run: one command shows a finding with evidence on a fixture pack. Every measurement so far uses fixture or open data.

Not there yet:

- a labelled corpus of real projects with two human raters on the same sample. Accuracy on real packs is not claimed;
- an acceptance profile signed by a specific organisation. `samples/` ships published rule sets;
- system-aware clash detection on the MEP system graph: `mep_system_clash` stays `NOT_VERIFIED`;
- proof that a CDE imports the exported BCF. Export is structural; import is `NOT_VERIFIED`.

## Try it

Python 3.12 and a venv in `backend/.venv`. The command-line demo does **not** need Node. The review shell needs Node 22.22.2+ and npm. Keep the quotes around `".[dev,raster]"` in PowerShell.

**Windows (PowerShell).** If ExecutionPolicy blocks `Activate.ps1`, skip activation and call `python.exe` directly.

```powershell
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM\backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,raster]"
.\.venv\Scripts\python.exe -m aerobim.tools.run_kt3_jury
```

Or double-click `run-jury.bat` at the **clone root** (quotes around the extra are inside the file; Node is not required). Do not run `python -m aerobim...` with the system interpreter — the package will be missing. Diagnostics: `.\check-launch.bat`.

`summary.passed=false` on the fixture pack is the expected fail. Do not set `AEROBIM_SIGNOFF_PROFILE=customer_pilot` on a first clone. `requirements-lock.txt` is the Linux/CI lock — do not install it on Windows.

**Linux / macOS**

```bash
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM/backend

python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,raster]"
```

The live CLI is in `backend/`. The fixture pack contains planted defects; the command finds them (`summary.passed=false`). Or from the clone root: `./run-jury.sh`.

```bash
python -m aerobim.tools.run_kt3_jury
python -m aerobim.tools.run_demo_ifc_acceptance_gate
python -m aerobim.tools.run_demo_vertical_slice

pytest tests -q
python -m aerobim.main   # http://127.0.0.1:8080/health
```

Start the review shell **from the clone root** (not from `frontend/`). FastAPI at `http://127.0.0.1:8080`, Vite/React at `http://127.0.0.1:5173`. The UI never writes `summary.passed`. You need `backend/.venv` already created and Node 22.22.2+.

- Linux/macOS: `./start.sh`
- Windows PowerShell: `.\start.bat` (the leading `.\` is required; bare `start` is Start-Process and will ask for FilePath)
- from `backend/`: `python -m aerobim.tools.run_review_stand`

If 8080 or 5173 is already bound, stop leftover Docker (`aerobim-backend`) or the previous `.\start.bat` and retry. Details: [`frontend/README.md`](frontend/README.md). Closed contour without pip: Docker image, not a bare wheelhouse — [`docs/offline-deployment-2026.md`](docs/offline-deployment-2026.md). pip TLS errors are a site proxy issue, not a wheelhouse recipe.

Optional extras `.[clash]`, `.[docling]`, `.[enterprise]`, `.[pdf-agpl]` are not needed for the commands above.

If `py -3.12` is missing, install CPython 3.12 from python.org — not the Microsoft Store stub. Do not type bare `py`: the launcher may pick 3.13. Use `git clone`, not the GitHub ZIP. If IfcOpenShell fails to import on Windows, install the Microsoft VC++ 2015-2022 x64 redistributable. Diagnostics: `.\check-launch.bat` from the clone root (not `python -m aerobim.tools.check_local_launch` without the venv). Doctor warnings do not stop the demo run; a fatal (exit 2) does. Clone into a short Latin path (`C:\AeroBIM`), not a user profile with non-ASCII characters.

<details>
<summary>uv, hashed Windows lock, Dev Container, closed contour</summary>

**uv** is faster when it is already on PATH. The attested first clone without uv remains `python.exe -m pip` above.

```powershell
cd AeroBIM\backend
uv venv --python 3.12
uv pip install -e ".[dev,raster]"
.\.venv\Scripts\python.exe -m aerobim.tools.run_kt3_jury
```

Hashed Windows deps (online, not air-gap): [`backend/requirements-win-lock.txt`](backend/requirements-win-lock.txt), then `.\.venv\Scripts\python.exe -m pip install -e . --no-deps`. Do not install the Linux [`requirements-lock.txt`](backend/requirements-lock.txt) on Windows (`uvloop`). This is not a wheelhouse.

Closed contour without pip is the Docker image: [`docs/offline-deployment-2026.md`](docs/offline-deployment-2026.md). `install_offline.ps1` loads the tar, not a lock.

Dev Container / Codespaces is a contributor environment, not the demo run: [`.devcontainer/`](.devcontainer/). Python 3.12, Node 22.22.2+, `.[dev,raster]`. Do not set `customer_pilot`.
</details>

## What a run does

```mermaid
flowchart LR
  pack["IFC + IDS + drawings + texts"] --> checks["Deterministic checks"]
  checks --> report["Report with evidence"]
  report --> reviewer["Reviewer decides"]
```

| Step | What it does | Where to look |
|---|---|---|
| 1. Model | Validates properties and quantities with IfcOpenShell 0.9. `IFC2x3` (buildingSMART schema; no ISO publication), `IFC4 ADD2` (ISO 16739-1:2018) and `IFC4x3` (ISO 16739-1:2024) go through one entry point (`open_ifc_model` / `open_ifc_file` / `open_ifc_session`). `ISO/PAS 16739:2005` is the IFC2x Platform, not `IFC2x3`. Pre-final `IFC4x3` headers (`IFC4X3`, `ADD1`, `TC1`) are normalized to `IFC4X3_ADD2` in a temporary copy and checked against the SPF entity count; models above 256 MiB up to 1.5 GB open through RocksDB with entity count reconciliation against SPF. Where property-set names diverge between releases, the difference is a `ValidationIssue`, not a silent skip | [`docs/ifc-compatibility-matrix.md`](docs/ifc-compatibility-matrix.md) |
| 2. Rules | Validates IDS 1.0 with IfcTester 0.9. Base W3C XSD schemas are mapped to local `xmlschema` copies (`allow="local"`), so `ifctester.ids.open` makes no network requests. CI runs 290 official buildingSMART IDS 1.0 test cases. Published rule sets from Moscow Region State Expertise and SPb GAU CGE (CIM OKS ed. 3.1.0 + CIM RII ed. 1.1.0) ship in `samples/`; the CGE profile ([`samples/profiles/spb-cge/`](samples/profiles/spb-cge/)) is a published rule set, not a customer-signed acceptance profile. A requested rule set that cannot load fails the check | [`samples/profiles/spb-cge/`](samples/profiles/spb-cge/) |
| 3. Documents | Reads the model next to drawing notes, schedules, specifications and calculation tables. Numbers, steel grades, riser lists, title blocks and declared calculation rows follow the rules in the next section | [`docs/calculation-evidence-boundary-2026.md`](docs/calculation-evidence-boundary-2026.md) |
| 4. Report and decision | Every finding carries `finding_id`, `source_id` and `evidence_refs`; a finding without them is refused. A reviewer can accept, reject, mark a false positive, or ask for clarification; a rejection, false positive or clarification requires a note and never flips `summary.passed`. People get HTML; machines get JSON; issue exchange gets a structural BCF 2.1 / 3.0 ZIP. The browser review shell (web-ifc + Three.js) shows the IFC and the saved sheet preview with the zone from the report; it is not a drawing editor. The fixture overlay CLI remains a separate run | [`docs/architecture/ADR-001-verdict-ownership-2026.md`](docs/architecture/ADR-001-verdict-ownership-2026.md) |

`summary.passed` is assembled from deterministic errors and the capability table ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)). Advisory LLM/VLM text, if enabled, drafts remark wording only and never writes that flag; under customer sign-off profiles outbound advisory calls are forbidden. Every optional engine reports `ok`, `skipped` or `failed`; any `FAILED` forces `summary.passed=false`. The same boundary is served on `GET /v1/system/capabilities`. That flag is a Shared-gate under configured rules.

## Numbers, marks, stamps and calculations

- **Decimal band.** Sizes are converted to SI (`quantity.py`). The difference is `Decimal(str(a)) - Decimal(str(b))`, in `measured_delta` and `within_epsilon`. They agree when the absolute difference is at most `Decimal(str(epsilon))`. `1.1` and `1.0` at a tolerance of `0.1` stay inside the band. Russian grouping (`1 254,30`) and European grouping (`1.254,30`) are read. A token like `1.254` is ambiguous, so it is refused.
- **Steel grades and system marks.** `С345` and `C345` are one grade (`label_identity.py`). A Roman `I` stays `I`. A short riser list or range on a schedule (`В2.7,8,9`, `В2.4–В2.6`) matches any one riser inside it (`target_ref`). A grille size with a star (`П300*300`) stays a size. A GlobalId is 22 characters (ISO 10303-21), compared character by character, and the case matters. `ALL`, `*`, `ANY`, or an empty `target_ref` means every instance of that entity. A matching mark is not a clash between systems.
- **Stamps and drawing reads.** On a 2D title block (`stamp_dual_read.py`) the PDF text and the OCR text must match after cleanup: Unicode NFKC, `ё` and `Ё` become `е` and `Е`, runs of spaces collapse, then strip and casefold. OCR confidence has to be present and at least `0.5`. A mismatch, a missing score, or a low score returns `ABSTAIN`. If both sides are empty, the status is `NOT_VERIFIED`. In both cases `requires_hitl` is true. An optional VLM read uses the spoken confidence only as a floor (`abstention_sweep.py`, floors `0.35`, `0.45`, `0.60`, `0.75`). Raising the floor does not reduce how often a person must look. With no outcome labels, ECE and Brier stay empty.
- **Declared calculation tables.** Office tables (`xlsx`, `docx`, via `spreadsheet_load_evidence_adapter.py`) are set next to BIM and drawing tables (`calculation_table_compare.py`). The dimensionless tolerance is `0.001`. A row can be cited only when both sides have the same filled triple: `element_id`, `section_id`, `parameter_id`. That state is `COMPLETE`. A blank field, a missing side, a repeated `field_id`, or two different triples stay `NOT_VERIFIED`. `MATCH` means the printed numbers agree. The solver is not run again.

## Why the checker is built this way

| What showed up in 2025–2026 | What AeroBIM does |
|---|---|
| Vision and language models miscount repeated symbols on dense sheets (AECV-Bench, arXiv:2601.04819; Iversen and Huang, Automation in Construction 2025; Fuchs et al., EC3) | Only `EvidenceAssembler` and `DeterminismGate` set `summary.passed` ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)). The pack does not pass if there is a deterministic error, a required capability is not `OK`, intake is blocked, a drawing still needs a person, or a hard clash counts under the current policy. Warnings alone still pass (`pass_with_warnings`). LLM and VLM text is marked `origin="advisory"` and does not move the flag (`OFF == ON`) |
| A model’s own confidence is a weak probability (VL-Calibration, ACL 2026) | The number is only a floor for `hitl_required`. The region goes to a reviewer when confidence is below the floor, or when that confidence was never calibrated |
| A bare percentage on a small sample, and Cohen’s kappa when one class dominates, overstate the result | Shares use a Wilson 95% interval. The sample-size plan (`study_design.py`, `plan_adjudication_corpus.py`) takes the larger of 62 and 111, so the recommended size is 111. Nothing has been labeled yet (`n_labeled=0`). Agreement is Cohen’s kappa, Krippendorff’s alpha, and Gwet’s AC1 (`eval_statistics.py`, `rt001_dual_rater_simulation.py`): observed agreement minus chance agreement, divided by one minus chance agreement. Chance agreement uses the categories both raters actually marked. Calibration (`compute_reliability_report.py`, `eval_statistics.py`) reports equal-mass ECE and the Brier score. Outside a customer corpus, and when n is below 100, `publishable` stays false |
| A fixed alpha on every CI commit eventually raises false alarms | `sequential_inference.py` and `e_process_simulation.py` turn permutation p-values into e-values. The power calibrator is kappa times p to the power of (kappa − 1), with kappa between 0 and 1. At kappa `0.5` that is `0.5 / sqrt(p)`. The mixture is `(1 - p + p ln p) / (p (ln p)^2)`, and it equals `1/2` when p is 1. Truncated aGRAPA maps a step difference d from −1 to 1 into x = (d + 1) / 2, then multiplies wealth by `(1 + lambda_t * (x - 1/2))`. Ville’s bound: under the null, the chance that wealth ever reaches `1/alpha` is at most alpha |
| Numbers copied by hand drift away from the CI pin | `manuscript_tables.py` prints a cell only when the JSON pin has `attested_by="ci"` and a `claim_level` other than `product_accuracy`, `customer_accuracy`, or `cde_ready`. Otherwise the cell stays `withheld` |

## Capabilities

- IFC property and quantity validation; IDS 1.0 fails closed if the rule set cannot load or a schema check fails
- Cross-document contradictions and drawing notes vs IFC
- Decimal tolerance band (SI-normalised); lookalike steel grades and short system-mark lists share an identity; deterministic requirement extraction from narrative text; advisory LLM does not sign anything off
- Every check reports `ok` / `skipped` / `failed`; tenant/object ACL on artifacts under `customer_pilot` / `production` (off by default in development); HTML/JSON; PDF; structural BCF 2.1 / 3.0 ZIP
- PDF via pypdfium2 + pdfminer; default `AEROBIM_PDF_BACKEND=pdfium`
- Browser IFC viewer and the sheet preview with the zone stored on the report. Not a drawing editor
- Norm rule packs (a fixture pack is not a customer-signed profile) and an opt-in completeness inventory
- Quality measurement protocol (Wilson intervals, exact binomial sample-size planner, equal-mass ECE, Brier score, Gwet's AC1, e-process regression monitor)

Optional: geometry clash `.[clash]`; OCR `.[raster]`; PyMuPDF `pdf-agpl`; advisory LLM/VLM drafts (never write `summary.passed`); OpenCDE BCF push (experimental; not CDE import proof); DXF via ezdxf.

## HTTP API

`GET /health` is unauthenticated. `/v1/*` requires `AEROBIM_API_BEARER_TOKEN` unless `AEROBIM_ALLOW_ANONYMOUS_DEV=true` (development only; loopback bind or `AEROBIM_ANONYMOUS_EXTERNAL_LOOPBACK=true`).

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Readiness |
| `GET` | `/v1/auth/bff` | Auth discovery. Default **501**. Lab `200 LAB` is not customer SSO |
| `GET` | `/v1/system/capabilities` | Capability boundary |
| `POST` | `/v1/uploads` | Multipart ingest |
| `POST` | `/v1/validate/ifc` | Validate IFC against requirements and IDS |
| `POST` | `/v1/analyze/project-package` | Full package analysis |
| `POST` | `/v1/analyze/project-package/submit` | Queue a larger package in Redis for the dedicated `aerobim.worker` |
| `GET` | `/v1/analyze/project-package/jobs/{job_id}` | Poll a background job |
| `POST` | `/v1/analyze/project-package/jobs/{job_id}/cancel` | Cancel |
| `GET` | `/v1/reports` | List persisted reports |
| `GET` | `/v1/reports/{id}` | Fetch one report |
| `GET` | `/v1/reports/{id}/coverage` | Check coverage map |
| `GET` | `/v1/reports/{id}/revision-diff` | Finding delta; `no_longer_reported` does not mean resolved |
| `GET` | `/v1/reports/{id}/export/{json,html,pdf,bcf}` | Export; `?version=3` switches BCF 3.0 |
| `POST` | `/v1/reports/{id}/review-events` | Append reviewer HITL; never changes `summary.passed` |
| `GET` | `/v1/reports/{id}/review-events` | HITL history |
| `GET` | `/v1/reports/{id}/review-kpi` | Triage summary (not cycle-days in a CDE) |

Package analysis optionally accepts an OpenRebar reinforcement report with a SHA-256 provenance digest. This compares declared sources; it does not recompute anything. OpenCDE `POST .../export/bcf-api/push` is an experimental hub push, not proof of import into the customer CDE.

## Architecture

**48 domain Protocol ports** wire to **77 infrastructure adapter modules** through **63 DI tokens** in `bootstrap_container()`. Counts: [`docs/evidence/runtime-baseline-latest.json`](docs/evidence/runtime-baseline-latest.json).

Five layers, dependencies pointing inward only:

```text
core/            DI container, tokens, configuration
domain/          Immutable models, Protocol ports, logging contract
application/     Requirement assembly, contradiction detection
infrastructure/  IfcOpenShell, IfcTester, BCF, storage; IfcClash and Docling are optional extras
presentation/    FastAPI
```

Artifacts sit behind an `ObjectStore` port: a local disk or an S3-compatible bucket. That is one port and two adapters. Report summaries are indexed in Postgres when `AEROBIM_DB_URL` is set. Heavy package jobs submitted through `/v1/analyze/project-package/submit` are queued in Redis and executed by `aerobim.worker` over `BLMOVE` with leases, heartbeats, fencing tokens and a dead-letter queue (at-least-once delivery).

## Configuration

A local clone runs on defaults. CI checks the table against `settings.py` both ways.

<details>
<summary>Full <code>AEROBIM_*</code> table</summary>

| Variable | Default | Description |
|---|---|---|
| `AEROBIM_HOST` | `127.0.0.1` | Bind address |
| `AEROBIM_PORT` | `8080` | Bind port |
| `AEROBIM_DEBUG` | `false` | Debug mode (also enables localhost CORS defaults when origins unset) |
| `AEROBIM_STORAGE_DIR` | `var/reports` | Report persistence directory |
| `AEROBIM_CORS_ORIGINS` | *(auto)* | Comma-separated CORS origins |
| `AEROBIM_CORS_ALLOW_CREDENTIALS` | *(auto)* | `true` in development/test for a finite origin list; `customer_pilot`/`production` require explicit `true` |
| `AEROBIM_ENV` | `development` | Environment name; non-dev requires bearer/OIDC (fail-closed) |
| `AEROBIM_SIGNOFF_PROFILE` | *(auto)* | `customer_pilot` and `production` are closed customer contours: capabilities fail closed and outbound advisory LLM calls are forbidden. `customer_pilot_demo` and `moscow_agr_2026` are **honest-scope** contours (development/test only): clash/MEP/bSI-submit stay out of scope (honest SKIPPED, not faked); FAILED engines still block; LLM egress still forbidden. `moscow_agr_2026` cites DGP-R-1/26 CIM AGR, not demo convenience. Unset outside development resolves to `production`. Also accepts `development` and `fixture` |
| `AEROBIM_API_BEARER_TOKEN` | *(unset)* | Bearer for `/v1/*`; required unless `AEROBIM_ALLOW_ANONYMOUS_DEV` |
| `AEROBIM_ALLOW_ANONYMOUS_DEV` | `false` | Opt-in anonymous API in development/test only (`from_env`) |
| `AEROBIM_ANONYMOUS_EXTERNAL_LOOPBACK` | `false` | Ack anonymous + non-loopback bind (Docker: ports map to `127.0.0.1` only) |
| `AEROBIM_CLASH_AFFECTS_PASS` | `false` | Soft only in development/fixture; forced `true` under pilot/production sign-off |
| `AEROBIM_CLASH_SKIP_TINY` | `true` | Skip degenerate/tiny IFC products before IfcClash; all-skipped still FAILED |
| `AEROBIM_CLASH_MIN_AABB_VOLUME_M3` | `1e-6` | AABB volume threshold used when `AEROBIM_CLASH_SKIP_TINY` is on |
| `AEROBIM_REQUIRE_CLASH` | `false` | Soft only in development/fixture; forced under pilot/production |
| `AEROBIM_REQUIRE_MEP_SYSTEM_CLASH` | `false` | When true, MEP `NOT_VERIFIED` blocks Shared-gate pass |
| `AEROBIM_MEP_FEDERATED_SCOPE_PATH` | *(unset)* | Federated MEP scope JSON (VERIFIED customer or ENG_FIXTURE) |
| `AEROBIM_MEP_AABB_FILTER` | `true` | Optional AABB broadphase for MEP matrix pairs; still `geometry_verified=False` |
| `AEROBIM_PDF_BACKEND` | `pdfium` | Core PDF: `pdfium` / `none`; optional legacy `pymupdf` only with `pdf-agpl` |
| `AEROBIM_MAX_IFC_BYTES` | `268435456` | Max **SPF in-memory** IFC open: 256 MiB. Comparable to the buildingSMART Validation Service cap of 256 MB on an uncompressed `.ifc`, not the same unit. Files above this and up to the model ingest cap open via IfcOpenShell RocksDB |
| `AEROBIM_MAX_OFFICE_BYTES` | `268435456` (dev); `500000000` on `customer_pilot`/`production` unless `AEROBIM_APPLY_PILOT_UPLOAD_CAPS=0` | Office ingest cap (PDF/Office), 500 MB decimal when applied |
| `AEROBIM_MAX_MODEL_BYTES` | `268435456` (dev); `1500000000` on `customer_pilot`/`production` unless `AEROBIM_APPLY_PILOT_UPLOAD_CAPS=0` | Model ingest **and disk-analyze** cap (IFC/ZIP/CAD), 1.5 GB decimal when applied. WASM viewer stays 256 MiB |
| `AEROBIM_APPLY_PILOT_UPLOAD_CAPS` | `true` under `customer_pilot`/`production`; ignored in development | Apply the stated 500 MB / 1.5 GB caps. SPF open stays 256 MiB; 1.5 GB IFC uses RocksDB |
| `AEROBIM_CROSS_DOC_SEVERITY` | `warning` | Severity for cross-document contradictions: `error` (blocking), `warning`, `info` |
| `AEROBIM_REMARK_LOCALE` | `ru` | Remark template language for deterministic generators (`ru` / `en`) |
| `AEROBIM_PRIORITY_PROFILE` | `default` | Review priority weighting profile (`default`; `customer` in fixture SLA smoke only) |
| `AEROBIM_DB_URL` | *(unset)* | Optional Postgres URL for report summary indexing. Bootstrap issues `CREATE`/`ALTER`, so production should migrate schema out of band and then grant a DML-only role |
| `AEROBIM_REPORT_TTL_DAYS` | *(unset)* | Optional TTL for persisted report payloads; unset means unlimited retention |
| `AEROBIM_S3_BUCKET` | *(unset)* | Optional S3/MinIO bucket for object storage |
| `AEROBIM_S3_ENDPOINT_URL` | *(unset)* | Optional MinIO/custom S3 endpoint |
| `AEROBIM_S3_REGION` | `us-east-1` | Signing region for S3-compatible storage |
| `AEROBIM_S3_ACCESS_KEY_ID` | *(unset)* | Optional access key for S3-compatible storage |
| `AEROBIM_S3_SECRET_ACCESS_KEY` | *(unset)* | Optional secret key for S3-compatible storage |
| `AEROBIM_S3_PREFIX` | `aerobim` | Prefix applied to object keys in S3-compatible storage |
| `AEROBIM_LLM_ADVISORY_ENABLED` | `false` | Development only: opt-in OpenAI-compatible advisory model. Never sets `summary.passed`; reports `ready=false` under `customer_pilot` and `production`. The deprecated alias `AEROBIM_LLM_LOCAL_ENABLED` still works but warns at boot |
| `AEROBIM_LLM_BASE_URL` | *(unset; Studio default when provider=`yandex-ai-studio`)* | Loopback or RF HTTPS OpenAI-compat base (`…/v1`); SSRF-gated at boot |
| `AEROBIM_LLM_API_KEY` | *(unset)* | Optional bearer for Studio; never logged / never in `audit_event` |
| `AEROBIM_LLM_PROVIDER` | `qwen-local` | Provider label (`qwen-local` / `yandex-ai-studio`) |
| `AEROBIM_LLM_MODEL` | `Qwen3.6-27B` | Local bare id, or Yandex `gpt://{folder}/{model}` |
| `AEROBIM_LLM_MODEL_REVISION` | *(required if enabled)* | Exact catalog version (not `latest`/`rc`); composed into URI |
| `AEROBIM_LLM_FOLDER_ID` | *(unset)* | Yandex folder → `x-folder-id` + URI composition |
| `AEROBIM_LLM_AUTH_SCHEME` | `Bearer` | `Bearer` or `Api-Key`, depending on the provider |
| `AEROBIM_LLM_SEND_SEED` | `true` (`false` for Studio) | Omit `seed` when false (Yandex may 400) |
| `AEROBIM_LLM_RESPONSE_FORMAT_MODE` | `json_object` (`json_schema` for Studio) | Yandex prefers `json_schema` + `REMARK_JSON_SCHEMA` |
| `AEROBIM_LLM_DATA_LOGGING_ENABLED` | `false` | When false, send `x-data-logging-enabled: false` (audit-recorded) |
| `AEROBIM_LLM_MODEL_SHA256` | *(unset)* | Optional checkpoint hash in usage/audit |
| `AEROBIM_LLM_MAX_TOKENS_PER_CALL` | `4096` | Fail-closed token cap per call |
| `AEROBIM_LLM_MAX_TOKENS_PER_RUN` | `100000` | Fail-closed per-run cap |
| `AEROBIM_LLM_MAX_TOKENS_PER_DAY` | `300000` | Fail-closed daily cap |
| `AEROBIM_LLM_BUDGET_TZ` | `Europe/Moscow` | IANA timezone for day-roll of the daily cap |
| `AEROBIM_LLM_BUDGET_LEDGER` | *(unset)* | Shared JSON ledger path across workers; **required** for grant ops (without it: process-local ≈ N× day cap) |
| `AEROBIM_LLM_MAX_COMPLETION_TOKENS` | `512` | Completion budget passed to the API |
| `AEROBIM_LLM_MAX_CONCURRENT` | `4` | Semaphore for parallel advisory calls |
| `AEROBIM_LLM_ADVISORY_MAX_ISSUES` | `32` | Max findings to overlay with AI remark drafts per analyze |
| `AEROBIM_LLM_429_RETRIES` | `3` | Linear backoff retries on HTTP 429 before SKIPPED |
| `AEROBIM_LLM_ALLOWED_HOSTS` | *(built-in)* | Extra allowlisted hostnames (comma-separated); `-`/`none` replaces the set with empty. Alibaba/OpenAI always forbidden |
| `AEROBIM_CUSTOMER_PACK_LLM_EGRESS` | `deny` under pilot/production; `allow` in development | Customer-pack LLM/VLM host preset. `deny` empties the allowlist. `allow` under pilot/production requires written consent ref |
| `AEROBIM_CUSTOMER_PACK_LLM_EGRESS_CONSENT_REF` | *(unset)* | Required when egress=`allow` under `customer_pilot`/`production`. Letter/id of written consent; not a GO claim |
| `AEROBIM_HYBRID_PROVIDER_CONFIG` | *(unset)* | Path to hybrid provider JSON (`schema_version` ≥1.1 requires `model_revision`) |
| `AEROBIM_API_TENANT_ID` | *(unset)* | Optional tenant id for multi-tenant API auth |
| `AEROBIM_APP_NAME` | `aerobim` | Application name for logs / OpenAPI title |
| `AEROBIM_BCF_API_BASE_URL` | *(unset)* | Optional BCF API base URL (enterprise sync) |
| `AEROBIM_BCF_API_PROJECT_ID` | *(unset)* | Optional BCF project id |
| `AEROBIM_BCF_API_TOKEN` | *(unset)* | Optional BCF API bearer token |
| `AEROBIM_BCF_API_VERSION` | `2.1` | BCF API version label |
| `AEROBIM_BSI_API_TOKEN` | *(unset)* | Optional buildingSMART Validation Service token |
| `AEROBIM_BSI_VALIDATION_URL` | *(built-in)* | Optional override for bSI Validation Service URL |
| `AEROBIM_GATES_ATTESTED` | *(CI only)* | Comma-separated CI job names attested into the runtime baseline; ignored locally, and must equal the required gate set under GitHub Actions |
| `AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE` | `120` | Pre-auth **per-IP** bucket for mutating `/v1` POSTs and GET `/v1/auth/login` + `/callback` + `/session`; after successful auth a second **per-principal** (`tenant_id:subject`) bucket applies to those POSTs. `0` disables in development; **must be >0** under pilot/production |
| `AEROBIM_TRUSTED_PROXY_IPS` | *(unset)* | Comma-separated peer IPs allowed to supply `X-Forwarded-For` for rate-limit keys; empty = never trust XFF |
| `AEROBIM_IFC_PARSE_CACHE_DIR` | *(unset)* | Optional on-disk IFC parse cache directory |
| `AEROBIM_KIMI_API_BASE_URL` | *(unset)* | Deprecated alias of the primary VLM base URL (internal name). Default unset. Under `customer_pilot`/`production` VLM is not ready even if set. See [`docs/security/BUILD_WITHOUT_EXTERNAL_MODELS_2026.md`](docs/security/BUILD_WITHOUT_EXTERNAL_MODELS_2026.md) |
| `AEROBIM_KIMI_API_KEY` | *(unset)* | Optional Kimi API key (never logged) |
| `AEROBIM_KIMI_CACHE_DIR` | *(unset)* | Optional Kimi response cache directory |
| `AEROBIM_KIMI_CACHE_NAMESPACE` | *(unset)* | Optional Kimi cache namespace |
| `AEROBIM_KIMI_CACHE_PROJECT` | *(unset)* | Optional Kimi cache project key |
| `AEROBIM_KIMI_MODEL` | *(unset)* | Optional Kimi model id |
| `AEROBIM_KIMI_REASONING_EFFORT` | *(unset)* | Optional Kimi reasoning effort knob |
| `AEROBIM_LLM_TIMEOUT_SECONDS` | `120` | Advisory LLM HTTP timeout seconds |
| `AEROBIM_MEP_SCOPE_MEMO_REF` | *(unset)* | Optional memo ref for federated MEP scope provenance |
| `AEROBIM_NORM_RULE_PACK` | *(unset)* | Optional norm rule-pack id/path |
| `AEROBIM_OIDC_AUDIENCE` | *(unset)* | OIDC audience claim required under pilot/production |
| `AEROBIM_OIDC_ISSUER` | *(unset)* | OIDC issuer URL |
| `AEROBIM_OIDC_JWKS_EXTRA_HOSTS` | *(unset)* | Extra allowlisted JWKS hostnames |
| `AEROBIM_OIDC_JWKS_URL` | *(unset)* | OIDC JWKS URL |
| `AEROBIM_OIDC_ROLES_CLAIM` | `roles` | OIDC claim name for roles |
| `AEROBIM_OIDC_TENANT_CLAIM` | `tenant_id` | OIDC claim name for tenant (no `tid`/`org_id` fallback) |
| `AEROBIM_OIDC_BFF_CLIENT_ID` | *(unset)* | Lab-only OIDC BFF public client id; `auth_bff` stays **NOT_IMPLEMENTED** unless lab Phase 3 is fully configured |
| `AEROBIM_OIDC_BFF_AUTHORIZE_URL` | *(unset)* | Lab-only IdP authorize URL draft; not a production login |
| `AEROBIM_OIDC_BFF_REDIRECT_URI_ALLOWLIST` | *(unset)* | Comma-separated exact `redirect_uri` allowlist for lab BFF redirects |
| `AEROBIM_OIDC_BFF_TOKEN_URL` | *(unset)* | Lab-only token endpoint; required for Phase 3; SSRF-gated at boot |
| `AEROBIM_OIDC_BFF_CLIENT_SECRET` | *(unset)* | Confidential BFF client secret (lab); never a production SSO claim |
| `AEROBIM_OIDC_BFF_COOKIE_SECRET` | *(unset)* | HMAC secret for the lab session cookie; unset keeps Phase 3 off |
| `AEROBIM_REDIS_URL` | *(unset in dev)* | Required outside development/test for job records, the reliable ready/processing queue, and shared rate limits. `submit` publishes to Redis; the dedicated `aerobim.worker` executes with at-least-once delivery |
| `AEROBIM_VLM_ENABLED` | `false` | Opt-in advisory VLM drawing read; never sets `summary.passed` |

</details>

<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->
<!-- machine-checked parity list (export_runtime_baseline --check-readme)
AEROBIM_ALLOW_ANONYMOUS_DEV
AEROBIM_ANONYMOUS_EXTERNAL_LOOPBACK
AEROBIM_API_BEARER_TOKEN
AEROBIM_API_TENANT_ID
AEROBIM_APP_NAME
AEROBIM_APPLY_PILOT_UPLOAD_CAPS
AEROBIM_BCF_API_BASE_URL
AEROBIM_BCF_API_PROJECT_ID
AEROBIM_BCF_API_TOKEN
AEROBIM_BCF_API_VERSION
AEROBIM_BSI_API_TOKEN
AEROBIM_BSI_VALIDATION_URL
AEROBIM_CLASH_AFFECTS_PASS
AEROBIM_CLASH_MIN_AABB_VOLUME_M3
AEROBIM_CLASH_SKIP_TINY
AEROBIM_CORS_ALLOW_CREDENTIALS
AEROBIM_CORS_ORIGINS
AEROBIM_CROSS_DOC_SEVERITY
AEROBIM_CUSTOMER_PACK_LLM_EGRESS
AEROBIM_CUSTOMER_PACK_LLM_EGRESS_CONSENT_REF
AEROBIM_DB_URL
AEROBIM_DEBUG
AEROBIM_ENV
AEROBIM_GATES_ATTESTED
AEROBIM_HOST
AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE
AEROBIM_HYBRID_PROVIDER_CONFIG
AEROBIM_IFC_PARSE_CACHE_DIR
AEROBIM_KIMI_API_BASE_URL
AEROBIM_KIMI_API_KEY
AEROBIM_KIMI_CACHE_DIR
AEROBIM_KIMI_CACHE_NAMESPACE
AEROBIM_KIMI_CACHE_PROJECT
AEROBIM_KIMI_MODEL
AEROBIM_KIMI_REASONING_EFFORT
AEROBIM_LLM_429_RETRIES
AEROBIM_LLM_ADVISORY_ENABLED
AEROBIM_LLM_ADVISORY_MAX_ISSUES
AEROBIM_LLM_ALLOWED_HOSTS
AEROBIM_LLM_API_KEY
AEROBIM_LLM_AUTH_SCHEME
AEROBIM_LLM_BASE_URL
AEROBIM_LLM_BUDGET_LEDGER
AEROBIM_LLM_BUDGET_TZ
AEROBIM_LLM_DATA_LOGGING_ENABLED
AEROBIM_LLM_FOLDER_ID
AEROBIM_LLM_LOCAL_ENABLED
AEROBIM_LLM_MAX_COMPLETION_TOKENS
AEROBIM_LLM_MAX_CONCURRENT
AEROBIM_LLM_MAX_TOKENS_PER_CALL
AEROBIM_LLM_MAX_TOKENS_PER_DAY
AEROBIM_LLM_MAX_TOKENS_PER_RUN
AEROBIM_LLM_MODEL
AEROBIM_LLM_MODEL_REVISION
AEROBIM_LLM_MODEL_SHA256
AEROBIM_LLM_PROVIDER
AEROBIM_LLM_RESPONSE_FORMAT_MODE
AEROBIM_LLM_SEND_SEED
AEROBIM_LLM_TIMEOUT_SECONDS
AEROBIM_MAX_IFC_BYTES
AEROBIM_MAX_MODEL_BYTES
AEROBIM_MAX_OFFICE_BYTES
AEROBIM_MEP_AABB_FILTER
AEROBIM_MEP_FEDERATED_SCOPE_PATH
AEROBIM_MEP_SCOPE_MEMO_REF
AEROBIM_NORM_RULE_PACK
AEROBIM_OIDC_AUDIENCE
AEROBIM_OIDC_BFF_AUTHORIZE_URL
AEROBIM_OIDC_BFF_CLIENT_ID
AEROBIM_OIDC_BFF_CLIENT_SECRET
AEROBIM_OIDC_BFF_COOKIE_SECRET
AEROBIM_OIDC_BFF_REDIRECT_URI_ALLOWLIST
AEROBIM_OIDC_BFF_TOKEN_URL
AEROBIM_OIDC_ISSUER
AEROBIM_OIDC_JWKS_EXTRA_HOSTS
AEROBIM_OIDC_JWKS_URL
AEROBIM_OIDC_ROLES_CLAIM
AEROBIM_OIDC_TENANT_CLAIM
AEROBIM_PDF_BACKEND
AEROBIM_PORT
AEROBIM_PRIORITY_PROFILE
AEROBIM_REDIS_URL
AEROBIM_REMARK_LOCALE
AEROBIM_REPORT_TTL_DAYS
AEROBIM_REQUIRE_CLASH
AEROBIM_REQUIRE_MEP_SYSTEM_CLASH
AEROBIM_S3_ACCESS_KEY_ID
AEROBIM_S3_BUCKET
AEROBIM_S3_ENDPOINT_URL
AEROBIM_S3_PREFIX
AEROBIM_S3_REGION
AEROBIM_S3_SECRET_ACCESS_KEY
AEROBIM_SIGNOFF_PROFILE
AEROBIM_STORAGE_DIR
AEROBIM_TRUSTED_PROXY_IPS
AEROBIM_VLM_ENABLED
-->
<!-- AEROBIM_DOCUMENTED_ENV:END -->

## Repository

```text
backend/      FastAPI: core → domain → application → infrastructure → presentation
frontend/     Review shell (Vite + React; IFC 3D viewer)
samples/      IFC, IDS, drawing and specification fixtures
docs/         Documentation and evidence
audit/        Blocker register
submission/   Presentations: 7 slides and the full 43-slide deck
```

CI pass counts:

<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->
<!-- regenerated by: python -m aerobim.tools.export_runtime_baseline -->
tests_passed: backend=3499, frontend=410; commit c057a2e9f174; see docs/evidence/runtime-baseline-latest.json · src ~112860 LOC; tests ~73316 LOC; extraction macro_f1=0.8600000000000001 (fixture corpus; not product accuracy)
<!-- AEROBIM_RUNTIME_BASELINE:END -->

## Documentation

| Topic | Document |
|---|---|
| Presentation | [PowerPoint, 7 slides](submission/03-presentation/AeroBIM.pptx) · [PDF](submission/03-presentation/AeroBIM.pdf) · [slide text](submission/03-presentation/demo_day_slides.md) |
| Full deck | [PowerPoint, 43 slides](submission/03-presentation/AeroBIM-full.pptx) · [PDF](submission/03-presentation/AeroBIM-full.pdf) · [text](submission/03-presentation/AeroBIM-full.md) |
| Slide numbers | [what was measured and what it is not](submission/05-additional/README.md) |
| Verdict | [ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md) |
| Numbers in the pack | [calculation evidence](docs/calculation-evidence-boundary-2026.md) |
| Academic roadmap | [SOTA 2026 math and protocols](docs/quality/ACADEMIC_ROADMAP_2026_09.md) |
| IFC compatibility | [matrix](docs/ifc-compatibility-matrix.md) |
| Closed contour | [offline deployment](docs/offline-deployment-2026.md) |
| Review shell | [Frontend](frontend/README.md) |
| Licensing | [License policy](docs/license-policy-2026.md) |

## Cite

[`CITATION.cff`](CITATION.cff) or [`docs/CITATION.bib`](docs/CITATION.bib). Cite the Git tag or commit SHA, not a floating `latest`.

## Stack

Python 3.12+, FastAPI, Uvicorn. IFC — IfcOpenShell 0.9, IfcTester 0.9; IfcClash 0.9 optional. Review shell — Vite 8, React 19, web-ifc, Three.js, Vitest 5. PDF — pypdfium2, pdfminer.six, reportlab; PyMuPDF, RapidOCR and Docling optional.

## License

MIT for code authored in this repository. Third-party components keep their own licences: pypdfium2, pdfminer.six, Pillow and reportlab are permissive; IfcOpenShell and IfcTester are LGPL-3.0-or-later; web-ifc is MPL-2.0; PyMuPDF is dual AGPL-3.0 / Artifex and therefore stays an optional extra, absent from the runtime lock and the Docker image.

Inventory: [`audit/dependency_license_inventory.json`](audit/dependency_license_inventory.json) · policy: [`docs/license-policy-2026.md`](docs/license-policy-2026.md). This is not a legal opinion, and the product as a whole must not be described as MIT without disclosing third-party components.
