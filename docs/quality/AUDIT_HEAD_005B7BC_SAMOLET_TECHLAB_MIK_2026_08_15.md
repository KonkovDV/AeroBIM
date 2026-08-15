<!-- claims-lint: allow-file reason="HEAD 005b7bc Samolet/TechLab/MIK audit; forbidden phrases as non-claims; Checkpoint NO_GO" -->
---
title: "Audit — HEAD 005b7bc vs Samolet Task 07, TechLab KT#2, MIK"
date: "2026-08-15"
status: active
claim_boundary: >
  Release audit of verified commit 005b7bc plus labelled dirty-tree verification.
  Checkpoint NO_GO. Does not close RT-001/002/003. Not product accuracy.
  Local pytest is not a CI pin replacement (N-26). Not a term sheet.
---

# Audit: HEAD `005b7bc` × Task 07 × TechLab KT#2 × MIK

**Author relationship:** Internal self-assessment, 15.08.2026.  
**Evaluated commit (GitHub verified):** `005b7bcb6fb2b9f353cc046b44fe68f1b519b776` (14.08 23:40 MSK).  
**Parent:** `dd1a0a70aa1b6328ccfd912820fa88638f72899f`.  
**Working tree at audit:** **dirty** — speech/UI/hygiene not on GitHub. Commands below ran on the dirty tree unless marked HEAD-only.

## 1. Executive verdict

Engineering readiness improved. Customer readiness did not change. Fixture GO ≠ checkpoint GO.

| Lane | Result |
|---|---|
| Checkpoint | **NO_GO** |
| RT-001 / 002 / 003 | **OPEN** (`closes_rt*=false`, `customer_pack_hash=null`) |
| Wave A | Fixture substitutes. None close a customer blocker |
| KT#2 (20.08) | Survivable **if** live CLI slice + NO_GO first. On **published** HEAD, rehearsal still opens wall-guid HTML |
| MIK stage | Still **доработка**. Validation/effectiveness has not started |
| Fundraise / SAFE | **NOT READY** (no entity, no paid pilot) |

Formula: not more features → more evidence → narrower scope → real pack → measured effect → then integration.

## 2. Current HEAD and git status

| Field | Value |
|---|---|
| HEAD | `005b7bcb6fb2b9f353cc046b44fe68f1b519b776` |
| Message | `feat(kt2): Wave A survey XSD, clearance clash, IDS audit (blockers stay OPEN)` |
| Diff vs parent | 38 files, **+12116 / −80** (mostly vendored MinStroy XSD) |
| Branch | `main...origin/main` |
| Dirty | 41 modified, 3 untracked (executor report, local pytest pin, funding RT) |

HEAD-only defect: `docs/demo/KT2_DEMO_REHEARSAL_2026_08_12.md` minute 15–22 opens `wall-guid/report.html` (no `#kt2-overlay`). Dirty tree rewrites rehearsal to live CLI. **GitHub still has the miss.**

## 3. Tests and runtime confidence (commands 15.08.2026)

Focused (dirty tree): `test_egrz_intake_xml_checks` + `test_bcf_export_and_clash` + `test_samples_manifest_gate` + `test_p0_remediation_fail_closed` + `test_jurisdiction_ids_audit` + `test_rt_customer_blocker_honesty_lock` → **57 passed**.

| Gate | Result | Claim |
|---|---|---|
| `ruff format --check src tests` | 641 files already formatted, exit 0 | working tree |
| `ruff check src tests` | All checks passed | working tree |
| `mypy src` | 344 files, no issues | working tree |
| `pytest tests -q` | **2259 passed, 12 skipped, 0 failed** in 144.93s | **local Windows 3.12.10 + ifcclash extra**; not CI |
| `lint_claims --matrix-guard` / `--full-docs` | 0 violations | working tree |
| `--check-readme` | OK; pin **9** commits behind; max 50 | CI pin stays `88e726be` |
| `run_demo_vertical_slice` | exit 0; `passed=false`; `outcome=failed`; `checkpoint=NO_GO` | dirty; overlay sha `9826281f…` |

**Do not copy 2259 into README.** CI publishable pin remains `tests_passed=2167`, frontend=54, `attested_by=ci`, commit `88e726be`. On **committed** HEAD, `tests_collected=2178` disagrees with `test_functions=2271`; dirty tree only fixes collected→2271. N-26 forbids forging `attested_by=ci`.

## 4. Samolet Task 07 matrix

Source: `docs/partners/TECHLAB_TASK_07_READINESS_2026.md` + `audit/reports/TZ_RUNTIME_MATRIX.md`. Pilot success criteria (SLA ≤30 min, TP/(TP+FP)≥60%, time saved ≥20%, BCF visible in customer tool, signed adjudication) are all **BLOCKED_BY_CUSTOMER_DATA**.

| Requirement | Status |
|---|---|
| 2D drawings | PARTIAL (PDF text-layer / OCR extra; CV deferred) |
| BIM models | VERIFIED_FIXTURE_ONLY |
| TZ + calculations | PARTIAL (`calculation_correctness=NOT_IMPLEMENTED`) |
| Compare PD/RD/TZ/norms | PARTIAL; customer pack absent |
| Clashes | PARTIAL; `mep_system_clash=NOT_VERIFIED` |
| Qty / area / dimension | VERIFIED_FIXTURE_ONLY |
| Logic gaps / IDS exists | VERIFIED_FIXTURE_ONLY |
| Problem-zone overlay | VERIFIED_FIXTURE_ONLY |
| Prioritization | VERIFIED_FIXTURE_ONLY |
| Designer comments + HITL | VERIFIED_FIXTURE_ONLY |
| Customer SLA ≤30 min | BLOCKED_BY_CUSTOMER_DATA (fixture rail only) |
| Expert in the loop | VERIFIED_FIXTURE_ONLY |
| MVP viz + report | VERIFIED_FIXTURE_ONLY |
| CDE handoff | NOT_VERIFIED (`cde_import`) |
| Native DWG | MISSING / FAILED |
| DXF | VERIFIED_FIXTURE_ONLY optional `[cad]` |
| Docker offline | FOUNDATION (image-track); bare-metal NOT_VERIFIED |
| `trust_chain` | NOT_VERIFIED |

TZ matrix: 24 VERIFIED_FIXTURE_ONLY, 1 ADVISORY_ONLY, 1 FIXTURE_ONLY SLA, 1 MISSING DWG, 1 BLOCKED_BY_CUSTOMER_DATA (norm packs). **Zero** rows are customer `VERIFIED`.

## 5. TechLab KT#2 and MIK alignment

Public MIK frame (SPbSTU / ABN 2026): отбор → доработка → валидация эффективности → внедрение. Prize = paid pilot fund, not a prototype contest.

| Need | Status |
|---|---|
| Current version | HEAD Wave A + dirty speech/UI |
| Working user scenario | Live CLI vertical slice (stamp/title/thickness, not doors/windows) |
| Demo | **KT#2-ready on dirty tree**. Published HEAD rehearsal still points at wall-guid |
| What works / fixture-only | Honest if speech follows Claims Lock |
| Ask from Samolet | Pack + profile + dual raters; not a round |
| How effect is measured | Protocol exists; **no customer numbers** |
| Hidden limits | IDS fail-closed, NO_GO, not Renga — must be said first |

KT#3 / validation stage still needs the intake pack (§10). Implementation in partner infra is out of scope until measurement exists.

Position: specialized **evidence-linked semantic QA layer**. Not 10D, not Tangl, not CDE, not the expert, not autonomous sign-off.

## 6. Wave A delta (committed)

| Item | Allowed | Forbidden | Closes |
|---|---|---|---|
| A1 MinStroy survey/geological XSD | intake fail-closed | electronic expertise | RT-001 stays OPEN |
| A2 50 IDS / 0 document issues | document self-audit, IDS 1.0 XSD | certification / Samolet profile | RT-002 stays OPEN |
| A3 bSI Validation Service | — | — | **human account**; not done |
| A4 clearance-gap ~30 mm extra-method | engine rehearsal | MEP delivered | Analyze still `detect()` only |
| A5 clash → our BCF → file ingest | T1 structural ZIP | CDE import | `cde_import=NOT_VERIFIED` |
| A6 SP 63 cover template | synthetic 20 mm pset | solver / table 8.1 | `calculation_correctness=NOT_IMPLEMENTED` |

No new ports/DI on HEAD.

## 7. Vertical slice (15.08.2026)

Command: `python -m aerobim.tools.run_demo_vertical_slice` (backend, venv 3.12). Exit 0.

| Check | Result |
|---|---|
| PDF text-layer | `format=pdf_text_layer`; 150 mm / WALL-01 |
| Page / coordinates | page 1; bbox ≈ (72, 62.48, 150.05, 12) |
| `finding_id` / `source_id` / `evidence_refs` | present in HTML and JSON |
| Overlay PNG | sha256 `9826281f83a1a5608a3bd88e7d4f4f52475a702c5f3c3a5b4100d05f05f6a349` |
| HTML | `#kt2-overlay`, `#kt2-claim-boundary`, Checkpoint NO_GO, Not a CDE import |
| JSON / BCF ZIP / run-manifest | written; `passed=false`; `outcome=failed` |
| VLM | Qwen LIVE fixture; Kimi GATED; `comparison_status=comparison_not_run`; verdict owner = deterministic engine |
| IFC | IfcOpenShell fixture, **not** Renga, **not** Samolet |

`working_tree_dirty=true` on the slice envelope. Reproducibility hash binds dirty code; compare overlay PNG, not raw `report.json` bytes (`created_at` drift).

## 8. Documentation inconsistencies

| Surface | HEAD `005b7bc` | Dirty tree 15.08 |
|---|---|---|
| Rehearsal 15–22 min | **wall-guid HTML** | live CLI `#kt2-overlay` |
| Pitch | hide README NO_GO; ask «пилот + инвест» | NO_GO 15s; ask slot/pack |
| One-pager | implies эталон exists | эталон optional |
| CI `tests_collected` | **2178** vs functions 2271 | 2271 only (passed stays 2167) |
| README tests_passed | 2167 @ `88e726be` | **unchanged** (correct) |

Do not treat dirty speech as published. Jury on GitHub clone still hits the wall-guid miss unless local files are committed **or** the operator follows the dirty rehearsal.

## 9. Claims allowed / forbidden

**Allowed:** bounded pilot; fixture evidence; fail-closed Shared-gate; expert remains accountable; deterministic verdict; advisory AI; customer validation pending; 50 IDS document self-audit; clearance rehearsal; BCF file ingest; MIT + services until a paid pilot.

**Forbidden (unchanged):** product accuracy >90%; customer SLA ≤30 min; native DWG; MEP delivered; CDE-ready BCF; independent calc correctness; IDS 1.1 certification; Samolet acceptance profile; Tangl/10D integration; fixture = customer evidence; Wave A closed RT-001/002/003; 2259 replaces 2167; demo IFC = Renga/Samolet; Checkpoint GO; SAFE/round (no entity).

## 10. Customer intake checklist (Samolet)

One residential section, one revision, IFC from **Renga as-is** (do not alias IFC4↔IFC4X3) + text-layer PDF + TZ fragment; signed acceptance profile / rule pack; typical-error catalogue (≥20 patterns, customer-confirmed); signed scope memo (what is *not* checked); two adjudicators; baseline manual hours T; NDA / closed-contour transfer; **named** CDE/BCF import target (not 10D API this week).

Pilot KPIs after that pack: precision = TP/(TP+FP); recall = TP/(TP+FN); time_saved = (T−T′)/T; bind commit, pack hash, rules hash, report hash, revision identity, adjudication log.

Out of first pilot: native DWG, doors/windows CV, full MEP, Tangl replace, solver, CDE API, autonomous sign-off.

## 11. Top 3 next actions

1. **Publish or explicitly operate from dirty rehearsal** so KT#2 does not open wall-guid. Operator choice; this audit does not commit.  
2. **KT#2 show:** live slice + NO_GO first + IFC matrix + limits block. Video 19.08 = human.  
3. **Send Samolet intake** (`SAMOLET_WHAT_WE_NEED_2026_07-ru.md` + Renga IFC request). Commercial KPI = 3–5 scheduled demos, not 50 more cold emails.

## 12. Human-required

Video + ЛК; entity; warm intros; Burnaev slot 2; Samolet owner; pack/profile/adjudicators; bSI Validation account; N43 **not before 17.08**; ODA = KT#3. Do not invent a builder CV.

## 13. Commit recommendation

**Do not commit from this audit.** If the owner later asks to commit, split: (a) speech/UI/rehearsal/CDE wording; (b) `tests_collected` 2178→2271 consistency only; (c) never overwrite `tests_passed=2167` or `attested_by=ci`. Local 2259 stays in `docs/evidence/runtime-baseline-wave-a-windows-2026-08-15.md`.

MIK sources (15.08): [SPbSTU four stages](https://research.spbstu.ru/events/tehlab_moskva/), [ABN four-stage model](https://abn.agency/2026/04/13/moskovskij-innovaczionnyj-klaster-zapustil-programmu-kommerczializaczii-ii-reshenij-dlya-biznesa/), [i.moscow TechLab news](https://i.moscow/news/single/cf985cfba4134407a14c9a10fb877145).
