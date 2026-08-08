---
title: "Sprint 3 — week tasks status (IFC metrics, expertise GT, open docs)"
date: 2026-08-08
status: active
claim_boundary: >-
  Meeting brief only. Checkpoint NO_GO. No product accuracy >90%.
  IDS match-rate ≠ customer expertise precision.
  IFC4 p95 restabilized 2026-08-08 (n=20); IDS 0017 documented upstream edge.
---

# Sprint 3 — задачи на следующую неделю (статус исполнения)

Обсуждённые задачи и что уже можно показать на встрече.

| # | Задача | Статус | Короткий ответ |
|---|--------|--------|----------------|
| 1 | IFC-форматы: были ли прогоны + цифры точности/скорости | **Сделано (evidence)** | Да, IFC2X3/IFC4/IFC4X3. p95 стабилизирован (n=20). **Продуктовой точности нет** |
| 2 | Датасеты с заключениями экспертизы vs baseline | **RU GT нет; Mumbai foreign ACC скачан** | ЕГРЗ не даёт пар. Mumbai 333 scrutiny↔concession на диске (CC BY). Нужен пакет «Самолёта» для RT-001 |
| 3 | Расширить открытые датасеты, прогоны, фиксы | **В процессе** | SFC-A68 прогнан; OCR-баг numpy починен; construction-specs labels склонированы (без картинок в repo) |

---

## 1) IFC — цифры для встречи

### Были ли прогоны?

**Да.**

1. Fixture schema-suite: `project-package-ifc{2x3,4,4x3}-schema.json`
2. Внутренний open corpus (buildingSMART IFC4.3 samples + opensourceBIM)
3. IDS engine sample на BSI TestCases

Evidence:

- [`docs/evidence/ifc-release-benchmark-2026-08.md`](../evidence/ifc-release-benchmark-2026-08.md)
- [`docs/evidence/sprint3-week-ifc-metrics-2026-08.md`](../evidence/sprint3-week-ifc-metrics-2026-08.md)
- Internal JSON: `../aerobim-internal-data/reports/sprint3-week-ifc-metrics.json`

### Скорость Analyze (fixture, 20 measured + 2 warmup + suite prime)

| Schema | bytes | entities | **p50 ms** | **p95 ms** | max ms | spike | issues |
|---|---:|---:|---:|---:|---:|---:|---:|
| IFC2X3 | 997 | 12 | **23.9** | **24.6** | 24.7 | 1.04× | 6 |
| IFC4 | 997 | 12 | **23.4** | **24.2** | 25.0 | 1.07× | 4 |
| IFC4X3 | 1005 | 12 | **23.4** | **24.5** | 24.8 | 1.06× | 4 |

Стабилизация 2026-08-08: при n=5 nearest-rank p95 ≡ max (исторический IFC4 spike ≈568 ms). Suite теперь shared container + prime + n=20. Не customer SLA.

Evidence: [`ifc-release-benchmark-2026-08.md`](../evidence/ifc-release-benchmark-2026-08.md).

### Скорость открытия файла (`ifcopenshell.open`)

| Schema | files | размер | max entities | open p50 (median) | worst p95 |
|---|---:|---|---:|---:|---:|
| IFC2X3 | 7 | 1 KB – 7.3 MB | 130997 | **41.3 ms** | 476 ms |
| IFC4 | 2 | ~1 KB | 14 | **0.2 ms** | 0.2 ms |
| IFC4X3 | 9 | 1 KB – 237 KB | 3161 | **0.8 ms** | 12 ms |

### «Точность» — честная формулировка для слайда

| Что можно сказать | Число | Чего нельзя сказать |
|---|---|---|
| IDS engine agreement с BSI pass/fail (sample n=24) | **95.8%** (23/24) | «Точность AeroBIM 95% для заказчика» |
| issue_count на fixture | 4–6 | Product precision / recall |
| Product / expertise accuracy | **не измерена** | Любые % без dual adjudication |

Единственный mismatch sample: BSI `0017` (optional attribute null → expected pass; IfcTester → fail: *attribute value "None" is empty*). Класс: **upstream IDS/IfcTester edge**, не «ломается парсер IFC». Разбор: [`ids-case-0017-optional-null-2026-08.md`](../evidence/ids-case-0017-optional-null-2026-08.md); registry `samples/ids/buildingsmart-testcases/KNOWN_UPSTREAM_EDGES.json`. Не патчить адаптер ради 100%.

---

## 2) Заключения экспертизы — есть ли датасет для baseline?

| Источник | Пары документ↔замечание? | Решение |
|---|---|---|
| ЕГРЗ / ГГЭ | Нет (метаданные ≠ пакеты) | `REQUIRES_PERMISSION` — не скачивать автоматом |
| buildingSMART / IFC-Bench / IDS | Нет (не экспертиза) | open_bench / regression only |
| Mumbai Building Permit (CC BY 4.0) | **Да, scrutiny↔concession** (Индия, AutoDCR) | **На диске** (333 пары); зарубежный ACC-аналог; **не RU экспертиза** |
| Пакет «Самолёта» | Нужен | Единственный путь закрыть RT-001 |

**Вывод для встречи:** открытого корпуса российских заключений экспертизы с разметкой TP/FP **нет**. Сравнивать AeroBIM с «бейзлайном экспертизы РФ» на публичных данных **нельзя честно**. Можно: (a) IDS/IFC open-bench, (b) Mumbai как зарубежный ACC-аналог (**скачан**, exploratory), (c) customer intake.

Запрос данных: [`docs/datasets/customer-data-request-2026-08.md`](../datasets/customer-data-request-2026-08.md).

---

## 3) Расширение открытых документов + прогоны + фиксы

| Набор | Статус | Прогон | Фикс |
|---|---|---|---|
| SFC-A68 (CC BY) | extracted | OCR/hybrid/Analyze+PNG | **ADAPTER_BUG** numpy OCR `boxes or []` → fixed + regression test |
| BlueprintSymVL | on disk | inventory | — |
| PIDQA | text only | inventory | — |
| Construction-document-digitalization | cloned; **labels only**, images via Roboflow | labels inventoried; no PNG in zip | LICENSE unclear / incomplete assets |
| ArchCAD-400K | HF gated | blocked | needs `hf auth login` |
| PID_dataset Zenodo | 6.7 GB | not downloaded | size gate |

---

## Рекомендуемые слайды / talking points

1. **IFC2x3 / 4 / 4x3 открываются и гоняются** — p50 Analyze ~23–26 ms на fixture; крупные IFC2x3 open до ~0.5 s p95.
2. **Точность продукта не заявлена**; IDS sample 95.8% — только engine conformance.
3. **Экспертиза:** без данных «Самолёта» RU baseline blocked; Mumbai foreign ACC **скачан** (не заменяет RT-001).
4. **Уже починили** реальный OCR-баг на SFC-A68.

## Checkpoint

Проектный checkpoint: **NO_GO** (RT-001/002/003).  
Инженерный статус по open-corpus: **PARTIALLY_READY** / CONDITIONAL для внутренней демо.
