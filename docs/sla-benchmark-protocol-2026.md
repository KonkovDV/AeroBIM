<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "SLA benchmark protocol 2026 (P-014)"
status: active
version: "1.0.0"
date: "2026-07-31"
claim_boundary: "Fixture-числа непереносимы; customer SLA только на согласованном паке (schema гейт)."
---

# SLA benchmark protocol

Инструмент: `python -m aerobim.tools.measure_package_sla` (schema 1.3.0).

## Что фиксирует каждый прогон (VERIFIED-поля артефакта)

package_sha256 + file_inventory (включая вложенные `request`-входы);
`package_scale` (input_files, total_input_bytes, ifc_bytes, largest_input_bytes,
drawing_count) + `representative_scale` (пороги 1 MiB / 3 файла — явно в
артефакте); machine fingerprint (OS/CPU/RAM/Python); cold run всегда, warm —
`--warmup-iterations`; stage budgets (5+18+2+5 мин) и их консистентность;
corpus_kind + claim_level; команда воспроизведения.

## Правила заявлений

- `fixture_only`: разрешён только как «fixture wall-clock»; НЕ «≤30 мин на
  комплект». `representative_scale=false` обязан показываться рядом с числом.
- `customer_measurable`: refuse-without-evidence — требует corpus_kind=customer,
  pack hash, полный machine fingerprint и `--mandatory-capabilities-complete`.
- Skipped/failed capability в прогоне ⇒ это НЕ полноценный SLA (полнота
  обязательных capability — часть customer-гейта).

## Протокол до контрактного заявления (нужен customer-пак)

1. Согласовать состав эталонного пакета письменно (см. вопрос 1 опросника).
2. Прогнать cold + warm на согласованном железе: core / +raster / +clash.
3. Опубликовать артефакты с манифестом и stage timings.
4. Только после этого допустима формулировка «≤30 минут на согласованном пакете».

## Не реализовано (честно)

p50/p95/p99 по многим итерациям, профили памяти/CPU, parallel-run матрица,
GPU-вариант — P2; текущий инструмент однопоточный wall-clock.
