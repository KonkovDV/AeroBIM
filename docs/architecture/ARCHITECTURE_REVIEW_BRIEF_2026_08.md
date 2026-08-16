---
title: "Architecture review brief — IT mentor 11.08.2026"
date: 2026-08-05
head: "fa08f20"
audience: "IT mentor / external technical reader (≈5 min)"
claim_boundary: "Engineering inventory. Checkpoint NO_GO. Not product accuracy."
full_audit: "ARCHITECTURE_DEEP_AUDIT_2026_08_05.md"
---

# AeroBIM — бриф по архитектуре (11.08.2026, 12:00)

**Одной фразой.** Система умеет честно проверять openBIM-комплект на fixtures и открытых данных; три customer-блокера кодом не закрыть; рост портов за месяц обогнал сдвиг блокеров — это осознанный долг, не «ещё не доделали».

**Checkpoint:** `NO_GO` (RT-001 corpus · RT-002 норм-пак · RT-003 федеративная MEP).  
**HEAD:** `fa08f20` · `main` = `origin/main` · `.local` tracked = 0.

---

## 1. Что это за система (30 с)

Детерминированное Shared-gate ядро (IFC / IDS / cross-doc / provenance / BCF ZIP) + optional Hybrid AI **без права** ставить `summary.passed`. ИИ — advisory; вердикт — код. Fail-closed на hard-профилях.

---

## 2. Живой inventory (не README-легенда «20→48»)

| Метрика | Месяц назад (нарратив) | Live `fa08f20` |
|---|---:|---:|
| Public domain Protocol | ~20 → claim 48 | **46** |
| Adapter modules | ~30 → claim 67 | **71** |
| DI tokens | ~28 → claim 58 | **59** |
| `backend/src` LOC | — | **~55 351** (290 `.py`) |

Слои (LOC): `tools` 15.6k · `domain` 14.8k · `infrastructure` 14.1k · `application` 6.4k · `presentation` 2.4k · `core` 2.2k.

**Правило окна:** +0 новых доменных портов без обоснования; предпочитать удаление абстракции.

---

## 3. Кандидаты на устранение (1 адаптер + 1 typed consumer)

Именно про них уместен вопрос «зачем Protocol».

| Port | Почему кандидат | Оценка снятия |
|---|---|---|
| `SectionDiffAnalyzer` | Один JSON-адаптер, один UC | Низкая — inline / private helper |
| `RemarkGenerator` | Template-only | Низкая |
| `DocumentSignatureAuditor` | Один путь WP-03 | Низкая–средняя |
| `PackageInventoryLoader` | Один JSON loader | Низкая |
| `ExternalEvidenceVerifier` | OpenRebar-only | Средняя (если появится 2-й verifier — оставить) |
| `BsiValidationService` | HTTP optional | Низкая–средняя |
| `StructuredLogger` | Один JSON logger | Низкая (или оставить как observability seam) |
| `NormRulePackVersionStore` | Только HITL norm path | Средняя |
| `IfcSpatialIndexProvider` | Расширение IfcOpenShellValidator | Низкая — слить с validator |
| `DrawingAnalyzerPort` (TZ) | DI есть, analyze почти не использует | **Снять DI** — высокая ценность / низкий риск |

**11 DI-токенов вне analyze/report/export** (в т.ч. `IFC_MODEL_DIFF`, `CAD_ENTITY_LOADER`, `REQUIREMENT_INTERPRETER`, `ODA_CAD_MODEL_INGESTOR`, `AGENTIC_REVIEW_ORCHESTRATOR`) — зарегистрированы, на рабочем пути не резолвятся.

---

## 4. Три абстракции, которые окупились / три избыточных

**Окупились**

1. **Capability honesty matrix** — SKIPPED ≠ OK; FAILED блокирует pass. Без этого частичный прогон читается как «всё чисто».  
2. **`PrecisionClaim` / `claim_level`** — нельзя опубликовать % с fixtures как продукт.  
3. **Package completeness (WP-05)** — наличие разделов без customer norms; Task 3 поднял КР «обнаруживается» 0→≈8,3% на open/synthetic.

**Избыточны / преждевременны**

1. **TZ ports** (`DrawingAnalyzerPort`, `CadEntityLoaderPort`, `RequirementInterpreterPort`) — DI-wire без consumers на analyze.  
2. **`AgenticReviewOrchestrator` token** — analyze ходит в compliance напрямую.  
3. **Параллельные PDF backends** (pdfminer / pymupdf / disabled) — нужны лицензией, но увеличивают поверхность; ops-путаница, не доменная ценность.

---

## 5. Почему в регулируемой отрасли нужна прослеживаемость (1 абзац)

Госэкспертиза и заказчик принимают не «мнение модели», а **воспроизводимый след**: какой файл, какое правило, какой GUID/лист, какой профиль sign-off, почему capability не запускалась. Поэтому ядро — детерминированные Protocol-порты с явным provenance (`finding_id`, `evidence_refs`), а не единый LLM-вердикт; рост числа портов частично — цена fail-closed честности. Цена оправдана, только если каждый порт режет реальный класс ошибок или закрывает legal/honesty seam; иначе это сложность без сдвига RT-001/002/003.

---

## 6. Что не закрывается кодом (честно)

| Блокер | Open/synthetic замена | Закрытие |
|---|---|---|
| RT-001 точность | coverage map / open bench ≠ product % | Размеченный корпус + ≥2 адъюдикатора |
| RT-002 норм-пак | draft packs advisory | Customer-approved + journal |
| RT-003 MEP | ENG_FIXTURE / NOT_VERIFIED | Federated scope + signed matrix |

---

## 7. Ссылки

| Документ | Зачем |
|---|---|
| [Полный аудит](ARCHITECTURE_DEEP_AUDIT_2026_08_05.md) | 0.1–0.5 таблицы |
| [Exp B](../evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md) | покрытие типовых замечаний |
| [Task 3](../evidence/TASK3_COMPLETENESS_DEMONSTRATOR_2026_08_05.md) | 25п.п. полноты → ≈8,3 подтверждено |
| [ADR-001](ADR-001-verdict-ownership-2026.md) | кто ставит `summary.passed` |
| README Key Capabilities | заявленный статус vs код |

**ТРЕБУЕТСЯ ОТ ВЛАДЕЛЬЦА:** подтвердить слот 11.08; решить, идём ли в сессию с планом *сокращения* портов (да/нет) — не с планом новых абстракций.
