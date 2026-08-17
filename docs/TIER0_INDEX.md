---
title: "AeroBIM Tier-0 — TechLab jury"
status: active
version: "4.5.6"
last_updated: "2026-08-17"
tags: [aerobim, documentation, tier-0, techlab]
claim_boundary: "Jury pack only. Checkpoint NO_GO until RT-001/002/003. Eng readiness ≠ customer GO."
---

# Tier-0 (TechLab jury)

**`NO_GO`** — [CRITICAL_BLOCKERS](../audit/reports/CRITICAL_BLOCKERS.md) · [CLAIMS_LOCK](../audit/reports/CLAIMS_LOCK_2026_07_17.md) · [claim-boundary](pilot-claim-boundary-2026.md) · [ADR-001](architecture/ADR-001-verdict-ownership-2026.md)

| Document | Role |
|---------|------|
| [Jury technical justification (RU)](docs.md) | `docs.md` |
| [Engineering status](ENGINEERING_STATUS_2026_08.md) | Readiness — not Checkpoint GO |
| [Hostile QA playbook](demo/KT2_HOSTILE_QA_PLAYBOOK_2026_08_16.md) | Scripts pinned to SSOT |
| [3-minute video script](demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md) | Operator records 19.08 |
| [Jury FAQ](demo/KT2_JURY_FAQ_2026_08_12.md) | Speech card |
| [Fixture timing](demo/KT2_FIXTURE_TIMING_2026_08_16.md) | Order of magnitude — not customer SLA |
| [Task-07 comparison](demo/KT2_TASK07_COMPARISON_2026_08.md) | Five solutions; competitor numbers = their claims |
| [10D intake contract](demo/KT2_10D_INTAKE_CONTRACT_2026_08.md) | Proposed fields; not a 10D connector |
| [Corpus SSOT](demo/KT2_CORPUS_SSOT_2026_08.md) | Frozen line until KT#2 |
| [Samolet intake ask](partners/SAMOLET_KT2_ASK_2026_08_15.md) | Pack / profile / adjudicators / CDE |
| [Wedge freeze](partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md) | Product = IFC Acceptance Gate |
| [Unsigned acceptance profile v0.1](partners/SAMOLET_ACCEPTANCE_PROFILE_V0_1_2026_08_15.md) | RT-002 OPEN |
| [Quality / acceptance protocol](partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md) | Measurement method |
| [Task 07 readiness](partners/TECHLAB_TASK_07_READINESS_2026.md) | Form / readiness |
| [Jury / MIK red team](quality/RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md) | Stage = доработка |
| [Academic honesty](quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md) | Messick / Kane |
| [Literature triage](quality/ACADEMIC_LITERATURE_TRIAGE_2026_08.md) | August 2026 × IUA (Harbor NOT_RUN) |
| [Funding / diligence attacks](quality/RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md) | Hostile questions |
| [Interpretation/use ledger](quality/INTERPRETATION_USE_LEDGER_2026_08.md) | Licensed vs blocked inferences |
| [Accepted risks](quality/ACCEPTED_RISKS_REGISTRY_KT2_2026_08_09.md) | At KT#2 |
| [Data statement](evidence/DATA_STATEMENT_2026_08.md) | What exists; open benches ≠ RT-001 |
| [Citeable fixtures](evidence/README.md) | Evidence index |
| [Samolet strategy](samolet.md) | 10D context |
| [Customer TZ v2.0](tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) | Task 07 TZ |
| [Claim boundary](pilot-claim-boundary-2026.md) | Verified vs planned |
| [ADR-001 verdict ownership](architecture/ADR-001-verdict-ownership-2026.md) | Who owns `summary.passed` |
| [Target architecture](architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) | Hybrid design |
| [Capability / claim matrix](capability-claim-matrix-2026.md) | Allowed vs forbidden |
| [QA defense card](qa-defense-2026.md) | 20–30 s answers |
| [README](../README.md) · [README (RU)](../README.ru.md) | Product README |

Operator runbooks, session audits, and commercial PII live under `.local/` — not on GitHub.

## Submission pack (форма приёма решения)

Пять полей формы разложены по подпапкам: [пакет подачи КТ#2](../submission/README.md). Построчное покрытие ТЗ Задачи 07: [карта требований ТЗ](../submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md).

## Pre-flight (KT#2, 20.08)

Executable readiness = 5/5. Checkpoint **NO_GO**. Fixes are code+tests in this tree; rehearsal / operator mp4 / ЛК upload are human (`RED_TEAM_FINAL_VERDICT_2026_08_16.md` §4).

| # | Requirement (KT#2 card) | Deliverable in this tree | Gate |
|---|---|---|---|
| 1 | Видео 2–3 мин (17–19.08) | [3-minute video script](demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md) | live CLI; PII-first; snapshot HTML запрещён |
| 2 | Подход к решению | [Jury memo](docs.md) + [readiness](partners/TECHLAB_TASK_07_READINESS_2026.md) + [wedge freeze](partners/WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md) | deterministic gate; advisory ≠ verdict |
| 3 | Сравнение решений | [Task-07 comparison](demo/KT2_TASK07_COMPARISON_2026_08.md) | competitor numbers = их claims |
| 4 | Харденинг | [Hostile QA playbook](demo/KT2_HOSTILE_QA_PLAYBOOK_2026_08_16.md) §2 | §0 formula; RED_TEAM_FINAL_VERDICT §1 |
| 5 | Версия для проверки | [Engineering status](ENGINEERING_STATUS_2026_08.md) → `run_demo_ifc_acceptance_gate` | fail-closed; reproducibility hash |

Люди: dry-run 17–18.08, запись 19.08, ЛК upload 19–20.08. Не код.
