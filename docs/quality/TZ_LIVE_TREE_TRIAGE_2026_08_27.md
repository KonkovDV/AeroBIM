<!-- claims-lint: allow-file reason="Live-tree Red Team triage; TZ 90%/SLA/MEP as blocked inferences; NO_GO" -->
---
title: "Live-tree Red Team triage — 2026-08-27"
date: "2026-08-27"
last_updated: "2026-08-28"
status: active
version: "1.7.0"
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

PR-diff к `main` на первом проходе 27.08 был пустой. Этот файл — полный триаж живого дерева плюс проходы КТ#3 / OOS / локация замечания / канал 25.08 / таблица LIRA / стриминг IFC / HTTP `.lir` / JSON sidecar индекса / чек-листы типовых замечаний и счётчики страницы MVP (28.08) / адрес СОД заказчика (28.08). Не закрытие RT.

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
| RT-OOS-MANIFEST | `samples/oos` на диске, но нет в `DATASET_MANIFEST` | `test_samples_manifest_gate` |
| RT-REMARK-LOC | Этаж/ось из OCR или LLM | `IfcSpatialIndex` + шаблон «нет в индексе» |
| RT-PACKS-SLA | «5–10 комплектов/день» как замер SLA | `publishable_sla=false` в порогах |
| RT-NODATA-SPEECH | «Нет данных» после канала 25.08 | `speech_forbid_no_customer_data` |
| RT-IFC-RAISE | Default analyze = 1.5 ГБ | 256 МиБ analyze; ingest отдельно |
| RT-AXIS-NEAR | Ближайшее пересечение осей | Только `IfcGridAxis.AxisTag` |
| RT-CLOUD-OIDC | HTTPS = живой OIDC BFF | `auth_bff` 501 |
| RT-002-SPPACK | Unsigned СП 63 = RT-002b | `closes_rt002=false` |
| RT-LIRA-SOLVER | MATCH таблицы = solver | `compare_declared_tables` `solver=not_implemented` |
| RT-PDF-LIRA | PDF LIRA как таблица | `pdf_fragile`; `AEROBIM-LIRA-PDF` |
| RT-IFC-STREAM | Дизайн = живой disk R-tree / cap 1.5 ГБ | `raises_default_cap=false`; 256 МиБ |
| RT-ZIP-SNIFF | Namelist ZIP на sniff-префиксе = 415 вместо zip-bomb 422 | sniff = magic; `inspect_zip_path` затем Autodesk/LIRA |
| RT-LIRA-HTTP | `.lir`/`.spr` как «disallowed extension» без честной причины | `NATIVE_LIRA_CLOSED_REASON`; ZIP-члены после inspect |
| RT-SIDECAR-RTREE | JSON sidecar индекса = live disk R-tree | `dump_only`; `disk_r_tree=designed_not_implemented` |
| RT-TYP-CATALOG | «Каталог типовых ошибок принят», пока `customer_confirmed_patterns=0` и 2 чек-листа приёмки лежат неразобранными | `customer_share_ingested=false`; `acceptance_checklists_local.ingested_into_patterns=0`; detected 2 ≠ ingested |
| RT-PAGE-DRIFT | Строки страницы MVP (11 Autodesk, 1133 скан-PDF, 51 ТЗ) перекрывают пин инвентаря | `PUBLIC_REHEARSAL`: 27 rvt + 21 navis, 1127 pdf; `rehearsal_differs` ловит дрейф |
| RT-CDE-IDENT | Адрес ссылки назвал СОД заказчика → «импорт/интеграция доказаны» | `cde_import=NOT_VERIFIED` до T2-пакета (log+screenshot+hashes); демо-пуш на синтетике ≠ реестр заказчика |

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
