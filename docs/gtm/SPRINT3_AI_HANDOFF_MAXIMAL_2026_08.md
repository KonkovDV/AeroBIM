<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "AeroBIM Sprint 3 — engineering continuation brief"
date: 2026-08-07
audience: engineering team
repo: https://github.com/KonkovDV/AeroBIM
local_repo: this public repository
internal_corpus: sibling directory outside Git (aerobim-internal-data)
superseded_in_part_by: >-
  Internal reports/MAXIMAL_HANDOFF_2026_08_08.md (outside this Git tree;
  large-open wave complete: GNI fund, CISOL TD/unlabeled, BRIDGE, Eng_Diagrams,
  PID_dataset, PID2Graph + sample AeroBIM runs). Prefer that file for post-2026-08-08 continuation.
claim_boundary: >-
  Checkpoint NO_GO (RT-001/002/003). No production-ready / customer-ready /
  DWG-ready / accuracy-proven claims. IDS match-rate ≠ product precision.
  Internal corpus must never be committed to public Git.
---

# AeroBIM Sprint 3 — continuation brief

This document is the **Sprint-3 week continuation brief**. For the **large-open download wave (2026-08-08)** read first the internal report outside this Git tree (`reports/MAXIMAL_HANDOFF_2026_08_08.md` in the private data directory).
Prefer paths and evidence over re-deriving claims from unfiled notes.

---

## 0. Identity and constraints

| Item | Value |
|---|---|
| Product | AeroBIM — openBIM acceptance / validation assistant |
| Public repo | this tree → `https://github.com/KonkovDV/AeroBIM` |
| Internal data (OUTSIDE Git) | sibling directory `aerobim-internal-data/` |
| Intended consumers of internal data | author, Tehlab, Samolet (internal only) |
| Budget this phase | **$0** paid SDKs / licenses |
| Project checkpoint | **NO_GO** (RT-001, RT-002, RT-003 open) |
| Engineering / open-corpus status | **PARTIALLY_READY** |
| Forbidden slogans | `production-ready`, `customer-ready`, `DWG-ready`, `accuracy proven`, «точность 95% для заказчика» |
| Claims Lock | active — see `audit/reports/CLAIMS_LOCK_2026_07_17.md` |
| DWG | **not enabled**; requested DWG path must fail and keep `summary.passed=false` |
| VLM | advisory only; must not flip `summary.passed` |
| Commit/push | only if human explicitly asks |

### Hard rules for any continuation

1. Do **not** vendor `aerobim-internal-data/` into the public tree (`.gitignore` has `aerobim-internal-data/`).
2. Do **not** scrape ЕГРЗ/ГГЭ project packages without rightsholder legal basis.
3. Do **not** treat `issue_count` or IDS sample match-rate as customer accuracy.
4. Fix **only confirmed** product defects; add regression tests; re-run focused + broader gates.
5. Customer Samolet files → `corpus_kind=customer_internal`, separate from public datasets; no external VLM without written OK.
6. Author “full permissions” unlocks **intake of files they lawfully provide** and open datasets under their licenses — it does **not** unlock gated HF, government registry dumps, or invent missing customer files.

---

## 1. Sprint 3 discussed week tasks (authoritative status)

Source of truth: `docs/gtm/SPRINT3_WEEK_TASKS_STATUS_2026_08.md`

| # | Task | Status | Verdict |
|---|---|---|---|
| 1 | IFC formats tested? Meeting metrics (speed + accuracy honesty) | **DONE (evidence)** | Yes tested IFC2X3/IFC4/IFC4X3. Speed measured. Product accuracy **not** measured |
| 2 | Expertise-conclusion datasets for baseline comparison | **CHECKED — no RU open GT** | Cannot honestly baseline vs RU expertise on public data. Mumbai = foreign ACC analog (manual download). Need Samolet |
| 3 | Expand open docs, run, fix bugs | **DONE (engineering rails)** | Battery green; BSI 290 adjusted pass; IfcTester mapping fix; 22 upstream edges documented |

---

## 2. Repository state (public AeroBIM)

### Notable Sprint 3 / week artifacts in-repo

| Path | Role |
|---|---|
| `samples/benchmarks/project-package-ifc2x3-schema.json` | IFC2X3 fixture pack |
| `samples/benchmarks/project-package-ifc4-schema.json` | IFC4 fixture pack |
| `samples/benchmarks/project-package-ifc4x3-schema.json` | IFC4X3 fixture pack |
| `docs/evidence/ifc-release-benchmark-2026-08.md` | Schema-suite meeting table |
| `audit/evidence/ifc-release-benchmark-2026-08.json` | Schema-suite JSON |
| `docs/evidence/sprint3-week-ifc-metrics-2026-08.md` | Expanded IFC metrics for meeting |
| `docs/gtm/SPRINT3_WEEK_TASKS_STATUS_2026_08.md` | Week-task status |
| `docs/datasets/expertise-corpus-scan-2026-08.md` | Expertise GT inventory (answer: No) |
| `docs/datasets/customer-data-request-2026-08.md` | What Samolet must provide |
| `docs/quality/OPEN_CORPUS_TRIAGE_2026_08.md` | IFC2x3 Qto vs BaseQuantities honest non-support |
| `docs/dwg-blocker-memo-2026-08.md` | DWG legal/tech blocker |
| `samples/ids/buildingsmart-testcases/` | Vendored BSI IDS cases (CC BY-ND) |
| `backend/src/aerobim/domain/llm_extraction.py` | LLM extraction port (advisory) |
| `backend/src/aerobim/infrastructure/adapters/llm_extraction_adapters.py` | Adapters; live_provider=false in evidence |
| `backend/src/aerobim/infrastructure/adapters/raster_drawing_analyzer.py` | **FIXED** numpy OCR truth-test bug |
| `backend/tests/test_raster_drawing_analyzer.py` | Includes `test_numpy_ocr_boxes_do_not_crash_truth_test` |

### Uncommitted work

Many Sprint 3 files were **local/uncommitted** at last status (do not assume pushed). Before commit: human must ask; exclude secrets and internal corpus.

### Gates last known green (2026-08-08)

- ruff / mypy strict OK
- **1957 passed**, 7 skipped (full pytest)
- Red Team Waves 1–5b remediated (`2a4d1f4`)
- Open-corpora regression 7/7 (`docs/evidence/sprint3-open-corpora-regression-2026-08.md`)

### Runtime / deps relevant to drawings

- Raster OCR needs: `rapidocr` + `onnxruntime` (installed into `backend/.venv` during SFC-A68 run)
- Pillow present (hybrid priors)
- Official benchmark pack paths are **repo-root relative** and **cannot escape repo** (`_resolve_repo_path`). Absolute internal IFC must use custom scripts under `aerobim-internal-data/scripts/`, not `benchmark_project_package` packs pointing outside repo.

---

## 3. Internal corpus layout (outside this Git tree)

```text
aerobim-internal-data/
├── manifests/          # per-dataset JSON manifests + license decisions
├── raw/                # originals
│   ├── ifc/            # ifc43-sample-models, opensourcebim-testfiles
│   ├── ids/            # (mostly empty; BSI cases live in AeroBIM samples)
│   ├── architectural/  # SFC-A68.zip, empty FloorPlanCAD/AECV-Bench dirs
│   ├── engineering/    # BlueprintSymVL zip + unpacked
│   ├── pid/            # PIDQA clone
│   ├── pdf/            # Construction-document-digitalization clone
│   └── expertise/
│       └── customer_samolet_drop/   # EMPTY intake (ifc/pdf/remarks/ids)
├── normalized/
│   ├── architectural/SFC-A68/       # extracted 5577 files
│   └── pdf/construction-doc-digitalization-valid/
├── benchmark-packs/    # stubs + last_run pointers
├── hashes/
├── licenses/           # includes INTERNAL_AUTHORIZATION_2026-08-07.json
├── reports/            # catalogs, metrics, triage, run JSONs
├── logs/
├── rejected/
└── scripts/            # internal runners (NOT public product CLI)
```

### Key scripts (internal)

| Script | Purpose |
|---|---|
| `scripts/run_internal_analyze_smoke.py` | Analyze on absolute IFC paths |
| `scripts/run_internal_corpus_continuation.py` | Expanded IFC probe + Analyze + non-IFC inventory |
| `scripts/run_sfc_a68_aerobim.py` | Raster OCR + Hybrid + Analyze+PNG on SFC-A68 |
| `scripts/run_sprint3_week_ifc_metrics.py` | Meeting metrics: open speed + IDS sample |
| `scripts/hash_and_probe_ifc.py` | Earlier IFC probe helper |

### Authorization memo

`licenses/INTERNAL_AUTHORIZATION_2026-08-07.json` — author granted internal intake for lawfully provided files + APPROVED open sets. Explicitly does **not** grant EGRZ scrape, HF gate bypass, or customer→external VLM.

---

## 4. Dataset inventory (license + run status)

| dataset_id | location | license status | downloaded | run result |
|---|---|---|---|---|
| buildingsmart-ifc43-sample-models | `raw/ifc/ifc43-sample-models` | `LICENSE_UNCLEAR` | yes | open OK; exploratory Analyze |
| opensourcebim-testfiles | `raw/ifc/opensourcebim-testfiles` | `LICENSE_UNCLEAR` | yes | open OK; exploratory Analyze |
| AeroBIM fixtures | `AeroBIM/samples/ifc` | `APPROVED_INTERNAL` | in-repo | schema-suite + Analyze |
| BSI IDS TestCases | `samples/ids/buildingsmart-testcases` | `APPROVED_WITH_ATTRIBUTION` (CC BY-ND) | vendored | IDS sample 23/24; Analyze harness noise if wall-basic attached |
| PIDQA | `raw/pid/PIDQA` | `APPROVED_INTERNAL` (CC0 repo) | yes | QA md only; **no images** in clone |
| BlueprintSymVL | `raw/engineering/BlueprintSymVL` | `APPROVED_WITH_ATTRIBUTION` (CC BY 4.0) | yes (~6MB zip, 210 jpg unpacked) | inventory / VLM staging |
| SFC-A68 | zip + `normalized/.../SFC-A68` | `APPROVED_WITH_ATTRIBUTION` (CC BY 4.0) | yes | extracted; OCR/hybrid/Analyze+PNG run |
| construction-document-digitalization | `raw/pdf/...` | `LICENSE_UNCLEAR` | yes | **labels only**; images on Roboflow — not OCR-runnable |
| ArchCAD-400K | HF `jackluoluo/ArchCAD` | `REQUIRES_PERMISSION` (gated NC form) | no | machine `hf` **Not logged in** → 401 |
| Mumbai Building Permit | DOI 10.17632/fbytrnrdcr.1 | CC BY 4.0 | **downloaded** (666 PDF / 333 pairs) | foreign ACC scrutiny↔concession; **not RU expertise** |
| EGRZ/GGE project files | egrz.ru / gge.ru | `REQUIRES_PERMISSION` | **not downloaded** | do not scrape |
| Samolet customer | `customer_samolet_drop/` | awaiting written pack | **empty** | blocks RT-001 |
| PID_dataset Zenodo 8028570 | — | check before use | **not downloaded** | **6.7 GB** size gate |
| IFC-Bench v2 full models | HF | per-file; exclude GPLv3 | not full-mirrored | pins in `samples/benchmarks/ifc-bench-v2/`; smoke tooling exists |

Manifests: `aerobim-internal-data/manifests/*.json`.

---

## 5. IFC metrics (meeting-ready numbers)

### 5.1 Were IFC formats tested?

**Yes** — IFC2X3, IFC4, IFC4X3.

Commands used:

```bash
cd backend
python -m aerobim.tools.benchmark_project_package \
  --schema-suite --group-by schema --write-evidence \
  --output ../docs/evidence/ifc-schema-suite-meeting-2026-08.json
# defaults: iterations=20, warmup=2, shared container + suite prime
```

### 5.2 Analyze speed (fixture packs)

Evidence timestamp ~ `2026-08-08T07:37:03Z` (restabilized). Historical n=5 IFC4 p95≈568ms was nearest-rank≡max on one spike.

| Schema | bytes | entities | p50_ms | p95_ms | max_ms | spike max/p50 | issue_count (last) |
|---|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 997 | 12 | 23.882 | 24.617 | 24.728 | 1.035 | 6 |
| IFC4 | 997 | 12 | 23.379 | 24.203 | 24.976 | 1.068 | 4 |
| IFC4X3 | 1005 | 12 | 23.384 | 24.535 | 24.823 | 1.062 | 4 |

Machine fingerprint (schema suite): Windows-11-10.0.26200, Python 3.13.7, AMD64.  
Deps: ifcopenshell 0.8.5, ifctester 0.8.5, fastapi 0.140.0.

### 5.3 Open speed (`ifcopenshell.open`) — expanded corpus

| Schema | files | bytes min–max | entities max | open p50 (median across files) ms | worst open p95 ms |
|---|---:|---|---:|---:|---:|
| IFC2X3 | 7 | 997–7288853 | 130997 | 41.304 | 476.33 |
| IFC4 | 2 | 997–1142 | 14 | 0.176 | 0.222 |
| IFC4X3 | 9 | 1005–236853 | 3161 | 0.759 | 12.043 |

Earlier internal probe wave: **59 IFC OK / 0 fail** (`reports/ifc-ids-test-report.json`).

### 5.4 Accuracy — what may / may not be claimed

| Metric | Value | Meaning |
|---|---|---|
| Product / customer precision/recall/F1 | **NOT MEASURED** | No dual-adjudicated document↔remark GT |
| `accuracy_measured` on fixture benchmarks | **false** | By design |
| IDS engine match-rate vs BSI filename pass/fail | **0.9583 (23/24)** | IfcTesterIdsValidator vs TestCases sample — **not** expertise accuracy |
| Fixture `issue_count` | 4–6 | Not accuracy |

**Mismatch case:** `cases/0017/pass-an_optional_attribute_passes_if_null` — expected `pass`, IfcTester reports fail (`attribute value "None" is empty`). Classification: **upstream IDS/IfcTester edge**, not IFC parser crash. Do not “fix” by greenwashing. Locked in `KNOWN_UPSTREAM_EDGES.json` + [`ids-case-0017-optional-null-2026-08.md`](../evidence/ids-case-0017-optional-null-2026-08.md) + `test_ids_case_0017_upstream_edge.py`.

### 5.5 Known IFC honesty (not bugs)

From `docs/quality/OPEN_CORPUS_TRIAGE_2026_08.md`:

- IFC2x3 quantity set often named `BaseQuantities`, while IDS asks `Qto_WallBaseQuantities` → **honest non-support / degradation**, not PARSER_BUG.
- MEP-CLASH-001 stderr without federated MEP + scope memo → **EXPECTED_FAIL_CLOSED**.

---

## 6. Expertise conclusions / baseline comparison

### Question

Is there an open dataset of expertise conclusions with document↔remark pairs to compare AeroBIM to a baseline?

### Answer

**No usable Russian open corpus.** RT-001 cannot close from public data alone.

Full scan: `docs/datasets/expertise-corpus-scan-2026-08.md`  
Refresh: `aerobim-internal-data/reports/expertise-dataset-report.md`

| Source | Pairs? | Decision |
|---|---|---|
| ЕГРЗ / ГГЭ | No open packages | `REQUIRES_PERMISSION` — do not auto-download |
| BSI IDS / IFC-Bench / fixtures | Not expertise | open_bench / regression only |
| Mumbai Building Permit (CC BY 4.0) | Yes: scrutiny↔concession (India, 333 projects) | Foreign ACC analog; **on disk** (2026-08-08); never claim as RU expertise accuracy |
| Samolet package | Required | Only path to RT-001 |

### Baseline types possible today

| Baseline | Possible? |
|---|---|
| Empty / regex / IDS-only / deterministic AeroBIM on fixtures | Yes (engineering) |
| Human expertise on Samolet package | **Blocked** (no files on disk) |
| Mumbai ACC proxy | After manual download; claim_level must stay foreign ACC / exploratory |

### Samolet intake

Path: `aerobim-internal-data/raw/expertise/customer_samolet_drop/` (outside this Git tree).  
Need: `ifc/`, `pdf/`, `remarks/`, optional `ids/`, plus `AUTHORIZATION.txt`.  
See also: `docs/partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`, `docs/datasets/customer-data-request-2026-08.md`.

---

## 7. Drawing / document expansion runs

### 7.1 SFC-A68

| Field | Value |
|---|---|
| DOI | 10.5281/zenodo.14245850 |
| License | CC BY 4.0 |
| Zip SHA-256 | `A76E9801C2DA722F34989883FEA98ED3EFAEF6F7166F6CFE59D4BA20B5E9963F` |
| Extracted | 5577 files (~647 MB): 2176 png, 2176 svg, 1224 json |
| Splits | ML/GDL train 55 + test 13 each |
| PNG location for runs | `.../SFC-A68/IDL/test/<id>/input_imgs/*_inp_architectural_0000.png` |
| GT JSON | `.../SFC-A68/ML/test/<id>/<id>_data.json` |
| Run report | `reports/sfc-a68-aerobim-run.json` |

**Run summary (after OCR fix):**

| Path | Result |
|---|---|
| Raster OCR | 5/5 ok, 0 exceptions |
| Hybrid drawing | 5/5 ok (`hybrid_priors_ocr`) |
| AnalyzeProjectPackage + PNG (fixture IFC carrier) | 3/3 ok, `passed=false` expected |
| Space-label F1 vs SFC GT | **NOT computed** (`accuracy_measured=false`) |

**What was required to run drawings:** extracted PNGs + `pip install rapidocr onnxruntime` + DrawingSource path. Live VLM **not** required. SFC has **no** native IFC — Analyze uses fixture IFC as carrier.

### 7.2 Confirmed bug fixed (product)

| Field | Value |
|---|---|
| Classification | `ADAPTER_BUG` |
| Symptom | `ValueError: The truth value of an array with more than one element is ambiguous` when RapidOCR returns numpy `boxes` |
| Trigger | SFC-A68 IDL test case `0015` (non-empty OCR boxes ndarray) |
| Root cause | `boxes = getattr(...) or []` truth-tests numpy arrays |
| Fix | `RasterDrawingAnalyzer._ocr_sequence()` + coerce path to `str` for engine |
| File | `backend/src/aerobim/infrastructure/adapters/raster_drawing_analyzer.py` |
| Regression | `test_numpy_ocr_boxes_do_not_crash_truth_test` in `tests/test_raster_drawing_analyzer.py` |
| Re-run | SFC raster 5/5 ok after fix |

### 7.3 False bug candidates (do not “fix”)

| Case | Why not a product bug |
|---|---|
| `bsi-ids-0077` Analyze `passed=false` | `capabilities.ids=ok`; failures from attached `wall-basic.txt` (harness) |
| Open IFC + wall IDS exploratory fails | Rule pack not GT for those models |
| MEP-CLASH-001 stack traces | Expected fail-closed logging |

### 7.4 Construction-document-digitalization

- Cloned to `raw/pdf/Construction-document-digitalization`
- Contains `train.zip` / `valid.zip` / `test.zip` of **YOLO label .txt only**
- Images referenced via Roboflow / external PDF pages — **not in zip**
- `LICENSE_UNCLEAR` (no LICENSE file)
- Status: inventory only; not Analyze-ready

---

## 8. Architecture notes useful for continuation

### Analyze path

- DI: `Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE` via `bootstrap_container(Settings)`
- Drawings: `ValidationRequest.drawing_sources: tuple[DrawingSource, ...]`
- Raster suffixes: png/jpg/jpeg/webp/pdf (see `package_ingestion`)
- SVG **not** in raster asset suffixes — use PNG from SFC IDL `input_imgs`
- HybridDrawingAnalyzer allowlist sheet types: `plan_ar`, `plan_ov`, `title_block`; else OCR degrade

### Benchmark path limitation

`benchmark_project_package._resolve_repo_path` forbids paths outside repo root.  
For internal absolute IFC/PNG: use `aerobim-internal-data/scripts/*`.

### LLM extraction

Port + adapters exist; evidence docs mark live Kimi/Qwen **NOT RUN** / `live_provider=false`. Do not claim live LLM accuracy.

---

## 9. Evidence index (read these first)

### Public (AeroBIM)

1. `docs/gtm/SPRINT3_WEEK_TASKS_STATUS_2026_08.md`
2. `docs/evidence/sprint3-week-ifc-metrics-2026-08.md`
3. `docs/evidence/ifc-release-benchmark-2026-08.md`
4. `docs/datasets/expertise-corpus-scan-2026-08.md`
5. `docs/datasets/customer-data-request-2026-08.md`
6. `docs/quality/OPEN_CORPUS_TRIAGE_2026_08.md`
7. `docs/dwg-blocker-memo-2026-08.md`
8. `audit/reports/CLAIMS_LOCK_2026_07_17.md`
9. `audit/reports/SPRINT3_RED_TEAM_AUDIT_2026.md` (if present)

### Internal (never publish contents)

1. `reports/sprint3-week-ifc-metrics.json`
2. `reports/sfc-a68-aerobim-run.json`
3. `reports/internal-analyze-expanded.json`
4. `reports/ifc-ids-test-report.json`
5. `reports/dataset-catalog.md`
6. `reports/dataset-license-audit.md`
7. `reports/expertise-dataset-report.md`
8. `reports/error-triage.md`
9. `reports/architectural-drawing-report.md`
10. `licenses/INTERNAL_AUTHORIZATION_2026-08-07.json`
11. `manifests/*.json`

---

## 10. Recommended next actions (ordered)

1. **Meeting pack:** use §5 tables + `SPRINT3_WEEK_TASKS_STATUS` — do not invent accuracy %.
2. **Samolet:** if files appear in `customer_samolet_drop/`, quarantine as `customer_internal`, hash, de-identify check, run Analyze **without** mixing into public packs, **without** external VLM.
3. **Mumbai:** downloaded 2026-08-08 into `raw/expertise/mumbai-building-permit/` (CC BY attribution); claim_level `foreign_acc_analog`; exploratory PDF text only — never RU expertise accuracy.
4. **ArchCAD:** only after `hf auth login` + dataset terms acceptance; NC internal only.
5. **IDS 0017:** documented upstream edge — keep in denominator; do not claim AeroBIM IDS 100%.
6. **IFC4 p95:** restabilized 2026-08-08 (n=20 + suite prime); headline p95≈24ms. Keep fixture_only claim.
7. **Construction specs:** obtain images via Roboflow only if license clarified; else leave `LICENSE_UNCLEAR`.
8. **Do not** enable DWG or claim DWG support.
9. **Gates after code changes:**
   ```bash
   cd backend
   python -m ruff format --check src tests
   python -m ruff check src tests
   python -m mypy src
   python -m pytest tests -q
   ```

---

## 11. Red-team checklist (must remain true)

- [x] No EGRZ project files auto-downloaded
- [x] No customer files in Git
- [x] No external VLM on customer docs
- [x] Internal corpus outside public repo
- [x] LICENSE_UNCLEAR IFC not claimed freely redistributable
- [x] CC BY sets kept with attribution; not shipped in public distro
- [x] `summary.passed` not flipped by VLM
- [x] DWG not presented as supported
- [x] Fixture/open-bench metrics not labeled customer accuracy
- [x] Train/test of SFC not mixed into fake product accuracy
- [x] Mumbai on disk (foreign ACC; not RU GT)
- [ ] Samolet still empty (pending)

---

## 12. One-paragraph status for humans

IFC2x3/4/4x3 were tested with reproducible speed numbers (fixture Analyze p50 ~23–26 ms; large IFC2x3 open p95 ~0.5 s). Product accuracy is not measured; IDS engine sample agreement is 95.8% on 24 BSI cases and must not be sold as customer precision. No open Russian expertise-conclusion corpus exists for baseline comparison; Samolet data is required; Mumbai is a foreign ACC candidate pending manual download. Open corpus expanded (SFC-A68 run, BlueprintSymVL, etc.); one real OCR adapter bug was fixed with a regression test. Checkpoint remains NO_GO; internal open-corpus status PARTIALLY_READY.

---

## 13. Final machine statuses

| Scope | Status |
|---|---|
| Project checkpoint (RT-001/002/003) | `NO_GO` |
| Internal open-corpus testing | `PARTIALLY_READY` |
| Sprint 3 week task 1 (IFC metrics) | `DONE_WITH_EVIDENCE` |
| Sprint 3 week task 2 (expertise GT) | `BLOCKED_BY_DATA` (open RU) / Mumbai `foreign_acc_analog` **ON_DISK** |
| Sprint 3 week task 3 (expand/run/fix) | `PARTIALLY_DONE` (open-corpora 7/7; RT Waves 1–5b closed) |
| Meeting usability (Tehlab internal) | `YES` with Claims Lock |
| Customer / production claims | `NO_GO` |
