# TZ Runtime Matrix — Samolet Task 07

Statuses allowed: `VERIFIED` | `VERIFIED_FIXTURE_ONLY` | `PARTIAL` | `SCAFFOLD` | `ADVISORY_ONLY` | `NOT_RUNTIME_CONNECTED` | `MISSING` | `BLOCKED_BY_CUSTOMER_DATA`

**Refresh:** 2026-07-19 Red Team docs pass (`main`). Checkpoint **NO_GO** (RT-001/002/003).  
Historical narrative freezes (`c0c4b2b` / `8efbef8`) are superseded for rows marked below.

| # | Требование ТЗ | Код | Runtime path | Тест / команда | Реальные данные | Статус | Риск |
|---|---|---|---|---|---|---|---|
| 1 | Векторные 2D | DrawingAnalyzer / text paths | analyze drawing_sources | fixture tests | fixtures | PARTIAL | HIGH |
| 2 | Сканированные 2D / OCR | RasterDrawingAnalyzer + rapidocr extra | conditional | unit when extra present | optional-extra | PARTIAL | HIGH |
| 3 | DWG | honesty `dwg_dxf` | mixed package fail-closed | ACL/cad tests | none as product | MISSING (never OK) | BLOCKER if claimed |
| 4 | DXF | CadModelIngestor (ezdxf) optional `[cad]` | EntityGraph | cad tests | fixture | NOT_VERIFIED / PARTIAL | HIGH |
| 5 | IFC2x3 | ifcopenshell validator | validate/analyze | `test_ifc_release_compatibility` | samples | VERIFIED_FIXTURE_ONLY | MED |
| 6 | IFC4 | same | same | same | samples | VERIFIED_FIXTURE_ONLY | MED |
| 7 | IFC4x3 | same | same | same | samples | VERIFIED_FIXTURE_ONLY | MED |
| 8 | ТЗ RU | RequirementExtractor | analyze | extraction eval RU fixtures | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 9 | ТЗ EN | templates/remarks EN | partial | remark tests | fixture | PARTIAL | MED |
| 10 | Расчётные документы | calculation_source | analyze | analyze tests | fixture | PARTIAL | HIGH |
| 11 | Результаты расчётов | ExternalEvidenceVerifier / OpenRebar | reinforcement paths | openrebar tests | fixture | PARTIAL (сверка ≠ verification) | HIGH |
| 12 | Разделы ПД/РД | SectionDiffAnalyzer | pd/rd paths | section pairing tests | fixture | PARTIAL | HIGH |
| 13 | Нормативные пакеты | NormRulePackLoader | norm_rule_pack_paths / env | loader + fail-closed tests | synthetic only | BLOCKED_BY_CUSTOMER_DATA | BLOCKER |
| 14 | MEP-системы | `domain/mep.py` + Unconfigured provider **DI-wired** | probe → NOT_VERIFIED | architecture + capabilities API | none | SCAFFOLD / NOT_VERIFIED | BLOCKER if claimed delivered |
| 15 | Геометрические коллизии | IfcClashDetector | analyze clash | clash + sign-off tests; pilot/production `require_clash` → SKIPPED=FAILED | optional-extra | PARTIAL | CRITICAL |
| 16 | Площади | quantity / property rules | IFC + cross-doc | quantity tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 17 | Размеры | same | same | same | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 18 | Отсутствующие элементы | IDS / IFC rules | when configured | IDS e2e fixtures | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 19 | Неэффективное использование пространства | — | — | — | — | MISSING | HIGH |
| 20 | RU-замечания | RemarkGenerator | analyze attach | remark tests | fixture | VERIFIED_FIXTURE_ONLY | LOW |
| 21 | EN-замечания | RemarkGenerator | same | partial | fixture | PARTIAL | MED |
| 22 | Критичность / приоритет | severity + priority | compute_issue_priority | priority tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 23 | Подсветка зон | ProblemZone + frontend overlay | report + UI | frontend vitest **25** passed | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 24 | Редактор замечаний HITL | review-events API | POST review-events | API + UI tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 25 | BCF | export_bcf / export_bcf3 | export endpoints | structural T1 + dual consumers | no CDE import | PARTIAL | HIGH |
| 26 | SLA ≤30 мин | measure_package_sla | CLI | tool + fixture honesty JSON | fixture | FIXTURE_ONLY; customer НЕ ДОКАЗАНО | HIGH |

## VERIFIED rows — required pointers

No row is elevated to plain `VERIFIED` against **customer** data.

Closest `VERIFIED_FIXTURE_ONLY` examples:

| Item | Test | Command |
|---|---|---|
| Extraction quality (fixture) | evaluate_extraction harness | `cd backend && python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` |
| Backend unit/integration suite | pytest collection | `cd backend && python -m pytest -q` |
| Advisory does not flip pass | architecture seams + RT-E | `pytest tests/test_architecture_seams.py tests/test_red_team_signoff_remediation.py -q` |
| Norm pack fail-closed | `test_norm_pack_env_capability.py` | `pytest tests/test_norm_pack_env_capability.py -q` |
| Production sign-off / ACL 404 / SSRF | `test_rt_remediation_post.py` | `pytest tests/test_rt_remediation_post.py -q` |

## Explicit MEP line

```text
MEP system-aware clash: NOT VERIFIED (DI-wired Unconfigured provider ≠ delivered capability)
```

## Explicit Shared-gate line

```text
summary.passed = deterministic Shared-gate (ADR-001); not Shared→Published; AI/OCR cannot flip
```
