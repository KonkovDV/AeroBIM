<!-- claims-lint: allow-file reason="KT#3 re-scope without customer files; RT blockers stay OPEN; forbidden phrases as non-claims" -->
---
title: "KT#3 without Samolet files — owner re-scope"
date: "2026-08-23"
claim_level: fixture_and_proxy_only
claim_boundary: "Customer files are not expected in git. KT#3 is the live fixture gate plus public/synthetic proxies. Not product accuracy. Not customer SLA. Not MEP delivered. Not CDE-ready. Checkpoint NO_GO. closes_rt001/002/003 stay false."
checkpoint: NO_GO
closes_rt001: false
closes_rt002: false
closes_rt003: false
customer_files_expected: false
nda_corpus_in_git: false
plan_b_decision: re-scope
---

# КТ#3 без файлов Самолёта в git

Файлов заказчика **в git нет и не ожидается**. Календарная развилка программы **2026-09-15** не отменяется и не ждётся. Локальный диск владельца не входит в этот пакет и не закрывает RT-001.

- Checkpoint: **NO_GO**
- Стадия МИК: **доработка**
- Валидация эффективности: **не начата**
- nda_corpus_in_git: **false**
- closes_rt001: **false**
- closes_rt002: **false** (не произносить CLOSED без split a/b)
- closes_rt003: **false**
- Показ: `python -m aerobim.tools.run_demo_ifc_acceptance_gate`
- Пакет без заказчика: `python -m aerobim.tools.run_kt3_without_customer`
- Карточка речи: `docs/demo/KT3_JURY_FAQ_2026_08_25.md`
- Сценарий оператора: `docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md`

Customer files are not expected in git. KT#3 is the live fixture gate plus public/synthetic proxies. Not product accuracy. Not customer SLA. Not MEP delivered. Not CDE-ready. Checkpoint NO_GO. closes_rt001/002/003 stay false.

| Роль | Файл | Есть |
|---|---|---|
| demo_manifest | `samples/demo/vertical-slice-2026-08-11/manifest.json` | yes |
| synthetic_label_freeze | `samples/benchmarks/rt001-preregistration-synthetic-freeze-2026-08-14.json` | yes |
| jurisdiction_ids_pointer | `samples/ids/moexp/jurisdiction-profile-pointer.json` | yes |
| corpus_ssot | `docs/demo/KT2_CORPUS_SSOT_2026_08.md` | yes |
| tz_proxy_rehearsal | `docs/evidence/tz-proxy-rehearsal-2026-08.md` | yes |
| planted_federated_clash | `docs/evidence/federated-clash-planted-2026-08.md` | yes |
| intake_gate | `audit/evidence/customer-intake-gate.json` | yes |
| tz_v2 | `docs/tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md` | yes |
| moscow_agr_ruler | `samples/norm-packs/moscow_agr_2026/pack.json` | yes |
| kt3_jury_card | `docs/demo/KT3_JURY_FAQ_2026_08_25.md` | yes |
| kt3_operator_runbook | `docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md` | yes |
