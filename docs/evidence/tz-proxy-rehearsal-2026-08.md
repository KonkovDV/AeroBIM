<!-- claims-lint: allow-file reason="TZ proxy rehearsal; RT blockers stay OPEN; forbidden phrases as non-claims" -->
---
title: "TZ proxy rehearsal without Samolet files — construct validity"
date: "2026-08-14"
claim_level: tz_proxy_rehearsal
claim_boundary: >
  Public and synthetic proxies for Task 07. Messick content/substantive
  evidence is not criterion validity on a customer corpus. Checkpoint NO_GO.
closes_rt001: false
closes_rt002: false
closes_rt003: false
---

# Академический максимум ТЗ без файлов «Самолёта»

Интернет **не** отдаёт эталон экспертизы, подписанный EIR заказчика и BCF-истину координатора. Это не пробел поиска: ПП РФ 878 п. 23, ISO 19650 (EIR ≠ BEP) и лицензии клиентских BCF так устроены.

Ниже — что **можно** закрыть по ТЗ Задачи 07 на открытых и синтетических данных, и какая это валидность в смысле Messick (1995): шесть аспектов единой construct validity. L1/L2 ≠ L3: [`OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](../quality/OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md).

Команда:

```text
cd backend
python -m aerobim.tools.run_tz_proxy_rehearsal
```

Опционально (медленно, всё равно `mep_system_clash=NOT_VERIFIED`): `--include-open-federated`.

Checkpoint остаётся **NO_GO**.

## Рамка валидности (Messick 1995)

| Аспект | Что даёт прокси без «Самолёта» | Чего не даёт |
|---|---|---|
| **Content** | Классы типовых замечаний (Эксп. Б); 389 specs IDS МОГЭ; посаженные пересечения тел | Представительность комплекта ПД/РД жилого девелопера РФ |
| **Substantive** | IfcTester / IfcClash / inventory реально исполняются; `skipped`/`failed` явны | Процесс эксперта ГАУ на томе заказчика |
| **Structural** | Типизированные скоры: `coverage_map_only`, `official_ids_engine_coverage`, capability | Один F1 «по ТЗ >90%» |
| **Generalizability** | Регресс движка на fixture / open IFC | Перенос на корпус «Самолёта» (AECV-Bench §6 прямо ограничивает свой корпус) |
| **External (criterion)** | — | Dual-expert TP/FP, κ/α, held-out FN, signed `pack_hash` |
| **Consequential** | Claims Lock запрещает GO на L1/L2 | Публикация L1 как точности продукта была бы невалидным *использованием* скора |

Источник рамки: Messick, S. (1995). *Validity of psychological assessment*. [ERIC ED380496](https://files.eric.ed.gov/fulltext/ED380496.pdf). IDS как машиночитаемые information requirements: Tomczak et al., *Buildings* 15(3):378 (2025).

## Соответствие строкам ТЗ v2.0

| ID | Требование | Без «Самолёта» | Статус (не `done` на блокерах) |
|---|---|---|---|
| **ТР-8** | IDS / properties IFC | Fixture + IDS МОГЭ + BSI TestCases | done |
| **ТР-11** | Норм-пак, утверждённый заказчиком | IDS МОГЭ + AGR class-1 (включая sidecar TEP XML presence). Не EIR «Самолёта» | **partial** (RT-002) |
| **ТР-14** | Геометрические коллизии (IfcClash) | `detect_between` + посаженная пара пересекающихся стен (`clash-federated-box-{a,b}.ifc`) | **partial** |
| **ТР-15** | MEP system-aware | Федеративный инвентарь + опциональный IfcClash Duplex. Нет signed clearance matrix | **not_verified** (RT-003) |
| **ТР-6** | Нативный DWG | DXF / PDF/A; LibreDWG не линкуем | `TZ_MANDATORY_UNSUPPORTED` |
| **§9 точность** | Dual adjudication | Карта покрытия Эксп. Б (КР 4/24, АР 2/12, ВК 4/16) | **blocked** (RT-001) |

ISO 19650: IDS МОГЭ ближе к **information requirements органа**, не к BEP назначенной стороны и не к EIR «Самолёта». Публичный PDF АГР Москвы (ДГП-Р-1/26) — норма обмена, не `customer_approved` pack.

## Почему три блокера всё ещё OPEN

1. **RT-001.** ЕГРЗ открывает метаданные, не пары «том ↔ замечание». Типовые перечни — таксономия (content), не критерий. Dual κ/α без чужого комплекта не считается.
2. **RT-002.** 24 IDS / 389 specs МОГЭ исполняются (`closes_rt002_customer_profile: false`). Это не `approval` + `pack_hash` заказчика.
3. **RT-003.** IfcClash — движок intersection/collision/clearance ([документация IfcOpenShell](https://docs.ifcopenshell.org/ifcclash.html)). Публичные федеративные IFC не содержат BCF-истины. G55 Solibri — чужие клиентские данные, в git не копируем. AABB overlap ≠ geometric clash.

## Что произнести на КТ#2

Движок гоняем на официальном IDS МОГЭ, на карте типовых замечаний трёх органов и на IfcClash (посаженный + опционально открытый Duplex). Точность на комплекте заказчика не измерена. Профиль приёмки «Самолёта» не подписан. System-aware MEP не верифицирован. Нативный DWG в ТЗ остаётся fail-closed.

Человеческие ходы, которые меняют поле: приложения ТЗ, NDA/разметка, слот демо, видео 19.08. Их нет в этом файле.
