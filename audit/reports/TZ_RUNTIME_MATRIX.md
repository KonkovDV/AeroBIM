# TZ Runtime Matrix — Samolet Task 07

Statuses allowed: `VERIFIED` | `VERIFIED_FIXTURE_ONLY` | `PARTIAL` | `SCAFFOLD` | `ADVISORY_ONLY` | `NOT_RUNTIME_CONNECTED` | `MISSING` | `BLOCKED_BY_CUSTOMER_DATA`

Freeze: SHA `c0c4b2b` + dirty tree 2026-07-16. Author: self.

| # | Требование ТЗ | Код | Runtime path | Тест / команда | Реальные данные | Статус | Риск |
|---|---|---|---|---|---|---|---|
| 1 | Векторные 2D | DrawingAnalyzer / text paths | analyze drawing_sources | fixture tests | fixtures | PARTIAL | HIGH |
| 2 | Сканированные 2D / OCR | RasterDrawingAnalyzer + rapidocr extra | conditional | unit when extra present | **rapidocr absent** | PARTIAL / NOT available here | HIGH |
| 3 | DWG | — | — | — | — | MISSING | BLOCKER if claimed |
| 4 | DXF | — | — | — | — | MISSING | HIGH |
| 5 | IFC2x3 | ifcopenshell validator | validate/analyze | `test_ifc_release_compatibility` (may skip) | samples | VERIFIED_FIXTURE_ONLY | MED |
| 6 | IFC4 | same | same | same | samples | VERIFIED_FIXTURE_ONLY | MED |
| 7 | IFC4x3 | same | same | same | samples | PARTIAL — not separately proven as product matrix | MED |
| 8 | ТЗ RU | RequirementExtractor | analyze | extraction eval RU fixtures | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 9 | ТЗ EN | templates/remarks EN | partial | remark tests | fixture | PARTIAL | MED |
| 10 | Расчётные документы | calculation_source | analyze | some analyze tests | fixture | PARTIAL | HIGH |
| 11 | Результаты расчётов | ExternalEvidenceVerifier / OpenRebar | reinforcement paths | openrebar tests | fixture | PARTIAL (сверка ≠ verification) | HIGH |
| 12 | Разделы ПД/РД | SectionDiffAnalyzer | pd/rd paths | section pairing tests | fixture | PARTIAL | HIGH |
| 13 | Нормативные пакеты | NormRulePackLoader | norm_rule_pack_paths / env | loader + fail-closed tests | synthetic only | BLOCKED_BY_CUSTOMER_DATA | BLOCKER |
| 14 | MEP-системы | `domain/mep.py` | **not in bootstrap** | architecture marks missing | none | SCAFFOLD / NOT_RUNTIME_CONNECTED | BLOCKER |
| 15 | Геометрические коллизии | IfcClashDetector | analyze clash | clash tests; **ifcclash missing → SKIPPED** | optional | PARTIAL | CRITICAL |
| 16 | Площади | quantity / property rules | IFC + cross-doc | quantity tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 17 | Размеры | same | same | same | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 18 | Отсутствующие элементы | IDS / IFC rules | when configured | IDS e2e fixtures | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 19 | Неэффективное использование пространства | — | — | — | — | MISSING | HIGH |
| 20 | RU-замечания | RemarkGenerator | analyze attach | remark tests | fixture | VERIFIED_FIXTURE_ONLY | LOW |
| 21 | EN-замечания | RemarkGenerator | same | partial | fixture | PARTIAL | MED |
| 22 | Критичность / приоритет | severity + priority | compute_issue_priority | priority tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 23 | Подсветка зон | ProblemZone + frontend overlay | report + UI | **frontend tests FAIL** | fixture | PARTIAL | CRITICAL |
| 24 | Редактор замечаний HITL | review-events API | POST review-events | API tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 25 | BCF | export_bcf / export_bcf3 | export endpoints | unit + dirty multi-consumer | no CDE import artifact | PARTIAL | HIGH |
| 26 | SLA ≤30 мин | measure_package_sla | CLI | tool exists; no customer evidence artifact here | fixture/pilot | PARTIAL / НЕ ДОКАЗАНО for customer | HIGH |

## VERIFIED rows — required pointers

No row is elevated to plain `VERIFIED` against **customer** data in this audit.

Closest `VERIFIED_FIXTURE_ONLY` examples:

| Item | Test | Command |
|---|---|---|
| Extraction quality (fixture) | evaluate_extraction harness | `cd backend && python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` |
| Backend unit/integration suite | pytest collection | `cd backend && python -m pytest -q` |
| Advisory does not flip pass | `test_architecture_seams.py::test_advisory_off_equals_advisory_on_for_summary_passed` | `pytest tests/test_architecture_seams.py -q` |
| Norm pack fail-closed | `test_norm_pack_env_capability.py` | `pytest tests/test_norm_pack_env_capability.py -q` |
| MEP marked missing | `test_architecture_seams.py::test_tz_matrix_generator_marks_mep_missing` | same file |

## Explicit MEP line

```text
MEP system-aware clash: NOT VERIFIED
```
