<!-- claims-lint: allow-file reason="Funding Red Team; forbidden phrases as attacks/non-claims; Checkpoint NO_GO" -->
---
title: "Red Team + VC diligence attacks — AeroBIM КТ#2"
date: "2026-08-15"
status: active
last_updated: "2026-08-17"
claim_boundary: >
  Adversarial review for TechLab/jury and hypothetical seed diligence.
  Checkpoint NO_GO. Does not close RT-001/002/003. Not a term sheet.
  Not product accuracy. Not customer traction. Not a valuation.
---

# Red Team: атаки жюри, венчура и негативные траектории (15.08.2026)

**Author relationship:** Internal self-assessment after Wave A substitutes.  
**Checkpoint:** **`NO_GO`**.  
**Ask this week:** слот демо / корпус / профиль — **не** раунд. Юрлица нет.

Внешняя рамка diligence (не наши метрики): Zacua ConTech Investor Survey 2026 (n=140): team 83%, differentiation 50%, traction 48%; constraint is **adoption**, not more tech; exit concern 43%; AI/tech disruption 24%. Venture West 2026: seed diligence = field viability + end-user feedback, not dashboards. Building Ventures / Bau: domain founders and paid pilots beat AI wrappers.

## Verdict

| Lane | Result |
|---|---|
| Application security (new Critical/High this pass) | **0** — no new fetch/SSRF in this pack |
| Claims Lock | **PASS** — `lint_claims.py --matrix-guard` and `--full-docs` OK 15.08 after pitch/FAQ/one-pager/GTM |
| Customer Checkpoint | **NO_GO** (RT-001/002/003) |
| Fundraise / SAFE / priced round | **NOT READY** (no entity, no paid pilot, no customer corpus) |
| KT#2 speech | **Survivable if** NO_GO is first, demo is live slice, Wave A is not sold as CLOSED |

Engineering readiness improved. Customer and investor readiness did **not**.

## Current pass (17.08 evening — VC desk)

Ask remains **slot + labelled pack**, not a SAFE. No legal entity (journal 14.08). TIER0 «5/5» is intake-form completeness, not traction. CI pin is `runtime-baseline-latest.json` (`attested_by=ci`) and is not HEAD-complete (N-43 / RT-FUND-06). Kane IUA freeze `f9389bf` does not license customer precision.

| ID | Kill line | Status 17.08 evening |
|---|---|---|
| RT-FUND-25 | «5/5 executable readiness = you are GO / fundable» | **FIXED** — TIER0 now says form fields, not Checkpoint GO |
| RT-FUND-26 | «Letter already with the tracker / Samolet» | **FIXED** — form in git; delivery is operator, not a git fact |
| RT-FUND-06 | README `tests_passed` means HEAD fully tested | **ACCEPTED** — pin = `runtime-baseline-latest.json`; do not copy a local count |
| RT-FUND-10 | No entity → no SAFE | **ACCEPTED** — human; do not promise a round |
| RT-FUND-19 | No paid pilot, no LOI | **ACCEPTED** — KPI = 3–5 scheduled demos; git demos = 0 |

## Attack tree (how a hostile partner actually kills you)

### A. Evidence substitution (jury + associate)

| ID | Attack | Why it lands | Status after 15.08 |
|---|---|---|---|
| RT-FUND-01 | «50 IDS, 0 issues = certified / Samolet profile» | XmlIdsDocumentAuditor ≠ bSI IDS-Audit-tool; IDS 1.0 XSD on some 1.1 files | **MITIGATED** in Wave A RT + FAQ |
| RT-FUND-02 | «Clearance 30 mm = MEP delivered» | Extra-method; Analyze still `detect()`; HVAC has no tessellation | **MITIGATED** |
| RT-FUND-03 | «MinStroy XSD = экспертиза» | Intake format, not remark corpus | **MITIGATED** |
| RT-FUND-04 | «Clash→BCF = CDE-ready» | Own ZIP consume; `cde_import=NOT_VERIFIED` | **MITIGATED** (HTML/UI 15.08: «Not a CDE import») |
| RT-FUND-05 | «SP 63 template = solver» | 20 mm covering pset, not table 8.1 | **MITIGATED** |
| RT-FUND-06 | «README `tests_passed` means HEAD fully tested» | CI pin = `runtime-baseline-latest.json`; a local pytest count is not publishable (N-26) | **ACCEPTED** — do not copy a local count into README |
| RT-FUND-07 | Open 0.86 / 0.43 as product accuracy | Fixture F1 vs AECV open-bench | **MITIGATED** in pitch card; keep repeating |
| RT-FUND-08 | Harbor 160 skipped → invent false-pass % | Inventory 196 only | **ACCEPTED** SKIPPED |

### B. Venture kill shots (partner meeting)

| ID | Kill line | Fact in repo | Counter-speech | Close? |
|---|---|---|---|---|
| RT-FUND-09 | «You hide NO_GO on slide 1» | Pitch 05.08 said *don’t* open README NO_GO first | **Fixed:** lead with NO_GO 15s, then one finding | speech |
| RT-FUND-10 | «No entity → no SAFE» | Journal 14.08: юрлица нет | Don’t promise a round. Ask for a calendar slot | **human** |
| RT-FUND-11 | «50 cold / 0 replies = no market» | Tracker follow-up; KPI already flipped to 3–5 scheduled demos | Don’t send 50 more identical emails | **human** |
| RT-FUND-12 | «MIT means you have nothing to sell» | LICENSE MIT; ADR-002 accepted as *boundary*, not a split repo | Default speech **A: MIT + services** until a paid pilot. B is a *discussion*, not current SKU | **fixed** pitch |
| RT-FUND-13 | «AI wrapper; Cursor does this» | ADR-001: VLM cannot set `summary.passed` | Demo OFF==ON; fail-closed IDS version | product |
| RT-FUND-14 | «Tangl already checks BIM» | Public stack Renga+Tangl+10D | Tangl = **model**; we = **package** (PDF↔IFC↔IDS↔calc) | speech |
| RT-FUND-15 | «Самолёт writes this in 90 days» | True for *checks*; false for dual-rater pack + provenance contract | Sell a cheaper hypothesis test, not a moat-of-code | speech |
| RT-FUND-16 | «Where is the builder?» | Pitch already: don’t invent a construction CV | Name only facts; otherwise say the gap | **human** |
| RT-FUND-17 | «Adoption is the constraint, you keep adding ports» | Freeze lifted 14.08; extra-methods only | Show one command, not a layer diagram | process |
| RT-FUND-18 | «Asking for invest at NO_GO» | Pitch 4:00–5:00 said «пилот + инвест» | **Fixed:** ask slot / pack / dual raters, not a round | speech |
| RT-FUND-19 | «No paid pilot, no LOI» | Funnel in `.local` only; git demos = 0 | 3–5 scheduled demos is the only GTM KPI | **human** |
| RT-FUND-20 | «SSO/OIDC production» | BFF 501 | Never say production SSO | intact |
| RT-FUND-21 | «Native DWG in TZ» | FAILED/MISSING | IFC+PDF path; ODA = human KT#3 | intact |
| RT-FUND-22 | Exit story / strategic CVC | None | Don’t invent an acquirer. CVC wants parent ROI (Zacua: 41% CVC strategic alignment) | **don’t fake** |

### C. Негативные траектории (если не остановить)

1. **Substitution spiral.** Каждая волна (XSD, clearance, SP 63) читается как CLOSED blocker → на КТ#2 жюри ставит «врали про GO».  
2. **AI-premium valuation.** Питч как «AI для экспертизы» → 2026 clobbering SaaS/AI (Venture West). Потом down-round, когда VLM не ставит PASS.  
3. **MIT fork.** Заказчик копирует ядро, оставляет себе норм-пак. Выручка = 0, если речь не A/B.  
4. **GPL contamination.** LibreDWG «на выходных» → LICENSE conflict.  
5. **Program violation.** А101/Галс как «второй заказчик Техлаба» → конфликт с AM 05.08.  
6. **Demo miss 19.08.** Открывают `wall-guid/report.html` без `#kt2-overlay` → «нет продукта». Live CLI: `python -m aerobim.tools.run_demo_ifc_acceptance_gate`.  
7. **CI/local test split.** Ассоциат видит CI pin в README и другой счётчик локально → «врут в метриках». Держать pin CI; local count отдельно.  
8. **Harbor theatre.** Гонят 160 задач ради слайда → чужой бенч как accuracy.  
9. **Entity delay.** Слоты есть, договора нет → демо сгорают.  
10. **Single-customer capture.** Только Самолёт; без тёплых слотов экспертизы воронка = 0 вне программы.

### D. Voice / provenance (jury GitHub)

| ID | Attack | Why it lands | Status 15.08 |
|---|---|---|---|
| RT-FUND-23 | «Репозиторий ведёт языковая модель» | README «План ИИ»; copy-paste промпт; Cursor UUID субагентов | **MITIGATED** — операторские брифы, UUID сняты. Продуктовый ИИ (ADR-001 / VLM advisory) **сохранён** |
| RT-FUND-24 | «Вычистили ИИ = вычистили честность» | Риск стереть `closes_rt*=false` / NO_GO | **REFUSED** — honesty lock и Checkpoint **NO_GO** не ослаблялись |

## Triage (что чинить кодом/речью vs что только человеком)

| Pri | Item | Owner | 15.08.2026 |
|---|---|---|---|
| KILL | Юрлицо, SAFE, priced round | human | not in git |
| KILL | Paid pilot / LOI / 3–5 calendar demos | contractor + owner | KPI already restated |
| P0 | Hide NO_GO / ask for «инвест» on slide | speech | **pitch patched** |
| P0 | One-pager implies dual-rater эталон exists | speech | **one-pager patched** |
| P0 | Wave A = RT CLOSED | speech | FAQ + this RT |
| P0 | Copy a local pytest count into README | eng | **refused** (N-26) |
| P1 | Wrong demo HTML for Burnaev | docs | **done 15.08** |
| P1 | CDE wording in UI | eng | **done 15.08** |
| P1 | Stale Wave A «pytest not run» | docs | **this RT + Wave A note** |
| P2 | BSI account, Samolet pack, federated IFC | human | cannot fake |
| P2 | Domain founder CV | human | don’t invent |
| DEFER | AEC-Bench Harbor, ODA, live CDE, new MEP provider | calendar | not before KT#2 artifacts |

## Fundable sentence (единственная честная)

> AeroBIM is an evidence-first package checker: one command, a non-PASS finding with overlay and BCF ZIP, fail-closed IDS/IFC version, expert keeps the verdict. We are **not** customer-signed. We are raising a **pilot slot and a labeled pack**, not a claim that the checkpoint is GO.

If a partner needs GO language, **walk away**. Substituting fixture evidence is how this company dies.

## Sources (external)

- Zacua Ventures, ConTech Investor Survey 2026, 140 investors; team 83%; adoption over net-new tech.  
- BuiltWorlds / Venture West 2026: field-ready + end-user feedback at seed.  
- Building Ventures thesis (F4): domain expertise. Bau Ventures: no dashboard-only, no unpaid behavior change.

Internal SSOT: `CRITICAL_BLOCKERS.md`, Claims Lock, ADR-001, Academic RT 15.08 [`RED_TEAM_ACADEMIC_KT2_2026_08_15.md`](RED_TEAM_ACADEMIC_KT2_2026_08_15.md), CI pin in [`../evidence/runtime-baseline-latest.json`](../evidence/runtime-baseline-latest.json). Local pytest counts are not a second public pin.
