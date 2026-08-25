<!-- claims-lint: allow-file reason="KT#3 operator runbook; TZ 90%/SLA as non-goals; NO_GO; local NDA not git" -->
---
title: "КТ#3 — сценарий оператора (чужой ноутбук + опция NDA)"
date: "2026-08-25"
last_updated: "2026-08-25"
checkpoint: NO_GO
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Operator script. Jury-laptop track uses only git fixtures. Owner-laptop
  NDA track is coverage_map_only. Not product accuracy. Not customer SLA.
---

# КТ#3 — что нажимать

Карточка речи: [`KT3_JURY_FAQ_2026_08_25.md`](KT3_JURY_FAQ_2026_08_25.md).  
Re-scope: [`../partners/_2026_08_23.md`](../partners/_2026_08_23.md).  
ТЗ v2: [`../tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`](../tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md).

Два трека. **На защите жюри по умолчанию — трек A.** Трек B только если это машина владельца и жюри явно просит «ваш комплект».

## Трек A — чужой ноутбук (обязательный)

Offline. Сеть не нужна после `pip install`. Профиль: development + учебный пакет.

```text
cd backend
pip install -e ".[dev,raster]"
python -m aerobim.tools.run_demo_ifc_acceptance_gate
python -m aerobim.tools.run_kt3_without_customer
```

Успех трека A:

| Артефакт | Ожидание |
|---|---|
| `artifacts/ifc-acceptance-gate-demo/acceptance-gate.json` | есть; fixture gate |
| `report.html` / `report.json` / `findings.bcfzip` | есть |
| `summary.passed` / `passed` | **false** на учебной фикстуре — это сценарий, не поломка |
| `artifacts/kt3-without-customer/latest.json` | `checkpoint=NO_GO`, все `closes_rt00*=false`, `customer_files_expected=false`, `nda_corpus_in_git=false` |

В кадре показать **IDS-находку с GUID** (в прогоне 25.08: правило `IDS-Wall Fire Rating Multi`, GUID `1XYVUKGoDDbREfVxRKsHkl`, expected REI60 / observed REI30). Не первую строку `REQ-AREA-*`: там `ifc_guid=null` — жюри не увидит объект.

Stderr `MEP system graph probe failed` / `MEP-CLASH-001` на учебной модели — fail-closed, процесс всё равно заканчивается кодом 0. Это не падение демо. Capability `mep_system_clash=NOT_VERIFIED`.

**Не** ставить `AEROBIM_SIGNOFF_PROFILE=samolet_pilot` на чужом ноутбуке: clash/MEP форсируются и демо покраснеет не про шов. Если нужен городской контур:

```text
set AEROBIM_ENV=development
set AEROBIM_SIGNOFF_PROFILE=moscow_agr_2026
```

Clash/MEP на этом профиле — честный SKIPPED, не подделка (RT-003 OPEN).

P1, только если осталось время: `python -m aerobim.tools.run_demo_vertical_slice` (оверлей PDF). Не ядро вердикта.

Frontend (`npm ci` / `npm run dev`) — не показ КТ#3, если время жюри <12 мин.

## Трек B — машина владельца с `files/Техлаб` (опционально)

Gitignore. Не копировать в `samples/customer/`. Не коммитить выход.

Честный объём: **один** IFC дома 5, КР секций 1–3 (~6 МиБ), claim_level **`coverage_map_only`**.

Репетиция 25.08 на машине владельца (файл **не** в git): IFC2X3; колонны 676, балки 240, плиты 152, стены `IfcWallStandardCase` 588; `IfcReinforcingBar=0`; `IfcFlowSegment=0`. Обезличенная таблица в git: [`../evidence/-kr13-coverage-map-2026-08.md`](../evidence/-kr13-coverage-map-2026-08.md). Это карта того, *что в файле есть*, не точность продукта и не RT-001.

Не делать на защите:

- [redacted-site] АР ~267 МиБ (выше дефолтного analyze 256 MiB).
- Native `.rvt` / `.nwd` (415).
- Federated MEP (файлов нет).
- «Вот точность на Самолёте».

Если прогон не готов заранее — **не импровизировать**. Вернуться к треку A.

## Две ноги (не склеивать)

| Нога | Что | Pass-gate |
|---|---|---|
| Регуляторная | `moscow_agr_2026` × городские IDS | Линейка измерения. Не self-check АГР (бесплатный городской отчёт с 29.06) |
| Клиновая | Шов на учебном пакете / будущем injected pack | Шов чистый *до* `inject_defects`. Не filename/IDS АГР |

`python -m aerobim.tools.inject_defects` — для G2 recall **после** того, как владелец соберёт шовно-чистый мини-ПД. На защите КТ#3 **не** сажать дефекты в NDA-корпус и не в городские эталоны АГР.

## Перед выходом из дома (владелец, не агент)

1. Клон `main` собирается: две команды трека A на чистой машине хотя бы один раз.  
2. ИП / письма — календарь G1, не git.  
3. USB с репо **без** `files/Техлаб`, если ноутбук жюри. NDA не тащить в зал без нужды.  
4. Карточка речи распечатана или второй монитор.  
5. Стоп-лист прочитан вслух один раз.

## После показа

Не обещать GO. Зафиксировать ask: два разметчика; IFC ОВ/ВК/ЭОМ и арматура или out-of-scope; не native RVT в контуре проверки.
