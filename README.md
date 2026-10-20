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
[![CodeQL](https://img.shields.io/github/actions/workflow/status/KonkovDV/AeroBIM/codeql.yml?branch=main&label=CodeQL)](https://github.com/KonkovDV/AeroBIM/actions/workflows/codeql.yml?query=branch%3Amain)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Cite: CITATION.cff](https://img.shields.io/badge/cite-CITATION.cff-orange.svg)](CITATION.cff)

**AeroBIM** catches the seam in design and working documentation. The code is open, under the MIT licence.

The model is clean. The sheet is clean. The schedule agrees with itself. Then the site finds ten millimetres: 30 mm of cover in the model, 40 mm on the sheet. The program pulls them out. The card carries the clause, the storey or grid, the GUID. The expert decides. Out go HTML, JSON, PDF, and a BCF file.

Three shelves. AeroBIM is the one where the files meet.

| Shelf | What it does | Its job |
|---|---|---|
| CDE (10D, Pilot-BIM, Sarex) | Presence, route, versions | Carries the pack through the life of the project |
| Model checker (Tangl, Solibri) | Model, attributes, clashes in the authoring environment | Looks inside the model |
| **Pack gateway (AeroBIM)** | Cross-file check; the acceptance profile is IDS | Holds the seam: model, sheet, schedule, calculation |

One pack, one flag. The wording model can be off or on. The verdict stays the same.

**What a finding looks like.** The ten millimetres above are the scheme from the slides. The fixture pack in git carries its own planted defect, and one command finds it: requirement `REQ-FIRE-001` asks for a REI60 fire wall, and the wall `1XYVUKGoDDbREfVxRKsHkl` carries REI30 in the model. The card holds the requirement, the GUID, and the value on each side. A person decides. Out goes a BCF 2.1/3.0 file.

## Contents

- [Where to look](#where-to-look)
- [Pack answers](#pack-answers)
- [Alongside](#alongside)
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
- [Contributing and security](#contributing-and-security)
- [License](#license)

## Where to look

1. The finding — [try it](#try-it), one command on the fixture pack.
2. The expert's table — `.\start.bat` from the clone root: model, sheet and decision together.
3. The kernel — [numbers, marks, stamps and calculations](#numbers-marks-stamps-and-calculations). The expressions are [here](#the-expressions).
4. Where the 2025–2026 moves come from — [the design table](#why-the-checker-is-built-this-way).
5. How to join in — [contributing and security](#contributing-and-security).

## Pack answers

A doubt does not become a pass. A required capability in `NOT_VERIFIED` holds the pack. The rows are checked top to bottom, and the first match wins (`package_outcome.py`).

| Answer | When |
|---|---|
| Failed | `failed`. An error-level finding, or a hard clash while that policy is on |
| Held | `blocked`. The intake is closed, or a required capability is not `OK` |
| To the expert | `review_required`. A drawing read, a missing source or a low confidence waits for the expert |
| Passed, warnings alive | `pass_with_warnings`. Warnings leave the flag lit |
| Passed | `pass`. No fatal finding remains, and every required capability stands at `OK` |

`summary.passed` lights on the last two.

## Alongside

Each repository does its own work.

| | |
|---|---|
| [OpenRebar](https://github.com/KonkovDV/OpenRebar) | Lays the slab bars and writes a declared report. AeroBIM compares it with the pack by SHA-256 |
| [Kontur](https://github.com/KonkovDV/Kontur) | Compares design, working and as-built volumes. The inspector confirms the card |
| **AeroBIM** | Holds the seam of model, sheet, schedule and calculation. The program sets the flag |

## What AeroBIM accepts

| | |
|---|---|
| Ingest | IFC 2x3 / 4 / 4x3, IDS 1.0, PDF vector/raster, specification text |
| Cross-check | IFC, IDS and the other files in the pack. The tolerance on a number is decimal |
| Workplace | Review shell (Vite): the IFC model, the saved sheet, and the zone from the report, in Russian and English. The expert presses the decision. The drawing stays as drawn |
| Report | HTML + JSON + PDF + structural BCF 2.1 / 3.0 ZIP |
| Verdict | The program sets `summary.passed`. In ISO 19650 that is a Shared-gate: the pack cleared the rules that are on ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)) |

A pass begins where every mandatory check has finished.

## Stage

Regulatory-measurement MVP. One command on a fixture pack in `samples/` lays the finding next to its evidence. The run is already alive.

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

`summary.passed=false` on the fixture pack means the planted defects were found. The last line of the output is JSON with `"passed": false`, `"jury_rule_id": "REQ-FIRE-001"` and `"jury_ifc_guid": "1XYVUKGoDDbREfVxRKsHkl"`. Do not set `AEROBIM_SIGNOFF_PROFILE=customer_pilot` on a first clone. `requirements-lock.txt` is the Linux/CI lock — do not install it on Windows.

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

Start the review shell **from the clone root** (not from `frontend/`). FastAPI at `http://127.0.0.1:8080`, Vite/React at `http://127.0.0.1:5173`. The expert sits in the browser; the verdict stays with the program. You need `backend/.venv` already created and Node 22.22.2+.

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
| 4. Report and decision | Every finding carries `finding_id`, `source_id` and `evidence_refs`; a finding without them is refused. A reviewer can accept, reject, mark a false positive, or ask for clarification; a rejection, false positive or clarification requires a note and never flips `summary.passed`. People get HTML; machines get JSON; issue exchange gets a structural BCF 2.1 / 3.0 ZIP. The browser review shell (web-ifc + Three.js) shows the IFC and the saved sheet preview with the zone from the report; the drawing stays as drawn. The fixture overlay CLI remains a separate run | [`docs/architecture/ADR-001-verdict-ownership-2026.md`](docs/architecture/ADR-001-verdict-ownership-2026.md) |

The program builds `summary.passed` from its own errors and the capability table ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)). A language model, when it is on, drafts the wording; on a customer profile it stays inside the contour. Every optional check answers `ok`, `skipped` or `failed`; any `FAILED` puts the pass out. The same picture is on `GET /v1/system/capabilities`. That is a Shared-gate under the rules that are switched on.

## Numbers, marks, stamps and calculations

- **Decimal tolerance band.** Construction measurements are normalized to SI (`quantity.py`), and the difference is computed in `Decimal` (`measured_delta` / `within_epsilon`): $\delta(a, b) = \mathrm{Decimal}(\mathrm{str}(a)) - \mathrm{Decimal}(\mathrm{str}(b))$, and the values agree when $\lvert\delta(a, b)\rvert \le \mathrm{Decimal}(\mathrm{str}(\varepsilon))$. A value on the boundary stays inside the band: `1.1` and `1.0` at a tolerance of `0.1` agree without a binary floating-point tail. Russian (`1 254,30`) and European (`1.254,30`) grouped numbers are parsed; an ambiguous token such as `1.254` (one digit before three digits) is rejected instead of guessed.
- **Steel grades and system marks.** Cyrillic and Latin lookalike letters in a grade are folded (`С345` and `C345` are one steel grade in `label_identity.py`), while a Roman `I` stays `I`. A short riser list or range on a ventilation schedule (`В2.7,8,9`, `В2.4–В2.6`) matches any single riser inside it in `target_ref`. A grille dimension with `*` (`П300*300`) stays a dimension and is not expanded as a mark list. An `IfcRoot.GlobalId` (22 characters, ISO 10303-21) is matched character for character; `ALL`, `*`, `ANY` or an empty `target_ref` applies to all instances of the entity. Mark identity is not a system-clash verdict.
- **Title blocks and drawing reads.** On 2D stamps (`stamp_dual_read.py`), the vector PDF text layer and OCR must agree after normalization: Unicode NFKC, then `ё` and `Ё` map to `е` and `Е`, runs of whitespace collapse to one space, then strip and casefold. OCR confidence must be known and at least `0.5`. Disagreement, unknown confidence, or confidence below that floor returns `ABSTAIN` (or `NOT_VERIFIED` when both are empty) and sets `requires_hitl=true`. For optional VLM drawing reads, verbalized confidence is only an abstention floor (`abstention_sweep.py`, $\tau \in \lbrace 0.35, 0.45, 0.60, 0.75 \rbrace$). Raising the floor does not decrease the share of `hitl_required`. Without outcome labels, ECE and Brier stay `null`.
- **Declared calculation tables.** Office tables (`xlsx`, `docx` via `spreadsheet_load_evidence_adapter.py`) are compared against BIM/working-documentation tables by declared values inside the decimal tolerance band (`calculation_table_compare.py`, dimensionless $\varepsilon = 10^{-3}$). The citable observation unit is the triple `element_id`, `section_id`, `parameter_id`. When both sides carry the same non-empty triple, `observation_status` is `COMPLETE`. A blank coordinate, a missing side, a duplicate `field_id` or two different triples stay `NOT_VERIFIED`. `MATCH` means the printed numbers agree; the solver is not re-run.

## Why the checker is built this way

The 2025–2026 practice sits in the kernel. The last word stays with the program.

| Observation from 2025–2026 practice | Design choice in AeroBIM |
|---|---|
| A dense sheet can fool a model's eye (`AECV-Bench`, arXiv:2601.04819; Iversen & Huang, *Automation in Construction* 2025; Fuchs et al., EC3) | `EvidenceAssembler` and `DeterminismGate` light the verdict ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)). The wording draft carries `origin="advisory"`, and with the model off the verdict is the same: `OFF == ON` |
| A VLM likes its own confidence more than the sheet deserves (VL-Calibration, ACL 2026) | Confidence walks the region to the expert: the `hitl_required` floor and a living calibration |
| A small sample and a naive $\kappa$ on a skewed table paint too smooth a picture | Proportions live in a Wilson 95% interval. Labeling sample size (`study_design.py`, `plan_adjudication_corpus.py`, `n_labeled=0`) is the larger of 62 and 111, so `recommended_n = 111`. Agreement reports Cohen's $\kappa$, Krippendorff's $\alpha$ and Gwet's $\mathrm{AC}_1$. Calibration reports equal-mass ECE and the Brier score (`compute_reliability_report.py`, `eval_statistics.py`). It steps into the light on a customer corpus once $n \ge 100$. The expressions are below |
| A fixed $\alpha$ on every commit slowly raises the noise | Sequential monitoring (`sequential_inference.py`, `e_process_simulation.py`) turns $p$ into $e$ with the Vovk–Wang calibrators, or runs a truncated aGRAPA martingale. Ville's inequality holds the share of trajectories. The expressions are below |
| A number copied by hand drifts away from the run | `manuscript_tables.py` takes a cell from the pin when `attested_by="ci"` and `claim_level` is filled |

### The expressions

$$
V(\mathcal{P}) = \mathbb{I}\bigl(\lvert E_{\mathrm{det}}\rvert = 0 \quad\land\quad \forall c \in C_{\mathrm{req}}: \mathrm{state}(c) = \mathrm{OK}\bigr)
$$

A pass lights up when no fatal finding remains and every required capability stands at $\mathrm{OK}$. A closed intake, a drawing waiting for the expert, and a hard clash hold the pack. Warnings leave the pass alive.

$$
\mathrm{hitl}(c, \tau) = \mathbb{I}\bigl(c < \tau \quad\lor\quad \neg\mathrm{calibrated}\bigr)
$$

$$
\mathrm{AC}_1 = \frac{p_o - p_e^{(\gamma)}}{1 - p_e^{(\gamma)}}
$$

$$
\mathrm{ECE} = \sum_{m=1}^{K} \frac{\lvert B_m\rvert}{n}\bigl\lvert\mathrm{acc}(B_m) - \mathrm{conf}(B_m)\bigr\rvert, \qquad \mathrm{BS} = \frac{1}{n}\sum_{i=1}^{n}(f_i - o_i)^2
$$

$$
f_\kappa(p) = \kappa p^{\kappa - 1}, \qquad F(p) = \frac{1 - p + p\ln p}{p(\ln p)^2}
$$

$$
W_T = \prod_{t=1}^{T}\bigl(1 + \lambda_t(x_t - \tfrac{1}{2})\bigr)
$$

Here $x_t = (d_t + 1) / 2$, and $d_t$ is the step difference from $-1$ to $1$.

$$
\mathbb{P}_0\bigl(\sup_{t \ge 1} E_t \ge 1/\alpha\bigr) \le \alpha
$$

## Capabilities

- IFC property and quantity validation; IDS 1.0 opens with a living rule set and a whole schema
- Cross-document contradictions and drawing notes vs IFC
- Decimal tolerance band (SI-normalised); lookalike steel grades and short system-mark lists share an identity; deterministic requirement extraction from narrative text; the program signs the result
- Every check reports `ok` / `skipped` / `failed`; tenant/object ACL on artifacts under `customer_pilot` / `production` (off by default in development); HTML/JSON; PDF; structural BCF 2.1 / 3.0 ZIP
- PDF via pypdfium2 + pdfminer; default `AEROBIM_PDF_BACKEND=pdfium`
- Browser IFC viewer and the sheet preview with the zone stored on the report. The drawing stays as drawn
- Norm rule packs from the published sets in `samples/`, and an opt-in completeness inventory
- Quality measurement protocol (Wilson intervals, exact binomial sample-size planner, equal-mass ECE, Brier score, Gwet's $\mathrm{AC}_1$, e-process regression monitor)

Optional: geometry clash `.[clash]`; OCR `.[raster]`; PyMuPDF `pdf-agpl`; LLM/VLM drafts of the wording; OpenCDE BCF push (experimental; not CDE import proof); DXF via ezdxf.

## HTTP API

`GET /health` and `GET /ready` need no token. `/v1/*` requires `AEROBIM_API_BEARER_TOKEN` unless `AEROBIM_ALLOW_ANONYMOUS_DEV=true` (development only; loopback bind or `AEROBIM_ANONYMOUS_EXTERNAL_LOOPBACK=true`).

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness: storage, plus Redis outside development. A `503` names what is missing |
| `GET` | `/v1/system/capabilities` | Capability boundary |
| `POST` | `/v1/uploads` | Multipart ingest |
| `POST` | `/v1/validate/ifc` | Validate IFC against requirements and IDS |
| `POST` | `/v1/analyze/project-package` | Full package analysis |
| `POST` | `/v1/analyze/project-package/reinforcement-digest` | SHA-256 provenance digest of an OpenRebar report |
| `POST` | `/v1/analyze/project-package/submit` | Queue a larger package in Redis for the dedicated `aerobim.worker` |
| `GET` | `/v1/analyze/project-package/jobs/{job_id}` | Poll a background job |
| `POST` | `/v1/analyze/project-package/jobs/{job_id}/cancel` | Cancel |
| `GET` | `/v1/reports` | List persisted reports |
| `GET` | `/v1/reports/{id}` | Fetch one report |
| `GET` | `/v1/reports/{id}/coverage` | Check coverage map |
| `GET` | `/v1/reports/{id}/source/ifc` | The IFC behind the report, for the viewer |
| `GET` | `/v1/reports/{id}/drawing-assets/{asset_id}/preview` | The saved sheet preview |
| `GET` | `/v1/reports/{id}/revision-diff` | The delta of findings between two reports |
| `GET` | `/v1/reports/{id}/export/{json,html,pdf,bcf}` | Export; `?version=3` switches BCF 3.0 |
| `POST` | `/v1/reports/{id}/export/bcf-api/push` | Experimental send into an OpenCDE BCF API hub |
| `POST` | `/v1/reports/{id}/review-events` | The expert's decision lands in the journal |
| `GET` | `/v1/reports/{id}/review-events` | HITL history |
| `GET` | `/v1/reports/{id}/review-kpi` | The triage summary on the expert's table |
| `POST` | `/v1/norm-packs/{pack_id}/rule-events` | A rule edit becomes a new norm pack version. `customer_approved` needs a person signed in through OIDC |
| `GET` | `/v1/norm-packs/{pack_id}/versions` | Norm pack versions |
| `GET` | `/v1/auth/bff` | Auth discovery. Default **501**. A lab `200 LAB` lights the stand |
| `GET` | `/v1/auth/login` · `/v1/auth/callback` · `/v1/auth/session` | Lab OIDC sign-in with an HttpOnly session cookie. **501** until the lab is configured |
| `POST` | `/v1/auth/logout` | Ends the lab session |

In development, `POST /v1/demo/seed-fixture` loads the git fixture pack for a rehearsal. OpenAPI does not list it, and other environments do not mount it.

Package analysis takes an OpenRebar reinforcement report with a SHA-256 digest and compares the declared sources.

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
| Slide numbers | [how the numbers were taken](submission/05-additional/README.md) |
| Verdict | [ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md) |
| Numbers in the pack | [calculation evidence](docs/calculation-evidence-boundary-2026.md) |
| Academic roadmap | [SOTA 2026 math and protocols](docs/quality/ACADEMIC_ROADMAP_2026_09.md) |
| Reproducibility | [reference commit and FAIR check](docs/REPRODUCIBILITY-2026.md) |
| Claim boundary | [what is measured, and on which data](docs/pilot-claim-boundary-2026.md) |
| IFC compatibility | [matrix](docs/ifc-compatibility-matrix.md) |
| Closed contour | [offline deployment](docs/offline-deployment-2026.md) |
| Review shell | [Frontend](frontend/README.md) |
| Licensing | [License policy](docs/license-policy-2026.md) |

## Cite

[`CITATION.cff`](CITATION.cff) or [`docs/CITATION.bib`](docs/CITATION.bib). Cite a commit SHA. The CI-attested commit sits in [`docs/evidence/runtime-baseline-latest.json`](docs/evidence/runtime-baseline-latest.json).

## Stack

Python 3.12+, FastAPI, Uvicorn. IFC — IfcOpenShell 0.9, IfcTester 0.9; IfcClash 0.9 optional. Review shell — Vite 8, React 19, web-ifc, Three.js, Vitest 5. PDF — pypdfium2, pdfminer.six, reportlab; PyMuPDF, RapidOCR and Docling optional. DXF — ezdxf, optional.

## Contributing and security

Start with [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md). [`AGENTS.md`](AGENTS.md) carries the same rules for automated contributors, with the checks to run before a pull request. A vulnerability goes to private reporting, described in [`.github/SECURITY.md`](.github/SECURITY.md). Questions: [`.github/SUPPORT.md`](.github/SUPPORT.md). Conduct: [`.github/CODE_OF_CONDUCT.md`](.github/CODE_OF_CONDUCT.md). Releases: [`governance/RELEASE_POLICY.md`](governance/RELEASE_POLICY.md).

## License

MIT for code authored in this repository. Third-party components keep their own licences: pypdfium2, pdfminer.six, Pillow and reportlab are permissive; IfcOpenShell and IfcTester are LGPL-3.0-or-later; web-ifc is MPL-2.0; PyMuPDF is dual AGPL-3.0 / Artifex and therefore stays an optional extra, absent from the runtime lock and the Docker image.

Inventory: [`audit/dependency_license_inventory.json`](audit/dependency_license_inventory.json) · policy: [`docs/license-policy-2026.md`](docs/license-policy-2026.md). Name the third-party licences next to MIT.
