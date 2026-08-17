<!-- claims-lint: allow-file reason="TechLab/MIK/Novator jury Red Team; forbidden phrases as attacks/non-claims; Checkpoint NO_GO" -->
---
title: "Red Team — жюри Техлаб × МИК × Новатор"
date: "2026-08-16"
status: active
version: "1.2.0"
last_updated: "2026-08-17"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Adversarial jury review of the public GitHub pack. Checkpoint NO_GO.
  Does not close RT-001/002/003.
  Not product accuracy. Not paid-pilot result. Not Novator 2026 filing.
  Local pytest is not the CI pin.
---

# Red Team: жюри Техлаба, контур МИК (16.08)

**Persona:** член жюри / эксперт площадки, который клонирует репозиторий и читает верхний слой, не чат оператора.  
**Checkpoint:** **NO_GO**. `closes_rt001: false`. `closes_rt002: false`. `closes_rt003: false`.

**Stage call:** AeroBIM is in **доработка** (КТ#2 20.08). Validation of *effectiveness* (`валидация эффективности`) and *implementation* have **not started**. Speaking as if they have is a kill.

**Новатор 2026:** not a filing. Criteria are a thinking model only. Honest 2027 nomination, if any: «Меняющие реальность» — **not** «Лидеры инноваций» (no legal entity, no revenue).

## Current pass (public `main`, 17.08 evening — six desks)

Object: clone as TechLab jury, MIK stage officer, tracker Siginevich, IT mentor, scientific consultant, seed associate. Live demo = `python -m aerobim.tools.run_demo_ifc_acceptance_gate`. Overlay `run_demo_vertical_slice` is P1. Do not open `docs/evidence/kt2-handoff-2026-08-11/wall-guid/report.html` as overlay. IUA freeze remains `f9389bf`.

| ID | Desk | Attack | Status |
|---|---|---|---|
| RT-JURY-K01 | TechLab | Clone reads as LLM/session dump | **MITIGATED** — unpublished; gitignore |
| RT-JURY-K02 | TechLab | README leads with tracker dumps / Studio analysis | **MITIGATED** — front door = TIER0 + Hostile QA + Samolet ask |
| RT-JURY-D01 | TechLab | Open `wall-guid/report.html` as overlay | **MITIGATED** — live CLI first; hashed HTML is pin |
| RT-JURY-D02 | TechLab | Open `vertical-slice/report.html` | **FIXED** — unpublished from the public tree |
| RT-JURY-D06 | TechLab | 11.08 handoff / 5:30 pitch still overlay-first | **FIXED** 17.08 evening — sell-path = Acceptance Gate on handoff, pitch, tracker addendum |
| RT-JURY-G01 | IT mentor | Quote a local pytest count against the CI pin | **MITIGATED** — CI pin `acac02bd` / 2455 |
| RT-JURY-I01 | TechLab | Jury memo pins a stale `HEAD` SHA (`25ef3ee`) | **FIXED** — formula SSOT is the FAQ |
| RT-JURY-I02 | TechLab | AABB n=5 vs n=6 vs duplex 654 as one score | **FIXED** — fixture P/R **n=6**; 654 = inventory |
| RT-JURY-I04 | IT mentor | Clash README matrix quote still `n=5` while JSON `support=6` | **FIXED** 17.08 evening — matrix wording **n=6** |
| RT-JURY-I03 | IT mentor | N-43: runtime baseline lags HEAD after hygiene | **ACCEPTED** — do not mint a local attestation |
| RT-JURY-T06 | Tracker | 14.08 one-pager overlay-first + «1980 / 656» as if current | **MITIGATED** — addendum 17.08; historical row labelled snapshot |
| RT-JURY-S01 | Tracker | «Письмо уже у трекера» as a git fact | **FIXED** — form in repo; delivery = operator |
| RT-JURY-F01 | MIK / VC | «Executable readiness 5/5» read as Checkpoint GO / traction | **FIXED** — 5/5 = intake-form fields, not GO |
| RT-JURY-V01 | Science | Fixture fail-closed sold as Messick *criterion* for Samolet | **ACCEPTED** — Kane IUA still FAIL for customer use |
| RT-JURY-M01 | MIK | «Отобраны → продукт готов / валидирован» | **MITIGATED** — stage = доработка |
| RT-JURY-C01 | All | Kitchen cleanup flips Checkpoint GO | **REJECTED** — RT-001/002/003 stay OPEN |

### Six-desk scorecard (17.08 evening)

Scale: 0 = missing, 1 = protocol/fixture only, 2 = customer-evidenced. Do not average into product accuracy.

| Desk | What they open first | Licensed today | Kill if spoken | Score |
|---|---|---|---|---|
| **TechLab jury** | README formula → `submission/` → live CLI | Fail-closed finding on fixture; stage = доработка | Snapshot HTML as overlay; 27/1026 as product accuracy | 1 |
| **MIK** | Four-stage model + `docs.md` calendar | Stage 2 доработка; protocol for stage 3 exists | Валидация эффективности / внедрение as current fact; ENG_READY SLA | 1 (stage 2) / **0** (stages 3–4) |
| **Tracker** | [`TRACKER_MEETING_2026_08_14.md`](../demo/TRACKER_MEETING_2026_08_14.md) + addendum | Tasks 1–3: gate + IFC matrix + countable open benches; Plan B 15.09 | Overlay as *the* product; 1980/656 as CI; letter «already sent» | 1 |
| **IT mentor** | Live CLI + fail-closed IDS + CI pin | Reproducible gate; SKIPPED→FAILED; N-43 lag disclosed | Local pytest as README pin; clash README n=5 vs JSON n=6 | 1–2 (engine) |
| **Science** | Kane IUA ledger freeze `f9389bf` | Content/substantive for the engine; criterion FAIL for Samolet | Fixture F1 / AABB P/R as Task-07 precision | 1 (IUA) / **0** (criterion) |
| **VC / seed** | Funding RT; no entity | Ask = slot + labelled pack; MIT + services | SAFE / paid-pilot 2 млн as awarded; 5/5 as traction | **NOT READY** |

Engineering readiness improved. **Customer, MIK-act, and fundraise readiness did not.** Checkpoint stays **NO_GO**.

## Historical pass (15.08, object `0402a7e`)

The 15.08 attack tree below is kept as the MIK / Новатор thinking-model. It does not license GO.

## 0. External frame (opened 15.08.2026)

| Source | What it licenses |
|---|---|
| [SPbSTU / Фонд МИК](https://research.spbstu.ru/events/tehlab_moskva/) | Four stages: **отбор → доработка → валидация эффективности → внедрение**. Fund 20 млн ₽. Commercial agreement with the partner, not a prototype prize. |
| [ABN, 13.04.2026](https://abn.agency/2026/04/13/moskovskij-innovaczionnyj-klaster-zapustil-programmu-kommerczializaczii-ii-reshenij-dlya-biznesa/) | Verified demand; до 50 команд; валидация **эффективности** then внедрение on partner infra. |
| [i.moscow news](https://i.moscow/news/single/cf985cfba4134407a14c9a10fb877145) | Selection: competencies, scientific-technical novelty, **match to the customer request**, commercialization. |
| [LETI task card](https://new.etu.ru/ru/home/nauka/konkursy-i-granty-na-provedenie-niokr/konkursy-i-granty-na-provedenie-nauchno-issledovatelskih-rabot/programma-dorabotki-i-vnedreniya-naukoemkih-ii-reshenij) | Task 07 Самолёта: ИИ-платформа проверки ПД; prize = **paid pilot 2 млн ₽** (1 место). |
| [RBC / Новатор 2026 demo days](https://companies.rbc.ru/news/wIC3AQr71t/180-proektov-vyishli-v-finalnyij-etap-premii-mera-novator-moskvyi/) | Jury scores: team, novelty, problem relevance, scale, competitive edge, presentation logic, defence, market context. |
| [mos.ru / Unicorn Road](https://unicornroad.ru/competition/tpost/a0yhx6li81-konkurs-novator-moskvi-2026) | Nominations: «Проект будущего» / «Меняющие реальность» (prototype + business model) / «Лидеры инноваций» (**юрлицо + выручка**). Cycle 2026 **closed**. |

**Stage call:** AeroBIM is in **доработка** (КТ#2 20.08). Validation of *effectiveness* and *implementation* have **not started**. Speaking as if they have is a kill.

**Новатор 2026:** not a filing. Criteria are a thinking model only. Honest 2027 nomination, if any: «Меняющие реальность» — **not** «Лидеры инноваций» (no legal entity, no revenue).

## 1. Verdict

| Lane | Result |
|---|---|
| Application security (new Critical/High this pass) | **0** |
| Claims Lock | **PASS intended** after this pack |
| Customer Checkpoint | **NO_GO** |
| MIK stage | **Доработка.** Валидация эффективности = NOT STARTED. Внедрение = NOT STARTED |
| Novator-style score (thinking model) | Survive demo **if** NO_GO is first and live CLI is opened. Fail if snapshot HTML or ENG_READY SLA is sold as a result |
| Fundraise / SAFE | **NOT READY** |

Engineering readiness improved. **Customer and MIK-act readiness did not.**

## 2. Attack tree (how this jury actually kills you)

### A. Stage substitution (МИК four-stage)

| ID | Attack | Why it lands | Status after this pass |
|---|---|---|---|
| RT-JURY-M01 | «Отобраны → значит продукт готов / валидирован» | SPbSTU stage 3 is *effectiveness*, not GitHub stars | **MITIGATED** — README/docs.md already say participation ≠ proven effect. This RT restates stage = доработка |
| RT-JURY-M02 | MIK M5 «ENG_READY» on SLA ≤30 min / TP≥0.60 | Jury reads ENG_READY as measured | **FIXED** — protocol-ready, measurement BLOCKED_CUSTOMER_DATA |
| RT-JURY-M03 | «до 3 авг» still future tense on 15.08 | Looks like missed Fund deadline, then silence | **FIXED** — overdue / VERIFY_WITH_OPERATOR, no invented forms |
| RT-JURY-M04 | Act MIK with fixture 0.86 / AECV 0.43 | Goodhart; Messick criterion invalid | **ACCEPTED** — forbidden; protocol exists, numbers do not |
| RT-JURY-M05 | Paid-pilot 2 млн as if already awarded | Prize is *if* 1st on the task, after validation | **ACCEPTED** — ask = slot/pack, not the 2 млн cheque |

### B. Demo miss (КТ#2 20.08)

| ID | Attack | Why it lands | Status |
|---|---|---|---|
| RT-JURY-D01 | Open `wall-guid/report.html` as the overlay demo | No `#kt2-overlay`; clash reason was blank on 11.08 snapshot | **FIXED** — handoff table leads with live CLI; snapshot labelled; verifier checks it |
| RT-JURY-D02 | Open `vertical-slice/report.html` (11.08) | Same miss | **FIXED** — unpublished from the public tree |
| RT-JURY-D03 | Stale AUDIT_HEAD says GitHub still dirty / rehearsal still wall-guid | After `0402a7e` that sentence is false → integrity kill | **FIXED** — superseded banner + audit of `0402a7e` |
| RT-JURY-D04 | Clash `failed:` empty string on committed wall-guid HTML | Looks broken, not honest | **ACCEPTED** on frozen HTML (hash pin). Live detector now names type + fixture geom-init. Do not rewrite the 11.08 bundle |
| RT-JURY-D05 | IFC4X3 extra `AEROBIM-IDS-IFC-VERSION` sold as accuracy | Fail-closed BSI 0101 | **MITIGATED** in matrix evidence; keep repeating |

### C. Новатор thinking-model (not a 2026 filing)

| ID | Attack | Why it lands | Honest score |
|---|---|---|---|
| RT-JURY-N01 | Pitch as «Лидеры инноваций» | Needs юрлицо + выручка | **FAIL if claimed.** Nomination if 2027: «Меняющие реальность» at most |
| RT-JURY-N02 | Team / builder (criterion 2.6) | RBC: team competence is scored | **OPEN / human** — do not invent a construction CV |
| RT-JURY-N03 | IP 1.3 / Роспатент | Checklist exists, no application number in git | **OPEN / human** |
| RT-JURY-N04 | Scale / market | Funnel in `.local` only; git demos = 0 | KPI = 3–5 scheduled demos |
| RT-JURY-N05 | Presentation logic | Live CLI + NO_GO 15s is the only surviving shape | Rehearsal already rewritten |
| RT-JURY-N06 | Competitive edge vs Tangl/10D | Public stack is Renga+Tangl+10D | Speech: Tangl = model, we = package. Do not claim integration |

### D. Task 07 match (customer request)

| ID | Attack | Why it lands | Status |
|---|---|---|---|
| RT-JURY-T01 | Native DWG in TZ, FAILED in product | Tracker 07.08: requirement remains | **ACCEPTED** — IFC+PDF path; ODA = human KT#3 |
| RT-JURY-T02 | MEP / federated clash delivered | 654 AABB ≠ clash | RT-003 OPEN |
| RT-JURY-T03 | CDE-ready BCF | Own ZIP consume | `cde_import=NOT_VERIFIED` |
| RT-JURY-T04 | «AI understands drawings» | AECV doors/windows | Rehearsal forbids; ADR-001 |
| RT-JURY-T05 | Wave A closed blockers | XSD/IDS/clearance substitutes | `closes_rt*=false` locked |

## 3. Scorecard (thinking model — not a contest form)

Scale: 0 = missing, 1 = protocol/fixture only, 2 = customer-evidenced.

| Criterion | Score | Note |
|---|---|---|
| Match to Самолет Task 07 (IFC+PDF+IDS path) | 1 | Fixture demo exists; customer pack absent |
| Scientific-technical novelty (hybrid + fail-closed) | 1–2 | Architecture is real; not a unique moat vs in-house |
| Demo / presentation | 1 | Live CLI survives; 11.08 `wall-guid` HTML remains a hash pin, not overlay |
| Honesty / defence | 2 | NO_GO first is the strongest jury asset |
| Effectiveness validation (МИК stage 3) | **0** | No labelled pack, no dual raters, no time-saved |
| Implementation (МИК stage 4) | **0** | No CDE, no entity, no paid pilot |
| Team (builder on the call) | 0–1 | Human-only |
| Commercialization | 1 | MIT + services speech; no LOI |
| IP filing | 0 | Checklist only |
| Novator «Лидеры» eligibility | **0** | No юрлицо |

**Do not average this into a product accuracy number.**

## 4. What this pass changes in the repo

- Handoff index: live CLI first; wall-guid / 11.08 HTML are **not** the overlay demo.  
- `verify_kt2_handoff`: snapshot HTML must lack `#kt2-overlay`; rehearsal and handoff README must forbid opening it as the slice.  
- MIK / tri-source: SLA and interim precision are **protocol-ready**, not ENG_READY measurements. «до 3 авг» marked overdue.  
- Clash live reason: nameless `AssertionError` → type + tiny-fixture geom-init (frozen 11.08 HTML unchanged).  
- Audit of HEAD `0402a7e`; old `005b7bc` audit superseded.  
- Honesty lock on **this file**.

## 5. Still human-only

ЛК upload; entity; Samolet pack + two adjudicators; Renga IFC as-is; named CDE target; MIK agreement templates; Роспатент number; builder CV. Video is withdrawn (not recorded).

## 6. One sentence for the jury

> We are in **доработка**: one command shows a fail-closed, evidence-linked finding on a fixture. We are **not** in валидация эффективности. Checkpoint stays **NO_GO** until a labelled Samolet pack exists.

Formula: not more functions → more evidence → narrower scope → real pack → measured effect → then implementation.
