<!-- claims-lint: allow-file reason="KT#3 operator runbook; TZ 90%/SLA as non-goals; NO_GO; jury-laptop git fixtures only" -->
---
title: "КТ#3 — сценарий оператора (живой CLI из git)"
date: "2026-08-25"
last_updated: "2026-09-01"
checkpoint: GO
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Operator script. Jury-laptop track uses only git fixtures.
  Not product accuracy. Not customer SLA. Checkpoint GO; customer_go false.
---

# КТ#3 — что нажимать

Карточка речи: [`KT3_JURY_FAQ_2026_08_25.md`](KT3_JURY_FAQ_2026_08_25.md).  
ТЗ v2: [`../tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`](../tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md).

На защите жюри — только этот трек: живой CLI из git. Файлов заказчика в репозитории нет.

Предпочтительная одна команда:

```text
cd backend
pip install -e ".[dev,raster]"
python -m aerobim.tools.run_kt3_jury
```

Эквивалент двумя командами (если жюри просит «покажите gate отдельно»):

```text
python -m aerobim.tools.run_demo_ifc_acceptance_gate
python -m aerobim.tools.run_kt3_without_customer
```

Успех:

| Артефакт | Ожидание |
|---|---|
| `artifacts/ifc-acceptance-gate-demo/acceptance-gate.json` | есть; fixture gate |
| `report.html` / `report.json` / `findings.bcfzip` | есть |
| `summary.passed` / `passed` | **false** на учебной фикстуре — это сценарий, не поломка |
| `artifacts/kt3-without-customer/latest.json` | `checkpoint=GO`, все `closes_rt00*=false`, `customer_files_expected=false`, `nda_corpus_in_git=false` |
| `artifacts/kt3-jury/latest.json` | `passed=false`, GUID-находка, tracker item_count=6 |

В кадре показать **IDS-находку с GUID** (в прогоне 25.08: правило `IDS-Wall Fire Rating Multi`, GUID `1XYVUKGoDDbREfVxRKsHkl`, expected REI60 / observed REI30). Не первую строку `REQ-AREA-*`: там `ifc_guid=null` — жюри не увидит объект.

Stderr `MEP system graph probe failed` / `MEP-CLASH-001` на учебной модели — fail-closed, процесс всё равно заканчивается кодом 0. Это не падение демо. Capability `mep_system_clash=NOT_VERIFIED`.

**Не** ставить `AEROBIM_SIGNOFF_PROFILE=samolet_pilot` на чужом ноутбуке: clash/MEP форсируются и демо покраснеет не про шов. Если нужен городской контур:

```text
set AEROBIM_ENV=development
set AEROBIM_SIGNOFF_PROFILE=moscow_agr_2026
```

Clash/MEP на этом профиле — честный SKIPPED, не подделка (RT-003 OPEN).

P1, только если осталось время: `python -m aerobim.tools.run_demo_vertical_slice` (оверлей PDF). Не ядро вердикта.

Frontend (`npm ci` / `npm run dev`) — не показ КТ#3, если время жюри <12 мин. Трек ИТ-ментора: кнопка «Загрузить демонстрационный комплект» (`POST /v1/demo/seed-fixture`, только development). Не говорить «рабочее место сдано». Не сидировать в грязный `var/reports` как «объём канала».

## Две ноги (не склеивать)

| Нога | Что | Pass-gate |
|---|---|---|
| Регуляторная | `moscow_agr_2026` × городские IDS | Линейка измерения. Не self-check АГР (бесплатный городской отчёт с 29.06) |
| Клиновая | Шов на учебном пакете | Шов чистый *до* `inject_defects`. Не filename/IDS АГР |

`python -m aerobim.tools.inject_defects` — для G2 recall **после** того, как собран шовно-чистый мини-ПД. На защите КТ#3 **не** сажать дефекты в городские эталоны АГР.

## Перед показом

1. Клон `main` собирается: две команды выше на чистой машине хотя бы один раз.
2. Карточка речи распечатана или второй монитор.
3. Стоп-лист прочитан вслух один раз.

## После показа

Не обещать GO. Не обещать native RVT, MEP delivered, точность >90% или customer SLA.
