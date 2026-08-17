<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Expertise-conclusion corpus scan — August 2026"
date: 2026-08-07
status: inventory
claim_boundary: >-
  Inventory only. No product accuracy >90%. Checkpoint NO_GO.
  Open corpora do not close RT-001. Fixture-only until customer adjudication exists.
---

# Expertise-conclusion corpus scan (2026-08)

**Purpose:** Inventory public and in-repo sources for **document ↔ expertise-remark pairs** (заключение экспертизы ↔ замечания ↔ исходный комплект).  
**Question answered:** Can RT-001 (publishable product precision) be closed from open data alone?

**Answer: No.** No usable open expertise-conclusion corpus exists. RT-001 requires customer data under NDA with dual-adjudication labeling.

Related SSOT: [`OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](../quality/OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md), [`OPEN_SOURCE_CORPUS_INVENTORY_2026_08.md`](../dataset/OPEN_SOURCE_CORPUS_INVENTORY_2026_08.md), [`CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md).

---

## Scan table

| source | license | volume estimate | has document↔remark pairs? | suitability as GT |
|---|---|---|---|---|
| **ЕГРЗ / Главгosexpertiza (re-use registry, expertise conclusions)** | Public **metadata only** (ФЗ 275-ФЗ; Минстрой re-use registry). Conclusion PDFs and applicant packages **not** open redistribution | Registry entries: thousands (metadata); paired packages: **0 open** | **No** — registry lists project metadata, not remark↔document machine pairs | **Unusable for RT-001.** DEAD_CHANNEL for file download per [`OPEN_SOURCE_CORPUS_INVENTORY_2026_08.md`](../dataset/OPEN_SOURCE_CORPUS_INVENTORY_2026_08.md). May cite public **typical-remark catalogs** (Exp B) for coverage mapping only — not TP/FP |
| **buildingSMART Sample-Test-Files** (vendored subset) | **CC BY 4.0** — [`samples/ifc/public/buildingsmart-sample-test-files/LICENSE`](../../samples/ifc/public/buildingsmart-sample-test-files/LICENSE) | 2 IFC files in-repo; upstream repo larger | **No** — geometry/property fixtures only | **Regression / license-clear IFC only.** Not expertise GT |
| **buildingSMART IDS TestCases** | **CC BY-ND 4.0** — [`samples/ids/buildingsmart-testcases/NOTICE`](../../samples/ids/buildingsmart-testcases/NOTICE) | **290** IDS↔IFC pass/fail pairs | **No** — synthetic IDS expectations, not human expertise remarks | **IDS engine regression (L2).** Does not close RT-001 |
| **Duplex / Schependomlaan / Karhu-style open IFC** | Per-file (IFC-Bench card: mostly CC BY 4.0 / MIT; some **GPLv3** — exclude from MIT tree) | IFC-Bench v2: **51 models**, **22 projects**; Duplex/Schependomlaan appear in BatchPlan upstream examples and IFC-Bench project list | **No** — BIM models without paired expertise conclusions or remark sidecars | **Open IFC rehearsal / BatchPlan pipeline input.** Useful for property/clash/IDS regression; **not** expertise-conclusion GT |
| **IFC-Bench v2** (Hellin et al., HF + arXiv:2605.01698) | QA CSV: **CC BY 4.0**; per-model licenses vary (GPLv3 excluded) | **1 026** QA rows (measured CSV); **27/1026** smoke scored in-repo | **Partial** — natural-language Q&A about IFC content, **not** RU expertise remark adjudication | **Open bench (L1) only.** Honest use: `claim_level=open_bench_only`. Does **not** substitute dual-expert TP/FP on customer packages. See [`samples/benchmarks/ifc-bench-v2/README.md`](../../samples/benchmarks/ifc-bench-v2/README.md) |
| **Repo `samples/benchmarks/russian-aec-ground-truth.json`** | Fixture / MIT (repo) | **10 fixtures**, **50 requirements** (RU technical-spec → IFC property expectations) | **No** — requirements extraction GT, **not** expertise conclusions | **Requirements→IFC mapping benchmark only.** Explicitly **≠** expertise remark GT. Dual-adjudication still required before any product accuracy claim |
| **Sprint-2 synthetic packs / ablation fixtures** | Fixture / MIT — [`samples/benchmarks/sprint2-dataset/MANIFEST.json`](../../samples/benchmarks/sprint2-dataset/MANIFEST.json) | **15 cases** (drawing advisory, IFC/IDS mutations, cross-doc calc); `claim_level=synthetic_only` | **No** — programmatically planted defects with known expected findings | **Synthetic regression / ablation only.** `customer_precision_claim_publishable=false`, `closes_rt001=false`, `checkpoint=NO_GO` |
| **Annotation templates (`samples/benchmarks/annotation/`)** | Fixture / MIT | Templates: `iaa-worksheet-template.json`; sidecar README points to russian-aec SSOT | **Schema only** — empty adjudicator labels (`a1_label: null`) | **Protocol scaffold for future customer intake.** Not populated GT. See also [`detection-precision/labels-template.json`](../../samples/benchmarks/detection-precision/labels-template.json) |
| **Public «типовые замечания» expertiza lists** (e.g. Kirov KR, Mordovia AR/VK — Exp B evidence) | Public PDF/HTML (cite, do not republish copyrighted PDFs without license check) | Dozens of remark **classes** per organ; not paired to applicant IFC/PDF packages | **Partial** — remark **taxonomy** only; no document-level TP/FP labels | **Coverage map (AUTHOR_CLAIM).** Not precision. Do not download or vendor copyrighted expertise PDFs without explicit license |
| **ПНСТ 909-2024 Renga pack** (local pin) | Publisher ToS («ознакомительные») — not OSS | 45 IDS / 198 IFC (local pin) | **No** — IDS/IFC conformance scenarios | **Exp A regression axis** after ToS GO. Not customer expertise GT |
| **Procurement archives (zakupki.gov.ru)** | Public procurement text | Variable | **Rarely** — TZ language, sometimes acceptance criteria; almost never IFC+remark pairs | **Language-of-pain inventory.** Not RT-001 GT |

---

## Conclusion

| Finding | Implication |
|---|---|
| No open corpus pairs **full PD/RD packages** with **adjudicated expertise remarks** | RT-001 **cannot** be closed from public data |
| Open IFC (Duplex, Schependomlaan, IFC-Bench, buildingSMART) + IDS regression + synthetic Sprint-2 packs | Valid for **L1/L2** engineering measurability only |
| In-repo `russian-aec-ground-truth.json` | Measures **requirement extraction**, not expertise-conclusion correctness |
| Exp B typical-remark catalogs | Coverage **taxonomy** only — not publishable precision |

**RT-001 needs customer data.** Until dual-adjudicated customer corpus exists: Checkpoint **NO_GO**, `claim_level=fixture_only` / `open_bench_only` only.

---

## Data request checklist (customer intake — RT-001)

Use this when engaging a pilot org. Do **not** commit specific company names or contacts to git; keep them in a private ops log outside the repository until the engagement is confirmed.

### Files needed

| Item | Minimum | Preferred | Notes |
|---|---|---|---|
| Completed PD/RD package (one discipline slice) | 1 section (e.g. AR or KR) | Full federated slice + calcs + 2D | IFC required on analyze path today |
| Prior expertise conclusion or internal QC record | PDF or structured export with remark list | Machine-readable remark IDs + sheet refs | Pairs remark ↔ document element |
| Reference IFC (+ optional IDS / property table) | 1 model matching the section | Version history (2 revisions) for diff rehearsal |
| Agreed rule subset | Property table or IDS draft | Customer-approved norm pack (RT-002 separate track) | Not «all GOST» |
| Calculation extract | 1 table cross-checkable to model/drawing | Full calc book for load rows | Correctness ≠ consistency — state honestly |

### Volume (pilot measurability)

| Metric | Floor | Target | Gate |
|---|---|---|---|
| Adjudicated finding labels (TP/FP/FN) | ≥50 | ≥200 | Wilson CI publishable only above agreed n |
| Typical-error patterns with examples | ≥10 | ≥20 | Remark calibration |
| Adjudicating engineers | **2** (independent) | 2 + tie-breaker | Cohen's κ / Krippendorff's α before accuracy claim |
| Manual baseline hours (same package) | 1 measured run | 3 runs median | Time-saved KPI denominator |

### Dual-adjudication labeling protocol

1. Two qualified engineers label each finding independently (use [`iaa-worksheet-template.json`](../../samples/benchmarks/annotation/iaa-worksheet-template.json) or [`labels-template.json`](../../samples/benchmarks/detection-precision/labels-template.json)).
2. Consensus on disagreements before metrics publish.
3. Record `adjudication.method`, annotator IDs, and timestamp in sidecar JSON.
4. **Forbidden:** single-annotator labels presented as product accuracy.

### NDA / data handling

| Requirement | Rationale |
|---|---|
| Signed NDA before file transfer off customer premises | Claims Lock + pilot threat model |
| On-prem option for expertise orgs | Files need not leave customer network for first demo |
| No redistribution of customer IFC/PDF in public repo | Fixture-only public artifacts |
| Masking ≠ anonymization — document in scope memo | Hybrid contour not wired to verdict |

### What NOT to claim until GT exists

| Forbidden until customer GT + adjudication | Allowed meanwhile |
|---|---|
| Product accuracy / «точность >90%» | Open-bench scores with `claim_level=open_bench_only` |
| «Подтверждено на реальных проектах заказчика» | «Fixture regression n=7» / «BSI n=290» |
| Customer SLA (комплект ≤30 мин) | Fixture SLA schema with `claim_level=fixture_only` |
| Expertise-conclusion automation rate | Exp B coverage % with AUTHOR_CLAIM caveat |
| RT-001 / Checkpoint GO | Checkpoint **NO_GO** |
| Closing RT-002 (customer-approved norm pack) from draft/template packs | Draft norm advisory only |
| RT-003 MEP federated clash as delivered | ENG_PARTIAL scaffold, `geometry_verified=False` |

---

## References

- [`OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md`](../dataset/OPEN_SOURCE_SEARCH_RESULTS_2026_08_04.md)
- [`SAMOLET_WHAT_WE_NEED_2026_07.md`](../partners/SAMOLET_WHAT_WE_NEED_2026_07.md)
- [`pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md)
- [`adjudication-corpus-plan-latest.json`](../evidence/adjudication-corpus-plan-latest.json)
