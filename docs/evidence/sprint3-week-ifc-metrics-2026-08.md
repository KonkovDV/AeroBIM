# Sprint 3 — IFC metrics for next meeting

Generated: `2026-08-08T14:50:22.725567+00:00`

**Важно:** `accuracy_measured_product=false`. Число findings ≠ точность для заказчика.

## 1) Были ли прогоны IFC?

Да. Fixture schema-suite IFC2X3 / IFC4 / IFC4X3 + внутренний open corpus (probe/open speed).

## 2) Скорость Analyze (fixture packs, 5 measured + 1 warmup)

| Schema | bytes | entities | p50 ms | p95 ms | avg ms | issues (last) | peak mem B |
|---|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 997 | 12 | 23.882 | 24.617 | 23.86 | 6 | 539513 |
| IFC4 | 997 | 12 | 23.379 | 24.203 | 23.385 | 4 | 669617 |
| IFC4X3 | 1005 | 12 | 23.384 | 24.535 | 23.415 | 4 | 475545 |

## 3) Скорость открытия IFC (Ifcopenshell.open), расширенный корпус

| Schema | files | bytes min–max | entities max | open p50 (median files) ms | worst open p95 ms |
|---|---:|---|---:|---:|---:|
| IFC2X3 | 7 | 997–7288853 | 130997 | 42.829 | 909.724 |
| IFC4 | 2 | 997–1142 | 14 | 0.172 | 0.228 |
| IFC4X3 | 9 | 1005–236853 | 3161 | 0.72 | 12.04 |

## 4) «Точность» — что можно и чего нельзя сказать

| Метрика | Значение | Смысл |
|---|---|---|
| IDS engine match-rate (sample n=24) | **0.9583** (23/24) | Совпадение pass/fail с именем BSI TestCase через IfcTester — **не** точность экспертизы |
| Product / customer precision | **не измерена** | Нет adjudicated document↔remark GT |
| issue_count на fixture | см. таблицу выше | Не accuracy |

## 5) Ограничения для слайда

- Реальные пакеты «Самолёта» не прогонялись.
- Часть open IFC — LICENSE_UNCLEAR → только внутренняя встреча.
- IFC4 p95 в suite может быть выше из‑за cold start / MEP probe noise.

JSON: internal reports/sprint3-week-ifc-metrics.json (outside this Git tree).
