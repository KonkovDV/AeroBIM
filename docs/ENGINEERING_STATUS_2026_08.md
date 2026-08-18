---
title: "AeroBIM Engineering Status — August 2026"
status: active
version: "1.6.54"
last_updated: "2026-08-18"
claim_boundary: "Engineering readiness only. Checkpoint NO_GO. Open benches ≠ RF corpus. Public MOEXP IDS ≠ Samolet profile. Fixture != customer."
---

# Engineering Status — 2026-08-18

**Цифры тестов:** [`evidence/runtime-baseline-latest.json`](evidence/runtime-baseline-latest.json)  
**last_updated:** 2026-08-18 · **v1.6.54** — вход документации для жюри сужен; Checkpoint **NO_GO**; RT-001/002/003 OPEN  
**Checkpoint:** **`NO_GO`** — RT-001 (корпус ПД + экспертиза; открытые бенчи ≠ этот корпус) / RT-002 (подписанный профиль Самолёта; официальные IDS МОГЭ уже есть) / RT-003 (публичный федеративный инвентарь есть; clash NOT_VERIFIED; not MEP delivered)  
**Запрещённые формулировки:** [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) · датированная заморозка [`../audit/reports/CLAIMS_LOCK_2026_07_31.md`](../audit/reports/CLAIMS_LOCK_2026_07_31.md)  
**Жюри / МИК:** [`quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md`](quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md)  
**Академическая честность:** [`quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md`](quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md) · IUA [`quality/INTERPRETATION_USE_LEDGER_2026_08.md`](quality/INTERPRETATION_USE_LEDGER_2026_08.md) · литература [`quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md`](quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md)

## What improved (engineering — not customer GO)

| Track | Eng status | Customer |
|---|---|---|
| **HD11 RU/EU numbers** | `parse_localized_number` accepts `1 254,30` / NBSP / `1.254,30`; ambiguous `1.254` → `unparsed-numeric` (not silent AMBIGUOUS) | Not RT CLOSED; not customer accuracy |
| **HD10 cross-doc / reports** | SI ε-guard in classify; NFKC unit tokens; AbortController on report fetches | Not RT CLOSED; not customer accuracy |
| **Wave A (14.08 evening)** | MinStroy survey XSD intake; IfcClash `detect_clearance_between` extra-method on gap pair; clash→BCF **file ingest**; jurisdiction IDS document audit (50 files); SP 63 cover *template* | Not RT-001/002/003 CLOSED; HVAC fixture unused (no geometry); `cde_import=NOT_VERIFIED`; not a solver |
| **IDS fail-closed (0.4)** | SKIPPED / `ifcVersion` mismatch → ERROR; BSI 0101 live | Not product accuracy; labeled divergences |
| **Task 2 partial package** | `ifc_path` optional on analyze; document-only mode SKIPPED/NOT_VERIFIED for IFC engines; fail-closed if clash/MEP required | Not Checkpoint GO; not product accuracy |
| **Task 7 weekly eng status** | `python -m aerobim.tools.export_weekly_eng_status` → `docs/evidence/weekly-eng-status-latest.json`; funnel = OWNER_ONLY | Never invent commercial counts |
| **Task 4 adjudication plan** | `plan_adjudication_corpus` → recommended_n=111 for interim 0.60 @ expected 0.75 | Sizes labeling only; not precision |
| **External P1/P4 research** | Renga pin + IDS inventory 18/22; SPb/Amur AR recount; GOST **21.101-2026** п.8.2.4 GUID | Owner: Renga ToS cite; DWG A/B/C |
| **P4 Experiment A (Renga ПНСТ 909)** | **ToS GO**; runtime **18/22** IDS clean (snapshot 05.08); CLI in tree; live pack truncated → SKIPPED_PACK_INCOMPLETE | Evidence [`evidence/pnst909-22-scenario-runtime-latest.json`](evidence/pnst909-22-scenario-runtime-latest.json); not product accuracy |
| **Regulatory 21.101** | Marks OS/ODD/MBT; edition config; N-2 clause **8.2.4** | No full-compliance claim |
| **Demo format 2026-08** | 30–40 min script + criticality + discrepancy rule + on-prem expertise path | Ready for tracker pack |
| **Commercial ops quarantine** | Live funnel/outreach only locally, outside git; public = templates | Funnel numbers = owner only |
| **LOCAL→ADVISORY alias** | Boot WARNING; remove after 2026-09-21 | Docs must not reintroduce LOCAL-only |
| **CRITICAL_BLOCKERS RT-004…017** | Closed sections lead with **СТАТУС: ЗАКРЫТО** | RT-001/002/003 still OPEN → NO_GO |
| **Eng residuals wave** | VLM smoke gate; signature deepen; OIDC Phase 2 stubs; BCF T2 checklist; DWG native fail-closed; BSI IDS n=290 CC BY-ND; bare-metal wheelhouse DEFERRED | Checkpoint NO_GO unchanged |
| **Qwen / Studio KT#2** | RT budget charge+retry+ledger; inj: no model severity; PII `/Rotate`+counters; opaque client UUID; Red Team v1.5 | Checkpoint NO_GO; PII effectiveness NOT_MEASURED |
| **Open corpora + BSI IDS** | Fixture regression n=7 + BSI TestCases profile `regression-bsi` **honest_case_count=290** (CC BY-ND unmodified) | Regression only — not product accuracy |
| **WP-07 quality protocol** | Protocol doc + `compute_quality_protocol_stats` (Wilson P/R + sample-size planner); nDCG via existing `evaluate_ranking_quality`; interim target 0.60 | Not adjudicated customer precision; never >90% |
| **WP-06 open corpora** | Profiles under `samples/benchmarks/open-corpora/`; CI smoke pins | Regression/timing only — no expert TP/FP |
| **WP-05 package completeness** | Declared inventory: mandatory PD sections, format honesty (DWG native read not implemented), cipher/specs/schedules, PD↔RD pairing; soft opt-in via request flag | Fixture-grade only; not PP-87 / customer intake |
| **WP-04 norm pack v2** | Schema 2.0.0 RASE + `execution_mode` + expert confirmation journal; loader fail-closed without `customer_approved`+approval; `list_expert_required_norm_rules` | RT-002 OPEN; fixture ≠ customer pack |
| **WP-03 signature envelope** | Presence/hash/roles + signature_alg/value presence + optional package hash bind; trust_chain always NOT_VERIFIED | Never «УКЭП проверена»; crypto adapter missing |
| **WP-02 Hybrid advisory pre-gate** | Gate on Analyze advisory + kimi smoke PUBLIC egress | Not verdict path; Checkpoint NO_GO |
| **WP-01 runtime baseline** | Schema 1.4.0: passed/skipped/failed + gates + env fingerprint + **documented_env set equality (symdiff)** + **architecture_inventory** (48/72/63) checked in CI `--check-readme` + `docs-metadata-integrity` | Not Checkpoint GO |
| **ADR-002 open-core** | **accepted** 2026-08-05; LICENSE stays MIT | Boundary defined; not commercial features delivered |
| **OIDC BFF POST-05** | Phase 2 stubs + Phase 3 lab (`oidc_bff_phase3_ready`): nonce bind, HMAC session cookie, GET login/callback/**session** rate-limit; `safe_urlopen`; lab `identity_verified=false` without JWKS | Production IdP + FE bearer removal still required; default `auth_bff=NOT_IMPLEMENTED` |
| **BCF T2** | Verifier `--checklist` / `--eng-readiness`; pack STATUS stays NOT_VERIFIED | Needs real CDE log/screenshot/hashes |
| **Native DWG** | `python -m aerobim.tools.validate_dwg_toolchain` reports `dwg_native=NOT_IMPLEMENTED` | Forbidden: never DWG-ready; STUB-ODA-CAD-001 |
| **Tracker sprint 15.08 evening** | IFC-release matrix refresh (`clash=skipped` on tiny walls); dataset hunt + re-runs; consult pack; GTM KPI = scheduled demos | Not customer GO; Harbor NOT_RUN |
| **Wedge freeze (16.08)** | Product = IFC Acceptance Gate; CLI `run_demo_ifc_acceptance_gate` (`cv_sidecar=False`); overlay = P1 | Market GO ≠ Checkpoint GO; [`partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md`](partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md) |
| **HD triage remediations (16.08)** | 429 stamps CSP/XFO; outbound pin+null-proxy+shorthand; claims RU markers + four scanned files; baseline `tests_unaccounted=93` | Not RT-001/002/003 CLOSED |
| **HD close-out (16.08)** | Quota hold+reconcile; JWKS 30s cooldown; XFF must be an IP; IDS pass only if `status is True`; clash without GUID → failed | Not RT-001/002/003 CLOSED |
| **HD5 perimeter (16.08)** | SQL parameterized; deploy SQL for `tenant_id`; VLM egress allowlist; HTML href allowlist; PDF CR/LF → space | Not RT-001/002/003 CLOSED |
| **HD4 academic (16.08)** | Wilson n=111 regression; DOI year-twin lint; leak-scan JSON atoms; TokenVault LRU(4096) | Not RT-001/002/003 CLOSED |
| **HD3 engines (16.08)** | IDS missing `status` → SKIPPED/ERROR; malformed IfcClash → failed; IFC cache LRU(8); BFF cookie ≠ principal; unknown BCF version 400 | Not RT-001/002/003 CLOSED |
| **HD2 seams (16.08)** | JWKS kid refetch; `origin=advisory` out of reproducibility hash; DI singleton lock; trusted XFF; upload reserve-ahead + stale quota lock | Not RT-001/002/003 CLOSED |
| **Defensive engineering pass (15.08)** | OIDC tenant only from `AEROBIM_OIDC_TENANT_CLAIM`; ACL-before-read + 404 anti-enum; Redis required outside dev; ZIP NUL/XML depth+text; runtime lock excludes PyMuPDF | Not RT-001/002/003 CLOSED; not RELEASE_GO |
| **KT#2 speech pack (16.08)** | PII-first + sequence-not-rollback framing; fixture timing sheet (not SLA); Ask Самолёту (27/1026, 18/22 snapshot 05.08); 5-up Task-07 table; 10D intake page; corpus SSOT freeze | Not RT-001/002/003 CLOSED; видео не прилагаем (решение 17.08) |
| **IUA ledger (16.08)** | Kane Interpretation/Use table: what fixture/open-bench scores may mean for TZ / tracker / KT2–KT3 / IDS 1.0 / ISO 19650 | Not RT-001/002/003 CLOSED; [`quality/INTERPRETATION_USE_LEDGER_2026_08.md`](quality/INTERPRETATION_USE_LEDGER_2026_08.md) |
| **Academic literature triage (16.08)** | Kane/Messick map of Aug 2026 papers; Harbor NOT_RUN; IDS 1.1 not final; ISO 19650-6 not implemented | Not RT-001/002/003 CLOSED; [`quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md`](quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md) |
| **Residual close-out (16.08)** | `docs/partners/` claims-lint unblind (HDX-LINT-01); Postgres `001_reports_tenant_id.sql` + `AEROBIM_POSTGRES_APPLY_DDL=0`; IFC LRU ceiling 8×256 MiB JSON; mp4 gitignored | Not RT-001/002/003 CLOSED; mp4 gitignored; видео не прилагаем |
| **Architecture re-check remainder (16.08)** | `--day` default `latest` fail-closed; claims-lint scans tracked architecture/quality/gtm (no directory blinds); 413/415/422 upload quota release tests; `0` rate-limit rejected at boot on `samolet_pilot`/`production` | Not RT-001/002/003 CLOSED; 0=off remains development-only |
| **KT#2 readiness card (16.08)** | 5/5 **intake-form fields** have a tree deliverable: [`TIER0_INDEX.md`](TIER0_INDEX.md) → approach + 5-up comparison + playbook + status. Live CLI `run_demo_ifc_acceptance_gate` reproducible on fixture | Not RT-001/002/003 CLOSED; not Checkpoint GO; видео не прилагаем; ЛК upload = human |
| **Six-desk RT (17.08 evening)** | TechLab / MIK / tracker / IT mentor / science / VC pass: Gate sell-path, AABB n=6, tracker addendum, letter ≠ git-fact, Kane freeze `f9389bf` | Not RT CLOSED; N-43 lag **ACCEPTED**; criterion IUA still FAIL |
| **KT#2 video withdrawn (17.08)** | Ролик 2–3 мин не записываем и в форму не прикладываем. Показ = `run_demo_ifc_acceptance_gate`. Notice: [`demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md) | Not a recorded demo; not Checkpoint GO |
| **Jury-facing indexes (18.08)** | Вход `docs/README` и карта TIER0 сужены до документов Техлаба и МИК; служебный журнал разработки снят с обязательного чтения | Not RT-001/002/003 CLOSED; Checkpoint NO_GO |
| **KT#2 deck in git (17.08)** | Поле «Презентация»: [`../submission/03-presentation/aerobim_kt2.pptx`](../submission/03-presentation/aerobim_kt2.pptx) + [`../submission/03-presentation/aerobim_kt2.pdf`](../submission/03-presentation/aerobim_kt2.pdf). Речь: `slides.md`. Видео по-прежнему не прилагаем | Not Checkpoint GO |
| **Dataset CLI (task 3, 16.08)** | PNST 22-scenario CLI + frozen pairing; live pack truncated → `SKIPPED_PACK_INCOMPLETE` (05.08 **18/22** kept). IFC-Bench v2 **27/1026** re-run pin ok. Ishigaki gold XML processability 166/166 (not generation F1, no IFC). DrawingVQA link-only | Not a fresh 18/22; Harbor NOT_RUN; not RT-001 |
| **IfcClash tiny walls** | Skip degenerate products (`AEROBIM_CLASH_SKIP_TINY`, default on); all-skipped still FAILED | Not a silent pass |
| **LIC-001 Option B** | Core PDF = `pypdfium2` + `pdfminer.six`; PyMuPDF optional `pdf-agpl` only | Not a legal opinion |
| **P2-04 Annotation↔IFC** | Claimed GUID → `ifc_guid` only after spatial-index presence; index None clears pre-set guid | Not human-adjudicated matching |
| **P2-02 MEP honesty** | `edge_kinds` + optional AABB broadphase | RT-003 OPEN; never `mep_system_clash=OK` |
| **Offline** | Docker image-track smoke; bare-metal **DEFERRED** (`offline_bundle wheelhouse` exits 2) | Not “any air-gap without Docker” |
| **Checkpoint #2 pin** | Wall-guid evidence bundle pin | Live CDE T2 still NOT_VERIFIED |

## Plan / gap docs

| Doc | Role |
|---|---|
| [`roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md`](roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md) | Geometry honesty deepen plan + research anchors |
| [`roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md`](roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md) | MEP-CLASH-001 gap (updated 2026-08-01) |
| [`offline-deployment-2026.md`](offline-deployment-2026.md) | Docker offline VERIFIED; bare-metal deferred |
| [`license-policy-2026.md`](license-policy-2026.md) | LIC-001 Option B |
| [`extraction-integrity-2026.md`](extraction-integrity-2026.md) | EI signals + OCR PARTIAL |
| [`pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | WP-07 quality measurement protocol |
| [`partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md`](partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md) | Scope freeze: evidence layer, not TZ-wide AI reviewer |
| [`../samples/benchmarks/open-corpora/README.md`](../samples/benchmarks/open-corpora/README.md) | WP-06 open corpora profiles |
| [`evidence/checkpoint2-evidence-bundle-latest.json`](evidence/checkpoint2-evidence-bundle-latest.json) | Fixture GO pin |

## Forbidden (unchanged)

Forbidden until evidenced: Product accuracy >90%; customer SLA ≤30 min; native DWG; MEP delivered / `mep_system_clash=OK`; CDE_READY BCF; independent calc correctness; MIT-without-disclosure; bare-metal offline-ready; AABB/connects = verified geometric clash; open-corpora binary match / timing as product precision.

## Live CLI demo (KT#2)

Product path = IFC Acceptance Gate. Overlay PDF = P1. Freeze: [`partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md`](partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md).

```bash
cd backend
python -m aerobim.tools.run_demo_ifc_acceptance_gate
# optional P1 overlay:
python -m aerobim.tools.run_demo_vertical_slice
```

Do **not** present the 11.08 wall-guid snapshot HTML as a live overlay. Overlay PNG uses **pypdfium2** (LIC-001 Option B). Clone path is `pip install -e ".[dev,raster]"` — PyMuPDF / `pdf-agpl` is not required.

## Reproduce wall-guid fixture pin

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/benchmarks/project-package-wall-guid-demo.json \
  --output ../artifacts/evidence-bundle/checkpoint2-wall-guid
```
