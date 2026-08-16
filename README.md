<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# AeroBIM

[Русская версия](README.ru.md)

[![CI](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml/badge.svg)](https://github.com/KonkovDV/AeroBIM/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## КТ#2 — 20.08.2026 (промежуточная версия)

> **Checkpoint: `NO_GO`.** Не прячем. Тихий SKIPPED в IDS-контуре закрыт (`AEROBIM-IDS-IFC-VERSION`). Осталось: нет корпуса «ПД РФ + заключение экспертизы»; нет подписанного профиля приёмки «Самолёта» (IDS МОГЭ **есть**, это другое); federated MEP clash **NOT_VERIFIED** (duplex AABB 654 overlap pairs measured; not clash). Кодом GO не ставится.

| Корзина | Что |
| --- | --- |
| **Работает (fixture)** | **Product path:** `python -m aerobim.tools.run_demo_ifc_acceptance_gate` — IFC+IDS → `acceptance-gate.json` + HTML/JSON/BCF (`summary.passed=false`). Overlay PDF is P1: `run_demo_vertical_slice`. IFC2x3/4/4x3 kernel. Official MOEXP IDS → IfcTester. Stale-norm warning (21.101-2020→2026). AGR exchange-shape fixture (not full moscow_agr). |
| **Подтверждено внешне** | IDS Мособлгосэкспертизы ([TIM](https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/)) + AEC-Bench inventory 196 ([arXiv:2603.29199](https://arxiv.org/abs/2603.29199)). Цифры покрытия IDS — только после прогона, см. evidence. |
| **Экспериментально** | VLM advisory (штамп с листа **не отправляем** — PII). Qwen live roundtrip на title/spec fixture; Kimi на Studio закрыт гейтом. Не точность продукта. Open IFC: fixtures 15/15; GNI **224** header / **223** IfcOpenShell (1 oversize skip). Student models, not product accuracy. |
| **Заблокировано не молчанием заказчика** | Корпус «ПД РФ + заключение экспертизы» публично не существует. Профиль приёмки Самолёта не подписан. Federated MEP clash на публичных IFC **NOT_VERIFIED** (инвентарь duplex/mep измерен). |
| **Не утверждаем** | Not claimed: accuracy >90%, DWG-ready, MEP delivered, CDE-ready BCF, calculation check, Tangl/10D integration. Native DWG = **FAILED**. |

Tangl проверяет **модель**; AeroBIM — **комплект**. Не заменяем 10D, Renga, CDE или эксперта: **IFC Acceptance Gate** поверх существующего контура. Клин: [`docs/partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md`](docs/partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md). Демо-IFC в репо — IfcOpenShell fixture, не выгрузка Renga и не Самолёт. Публичный образец издателя (ПНСТ 909, Renga 8.7) измеряется отдельно: `python -m aerobim.tools.run_renga_export_probe` (бинарник gitignored). OSINT + вектор 14.08: [`docs/gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md`](docs/gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md).

Видео 3 мин: [`docs/demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](docs/demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md) — запись **19.08**, человек.  
Пакет подачи КТ#2 (пять полей формы): [`submission/README.md`](submission/README.md) · покрытие ТЗ [`submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md`](submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md).  
Пакет жюри: [`docs/TIER0_INDEX.md`](docs/TIER0_INDEX.md) · Hostile QA [`docs/demo/KT2_HOSTILE_QA_PLAYBOOK_2026_08_16.md`](docs/demo/KT2_HOSTILE_QA_PLAYBOOK_2026_08_16.md).  
Запрос Самолёту: [`docs/partners/SAMOLET_KT2_ASK_2026_08_15.md`](docs/partners/SAMOLET_KT2_ASK_2026_08_15.md).

Open-source **IFC Acceptance Gate** for openBIM packages: IFC + IDS/requirements → evidence-backed findings → HTML/JSON/BCF. Helps an expert catch package defects **before** coordination/expertise. Not a CDE, not a viewer, not an expert replacement.

## Problem (concrete example)

A schedule on a PDF sheet shows one area; the IFC wall with the same GUID shows another. Each file looks fine alone; the error appears only when they are compared. AeroBIM raises a finding with provenance to the sheet and the GUID, leaves the verdict to the expert, and never authorizes Shared→Published.

## What works

Project-package analyze; IFC / IDS / cross-doc; deterministic Shared-gate `summary.passed` (fail-closed); provenance; structural BCF ZIP; HITL; Docker offline-bundle; CI. Full map — **Technical depth** below. LOC/test counts — [runtime baseline](docs/evidence/runtime-baseline-latest.json).

## Where it applies

Pre-construction package review (expertise / chief engineer / doc QC): model ↔ drawings ↔ requirements. Not a CDE replacement and not a field defect journal. Samolet contour / pilot framing: [`docs/docs.md`](docs/docs.md) · [`docs/samolet.md`](docs/samolet.md).

## Readiness status

> ## Checkpoint: `NO_GO`
>
> Samolet TechLab Task 07 is **not** ready for customer sign-off. Open blockers:
> **RT-001** (no public «RF PD + expertise conclusion» corpus; AEC-Bench / IFC-Bench / GNI exist and are not that corpus), **RT-002** (no Samolet-signed acceptance profile; official MOEXP IDS exist — that is not the same thing), **RT-003** (public federated IFC inventory exists; clash NOT_VERIFIED; MEP delivered not claimed) —
> see [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md).
> Claims SSOT: [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](audit/reports/CLAIMS_LOCK_2026_07_17.md) ·
> dated eng freeze: [`audit/reports/CLAIMS_LOCK_2026_07_31.md`](audit/reports/CLAIMS_LOCK_2026_07_31.md) ·
> verified vs planned: [`docs/pilot-claim-boundary-2026.md`](docs/pilot-claim-boundary-2026.md) ·
> **Aug 2026 eng status:** [`docs/ENGINEERING_STATUS_2026_08.md`](docs/ENGINEERING_STATUS_2026_08.md) ·
> Tier-0 docs: [`docs/TIER0_INDEX.md`](docs/TIER0_INDEX.md) ·
> verdict ownership: [`docs/architecture/ADR-001-verdict-ownership-2026.md`](docs/architecture/ADR-001-verdict-ownership-2026.md).
> Forbidden until evidenced: product accuracy >90%, DWG-ready, MEP delivered, CDE-ready BCF, independent calc *correctness*.
>
> **Engineering readiness improved (2026-07 → 2026-08)** without closing customer blockers:
> LIC-001 Option B; P2-04 / P2-02 honesty; Docker offline track; **P0 TechLab eng package WP-01…08**
> (runtime baseline, Hybrid advisory pre-gate, signature envelope, norm pack v2, package completeness,
> open-corpora n=7, quality protocol interim 0.60, README/baseline sync) — see
> [`docs/ENGINEERING_STATUS_2026_08.md`](docs/ENGINEERING_STATUS_2026_08.md).
> Fixture GO ≠ Checkpoint GO.

AeroBIM runs a deterministic Shared-gate style check (ISO 19650 framing: evidence for *Shared*, not contractual *Published* authorization). It fuses IFC property/quantity checks, IDS, drawings, and calculation text into a single report with explicit capability honesty, finding provenance, and BCF **ZIP export**. Independent CDE import and customer accuracy claims remain **out of scope until evidenced**. Architecture SSOT: [`docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md).

## Technical depth

## Status map (honest)

| Bucket | Meaning |
|---|---|
| **What works** | Fixture/repo-proven; Shared-gate honesty |
| **Experimental** | Code present; not customer-proven |
| **Planned** | Design only / deferred Wave 2+ |
| **Needs customer** | Samolet models + signed profile; RF expertise corpus — checkpoint **NO_GO** |
| **Not claimed** | Forbidden wording until dual evidence |

**What works:** project-package analyze; IFC/IDS/cross-doc; `summary.passed` Shared-gate ([ADR-001](docs/architecture/ADR-001-verdict-ownership-2026.md)); pilot/production fail-closed profiles; ACL 404; SSRF outbound guard; provenance stamp/persist; BCF 2.1/3.0 structural ZIP; HITL review-events; evidence bundle CLI (`python -m aerobim.tools.export_evidence_bundle`); **annotation claimed-GUID presence confirm** (P2-04); **core PDF via pypdfium2/pdfminer** (LIC-001 Option B); **HybridRouteGate advisory pre-gate** (WP-02); **detached signature envelope audit** (WP-03 ENG_PARTIAL); **norm pack v2 eligibility** (WP-04); **package completeness inventory** (WP-05); **open-corpora profiles** (WP-06 regression/timing only); **quality measurement protocol** (WP-07 Wilson planner; interim 0.60); **L1 open-bench** IFC-Bench smoke + AECV live counting on Yandex Qwen (`claim_level=open_bench_only`, ≠ RT-001 — [evidence](docs/evidence/README.md)); Docker offline-bundle smoke; pytest / vitest counts SSOT via [runtime baseline](docs/evidence/runtime-baseline-latest.json) (`frontend.tests_passed` when recorded; else see baseline/CI).

**Experimental:** OpenCDE BCF API push; BCF 3.0 consumer path; optional clash/OCR extras; IFC KG advisory scaffold; MEP federated ENG_FIXTURE graph + AABB broadphase (capability stays `NOT_VERIFIED`); **advisory `LlmExtractionPort` (regex/Kimi/Qwen eval harness — never verdict)**.

**Available (eng):** `PackageOutcome` on `summary.outcome` (`pass` / `pass_with_warnings` / `review_required` / `blocked` / `failed`); run manifest + reproducibility hash; stage timeout budgets; **Hybrid AI routing** (classify/policy/guard/audit + **WP-02 `HybridRouteGate` advisory pre-gate** on Analyze + **kimi smoke PUBLIC egress gate**) — domain-pure, verdict-neutral (OFF==ON), **never sets `summary.passed`**; masking ≠ anonymity; Checkpoint **NO_GO**.

**Planned:** Stage-3 finding field expansion; profiling-driven performance wave; customer-gated RT-001/002/003 evidence.

**Needs customer:** RF PD+expertise corpus · Samolet-signed acceptance profile · measured federated MEP on public IFC ([CRITICAL_BLOCKERS](audit/reports/CRITICAL_BLOCKERS.md), [DATASETS](docs/DATASETS.md)). Official MOEXP IDS are already in-repo. Public federated models exist; we have not published a measured run.

**Not claimed:** product accuracy >90%; customer ≤30 min SLA; native DWG; MEP system clash delivered; independent calc *correctness*; CDE-ready BCF; bare-metal offline without Docker; AABB/connects = verified geometric clash. See [capability-claim-matrix](docs/capability-claim-matrix-2026.md) · [PROJECT_STATUS_AUDIT](docs/PROJECT_STATUS_AUDIT_2026.md) · [ENGINEERING_STATUS_2026_08](docs/ENGINEERING_STATUS_2026_08.md) · [pilot-protocol](docs/pilot-protocol-samolet-2026.md) · [benchmark-evidence](docs/benchmark-evidence-2026.md).

## Key Capabilities

Statuses below are **repository / fixture** capabilities unless marked otherwise. Optional extras and fail-closed policies govern whether a green `summary.passed` is honest.

| Capability | Status | Evidence level | Notes |
|---|---|---|---|
| IFC property/quantity validation (IfcOpenShell) | Available | fixture | IFC2x3 / IFC4 / IFC4x3 kernel |
| IDS 1.0 validation (IfcTester) | Available | fixture | Requested path fail-closed when misconfigured |
| Cross-document contradiction detection | Available | fixture | `ConflictKind` taxonomy (subset) |
| Configurable contradiction severity policy | Available | fixture | — |
| Drawing annotation ↔ IFC cross-validation | Available | fixture | Claimed GUID → `ifc_guid` only after spatial-index presence (P2-04); not human-adjudicated |
| ISO 12006-3 tolerance algebra (ε-band) | Available | fixture | — |
| Narrative text → requirements (deterministic regex) | Available | fixture | Not an LLM sign-off contour |
| Russian AEC extraction benchmark (fixture corpus) | Available | fixture | macro_f1 on fixtures ≠ product accuracy |
| ISO 19650-lite metadata on reports | Available | fixture | Stage/revision/container fields only — not a CDE product |
| Clash detection (IfcClash) | Optional extra | optional-extra | `.[clash]`; `detect` on analyze; adapter extra-methods `detect_between` / `detect_clearance_between` are engine rehearsal, not MEP system clash; under `require_clash`, SKIPPED→FAILED |
| Report capability honesty (`ok`/`skipped`/`failed`/`missing`/…) | Available | fixture | FAILED blocks `summary.passed`; honesty surface via `/v1/system/capabilities` |
| Finding provenance (`finding_id`, `source_id`, `evidence_refs`) | Available | fixture | Persist reject if missing |
| Tenant / object ACL on report artifacts | Available | fixture | Bearer/OIDC principal + report `tenant_id` |
| BCF 2.1 / 3.0 ZIP export | Available | fixture (T1) | Structural + dual-consumer + file ingest CLI; **CDE import NOT VERIFIED (T2)** |
| OpenCDE BCF API push | Foundation | experimental | Not a substitute for T2 import proof |
| HTML / JSON report export | Available | fixture | — |
| Browser IFC viewer (`web-ifc` + Three.js) | Available | fixture | — |
| 2D problem-zone overlay | Available | fixture | — |
| Deterministic PDF text/crop (pypdfium2 + pdfminer) | Available | core | LIC-001 Option B; default `AEROBIM_PDF_BACKEND=pdfium` |
| Optional PyMuPDF | Optional extra | `pdf-agpl` | AGPL/Artifex dual; **not** in runtime lock/Docker |
| Image OCR (RapidOCR) | Optional extra | optional-extra | `.[raster]`; EI OCR-aware signals PARTIAL; zero-yield → FAILED when requested |
| Extraction integrity capability | Available | fixture | Text-layer + optional OCR disagreement WARNING; not product visual integrity |
| DWG native analysis | Missing / Failed | — | Fail-closed; never OK; PDF/IFC = derived input with provenance only |
| DXF via CadModelIngestor | Partial / Not verified | fixture | Optional ezdxf; honesty never OK; ≠ DWG support |
| Human-level CV / drawing literacy | Missing | — | Explicit `MISSING` (OCR degrade ≠ VLM) |
| MEP system-aware clash | Not verified / blocked | fixture_only | ENG_PARTIAL: edge_kinds + AABB broadphase; always `geometry_verified=False`; public federated IFC unmeasured |
| Offline Docker image-track | Available | eng | И1 **CLOSED** — `closed-contour --smoke`; bare-metal OUT_OF_SCOPE |
| IFC knowledge graph (I9) | Advisory scaffold | fixture | Port+DI+`query_ifc_kg`+fixture QA; **not GraphRAG / IfcLLM product** |
| Independent calculation *correctness* | Not implemented | — | сверка источников only — not a calculation solver |
| Frontend vitest review-shell | Green in CI | release-readiness | **54** passed (frontend CI job; SSOT `frontend.tests_passed` in runtime baseline) |
| Hybrid AI routing + advisory pre-gate (WP-02) | Available (eng) | fixture | Gate before advisory observations; OFF==ON for `summary.passed`; masking ≠ anonymity; Checkpoint NO_GO |
| Detached signature envelope (WP-03) | ENG_PARTIAL | fixture | Hash/roles audit; trust_chain always NOT_VERIFIED — never «УКЭП проверена» |
| Norm pack v2 eligibility (WP-04) | Available (eng) | fixture | RASE + execution_mode + expert journal; fixture ≠ Samolet-signed profile |
| Package completeness inventory (WP-05) | Available (eng) | fixture | Soft opt-in; no native DWG; not PP-87 / customer intake |
| Open corpora measurability (WP-06) | Available (eng) | fixture/open | Fixture n=7 + BSI IDS TestCases n=290 (CC BY-ND); CI smoke pins — not product accuracy |
| Quality measurement protocol (WP-07) | Available (eng) | protocol | Wilson P/R + sample-size planner; interim confirmed-finding target 0.60; never >90% |
| OIDC BFF (POST-05) | NOT_IMPLEMENTED | design+stub+lab | Default 501; Phase 3 lab cookie only when `oidc_bff_phase3_ready` — not production SSO |
| BCF T2 CDE import | NOT_VERIFIED | template | Checklist/verifier ready; needs real CDE log+screenshot+hashes |
| Customer accuracy >90% / approved norms | Blocked | customer | See Claims Lock |

## IFC Release Compatibility

| IFC Release | Schema | Validation Support | Notes |
|---|---|---|---|
| IFC2x3 | ISO 16739:2005 | ✅ Core | Most widely deployed; full property/quantity validation |
| IFC4 (IFC4 ADD2) | ISO 16739-1:2018 | ✅ Core | Pset naming normalised; unit assignment via `IfcUnitAssignment` |
| IFC4x3 | ISO 16739-1:2024 | ✅ Core | Alignment and infrastructure extensions; same validation kernel |

All three releases pass through the same `IfcOpenShellValidator` and `IfcTesterIdsValidator` adapters.
Pset/property name divergence between releases is surfaced as a `ValidationIssue` rather than a silent skip.
IFC2x3, IFC4, and IFC4x3 fixture files live in `samples/ifc/`.
See [`docs/ifc-compatibility-matrix.md`](docs/ifc-compatibility-matrix.md) for the formal compatibility matrix and per-feature degradation rules.

## BCF Evidence Ladder

Canonical taxonomy: [`docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md`](docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md).

| Tier | Status | Notes |
|---|---|---|
| T0 BCF ZIP export surface | **AVAILABLE** | 2.1 default `/export/bcf`; 3.0 experimental `?version=3` |
| T1 structural + dual-consumer | Evidenced | [`audit/evidence/bcf-structural-handoff-2026-07-25.json`](audit/evidence/bcf-structural-handoff-2026-07-25.json) |
| OpenCDE BCF API push | Foundation | `/export/bcf-api/push` — hub sync not a T2 substitute |
| T2 independent CDE import | **NOT_VERIFIED** | [`audit/evidence/cde-import-proof/STATUS.json`](audit/evidence/cde-import-proof/STATUS.json) |
| T3 round-trip fidelity | Not started | Blocked on T2 |
| T4 production handoff | Not started | Blocked on T2/T3 |

Allowed: structural ZIP **AVAILABLE**. Forbidden until T2: “BCF ready for CDE”, “CDE interoperable”.

## Enterprise Storage Foundation

Iteration B.1 has started with a compatibility-first storage foundation:

- `ObjectStore` domain port for binary artifacts (`put/get/delete/presign`);
- `LocalObjectStore` for current local/runtime flows;
- `S3ObjectStore` for S3/MinIO-compatible buckets via optional enterprise extras;
- `PostgresAuditStore` foundation that adds a Postgres report-summary index while keeping full payload round-tripping on the existing JSON/object path;
- `AEROBIM_REPORT_TTL_DAYS` retention knob for persisted report payloads.

Current behaviour is intentionally safe-by-default:

- without enterprise extras, AeroBIM keeps working with local storage;
- when `AEROBIM_DB_URL` and enterprise dependencies are available, report summaries are indexed in Postgres. Constructor bootstrap issues `CREATE TABLE` / `ALTER TABLE` (HD5-PGSQL-02: runtime role needs DDL). Pilot-acceptable; production should migrate schema out of band, then use a DML-only role — not Checkpoint GO;
- IFC source binaries and persisted drawing previews are stored behind the `ObjectStore` abstraction, so S3/MinIO rollout no longer requires HTTP contract changes.

## Quick Start

```bash
# Clone
git clone https://github.com/KonkovDV/AeroBIM.git
cd AeroBIM/backend

# Create virtual environment on CPython 3.12 (CI pin). Windows: py -3.12 -m venv .venv
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install (core PDF = pypdfium2; overlay PNG does not need PyMuPDF)
pip install -e ".[dev,raster]"

# Product path: IFC Acceptance Gate (fixture; no overlay required)
python -m aerobim.tools.run_demo_ifc_acceptance_gate
# Open artifacts/ifc-acceptance-gate-demo/report.html and acceptance-gate.json
# summary.passed=false. Checkpoint NO_GO. Not customer accuracy.

# P1 overlay modality (KT#2 video still uses this command)
python -m aerobim.tools.run_demo_vertical_slice
# Open artifacts/vertical-slice-demo/report.html — fragment, overlay, text evidence,
# finding_id/source_id/evidence_refs, capability table, run-manifest.json, BCF ZIP.
# summary.passed=false. Checkpoint NO_GO. Fixture demo, not CV.
# Do not open docs/evidence/kt2-handoff-2026-08-11/wall-guid/report.html as this demo.

# Optional extras
# pip install -e ".[clash]"    # enable geometry clash detection
# pip install -e ".[docling]"  # enable non-text document extraction
# pip install -e ".[enterprise]"  # enable S3/Postgres enterprise storage adapters
# pip install -e ".[pdf-agpl]"  # legacy PyMuPDF tools only; not required for the demo overlay

# Run tests
pytest tests -q

# Extraction quality gate (Russian AEC corpus)
python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
python -m aerobim.tools.evaluate_detection_precision \
  --labels ../samples/benchmarks/detection-precision/labels-synthetic.json \
  --detections ../samples/benchmarks/detection-precision/detections-synthetic.json \
  --min-precision 0.6 --min-recall 0.6 --min-f1 0.6

# Seed one deterministic runtime smoke report
python -m aerobim.tools.seed_smoke_report

# Or run the full live review smoke chain in one command
python -m aerobim.tools.run_live_review_smoke

# Or run the baseline throughput rail against the representative benchmark pack
python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0

# Or run the second fire-compliance benchmark profile explicitly
python -m aerobim.tools.benchmark_project_package --pack ../samples/benchmarks/project-package-fire-compliance.json --iterations 1 --warmup-iterations 0

# Or run the stress multisource benchmark profile explicitly
python -m aerobim.tools.benchmark_project_package --pack ../samples/benchmarks/project-package-stress-multisource.json --iterations 1 --warmup-iterations 0

# Start server
python -m aerobim.main
# → http://127.0.0.1:8080/health
```

## Local Quality Gate

Before pushing to `main`, run the same baseline checks used by CI:

```bash
cd AeroBIM/backend
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
```

If `ruff format --check` reports files to reformat, run:

```bash
python -m ruff format src tests
```

## Benchmarks and Evidence

Verified capabilities are backed by tests, API contracts, or persisted report artifacts. Planned / missing contours (DWG, human CV, MEP system clash, calculation *correctness*, customer accuracy) are explicit on `GET /v1/system/capabilities` and in the Claims Lock.

```bash
cd backend
python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0
python -m aerobim.tools.measure_package_sla --corpus-kind fixture
python -m aerobim.tools.verify_bcf_structural_handoff
python -m aerobim.tools.run_ablation_study
python -m aerobim.tools.generate_benchmark_report --output-dir ../docs/evidence
python -m aerobim.tools.export_runtime_baseline
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-techlab-demo.json \
  --output ../artifacts/evidence-bundle/techlab-demo

# P2-04 wall-guid presence demo (fixture GO pin)
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-wall-guid-demo.json \
  --output ../artifacts/evidence-bundle/checkpoint2-wall-guid
```

| Topic | Document |
|---|---|
| Claims lock (forbidden / allowed wording) | [audit/reports/CLAIMS_LOCK_2026_07_17.md](audit/reports/CLAIMS_LOCK_2026_07_17.md) |
| Claims lock — eng freeze 2026-07-31 | [audit/reports/CLAIMS_LOCK_2026_07_31.md](audit/reports/CLAIMS_LOCK_2026_07_31.md) |
| Claims × evidence matrix | [audit/reports/CLAIMS_EVIDENCE_MATRIX.md](audit/reports/CLAIMS_EVIDENCE_MATRIX.md) |
| Critical blockers / checkpoint | [audit/reports/CRITICAL_BLOCKERS.md](audit/reports/CRITICAL_BLOCKERS.md) |
| Engineering status (Aug 2026) | [docs/ENGINEERING_STATUS_2026_08.md](docs/ENGINEERING_STATUS_2026_08.md) |
| Claim boundary (pilot / publication) | [docs/pilot-claim-boundary-2026.md](docs/pilot-claim-boundary-2026.md) |
| Project status audit | [docs/PROJECT_STATUS_AUDIT_2026.md](docs/PROJECT_STATUS_AUDIT_2026.md) |
| Capability × claim matrix | [docs/capability-claim-matrix-2026.md](docs/capability-claim-matrix-2026.md) |
| License policy (LIC-001 Option B) | [docs/license-policy-2026.md](docs/license-policy-2026.md) |
| Offline deployment (Docker track) | [docs/offline-deployment-2026.md](docs/offline-deployment-2026.md) |
| Extraction integrity | [docs/extraction-integrity-2026.md](docs/extraction-integrity-2026.md) |
| MEP system-aware clash gap | [docs/roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md](docs/roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md) |
| P2-02 geometry honesty plan | [docs/roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md](docs/roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md) |
| Checkpoint #2 evidence pin | [docs/evidence/checkpoint2-evidence-bundle-latest.json](docs/evidence/checkpoint2-evidence-bundle-latest.json) |
| L1 open-bench (IFC / AECV / AEC) | [docs/evidence/README.md](docs/evidence/README.md) · [Red Team AECV live](docs/quality/RED_TEAM_AECV_LIVE_YANDEX_2026_08_04.md) · [vs RT-001](docs/quality/OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md) |
| Benchmark evidence boundaries | [docs/benchmark-evidence-2026.md](docs/benchmark-evidence-2026.md) |
| Samolet pilot protocol | [docs/pilot-protocol-samolet-2026.md](docs/pilot-protocol-samolet-2026.md) |
| Hybrid AI routing foundation (design + final report) | [audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md](audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md) |
| Reproducibility (FAIR) | [docs/REPRODUCIBILITY-2026.md](docs/REPRODUCIBILITY-2026.md) |
| Extraction corpus / IAA | [`samples/benchmarks/annotation/README.md`](samples/benchmarks/annotation/README.md) · RU GT in `samples/benchmarks/` |
| Benchmark packs | [samples/benchmarks/README.md](samples/benchmarks/README.md) |
| Public buildingSMART IFC samples (CC BY 4.0) | [samples/ifc/public/buildingsmart-sample-test-files/](samples/ifc/public/buildingsmart-sample-test-files/) |
| Audit evidence (T1 BCF, SLA 1.2, intake gate) | [audit/evidence/](audit/evidence/) |
Throughput and F1 figures are environment-specific and **fixture-scoped** unless `corpus_kind=customer` and adjudication gates pass. Publish pack paths, CLI flags, machine fingerprint, and artifact hashes with any performance claim. Cite via [CITATION.cff](CITATION.cff) or [docs/CITATION.bib](docs/CITATION.bib).

## API Endpoints

| `GET` | `/v1/system/capabilities` | Static honesty surface (DWG/CV/MEP/calculation claim boundary) |
| `GET` | `/health` | Readiness probe |
| `POST` | `/v1/validate/ifc` | Validate IFC against requirements + IDS |
| `POST` | `/v1/analyze/project-package` | Multimodal validation (spec + calc + drawing + IDS + IFC) |
| `POST` | `/v1/analyze/project-package/reinforcement-digest` | OpenRebar provenance digest (**сверка** labels; not correctness verification) |
| `POST` | `/v1/analyze/project-package/submit` | Accept a same-process background analysis job for larger packages |
| `GET` | `/v1/analyze/project-package/jobs/{job_id}` | Poll async project-package job status |
| `POST` | `/v1/uploads` | Multipart document ingest; returns storage-relative `path` for analyze |
| `GET` | `/v1/reports` | List persisted reports with optional `project`, `discipline`, and `passed` filters |
| `GET` | `/v1/reports/{id}` | Get report by ID |
| `POST` | `/v1/reports/{id}/review-events` | Append HITL review telemetry (does not affect pass/fail) |
| `GET` | `/v1/reports/{id}/review-events` | List review events for a report |
| `GET` | `/v1/reports/{id}/review-kpi` | Aggregate triage/acceptance KPIs |
| `GET` | `/v1/reports/{id}/source/ifc` | Download the report-scoped IFC source for browser viewing |
| `GET` | `/v1/reports/{id}/drawing-assets/{asset_id}/preview` | Download a report-scoped drawing preview for 2D evidence overlays |
| `GET` | `/v1/reports/{id}/export/json` | Download JSON export |
| `GET` | `/v1/reports/{id}/export/html` | Download HTML export |
| `GET` | `/v1/reports/{id}/export/bcf` | Download BCF 2.1 ZIP by default; use `?version=3` for BCF 3.0 |

`POST /v1/analyze/project-package` also supports optional OpenRebar provenance fields:

- `reinforcement_report_path`: path (inside `AEROBIM_STORAGE_DIR`) to an OpenRebar canonical `*.result.json` report;
- `reinforcement_source_digest`: expected SHA-256 digest for report provenance fingerprint checks.
- `reinforcement_waste_warning_threshold_percent`: optional waste threshold (percent) for coordination warnings.
- `reinforcement_provenance_mode`: `advisory` (default) or `enforced` to escalate OpenRebar provenance warnings into blocking errors.

Use `/v1/analyze/project-package/reinforcement-digest` to generate `reinforcement_source_digest` directly from a stored OpenRebar report before calling project-package analysis.

For offline or CI shell workflows, use:

`python -m aerobim.tools.openrebar_provenance_digest <path-to-openrebar-result.json>`

When provided, AeroBIM adds cross-document warnings if:

- OpenRebar report contract ID is unexpected;
- OpenRebar optimizer indicates fallback master solver usage;
- OpenRebar master-problem strategy does not indicate a HiGHS-backed path;
- project context mismatches (`project_name` vs `metadata.projectCode`);
- supplied provenance digest does not match report fingerprint.
- reported `summary.totalWastePercent` exceeds the configured warning threshold.

## Architecture

Five-layer Clean Architecture with strict inward dependency direction:

```
core/          DI container, tokens, config (no project imports)
domain/        Immutable models, Protocol ports, logging contract
application/   Use case orchestration (requirement fusion, cross-doc detection)
infrastructure/ Adapters: IfcOpenShell, IfcTester, Docling, IfcClash, BCF, filesystem
presentation/  FastAPI HTTP API, correlation middleware
```

Infrastructure now also includes an artifact `ObjectStore` seam plus an optional Postgres summary-index adapter for Iteration B.1.

**48 domain Protocol ports** → **72 infrastructure adapter modules** → **63 DI tokens** — wired in `bootstrap_container()`. Counts are **live inventory** regenerated into `docs/evidence/runtime-baseline-latest.json` (`architecture_inventory`) and checked in CI via `export_runtime_baseline --check-readme` against README EN/RU; do not hand-edit older 20/30/28 or stale 47/71/60 figures.
Report payloads include an explicit `capabilities` object (`ok` / `skipped` / `failed`) so optional engines (clash, IDS, unit scale, raster, schema) cannot silently look like a clean PASS. **Any `FAILED` capability forces `summary.passed=false`.**

## Configuration

All settings are read from environment variables (see [`backend/.env.example`](backend/.env.example)):

| Variable | Default | Description |
|---|---|---|
| `AEROBIM_HOST` | `127.0.0.1` | Bind address |
| `AEROBIM_PORT` | `8080` | Bind port |
| `AEROBIM_DEBUG` | `false` | Debug mode (also enables localhost CORS defaults when origins unset) |
| `AEROBIM_STORAGE_DIR` | `var/reports` | Report persistence directory |
| `AEROBIM_CORS_ORIGINS` | *(auto)* | Comma-separated CORS origins |
| `AEROBIM_ENV` | `development` | Environment name; non-dev requires bearer/OIDC (fail-closed) |
| `AEROBIM_SIGNOFF_PROFILE` | *(auto)* | **`samolet_pilot` / `production` = закрытый контур заказчика**: fail-closed capabilities; **внешний advisory LLM egress запрещён**. Unset under non-dev → `production`. Also: `development` / `fixture` |
| `AEROBIM_API_BEARER_TOKEN` | *(unset)* | Bearer for `/v1/*`; required unless `AEROBIM_ALLOW_ANONYMOUS_DEV` |
| `AEROBIM_ALLOW_ANONYMOUS_DEV` | `false` | Opt-in anonymous API in development/test only (`from_env`) |
| `AEROBIM_CLASH_AFFECTS_PASS` | `false` | Soft only in development/fixture; forced `true` under pilot/production sign-off |
| `AEROBIM_CLASH_SKIP_TINY` | `true` | Skip degenerate/tiny IFC products before IfcClash; all-skipped still FAILED |
| `AEROBIM_CLASH_MIN_AABB_VOLUME_M3` | `1e-6` | AABB volume threshold used when `AEROBIM_CLASH_SKIP_TINY` is on |
| `AEROBIM_REQUIRE_CLASH` | `false` | Soft only in development/fixture; forced under pilot/production |
| `AEROBIM_REQUIRE_MEP_SYSTEM_CLASH` | `false` | When true, MEP `NOT_VERIFIED` blocks Shared-gate pass |
| `AEROBIM_MEP_FEDERATED_SCOPE_PATH` | *(unset)* | Federated MEP scope JSON (VERIFIED customer or ENG_FIXTURE) |
| `AEROBIM_MEP_AABB_FILTER` | `true` | Optional AABB broadphase for MEP matrix pairs; still `geometry_verified=False` |
| `AEROBIM_PDF_BACKEND` | `pdfium` | Core PDF: `pdfium` / `none`; optional legacy `pymupdf` only with `pdf-agpl` |
| `AEROBIM_MAX_IFC_BYTES` | `268435456` | Max IFC size (256 MiB, aligned with bSI Validation Service) |
| `AEROBIM_CROSS_DOC_SEVERITY` | `warning` | Severity for cross-document contradictions: `error` (blocking), `warning`, `info` |
| `AEROBIM_REMARK_LOCALE` | `ru` | Remark template language for deterministic generators (`ru` / `en`) |
| `AEROBIM_PRIORITY_PROFILE` | `default` | Review priority weighting profile (`default`; `samolet` in fixture SLA smoke only) |
| `AEROBIM_DB_URL` | *(unset)* | Optional Postgres URL for report summary indexing. Boot runs CREATE/ALTER (HD5-PGSQL-02); production: migrate out of band, DML-only role |
| `AEROBIM_REPORT_TTL_DAYS` | *(unset)* | Optional TTL for persisted report payloads; unset means unlimited retention |
| `AEROBIM_S3_BUCKET` | *(unset)* | Optional S3/MinIO bucket for object storage |
| `AEROBIM_S3_ENDPOINT_URL` | *(unset)* | Optional MinIO/custom S3 endpoint |
| `AEROBIM_S3_REGION` | `us-east-1` | Signing region for S3-compatible storage |
| `AEROBIM_S3_ACCESS_KEY_ID` | *(unset)* | Optional access key for S3-compatible storage |
| `AEROBIM_S3_SECRET_ACCESS_KEY` | *(unset)* | Optional secret key for S3-compatible storage |
| `AEROBIM_S3_PREFIX` | `aerobim` | Prefix applied to object keys in S3-compatible storage |
| `AEROBIM_LLM_ADVISORY_ENABLED` | `false` | **Development only:** opt-in OpenAI-compat advisory LLM; never sets `summary.passed`; ignored/`ready=false` under `samolet_pilot`/`production`. Deprecated alias `AEROBIM_LLM_LOCAL_ENABLED` logs a boot warning and is **removed after KT#3 (2026-09-21)** |
| `AEROBIM_LLM_BASE_URL` | *(unset; Studio default when provider=`yandex-ai-studio`)* | Loopback or RF HTTPS OpenAI-compat base (`…/v1`); SSRF-gated at boot |
| `AEROBIM_LLM_API_KEY` | *(unset)* | Optional bearer for Studio; never logged / never in `audit_event` |
| `AEROBIM_LLM_PROVIDER` | `qwen-local` | Provider label (`qwen-local` / `yandex-ai-studio`) |
| `AEROBIM_LLM_MODEL` | `Qwen3.6-27B` | Local bare id, or Yandex `gpt://{folder}/{model}` |
| `AEROBIM_LLM_MODEL_REVISION` | *(required if enabled)* | Exact catalog version (not `latest`/`rc`); composed into URI |
| `AEROBIM_LLM_FOLDER_ID` | *(unset)* | Yandex folder → `x-folder-id` + URI composition |
| `AEROBIM_LLM_AUTH_SCHEME` | `Bearer` | `Bearer` or `Api-Key` (confirm with live curl before first spend) |
| `AEROBIM_LLM_SEND_SEED` | `true` (`false` for Studio) | Omit `seed` when false (Yandex may 400) |
| `AEROBIM_LLM_RESPONSE_FORMAT_MODE` | `json_object` (`json_schema` for Studio) | Yandex prefers `json_schema` + `REMARK_JSON_SCHEMA` |
| `AEROBIM_LLM_DATA_LOGGING_ENABLED` | `false` | When false, send `x-data-logging-enabled: false` (audit-recorded) |
| `AEROBIM_LLM_MODEL_SHA256` | *(unset)* | Optional checkpoint hash in usage/audit |
| `AEROBIM_LLM_MAX_TOKENS_PER_CALL` | `4096` | Fail-closed token cap per call |
| `AEROBIM_LLM_MAX_TOKENS_PER_RUN` | `100000` | Fail-closed per-run cap (~two measured 100-finding packs; measured ~44k tokens/pack with think off) |
| `AEROBIM_LLM_MAX_TOKENS_PER_DAY` | `300000` | Fail-closed daily cap while card-bound (no `TRIAL_EXPIRED`). Convert to ₽ after console tariff for `qwen3.6-35b-a3b` |
| `AEROBIM_LLM_BUDGET_TZ` | `Europe/Moscow` | IANA timezone for day-roll of the daily cap |
| `AEROBIM_LLM_BUDGET_LEDGER` | *(unset)* | Shared JSON ledger path across workers; **required** for grant ops (without it: process-local ≈ N× day cap) |
| `AEROBIM_LLM_MAX_COMPLETION_TOKENS` | `512` | Completion budget passed to the API |
| `AEROBIM_LLM_MAX_CONCURRENT` | `4` | Semaphore for parallel Studio calls (unused until overlay fan-out) |
| `AEROBIM_LLM_ADVISORY_MAX_ISSUES` | `32` | Max findings to overlay with AI remark drafts per analyze |
| `AEROBIM_LLM_429_RETRIES` | `3` | Linear backoff retries on HTTP 429 before SKIPPED |
| `AEROBIM_LLM_ALLOWED_HOSTS` | *(built-in)* | Extra allowlisted hostnames (comma-separated); Alibaba/OpenAI always forbidden |
| `AEROBIM_HYBRID_PROVIDER_CONFIG` | *(unset)* | Path to hybrid provider JSON (`schema_version` ≥1.1 requires `model_revision`) |
| `AEROBIM_API_TENANT_ID` | *(unset)* | Optional tenant id for multi-tenant API auth |
| `AEROBIM_APP_NAME` | `aerobim` | Application name for logs / OpenAPI title |
| `AEROBIM_BCF_API_BASE_URL` | *(unset)* | Optional BCF API base URL (enterprise sync) |
| `AEROBIM_BCF_API_PROJECT_ID` | *(unset)* | Optional BCF project id |
| `AEROBIM_BCF_API_TOKEN` | *(unset)* | Optional BCF API bearer token |
| `AEROBIM_BCF_API_VERSION` | `2.1` | BCF API version label |
| `AEROBIM_BSI_API_TOKEN` | *(unset)* | Optional buildingSMART Validation Service token |
| `AEROBIM_BSI_VALIDATION_URL` | *(built-in)* | Optional override for bSI Validation Service URL |
| `AEROBIM_GATES_ATTESTED` | *(CI only)* | Comma-separated CI job names attested into runtime baseline; ignored locally; must equal required gate set under GitHub Actions (N-23) |
| `AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE` | `120` | Per-client limit for analyze/validate/upload POSTs and GET `/v1/auth/login` + `/v1/auth/callback`; `0` disables in development; **must be >0** under pilot/production |
| `AEROBIM_TRUSTED_PROXY_IPS` | *(unset)* | Comma-separated peer IPs allowed to supply `X-Forwarded-For` for rate-limit keys; empty = never trust XFF |
| `AEROBIM_IFC_PARSE_CACHE_DIR` | *(unset)* | Optional on-disk IFC parse cache directory |
| `AEROBIM_KIMI_API_BASE_URL` | *(unset)* | Optional Kimi OpenAI-compat base URL |
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
| `AEROBIM_REDIS_URL` | *(unset in dev)* | Required outside development/test for durable jobs and shared rate limits |
| `AEROBIM_VLM_ENABLED` | `false` | Opt-in advisory VLM drawing read; never sets `summary.passed` |


<!-- AEROBIM_DOCUMENTED_ENV:BEGIN -->
AEROBIM_ALLOW_ANONYMOUS_DEV
AEROBIM_API_BEARER_TOKEN
AEROBIM_API_TENANT_ID
AEROBIM_APP_NAME
AEROBIM_BCF_API_BASE_URL
AEROBIM_BCF_API_PROJECT_ID
AEROBIM_BCF_API_TOKEN
AEROBIM_BCF_API_VERSION
AEROBIM_BSI_API_TOKEN
AEROBIM_BSI_VALIDATION_URL
AEROBIM_CLASH_AFFECTS_PASS
AEROBIM_CLASH_MIN_AABB_VOLUME_M3
AEROBIM_CLASH_SKIP_TINY
AEROBIM_CORS_ORIGINS
AEROBIM_CROSS_DOC_SEVERITY
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
<!-- AEROBIM_DOCUMENTED_ENV:END -->

## Project Structure

```text
aerobim/
├── backend/                 # Python FastAPI backend (see generated baseline below)
│   ├── src/aerobim/         # Source: core → domain → application → infrastructure → presentation
│   ├── tests/               # Backend test suite (see generated baseline below)
│   └── pyproject.toml
├── clients/revit-plugin/    # Thin authoring-side client boundary (planned)
├── docs/                    # TechLab jury docs only (see docs/README.md)
├── frontend/                # Browser review shell
├── audit/                   # Claims lock, blockers, citeable honesty fixtures
├── samples/                 # IFC, IDS, drawing, spec fixtures
├── .github/workflows/       # CI pipeline (lint, typecheck, test, benchmark-smoke) + manual release-readiness gates
└── LICENSE                  # MIT
```

<!-- AEROBIM_RUNTIME_BASELINE:BEGIN -->
<!-- regenerated by: python -m aerobim.tools.export_runtime_baseline -->
tests_passed: backend=2167, frontend=54; commit 88e726be20bc; see docs/evidence/runtime-baseline-latest.json · src ~74536 LOC; tests ~48215 LOC; extraction macro_f1=0.8600000000000001 (fixture corpus; not product accuracy)
<!-- AEROBIM_RUNTIME_BASELINE:END -->

## Documentation

Public GitHub is the **TechLab jury pack only**: code + TZ / claims / architecture + curated eng status. Operator runbooks and session dumps stay in `.local/` (not published).

| Need | Document |
|------|----------|
| **Start** | [`docs/TIER0_INDEX.md`](docs/TIER0_INDEX.md) · [`docs/README.md`](docs/README.md) |
| KT#2 submission pack | [`submission/README.md`](submission/README.md) |
| Jury memo (RU) | [`docs/docs.md`](docs/docs.md) |
| Samolet strategy | [`docs/samolet.md`](docs/samolet.md) |
| TZ Task 07 | [`docs/tz/README.md`](docs/tz/README.md) |
| Claims lock | [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](audit/reports/CLAIMS_LOCK_2026_07_17.md) |
| Eng freeze / status | [`audit/reports/CLAIMS_LOCK_2026_07_31.md`](audit/reports/CLAIMS_LOCK_2026_07_31.md) · [`docs/ENGINEERING_STATUS_2026_08.md`](docs/ENGINEERING_STATUS_2026_08.md) |
| Accepted risks (KT#2) | [`docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md`](docs/quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md) |
| Checkpoint | [`audit/reports/CRITICAL_BLOCKERS.md`](audit/reports/CRITICAL_BLOCKERS.md) · **NO_GO** |
| Project status audit | [`docs/PROJECT_STATUS_AUDIT_2026.md`](docs/PROJECT_STATUS_AUDIT_2026.md) |
| Capability × claim matrix | [`docs/capability-claim-matrix-2026.md`](docs/capability-claim-matrix-2026.md) |
| Quality protocol (WP-07) | [`docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) |
| Open corpora (WP-06) | [`samples/benchmarks/open-corpora/README.md`](samples/benchmarks/open-corpora/README.md) |
| License / offline | [`docs/license-policy-2026.md`](docs/license-policy-2026.md) · [`docs/offline-deployment-2026.md`](docs/offline-deployment-2026.md) |
| Benchmark evidence | [`docs/benchmark-evidence-2026.md`](docs/benchmark-evidence-2026.md) |
| Pilot protocol | [`docs/pilot-protocol-samolet-2026.md`](docs/pilot-protocol-samolet-2026.md) |
| Claim boundary | [`docs/pilot-claim-boundary-2026.md`](docs/pilot-claim-boundary-2026.md) |
| Architecture | [`docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) |
| Alignment R1–R15 | [`docs/samolet-techlab-alignment-2026.md`](docs/samolet-techlab-alignment-2026.md) |
| Partners / readiness | [`docs/partners/TECHLAB_TASK_07_READINESS_2026.md`](docs/partners/TECHLAB_TASK_07_READINESS_2026.md) |
| Reproducibility | [`docs/REPRODUCIBILITY-2026.md`](docs/REPRODUCIBILITY-2026.md) |
| Fixtures | [`docs/evidence/README.md`](docs/evidence/README.md) · [`samples/benchmarks/README.md`](samples/benchmarks/README.md) |

## Git commits

Keep authorship honest: `Co-authored-by:` trailers are allowed when an assistant materially contributed. Optional hooks (pass-through, no trailer stripping):

```bash
git config core.hooksPath .githooks
```

Suggested repo About — [.github/repository-metadata.md](.github/repository-metadata.md).

## Governance

- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Citation Metadata](CITATION.cff)
- [Support](SUPPORT.md)
- [Maintainers](MAINTAINERS.md)
- [Release Policy](RELEASE_POLICY.md)

## Release Readiness

Use the manual GitHub Actions workflow `.github/workflows/release-readiness.yml` when preparing a release candidate.

It runs benchmark rails by default and can optionally run the full live review smoke harness with browser artifacts.
The live-smoke path now installs Playwright and Chromium inside the workflow job so browser capture is reproducible in CI.
Main CI benchmark-smoke runs now also emit a compact benchmark summary table in workflow output and artifacts.
When needed, `require_live_smoke_gate=true` enforces live-smoke execution as a mandatory policy gate for that release-readiness run.
CI benchmark-smoke now also runs advisory threshold evaluation from `samples/benchmarks/benchmark-thresholds.json` and publishes the threshold summary alongside benchmark artifacts.
Release-readiness benchmark rails now support `benchmark_threshold_mode` (`advisory` or `enforced`) plus explicit threshold profile path selection.

## Stack

- **Python 3.12+**, **FastAPI**, **Uvicorn**
- **IfcOpenShell** / **IfcTester** / **IfcClash** (buildingSMART toolchain)
- **web-ifc** + **Three.js** for browser-side IFC review
- **pypdfium2** + **pdfminer.six** for core PDF (LIC-001 Option B); optional **PyMuPDF** only via `pdf-agpl`
- **RapidOCR** only when `.[raster]` is installed (EI OCR-aware signals PARTIAL)
- **Docling** (optional, document parsing)
- 5-layer Clean Architecture, constructor DI, Protocol ports

## License

MIT for **AeroBIM-authored** code. Third-party components keep their own licenses:

- **pypdfium2** / **pdfminer.six** / **Pillow** — production PDF path (permissive; see inventory)
- **PyMuPDF** — dual AGPL-3.0 / Artifex commercial; **optional `pdf-agpl` only** (absent from runtime lock / Docker after LIC-001 Option B)
- **IfcOpenShell / IfcTester** — LGPL-3.0-or-later
- **web-ifc** — MPL-2.0

Machine-readable inventory: [`audit/dependency_license_inventory.json`](audit/dependency_license_inventory.json) · policy: [`docs/license-policy-2026.md`](docs/license-policy-2026.md).  
**Not a court opinion.** Do not claim “entire product is MIT” without third-party disclosure.

