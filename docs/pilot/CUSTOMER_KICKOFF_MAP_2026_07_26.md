---
title: "Kickoff-карта пилота: входы заказчика ↔ intake gates ↔ этапность до 21.09"
status: active
version: "1.0.0"
last_updated: "2026-07-26"
claim_boundary: ">90% и SLA ≤30 мин — только на согласованном корпусе заказчика после двойной слепой разметки. AeroBIM — ассистент эксперта. Checkpoint NO_GO до RT-001/002/003."
tags: [aerobim, samolet, kickoff, intake, stages]
---

# Kickoff-карта пилота (Самолёт × Техлаб, Задача №7)

Единый маппинг: письмо заказчику → машинные ворота `audit/evidence/customer-intake-gate.json` → календарь.
SSOT: [`PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md`](PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md),
[`FOUR_DIRECTION_GAP_ANALYSIS_2026_07_24.md`](FOUR_DIRECTION_GAP_ANALYSIS_2026_07_24.md) (§6 матрица запросов),
[`../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](../partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md).

## 1. Блокирующие входы → gate keys

| Вход от заказчика | Gate key (intake-gate.json) | RT | Дедлайн |
|---|---|---|---|
| Обезличенный комплект 1–2 разделов (ПД/РД, IFC, ТЗ/EIR, расчёты; жел. 2 ревизии, метаданные IFC, правила экспорта, примеры замечаний) | `customer_package_in_samples_customer` | RT-001 | 4–10 авг |
| Утверждённый список норм/стандартов + пункты проверки (IDS или таблица→IDS) | `customer_approved_norm_pack_with_approval_ref` + `ids_or_property_table_present` | RT-002 | 4–10 авг |
| Каталог ≥20 типовых ошибок/коллизий (пример, критичность, ожидаемая реакция) | вход в labeling-протокол (RT-001 корпус) | RT-001 | 4–10 авг |
| Два независимых эксперта (слепая разметка; LLM не считается — `llm_assist_counts_as_adjudicator=false`) | `dual_human_adjudicators_named` → `cohens_kappa_or_krippendorff_alpha_reported` | RT-001 | 4–10 авг |
| Baseline ручного ревью (время, трудозатраты, итерации, замечания) | `customer_sla_pack_measured` | SLA/ROI | 4–10 авг |
| Тестовый контур СОД + версия BCF | `cde_bcf_import_evidence` (T2: log + screenshot + hashes) | RT-008 | до 20 авг |
| (если MEP в scope) федеративный IFC + signed scope memo + clearance matrix | `mep_federated_scope` | RT-003 | 4–20 авг |
| NDA + signed scope memo | `nda_signed`, `scope_memo_signed` | — | до 3 авг |

Все ворота сейчас `false` → checkpoint **NO_GO**; fixture-контур ≠ замена этих входов.

**Параллельный трек МИК (оператор программы, до 3 авг):** запросить у менеджера Фонда
шаблон соглашения, форму программы пилотирования, форму акта и требования
финотчётности по гранту 2 млн ₽ — см. [`MIK_PILOT_COMPLIANCE_2026.md`](../partners/MIK_PILOT_COMPLIANCE_2026.md)
и [`TRI_SOURCE_REQUIREMENTS_MATRIX_2026.md`](../tz/TRI_SOURCE_REQUIREMENTS_MATRIX_2026.md).

## 2. Согласовать письменно до Phase 0

1. Границы пилота и перечень обязательных проверок (что влияет на `summary.passed`).
2. Режим обработки данных: закрытый контур, обезличивание, приём в gitignored `samples/customer/`.
3. Ограничения claims (Claims Lock): DWG — native `MISSING`, только derived (PDF/IFC/DXF);
   MEP — hard clash ≠ system-aware (RT-003); расчёты — сверка источников, не решатель;
   CV/VLM — вспомогательный, не критерий приёмки MVP.
4. Пороги письменно: interim TP (стартовое предложение ≥0.60), κ≥0.60 / α≥0.67, критический recall.
5. >90% и SLA ≤30 мин — оцениваются исключительно на согласованном корпусе (fixture ≠ customer).
6. AeroBIM = ассистент эксперта; Shared-gate ≠ Published / замена решения.

## 3. Этапность (синхронизирована с календарём Checkpoint #2)

### До 3 августа — стабилизация ядра (без данных заказчика)
- Ядро: IFC/IDS, атрибуты/количества, сверка ПД↔РД↔ТЗ↔расчёты, PDF/сканы,
  сопоставление чертежей с IFC, геометрические коллизии, приоритизация, отчёты.
- Тесты на открытых данных, редкие сценарии, критические ошибки.
- Готовим: протокол пилота, методику разметки
  ([`EXPERT_LABELING_INSTRUCTION_2026.md`](EXPERT_LABELING_INSTRUCTION_2026.md)),
  norm pack ([`NORM_PACK_RASE_GUIDE_2026.md`](NORM_PACK_RASE_GUIDE_2026.md)),
  каталог типовых ошибок (шаблон), демо-прогон + evidence-бандл.

### 4–20 августа — промежуточная версия (КТ2)
- Полный сценарий ПД/РД/IFC/ТЗ/расчёты; размеры, площади, атрибуты, ревизии, противоречия разделов.
- Чертежи: текстовый разбор + OCR сканов + визуальная подсветка зон.
- CV/VLM — только вспомогательно; сравнение Qwen/Kimi/Gemma по протоколу
  [`VLM_OCR_COMPARISON_PROTOCOL_2026_08.md`](VLM_OCR_COMPARISON_PROTOCOL_2026_08.md)
  (выбор по инженерным документам с CI/p-values, не по рейтингам).
- MEP: состав федеративной модели + правила коллизий; системный анализ — только после данных (RT-003).

### 3–21 сентября — финал (КТ3)
- Прогон на согласованном корпусе + независимая разметка ≥2 экспертов.
- Метрики: полнота/точность, κ/α, FP-rate по разделам, время до первого замечания, качество приоритизации.
- Эталонный комплект за 30 мин; сравнение трудозатрат с baseline; подтверждение каталога ≥20 ошибок;
  импорт BCF в СОД заказчика (T2 evidence).

## 4. Итоговая формулировка (Claims-Lock-safe)

Подтверждаемый результат: единый анализ комплекта, IFC/IDS, сверка документов, коллизии,
evidence по каждому замечанию, просмотр IFC и чертежей, панель эксперта, отчёты, BCF 2.1.
**Только после данных и испытаний заказчика:** нативный DWG, корректность расчётов,
полный system-aware MEP, точность >90%.
