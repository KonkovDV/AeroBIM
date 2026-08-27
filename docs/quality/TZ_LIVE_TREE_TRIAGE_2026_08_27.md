<!-- claims-lint: allow-file reason="Live-tree Red Team triage; TZ 90%/SLA/MEP as blocked inferences; NO_GO" -->
---
title: "Live-tree Red Team triage — 2026-08-27"
date: "2026-08-27"
last_updated: "2026-08-27"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  KILL/HOLD/ACCEPT over the live tree after TZ v1 pin and the KT#3 pack.
  Not product accuracy. Not customer SLA. Not MEP delivered. Checkpoint NO_GO.
---

# Live-tree triage (27.08.2026)

PR-diff к `main` на первом проходе 27.08 был пустой. Этот файл — полный триаж живого дерева плюс второй проход (КТ#3 / трекер / OOS / инвентарь). Не закрытие RT.

Машина: `python -c "from aerobim.domain.live_tree_triage import triage_snapshot"`.

Checkpoint **`NO_GO`**. `detected_count: 0`.

## Этот проход (KILL, затор в коде)

| ID | Атака | Тормоз |
|---|---|---|
| RT-V1-01 | Цифра точности из ТЗ v1 как замер AeroBIM | `mik_act_may_cite_tz_v1_accuracy_as_measured()==False` · `SAM-10` |
| RT-V1-02 | Четыре бумаги Самолёта — один документ | `PAPER_OBJECTS` |
| RT-V1-03 | Бинарь PDF в git / sha256 брифа = NDA `pack_hash` | `binary_in_git=false`; в снимке нет `pack_hash` |
| RT-V1-04 | Акт МИК цитирует v1 вместо interim 0.60 | горизонт `interim_tp_fp_ge_0_60` |
| RT-INJ-NEST | `inject_defects` output внутри source → `rmtree` пакета | деревья не равны и не вложены |
| RT-INJ-NDA | source = `samples/customer` или `files/` | posix-маркеры |
| RT-KIT-01 | Кухонные топонимы / фамилия трекера снова в публичном дереве | `lint_claims` kitchen tokens |
| RT-KT3-01 | `passed=false` на фикстуре = Checkpoint GO | `require_kt3_jury_gate` |
| RT-KT3-02 | Первая строка жюри = `REQ-AREA` без GUID | `select_jury_finding` |
| RT-KT3-03 | Fixture MEP `OK` = MEP delivered | gate rejects `OK`/`DELIVERED` |
| RT-TRK-05 | KPI 3–5 демо как факт git | `scheduled_demos_in_git=false` |
| RT-TRK-GO | `agent_done_count` = шесть задач закрыты у заказчика | `owner_blocked_count≥4`; NO_GO |
| RT-OOS-01 | Unsigned OOS = skip / signed OOS = RT CLOSED | `evaluate_oos` |
| RT-INV-01 | Имена/хэши `files/` в `docs/` | `require_local_only_output` |

## HOLD (не чиним в этом коммите)

| ID | Атака | Почему HOLD |
|---|---|---|
| RT-SEAM-HOLD | Карта семи задач = Meets / RT CLOSED | §5 TZ seam уже KILL; критерий Uncertain |
| RT-FULL-D01 | `/v1/validate/ifc` зелёный в production через development | DI берёт `settings.signoff_profile`; soft `passed` не authoritative |
| RT-AGR-002 | `moscow_agr_2026` `status=approved` = профиль Самолёта | RT-002a ≠ RT-002b; профиль не customer-hard |
| RT-INV-HOLD | Счётчики 2383/15/1 = `pack_hash` / RT-001 CLOSED | `coverage_map_only`; имён нет; intake blocked |

## ACCEPT (тормоз уже стоит)

| ID | Атака | Тормоз |
|---|---|---|
| RT-ADR-001 | LLM/VLM пишет `summary.passed` | DeterminismGate: advisory → INFO |
| RT-CAP-IFC | Поднять cap IFC из-за одного АР | default 256 MiB |

Июльский полный аудит (`RT-FULL-*` SSRF/OIDC/locks) не переоткрываем как новые CRITICAL. Не поднимаем IFC cap. Не парсим RVT/NWD/LIRA.

Связанные пины: [`TZ_V1_CONTEST_BRIEF_PIN_2026_08.md`](../tz/TZ_V1_CONTEST_BRIEF_PIN_2026_08.md) · [`TZ_SEAM_COVERAGE_MAP_2026_08.md`](TZ_SEAM_COVERAGE_MAP_2026_08.md) §5 · [`OWNER_AI_PLAN_EXECUTION_2026_08_27.md`](OWNER_AI_PLAN_EXECUTION_2026_08_27.md).
