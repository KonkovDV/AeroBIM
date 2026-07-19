---
title: "AeroBIM Strategic Assessment — Samolet TechLab Task 07"
status: active
version: "1.1.0"
last_updated: "2026-07-19"
checkpoint: NO_GO
tags: [aerobim, techlab, samolet, strategy, positioning]
---

# Короткий вывод

**AeroBIM уже не просто «AI для BIM», а инженерное ядро проверки openBIM-комплектов.** Сильная сторона — не обещание распознавать всё, а правильная идея: взять IFC, IDS, чертежи и расчётные материалы, сопоставить их, показать доказательства и не позволить AI/OCR самостоятельно изменить Shared-gate статус `summary.passed` (ADR-001). Автоматический технический статус ≠ Shared→Published.

По ТЗ Самолёта это пока **сильный MVP / pilot foundation, а не готовая промышленная система приёмки.** Главная причина — не отсутствие ещё одной AI-функции, а отсутствие реальных данных заказчика, утверждённого нормативного пакета и доказанного federated MEP-сценария.

**Каноническое позиционирование:**

> Open-source openBIM validation kernel and expert review assistant for IFC, IDS and cross-document evidence.

**Запрещённое позиционирование:**

> AI-система, которая автоматически проверяет всю проектную документацию, расчёты, DWG, MEP и нормы с точностью более 90%.

Связанные артефакты: [`TECHLAB_TASK_07_READINESS_2026.md`](TECHLAB_TASK_07_READINESS_2026.md) · [`../../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md) · [`../../audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md) · [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md)

---

# 1. Что такое AeroBIM простыми словами

Инженер получает комплект: IFC, IDS, PDF-чертежи, ТЗ, расчёты, документы смежных разделов. Обычно проверка разрозненна; связь замечания с доказательством часто теряется.

AeroBIM строит единый конвейер:

```text
Комплект документов
        ↓
Загрузка и проверка входных данных
        ↓
Извлечение требований
        ↓
Проверка IFC и IDS
        ↓
Сопоставление IFC, чертежей и текстов
        ↓
Проверка коллизий
        ↓
Формирование findings с provenance
        ↓
Экспертный review
        ↓
HTML / JSON / BCF
```

**Finding** — структурированное замечание с provenance (правило, файл, лист, IFC GUID, зона, confidence, адаптер, HITL-статус). Инженер видит не только вывод, но и **доказательство вывода**.

---

# 2. Что сделано хорошо

## 2.1. Центр продукта

Не замена Revit / полный CDE / новый Solibri / автономная сертификация. Позиция: **validation kernel и ассистент эксперта**. Ценность — повторяемость: одна модель, одна версия правил, объяснимый результат.

## 2.2. Clean Architecture

```text
core → domain → application → infrastructure → presentation
```

Слои меняются с разной скоростью (IFC/IDS стабильнее; OCR/VLM/CDE/storage — эволюционируют).

## 2.3. openBIM-стек

IFC, IDS, BCF, bSDD, openCDE; адаптеры IfcOpenShell / IfcTester / IfcClash. Разделение:

```text
IFC syntax/schema ≠ IFC semantic ≠ IDS ≠ project rules ≠ geometry/clash ≠ cross-document
```

## 2.4. DeterminismGate и HITL

```text
Детерминированный движок → основной результат
AI / OCR / VLM             → рекомендация
Расхождение                → DivergenceRecord
Эксперт                    → окончательное решение review
```

---

# 3. Слои и требования к усилению

## 3.1. Ingestion (P0 gaps)

Нужно: magic bytes, лимиты не только IFC, streaming, zip-bomb protection, artifact hash, quarantine seam, per-tenant quotas.

## 3.2. Deterministic validation

Четыре состояния: выполнена/OK · выполнена/ошибка · не запускалась · упала. Пункты 3–4 ≠ успех. Quantity exception при обязательном профиле → block `passed`.

## 3.3. AI advisory

Структурированный ответ (claim, confidence, evidence_refs, model, prompt_version, abstained). Запрет прямого изменения verdict / activation norm pack / BCF publish.

## 3.4. Evidence reporting

Версия кода/правил, hashes входов, стадии, unavailable adapters, почему passed/failed, HITL status.

---

# 4. Аналоги (июль 2026)

| Аналог | Урок для AeroBIM |
|--------|------------------|
| Solibri | Ниша: multimodal evidence layer, не desktop replacement |
| BIMcollab Zoom | Evidence fusion + red-team honesty, не копия issue CDE |
| bSI Validation Service | Pre-gate schema ≠ project rules |
| usBIM.checker | Открытая claim/evidence модель |
| OpenAEC / web-ifc viewers | Viewer UX; ядро остаётся validation kernel |

Дифференциация AeroBIM: `IFC + IDS + PDF + calculation + provenance`, не только `IFC + IDS → PASS/FAIL`.

---

# 5–6. ТЗ Самолёта и NO_GO

Хорошо: IFC/IDS, cross-doc, provenance, HITL, BCF structural.  
Частично: Office, TZ→requirements, calc matching, norm packs, generic clash.  
Не закрыто: native DWG, human CV, calc correctness, MEP system-aware, >90%, approved pack, CDE import, space efficiency, federated corpus.

`NO_GO` = нельзя честно заявлять готовность к приёмке на реальных данных заказчика.

---

# 7. Главные технические риски (P0)

1. False pass (SKIPPED/FAILED → green)  
2. Transactionality / orphans  
3. HITL region validation & event integrity  
4. Security (ACL, path jail, uploads)  

---

# 8–9. Целевой промышленный вариант и приоритеты

P0: false-pass, transactions, audit, ACL, upload security, advisory ON/OFF, schema round-trip, profiles.  
P1: manifest, durable jobs, orphan scanner, OpenAPI/security tests.  
P2: customer corpus + approved norms + MEP + CDE proof.  
P3: VLM/LLM/GraphRAG только как advisory.

---

# 10. Итоговая оценка и позиционирование

| Область | Оценка |
|---|---:|
| Архитектурная идея | 8/10 |
| openBIM-направление | 8/10 |
| IFC/IDS foundation | 7/10 |
| Provenance | 7/10 |
| HITL-концепция | 7/10 |
| Browser review | 6/10 |
| Production security | 5/10 |
| Persistence/recovery | 5/10 |
| MEP readiness | 3/10 |
| Customer validation | 2/10 |
| Normative readiness | 2/10 |
| AI maturity | 3/10 |
| «Готово для Самолёта» | 2/10 |
| Честный technical pilot | 6/10 |

**Канон:** openBIM validation kernel + expert review assistant.  
**Следующий доказательный slice:** `IFC + IDS + PDF + один cross-doc сценарий → deterministic → provenance → HITL → BCF 2.1 → эксперт`.
