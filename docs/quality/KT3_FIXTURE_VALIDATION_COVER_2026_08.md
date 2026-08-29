<!-- claims-lint: allow-file reason="Fixture validation cover for B2 floor; not partner metrics; fixture SLA not representative; NO_GO" -->
---
title: "KT#3 fixture validation cover"
date: "2026-08-29"
last_updated: "2026-08-29"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Cover sheet for engine regression and the live jury CLI. Not partner
  acceptance. Not customer SLA. Fixture p95 on kilobyte files is not the
  30-minute TZ goal. Checkpoint NO_GO.
---

# Обложка валидации фикстуры (нижняя полка Б2)

Это **не** протокол приёмочных испытаний партнёра и **не** подтверждённые
метрики эффективности. Б2 в Приложении 3 требует оба. Здесь только то, что
уже можно показать из git.

## Что прогнано

| Слой | Где смотреть | Граница |
|---|---|---|
| Движок (pytest) | [`../evidence/runtime-baseline-latest.json`](../evidence/runtime-baseline-latest.json) | `attested_by=ci` only; local pytest не публикуем |
| Живой CLI жюри | `python -m aerobim.tools.run_kt3_jury` | `passed=false`; GUID-находка |
| Показ без файлов заказчика | `python -m aerobim.tools.run_kt3_without_customer` | Канал ≠ хеш-пакет |

Цифры `tests_passed` / `tests_collected` брать **из pin-файла**, не из памяти
и не с чужой машины.

## Что нельзя называть метрикой партнёра

Файл [`../evidence/samolet-sla-fixture-p95-2026-08-04.json`](../evidence/samolet-sla-fixture-p95-2026-08-04.json):
`package_scale.is_representative=false`, `total_input_bytes=4784`. p95 на этом
пакете **не** «укладываемся в 30 минут на комплект Самолёта».

Open-bench (AECV и прочие) остаётся `open_bench_only`.

## Чего нет

- Dual-rater κ/α на комплекте партнёра.
- Precision/recall по классам дефектов на их ПД/РД.
- Согласованный KPI (в том числе «>90%») в письме партнёра.

Методика, когда корпус появится: [`PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md`](../partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md).
Checkpoint **`NO_GO`**.
