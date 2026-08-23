<!-- claims-lint: allow-file reason="KT#3 re-scope without customer files; RT blockers stay OPEN; forbidden phrases as non-claims" -->
---
title: "KT#3 without Samolet files — owner re-scope"
date: "2026-08-23"
claim_level: fixture_and_proxy_only
claim_boundary: "Owner re-scope 2026-08-23: customer files are not expected. KT#3 is the live fixture gate plus public/synthetic proxies. Not product accuracy. Not customer SLA. Not MEP delivered. Not CDE-ready. Checkpoint NO_GO. closes_rt001/002/003 stay false."
checkpoint: NO_GO
closes_rt001: false
closes_rt002: false
closes_rt003: false
customer_files_expected: false
plan_b_decision: re-scope
---

# КТ#3 без файлов Самолёта

Файлов заказчика не будет. Решение владельца **re-scope** (2026-08-23). Календарная развилка программы **2026-09-15** не отменяется и не ждётся.

- Checkpoint: **NO_GO**
- Стадия МИК: **доработка**
- Валидация эффективности: **не начата**
- closes_rt001: **false**
- closes_rt002: **false**
- closes_rt003: **false**
- Показ: `python -m aerobim.tools.run_demo_ifc_acceptance_gate`
- Пакет без заказчика: `python -m aerobim.tools.run_kt3_without_customer`

Owner re-scope 2026-08-23: customer files are not expected. KT#3 is the live fixture gate plus public/synthetic proxies. Not product accuracy. Not customer SLA. Not MEP delivered. Not CDE-ready. Checkpoint NO_GO. closes_rt001/002/003 stay false.

| Роль | Файл | Есть |
|---|---|---|
| demo_manifest | `samples/demo/vertical-slice-2026-08-11/manifest.json` | yes |
| synthetic_label_freeze | `samples/benchmarks/rt001-preregistration-synthetic-freeze-2026-08-14.json` | yes |
| jurisdiction_ids_pointer | `samples/ids/moexp/jurisdiction-profile-pointer.json` | yes |
| corpus_ssot | `docs/demo/KT2_CORPUS_SSOT_2026_08.md` | yes |
| tz_proxy_rehearsal | `docs/evidence/tz-proxy-rehearsal-2026-08.md` | yes |
| planted_federated_clash | `docs/evidence/federated-clash-planted-2026-08.md` | yes |
| intake_gate | `audit/evidence/customer-intake-gate.json` | yes |
| rt_without_samolet | `docs/datasets/RT001_002_003_WITHOUT_SAMOLET_2026_08_14.md` | yes |
