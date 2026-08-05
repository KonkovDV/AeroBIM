---
title: "PNST 909 — 22-scenario second coverage axis"
date: 2026-08-05
status: PLANNED
claim_boundary: >-
  Coverage map vs external standard scenarios + IDS. Not product accuracy.
  Requires Renga pack pin. Checkpoint NO_GO.
---

# Вторая ось покрытия: 22 сценария ПНСТ 909-2024

**Зачем:** Exp B даёт карту vs типовые замечания экспертизы (AUTHOR_CLAIM). ПНСТ 909 даёт **независимый** машиночитаемый эталон требований (IDS) на том же классе «полнота/свойства/состав».

| Ось | Эталон | Метрика | Статус |
|---|---|---|---|
| A — Exp B | Перечни госэкспертиз (Киров/Мордовия/→СПб/Амур) | доля «обнаруживается» | **RUN** (КР ≈16,7%) |
| B — ПНСТ 909 | 22 сценария + IDS Renga | доля сценариев с runtime proof | **PLANNED** (нужен pack) |

**Не смешивать** проценты осей в одной цифре без таблицы.

## DoD

1. Пин комплекта Renga в `.local/renga-pnst909/`.  
2. Таблица 22×{сценарий, IDS path, AeroBIM capability, status: fires/skipped/out_of_scope}.  
3. Evidence JSON + строка в baseline PDF: «вторая ось — стандарт, не эксперт».  
4. Claim: coverage_map only.

## Связь с Task 3

Task 3 на synthetic закрыл класс полноты (4/6 КР строк). Прогон Renga+IDS — **тот же класс** на реальном объекте + внешний IDS-эталон.
