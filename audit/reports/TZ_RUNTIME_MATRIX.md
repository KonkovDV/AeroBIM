# TZ Runtime Matrix — Samolet Task 07

Statuses allowed: `VERIFIED` | `VERIFIED_FIXTURE_ONLY` | `PARTIAL` | `SCAFFOLD` | `ADVISORY_ONLY` | `NOT_RUNTIME_CONNECTED` | `MISSING` | `BLOCKED_BY_CUSTOMER_DATA` | `FIXTURE_ONLY`

**Refresh:** 2026-08-04 — Finding 0 (MS Office + version/doc-type compare rows), EN remark parity → `VERIFIED_FIXTURE_ONLY`, space-efficiency → `ADVISORY_ONLY`, SLA gate → **p95**. Checkpoint **NO_GO** (RT-001/002/003 unchanged).

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
| 9 | ТЗ EN | RequirementExtractor + `english-aec-ground-truth.json` | extraction (EN corpus not CI-gated) | thin narrative EN unit; full EN F1 gate **not** wired | fixture | PARTIAL | MED |
| 10 | Расчётные документы | calculation_source | analyze | analyze tests | fixture | PARTIAL | HIGH |
| 11 | Результаты расчётов | ExternalEvidenceVerifier / OpenRebar | reinforcement paths | openrebar tests | fixture | PARTIAL (сверка ≠ verification) | HIGH |
| 12 | Разделы ПД/РД | SectionDiffAnalyzer | pd/rd paths | section pairing tests | fixture | PARTIAL | HIGH |
| 13 | Нормативные пакеты | NormRulePackLoader | norm_rule_pack_paths / env | loader + fail-closed tests | synthetic only | BLOCKED_BY_CUSTOMER_DATA | BLOCKER |
| 14 | MEP-системы | `domain/mep.py` + Unconfigured provider **DI-wired** | probe → NOT_VERIFIED | architecture + capabilities API | none | SCAFFOLD / NOT_VERIFIED | BLOCKER if claimed delivered |
| 15 | Геометрические коллизии | IfcClashDetector | analyze clash | clash + sign-off tests; pilot/production `require_clash` → SKIPPED=FAILED | optional-extra | PARTIAL | CRITICAL |
| 16 | Площади | quantity / property rules | IFC + cross-doc | quantity tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 17 | Размеры | same | same | same | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 18 | Отсутствующие элементы | IDS / IFC rules | when configured | IDS e2e fixtures | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 19 | Неэффективное использование пространства | `space_efficiency_advisory` + IfcSpace inventory | AdvisoryOrchestrator (local IFC; optional layout note) | `test_space_efficiency_advisory.py` | fixture IFC | ADVISORY_ONLY^[fn19] | MED |
| 20 | RU-замечания | RemarkGenerator | analyze attach | remark tests | fixture | VERIFIED_FIXTURE_ONLY | LOW |
| 21 | EN-замечания | RemarkGenerator `locale=en` + BCF Description | analyze attach / export BCF | `test_remark_locale_parity.py` + `test_tz_p0_upload_remarks.py` | fixture | VERIFIED_FIXTURE_ONLY | LOW |
| 22 | Критичность / приоритет | severity + priority | compute_issue_priority | priority tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 23 | Подсветка зон | ProblemZone + frontend overlay | report + UI | frontend vitest | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 24 | Редактор замечаний HITL | review-events API | POST review-events | API + UI tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 25 | BCF | export_bcf / export_bcf3 | export endpoints | structural T1 + dual consumers | no CDE import | PARTIAL | HIGH |
| 26 | SLA ≤30 мин | measure_package_sla (gate=**p95**) | CLI | `test_measure_package_sla.py`; evidence `samolet-sla-fixture-p95-2026-08-04.json` | fixture | FIXTURE_ONLY; customer НЕ ДОКАЗАНО | HIGH |
| 27 | Загрузка MS Office (docx/xlsx/…) | `DoclingOfficeDocumentIngestor` + upload allowlist | hydrate in analyze; `POST /v1/uploads` | `test_cad_office_ingest.py` (fail-closed + txt; **no** real docx fixture) | none real Office | PARTIAL^[fn27] | MED |
| 28 | Сравнение версий и типов документации | `STAGE_MISMATCH` / `VERSION_MISMATCH` | multi-package CDE compare | — | none | MISSING^[fn28] | HIGH |

## Status summary (28 rows)

| Status | Count |
|---|---:|
| VERIFIED_FIXTURE_ONLY | 12 |
| PARTIAL | 9 |
| ADVISORY_ONLY | 1 |
| FIXTURE_ONLY | 1 |
| SCAFFOLD / NOT_VERIFIED | 1 |
| MISSING / MISSING (never OK) | 2 |
| BLOCKED_BY_CUSTOMER_DATA | 1 |
| NOT_VERIFIED / PARTIAL (DXF) | 1 |

## VERIFIED rows — required pointers

No row is elevated to plain `VERIFIED` against **customer** data.

Closest `VERIFIED_FIXTURE_ONLY` examples:

| Item | Test | Command |
|---|---|---|
| Extraction quality (fixture) | evaluate_extraction harness | `cd backend && python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` |
| EN remarks parity + BCF | locale parity | `pytest tests/test_remark_locale_parity.py -q` |
| Space-efficiency advisory | domain candidates | `pytest tests/test_space_efficiency_advisory.py -q` |
| Backend unit/integration suite | pytest collection | `cd backend && python -m pytest -q` |
| Advisory does not flip pass | architecture seams + RT-E | `pytest tests/test_architecture_seams.py tests/test_red_team_signoff_remediation.py tests/test_qwen_local_advisory.py::LlmLocalOffEqualsOnTests -q` |
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

^[fn19]: **ADVISORY_ONLY** — IFC `IfcSpace` inventory (+ optional PII-gated layout note) as INFO candidates with `ai_generated` / expert confirmation. **No** numeric efficiency thresholds. Does **not** close RT-001. VLM crop enrichment optional when Studio multimodal is enabled.

^[fn27]: Upload allowlist + Docling hydrate + DI + fail-closed without Docling are wired. **Not** `VERIFIED_FIXTURE_ONLY` until a real `.docx`/`.xlsx` round-trip fixture exists. `package_completeness` accepts declared `xlsx` only (not `docx`).

^[fn28]: Enum + PD↔RD JSON section scaffold (row 12) and same-request revision-merge guard **emit** these kinds, but they do **not** satisfy TZ «сравнение версий и типов» as multi-package CDE compare. Product capability remains **MISSING** until package-vs-package compare ships (KT#3 II.3). Hiding this gap is worse than listing it.
