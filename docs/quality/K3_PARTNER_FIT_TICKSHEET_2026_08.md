<!-- claims-lint: allow-file reason="K3 partner-fit ticksheet; fit is not B2 metrics; NO_GO" -->
---
title: "K3 partner-fit ticksheet — fit is not validation metrics"
date: "2026-08-29"
last_updated: "2026-08-29"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Fit to the public Partner mandate. Not Partner validation metrics (B2).
  Not TZ >90%. Not a predicted K3 score. Checkpoint GO; customer_go false.
---

# К3: посадка на запрос партнёра, не метрики Б2

К3 системы A — **соответствие задаче партнёра**. Б2 системы B — протоколы **и**
подтверждённые метрики. Путать их — отдавать 15 баллов К3 как будто это Б2.

Публичный запрос (карточка [i.moscow/techlab/samolet](https://i.moscow/techlab/samolet);
приложение 4 **№6**): ассистент проверки ПД/РД, не замена эксперта.

| Запрос карточки | Что в git | Честная речь |
|---|---|---|
| 2D + BIM + ТЗ + расчёты | PDF/OCR, IFC/IDS, тексты, сверка чисел | Native RVT/NWD/DWG закрыты явно |
| Сверка между собой и с правилами | IDS + кросс-док + шаблонные нормы | Профиль Самолёта не подписан |
| Коллизии, размеры, площади, логика, пропуски | IfcClash-фикстура; IDS exists; площади без QTO — Missing | Не «коллизии >90% сданы» |
| Подсветка и приоритет замечаний | overlay; `compute_issue_priority` | Не CV-грамотность инженера |
| Отчёты / BCF | HTML + JSON + BCF ZIP | Импорт в СОД не VERIFIED |
| ≤30 мин на согласованном комплекте | Протокол + tool; fixture не representative | Цель, не SLA партнёра |
| Эксперт в контуре | ADR-001; HITL | Не замена ГИП |

Честный отказ читать RVT/NWD — **посадка** на openBIM-запрос, не дыра К3.

Протокол измерения (interim TP/(TP+FP) ≥ 0,60, не 90 %) уже написан:
[`PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md`](../partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md).
Капитан **отправляет** партнёру обложку «готово подписать». Подпись двигает
К3/Б1/Б2; git её не ставит.

`k3_equals_validation_metrics() == False`.
`partner_kpis_agreed_in_writing() == False`.
