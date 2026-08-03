---
title: "Red Team — remote KT#2 exec audit vs local HEAD"
status: active
version: "1.0.0"
last_updated: "2026-08-03"
claim_boundary: "Local HEAD verify of remote-read exec summary. Checkpoint NO_GO. Not legal opinion."
---

# Red Team — remote KT#2 exec audit vs local HEAD

**Date:** 2026-08-03  
**Remote source:** executive summary (remote-read, no clone/run; INFERRED unless file-backed)  
**Local HEAD:** `09fdb47255c533b9786f58d75952b36edc9c1097` (2026-08-03)  
**Checkpoint:** **NO_GO** (RT-001 / RT-002 / RT-003 OPEN)

## Boundary (read first)

Remote audit warned of GitHub raw/API snapshot drift (~20.07 README «9 ports / 171 tests», stale `ci.yml`).  
**This file supersedes point-level BLOCKER claims only where local HEAD contradicts them.**  
External law/market citations from the remote text are **not re-verified here** (status = as in remote: VERIFIED / PUBLIC CLAIM / NOT VERIFIED).

## Snapshot drift — local check

| Claim from remote | Local HEAD | Verdict |
|---|---|---|
| `ci.yml` findings may be BLOCKER if reproduced | `.github/workflows/ci.yml` present; hashed locks; `offline-bundle-smoke`; install contract RT-POST-09 | **Stale-CI BLOCKER NOT REPRODUCED** |
| README «9 ports / 171 tests» (April) | README documents LIC-001 Option B, runtime baseline SSOT, Checkpoint NO_GO | **Stale README NOT REPRODUCED** |
| Core deps include `pymupdf` (AGPL) | `dependencies` = `pypdfium2` + `pdfminer.six`; `pymupdf` only in optional `pdf-agpl` | **AGPL-in-core BLOCKER RETRACTED** |

## Ten kill-points vs HEAD

| # | Remote claim | Local status | RT ID | KT#2 action |
|---|---|---|---|---|
| 1 | AGPL in core via pymupdf; MIT slide broken | **RETRACTED as core BLOCKER.** LIC-001 Option B landed. Residual: optional `pdf-agpl`, slide must still say MIT = own code only; CI dev-lock still compiles `--extra=pdf-agpl` (dev/fixture, not runtime install of `-e .`) | RT-018 | Keep Claims Lock; do not re-open unless someone installs `pdf-agpl` into customer contour |
| 2 | Customer contour: no offline path | **PARTIAL (matches remote).** Docker image-track smoke VERIFIED; bare-metal wheelhouse DEFERRED (`exit 2`); no GitVerse mirror / docker-save release pack as product deliverable | RT-019 | Deliverable: release tarball + SBOM + mirror plan by 12.08 if contour demo required |
| 3 | PDF semantic integrity hole under deterministic core | **OPEN literature; ENG_PARTIAL wired.** Digit-run text↔OCR collision → FAILED (pass-blocking) when RapidOCR present; char-ratio WARNING; not arXiv full coverage | RT-020 | Keep Claims Lock; ship with `raster` for contour demo; do not claim 25-gap closure |
| 4 | УКЭП required by ГрК; repo only presence-only | **OPEN / honesty MITIGATED.** `RT-RES-SIG-01`; trust_chain `not_verified`; no CryptoPro contour | RT-021 | Product: read-only originals + hash chain; УКЭП verify = NOT_VERIFIED without ГОСТ provider |
| 5 | Competitive slide wrong (Pilot-BIM / 10D vs Solibri…) | **Strategy OPEN** (docs not the gate). BCF→10D UNKNOWN | RT-022 | Meeting Q1: 10D BCF/API contract; retire Solibri-as-incumbent slide for РФ закупка |
| 6 | RT-002 / LLM→IDS — ITMO peer work exists | **OPEN (customer norms).** RequirementToIds = planned; do not claim compiler SOTA without peer baseline | RT-023 | Partner or “advisory + HITL + published metrics compare” |
| 7 | Buyer = ГИП / audit trail, not −20% hours | **Strategy OPEN.** NРС exclusion thesis = NOT VERIFIED in remote | RT-024 | Slide: personalized audit trail; no NРС claim without norm cite |
| 8 | ЕИСЖС / ПНСТ 909 pre-flight product | **Strategy OPEN.** Norm packs already versioned; ПНСТ sunset 01.02.2027 noted externally | RT-025 | Optional product lane; version packs to edition |
| 9 | RT-001 κ>0.8 protocol indefensible | **OPEN methodology.** Repo has Krippendorff α tooling; protocol incomplete (n, strata, Gwet AC1, prereg) | RT-026 | Preregister protocol **before** corpus lands |
| 10 | AI regulation + 152-ФЗ missing from Claims Lock | **PARTIAL gap.** LLM advisory + PII gate exist; synthetic-content marking + role matrix not locked | RT-027 | Claims Lock patch: mark LLM remarks; SaaS vs contour operator roles; stamps = ПДн |

## What remote got right (do not touch)

- DeterminismGate / Shared-gate `summary.passed` / capability honesty / provenance reject / Claims Lock / public NO_GO — keep.
- Problem class = delivery hygiene + jurisdiction, not architecture rewrite.
- RT-001/002/003 remain Checkpoint blockers (customer artifacts).

## What remote got wrong on HEAD

1. **AGPL in core** — false after LIC-001 Option B (`pyproject.toml` lines 23–33 vs optional 83–87).  
2. **Stale CI / April README** — not current on `09fdb47`.  
3. Treating LIC-001 as unfinished 1–2 day fix — already shipped; residual is contour discipline (`pdf-agpl` must not ship to Samolet closed contour).

## Registry RT-018 … RT-031

| ID | Theme | Severity | Status |
|---|---|---|---|
| RT-018 | AGPL/PyMuPDF core claim drift | Medium (residual) | **MITIGATED** core; residual optional extra |
| RT-019 | Offline / RF supply (wheelhouse, docker save, mirror) | High (demo) | **ENG_PARTIAL** — docker save + SBOM-lite + INSTALL/MIRROR docs; bare-metal DEFERRED; GitVerse = checklist only |
| RT-020 | PDF semantic integrity (render≠extract) | High (trust) | ENG_PARTIAL digit-run collision; literature OPEN |
| RT-021 | УКЭП / ГрК vs envelope ENG_PARTIAL | High (law) | OPEN crypto; honesty MITIGATED; **hash-chain eng landed** |
| RT-022 | Competitive framing / 10D CDE | Medium (sales) | OPEN |
| RT-023 | LLM→IDS vs ITMO / Ishigaki baseline | Medium (claims) | **DOCUMENTED** — `docs/research/LLM_TO_IDS_BASELINE_2026_08_03.md`; no SOTA claim |
| RT-024 | Buyer / value prop (ГИП vs hours) | Medium (sales) | OPEN |
| RT-025 | ЕИСЖС / ПНСТ 909 pre-flight lane | Low–Med (product) | OPEN optional |
| RT-026 | RT-001 inter-rater protocol | High (science) | **DRAFT + AC1 wired** — protocol + prereg template + Gwet AC1 |
| RT-027 | AI FZ draft + 152-ФЗ / synthetic mark | Medium (claims) | **PARTIAL** — Claims Lock + UI mark when `ai_generated` |
| RT-028 | Snapshot-drift / remote-read false positives | Process | **CLOSED** by this verify |
| RT-029 | Studio grant burn / card auto-charge (ops) | Medium (ops) | OPEN operator — see grant ops report |
| RT-030 | Analyze advisory overlay vs HybridRouteGate audit | Medium (eng) | **MITIGATED** — gate before overlay |
| RT-031 | Day-cap ledger not fail-closed at boot | Medium (eng) | **MITIGATED** — ledger required when LLM ready |

## 4-day / 17-day triage (engineering only)

**Do first (protect Checkpoint honesty):** RT-026 protocol draft ✅; RT-027 Claims Lock ✅; RT-020 digit-run collision ✅; RT-030/031 ✅.  
**Do if contour demo:** RT-019 release pack.  
**Do not re-litigate:** RT-018 core AGPL as if unfixed.  
**Customer-gated (cannot eng-close):** RT-001/002/003, RT-021 crypto without CryptoPro license, RT-022 10D contract.  
**Operator:** RT-029 grant burn / live ₽ measure.

## Questions to «Самолёт» (from remote + local)

1. Target CDE for BCF = **10D СОД**? API/BCF contract / sample import evidence?  
2. Contour: Docker-only offline acceptable, or bare-metal wheelhouse mandatory?  
3. УКЭП: CryptoPro (or equivalent) available in contour, or accept `NOT_VERIFIED` for pilot?  
4. Norm pack owner + expert journal for RT-002?  
5. Corpus access + labeling SLA for RT-001 (before we publish κ/α)?  
6. Confidentiality tier for pilot packages (blocks Studio cloud path if CONFIDENTIAL)?

## ClickUp Task 07 reply (2026-08-03 local HEAD)

Remote doc still asserts three urgent items. **Local `origin/main` = `09fdb47`:**

### 1. License — do not spend 06.08 on “move pymupdf out of core”

```text
git show origin/main:backend/pyproject.toml
```

- `dependencies` = `pypdfium2` + `pdfminer.six` (+ FastAPI stack).  
- `pymupdf` is **only** under `[project.optional-dependencies] pdf-agpl`.  
- Claims Lock + README already: MIT = own code; PyMuPDF = optional AGPL dual.  
**Action for ClickUp author:** retract AGPL-in-core BLOCKER; residual = never ship `pdf-agpl` into customer contour / never say «весь продукт MIT».

### 2. CI vs RT-POST-09 — snapshot drift confirmed (audit finding, not code)

Exact check requested:

```text
git show origin/main:.github/workflows/ci.yml | grep -nE "uses:|require-hashes"
```

**Reproduced on HEAD:** every install path uses `pip install --require-hashes -r requirements-dev-lock.txt`; actions pinned by full SHA (`actions/checkout@3d3c42e5…`, `setup-python@5fda3b95…`, …).  
**Conclusion:** remote `ci.yml` without hashes/SHA was a stale raw snapshot (~20.07). Finding devalues remote license/CI sections; keep strategy/legal items.

### 3. PDF integrity moat — digit-run collision landed (ENG_PARTIAL)

Char-count alone misses «3000» vs «3300». Domain now fails when text-layer vs OCR digit runs (≥3 digits) disagree; producer fills both when RapidOCR (`raster`) present. See `docs/extraction-integrity-2026.md`. Still **not** arXiv:2606.15020 full coverage claim.

### Citations

- ASK-BIM → Data & Knowledge Engineering (not Information Fusion): `docs/research/CITATION_ERRATA_2026_08_03.md`  
- НРС 2-year exclusion → keep off slides without norm cite.
