# Sprint 3 — IFC metrics for next meeting

Generated: `2026-08-08T07:37:03+00:00` (schema-suite restabilized)

**Важно:** `accuracy_measured_product=false`. Число findings ≠ точность для заказчика.

## 1) Были ли прогоны IFC?

Да. Fixture schema-suite IFC2X3 / IFC4 / IFC4X3 + внутренний open corpus (probe/open speed).

## 2) Скорость Analyze (fixture packs, 20 measured + 2 warmup + suite prime)

Стабилизация (2026-08-08): shared DI container, process prime, `gc.collect` после warmup,
default n=20 — иначе при n=5 nearest-rank p95 ≡ max (исторический IFC4 spike ≈568 ms на одной итерации).

| Schema | bytes | entities | p50 ms | p95 ms | max ms | spike max/p50 | issues (last) |
|---|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 997 | 12 | 23.882 | 24.617 | 24.728 | 1.035 | 6 |
| IFC4 | 997 | 12 | 23.379 | 24.203 | 24.976 | 1.068 | 4 |
| IFC4X3 | 1005 | 12 | 23.384 | 24.535 | 24.823 | 1.062 | 4 |

## 3) Скорость открытия IFC (Ifcopenshell.open), расширенный корпус

| Schema | files | bytes min–max | entities max | open p50 (median files) ms | worst open p95 ms |
|---|---:|---|---:|---:|---:|
| IFC2X3 | 7 | 997–7288853 | 130997 | 41.304 | 476.33 |
| IFC4 | 2 | 997–1142 | 14 | 0.176 | 0.222 |
| IFC4X3 | 9 | 1005–236853 | 3161 | 0.759 | 12.043 |

## 4) «Точность» — что можно и чего нельзя сказать

| Метрика | Значение | Смысл |
|---|---|---|
| IDS engine match-rate (sample n=24) | **0.9583** (23/24) | Совпадение pass/fail с именем BSI TestCase через IfcTester — **не** точность экспертизы |
| Product / customer precision | **не измерена** | Нет adjudicated document↔remark GT |
| issue_count на fixture | см. таблицу выше | Не accuracy |

Mismatch: BSI `0017` optional null Name — filename expects pass; IfcTester: *attribute value "None" is empty*. См. [`ids-case-0017-optional-null-2026-08.md`](ids-case-0017-optional-null-2026-08.md). Не патчить адаптер ради 100%.

## 5) Ограничения для слайда

- Реальные пакеты «Самолёта» не прогонялись.
- Часть open IFC — LICENSE_UNCLEAR → только внутренняя встреча.
- IFC4 p95 стабилизирован методологией (n=20 + warmup/prime); не customer SLA.

JSON: `audit/evidence/ifc-release-benchmark-2026-08.json`  
Internal: `C:\plans\aerobim-internal-data\reports\sprint3-week-ifc-metrics.json` / `ifc-schema-suite-meeting-2026-08.json`
