# TZ Runtime Matrix — Samolet Task 07

Statuses allowed: `VERIFIED` | `VERIFIED_FIXTURE_ONLY` | `PARTIAL` | `SCAFFOLD` | `ADVISORY_ONLY` | `NOT_RUNTIME_CONNECTED` | `MISSING` | `BLOCKED_BY_CUSTOMER_DATA` | `FIXTURE_ONLY`

**Refresh:** 2026-08-14 evening — survey XSD intake, IfcClash clearance gap pair, clash→BCF file ingest, SP 63 cover *template*, jurisdiction IDS document audit. 2026-08-28: row 25 footnote — customer CDE identified at address level (10D contour via share-link origin); T2 closure path via public API + demo license; status unchanged. 2026-08-28 (вечер): критическое издание ответов 25.08 — fn11 (записки PDF/Excel, не бинари; +нагрузки/площади), fn13 (перечень стандартов выдан; блокер = доступ), fn15 (сводная модель в NWD), fn19 (норматив продаваемой площади), fn25 (п. 2.2.2: интеграция не требуется); строка 31 (ТР-67 сверка объёмов) — **PARTIAL** на объявленных тройках, не ingest. Checkpoint **NO_GO** (RT-001/002/003 unchanged). Native DWG still **MISSING**.

| # | Требование ТЗ | Код | Runtime path | Тест / команда | Реальные данные | Статус | Риск |
|---|---|---|---|---|---|---|---|
| 1 | Векторные 2D | StructuredDrawingAnalyzer + PDF text (pdfminer) | analyze drawing_sources | committed `samples/drawings/` txt/json/pdf | fixture | VERIFIED_FIXTURE_ONLY^[fn1] | MED |
| 2 | Сканированные 2D / OCR | RasterDrawingAnalyzer + rapidocr extra | conditional | committed `wall-thickness-scan.png`; skip without `[raster]` | optional-extra | VERIFIED_FIXTURE_ONLY^[fn2] | MED |
| 3 | DWG | honesty `dwg_dxf` | mixed package fail-closed | derived sidecar `placeholder-source.dwg` | none as product | MISSING (never OK)^[fn3] | BLOCKER if claimed |
| 4 | DXF | CadModelIngestor (ezdxf) optional `[cad]` | EntityGraph | `test_cad_office_ingest.py` committed `samples/cad/minimal-entities.dxf` | fixture | VERIFIED_FIXTURE_ONLY^[fn4] | MED |
| 5 | IFC2x3 | ifcopenshell validator | validate/analyze | `test_ifc_release_compatibility` | samples | VERIFIED_FIXTURE_ONLY | MED |
| 6 | IFC4 | same | same | same | samples | VERIFIED_FIXTURE_ONLY | MED |
| 7 | IFC4x3 | same | same | same | samples | VERIFIED_FIXTURE_ONLY | MED |
| 8 | ТЗ RU | RequirementExtractor | analyze | extraction eval RU fixtures | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 9 | ТЗ EN | RequirementExtractor + `english-aec-ground-truth.json` | `evaluate_extraction --manifest …/english-aec-ground-truth.json --min-macro-f1 0.70` | `test_eval_statistics.py` EnglishExtractionGateTests | fixture | VERIFIED_FIXTURE_ONLY^[fn9] | MED |
| 10 | Расчётные документы | calculation_source + LOAD table сверка | analyze | `area-requirement.txt` + `load-table.txt` | fixture | VERIFIED_FIXTURE_ONLY^[fn10] | MED |
| 11 | Результаты расчётов | OpenRebarEvidenceVerifier | reinforcement paths | committed `openrebar-slab-03.result.json` | fixture | VERIFIED_FIXTURE_ONLY^[fn11] | HIGH |
| 12 | Разделы ПД/РД | SectionDiffAnalyzer | pd/rd paths | `test_section_diff_analyzer.py` AR+KZH JSON | fixture | VERIFIED_FIXTURE_ONLY^[fn12] | MED |
| 13 | Нормативные пакеты | NormRulePackLoader | norm_rule_pack_paths / env | loader + fail-closed tests; SP 63 cover template | synthetic only | BLOCKED_BY_CUSTOMER_DATA^[fn13] | BLOCKER |
| 14 | MEP-системы | FederatedIfcMepSystemGraphProvider + matrix | ENG_FIXTURE HVAC IFC | `test_p2_perf_2d_mep.py` | fixture graph | VERIFIED_FIXTURE_ONLY^[fn14] | HIGH |
| 15 | Геометрические коллизии | IfcClashDetector | analyze clash + detect_between + detect_clearance_between | planted federated boxes; clearance-gap pair; optional `[clash]` | fixture | VERIFIED_FIXTURE_ONLY^[fn15] | CRITICAL |
| 16 | Площади | quantity / property rules | IFC + cross-doc | quantity tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 17 | Размеры | same | same | same | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 18 | Отсутствующие элементы | IDS / IFC rules | when configured | IDS e2e fixtures | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 19 | Неэффективное использование пространства | `space_efficiency_advisory` + IfcSpace inventory | AdvisoryOrchestrator (local IFC; optional layout note) | `test_space_efficiency_advisory.py` | fixture IFC | ADVISORY_ONLY^[fn19] | MED |
| 20 | RU-замечания | RemarkGenerator | analyze attach | remark tests | fixture | VERIFIED_FIXTURE_ONLY | LOW |
| 21 | EN-замечания | RemarkGenerator `locale=en` + BCF Description | analyze attach / export BCF | `test_remark_locale_parity.py` + `test_tz_p0_upload_remarks.py` | fixture | VERIFIED_FIXTURE_ONLY | LOW |
| 22 | Критичность / приоритет | severity + priority | compute_issue_priority | priority tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 23 | Подсветка зон | ProblemZone + frontend overlay | report + UI | frontend vitest | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 24 | Редактор замечаний HITL | review-events API | POST review-events | API + UI tests | fixture | VERIFIED_FIXTURE_ONLY | MED |
| 25 | BCF | export_bcf / consume_bcf_zip_path | export endpoints + file ingest CLI | committed `samples/bcf/fixture-topics.bcfzip` | no CDE import | VERIFIED_FIXTURE_ONLY^[fn25] | HIGH |
| 26 | SLA ≤30 мин | measure_package_sla (gate=**p95**) | CLI | `test_measure_package_sla.py`; evidence `samolet-sla-fixture-p95-2026-08-04.json` | fixture | FIXTURE_ONLY; customer НЕ ДОКАЗАНО | HIGH |
| 27 | Загрузка MS Office (docx/xlsx/…) | `OfficeDocumentIngestor` + upload allowlist | hydrate in analyze; `POST /v1/uploads` | `test_office_native_ingest.py` committed `samples/office/` | synthetic Office | VERIFIED_FIXTURE_ONLY^[fn27] | MED |
| 28 | Сравнение версий и типов документации | `compare_package_document_identities` | CLI `compare_package_identities` | `test_package_identity_compare.py` | synthetic inventories | VERIFIED_FIXTURE_ONLY^[fn28] | HIGH |
| 29 | Извлечение инженерных сетей из 2D | — | — | — | none | MISSING^[fn29] | HIGH |
| 30 | Снижение когнитивной нагрузки | review-events journal (метрики ТР-65) | — | — | none | MISSING^[fn30] | MED |
| 31 | Сверка объёмов спецификации ↔ графика/BIM («логические коллизии») | `compare_spec_volumes` | domain declared triples | `test_spec_volume_compare.py` | none | PARTIAL^[fn31] | HIGH |

## Status summary (31 rows)

| Status | Count |
|---|---:|
| VERIFIED_FIXTURE_ONLY | 24 |
| ADVISORY_ONLY | 1 |
| FIXTURE_ONLY | 1 |
| PARTIAL | 1 |
| MISSING (never OK) | 1 |
| MISSING | 2 |
| BLOCKED_BY_CUSTOMER_DATA | 1 |

## VERIFIED rows — required pointers

No row is elevated to plain `VERIFIED` against **customer** data.

Closest `VERIFIED_FIXTURE_ONLY` examples:

| Item | Test | Command |
|---|---|---|
| Extraction quality (fixture) | evaluate_extraction harness | `cd backend && python -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70` |
| EN extraction (fixture) | English corpus F1 gate | `cd backend && python -m aerobim.tools.evaluate_extraction --manifest ../samples/benchmarks/english-aec-ground-truth.json --min-macro-f1 0.70` |
| Package identity compare (fixture) | previous vs current identities | `cd backend && python -m aerobim.tools.compare_package_identities --input ../samples/packages/identity-compare-pd-rd.json` |
| OpenRebar сверка (fixture) | committed reinforcement JSON | `pytest tests/test_openrebar_provenance_digest.py::OpenRebarProvenanceDigestToolTests::test_committed_openrebar_fixture_sverka_without_digest_mismatch -q` |
| Planted IfcClash (optional extra) | federated boxes | `pytest tests/test_bcf_export_and_clash.py::ClashDetectorPortTests::test_planted_federated_boxes_clash_when_ifcclash_installed -q` |
| Clearance IfcClash (optional extra) | gap pair ~30 mm | `pytest tests/test_bcf_export_and_clash.py::ClashDetectorPortTests::test_clearance_gap_hits_when_ifcclash_installed -q` |
| Clash→BCF file ingest (not CDE) | planted pair round-trip | `pytest tests/test_bcf_export_and_clash.py::ClashDetectorPortTests::test_planted_clash_exports_bcf_file_ingest_round_trip -q` |
| BCF file ingest (not CDE) | committed BCFZIP | `cd backend && python -m aerobim.tools.ingest_bcf_zip --input ../samples/bcf/fixture-topics.bcfzip` |
| Derived DWG sidecar (never native OK) | placeholder DWG→DXF | `pytest tests/test_dwg_derived_provenance.py::DerivedProvenanceVerificationTests::test_committed_placeholder_dwg_derived_dxf_sidecar -q` |
| Vector PDF + structured 2D | committed drawings | `pytest tests/test_structured_drawing_analyzer.py tests/test_raster_drawing_analyzer.py -q` |
| LOAD table сверка | committed calc table | `pytest tests/test_consistency_ports.py::ConsistencyPortsTests::test_committed_load_table_fixture -q` |
| EN remarks parity + BCF | locale parity | `pytest tests/test_remark_locale_parity.py -q` |
| Space-efficiency advisory | domain candidates | `pytest tests/test_space_efficiency_advisory.py -q` |
| Backend unit/integration suite | pytest collection | `cd backend && python -m pytest -q` |
| Advisory does not flip pass | architecture seams + RT-E | `pytest tests/test_architecture_seams.py tests/test_red_team_signoff_remediation.py tests/test_qwen_local_advisory.py::LlmLocalOffEqualsOnTests -q` |
| Norm pack fail-closed | `test_norm_pack_env_capability.py` | `pytest tests/test_norm_pack_env_capability.py -q` |
| Production sign-off / ACL 404 / SSRF | `test_rt_remediation_post.py` | `pytest tests/test_rt_remediation_post.py -q` |

## Explicit MEP line

```text
MEP system-aware clash: NOT VERIFIED (ENG_FIXTURE graph ≠ delivered capability; default DI Unconfigured)
```

## Explicit Shared-gate line

```text
summary.passed = deterministic Shared-gate (ADR-001); not Shared→Published; AI/OCR cannot flip
```

^[fn19]: **ADVISORY_ONLY** — IFC `IfcSpace` inventory (+ optional PII-gated layout note) as INFO candidates with `ai_generated` / expert confirmation. **No** numeric efficiency thresholds. Does **not** close RT-001. VLM crop enrichment optional when Studio multimodal is enabled. 28.08 (п. 2.1.4): критерий — **внутренний норматив продаваемой площади** заказчика (лежит в выданных, но закрытых папках 1.2.1), а не СП. До доступа к папкам ADVISORY_ONLY — единственный честный статус, не недоработка.

^[fn1]: Structured TXT/JSON annotations plus vector PDF text via pdfminer on `samples/drawings/wall-thickness-vector.pdf`. **Not** CAD entity extraction, **not** native DWG, **not** human-level CV.

^[fn2]: Synthetic scan PNG `samples/drawings/wall-thickness-scan.png`. Live RapidOCR when `aerobim-backend[raster]` is installed; tests skip without the extra. **Not** a customer scanned sheet.

^[fn3]: Native DWG parser is **not implemented**. LibreDWG is GPL-3 and is **not** linked. Committed `placeholder-source.dwg` + hash-bound DXF sidecar documents the derived route only — `dwg_dxf` stays never OK.

^[fn4]: DXF via optional `ezdxf` (`aerobim-backend[cad]`) on the committed `samples/cad/minimal-entities.dxf` fixture. Tests skip when the extra is absent. Native **DWG** remains **MISSING** (row 3). Not a customer CAD package.

^[fn9]: English structured-text corpus F1 gate is fixture-only (2 fixtures / 10 requirements). Never customer accuracy (RT-001).

^[fn10]: Narrative calc ingest (`area-requirement.txt`) plus LOAD-table сверка (`load-table.txt`). **Not** independent structural verification (row 11 / OpenRebar). Not customer calculation volumes.

^[fn11]: OpenRebar provenance сверка on committed `samples/calculations/openrebar-slab-03.result.json`. `calculation_correctness` stays **NOT_IMPLEMENTED**. SP 63 cover pack is a synthetic template, not a solver. 28.08 (критическое издание ответов, п. 2.1.1): источник сверки — **расчётные записки PDF/Excel**, не бинарные файлы комплекса; добавлены объекты сверки **нагрузки и площади**. Обратная разработка закрытого формата исключена из плана по воле заказчика.

^[fn12]: Deterministic PD↔RD JSON pairing on `samples/sections/` (AR+KZH). **Not** customer PD/RD volumes and not a full PP RF 87 parser.

^[fn13]: Loader + fail-closed approval contract. `samples/rule-packs/sp63-cover-template.json` is a 20 mm cover *template* (not SP 63 table 8.1, not exposure class). Customer-approved pack still missing. Does **not** close RT-002. 28.08: перечень внутренних стандартов и регламентов BIM **выдан 25.08** — две ссылки в ответе 1.2.1, но это внутренние пути контура заказчика (два разных проекта СОД), снаружи не открываются. Блокер перешёл из «нет данных» в «нет доступа к выданному»: запрос = опубликовать две папки тем же способом, что датасет.

^[fn14]: ENG_FIXTURE HVAC/sprinkler graph + clearance-matrix template. HVAC fixture has **no tessellated geometry** — live IfcClash clearance uses `clash-clearance-gap-{a,b}.ifc`, not that HVAC file. Default DI remains `UnconfiguredMepSystemGraphProvider`. Geometric MEP system clash stays **NOT_VERIFIED**. Does **not** close RT-003.

^[fn15]: Planted IfcClash on `clash-federated-box-{a,b}.ifc` plus clearance-gap pair (`detect_clearance_between`, 50 mm). Optional `[clash]` extra. Clash→our BCF export→`consume_bcf_zip` is **file ingest**. Engine rehearsal only. `closes_rt003=false`. `cde_import=NOT_VERIFIED`. Not coordinator BCF gold. 28.08 (п. 1.1.5 ответов): федеративная (сводная) модель у заказчика **существует — в NWD**. Блокер снимается выгрузкой NWD→IFC штатным пакетным экспортом СОД по одному корпусу, а не ожиданием «федеративного IFC»; до выгрузки критерий ТЗ на пакете неизмерим (RT-CLASH-MEASURE).

^[fn25]: BCF 2.1/3.0 export + file ingest (`consume_bcf_zip_path`, `samples/bcf/fixture-topics.bcfzip`). `cde_import` stays **NOT_VERIFIED**. Not RT-008 T2. 2026-08-28: target CDE **identified at address level** — the customer pack share link resolves to the 10D contour (session-gated; contents not read). Closure path without customer files: vendor public Swagger API + free developer license, synthetic BCF push into a demo-tenant registry, then T2 pack (log+screenshot+hashes). Demo-tenant push ≠ customer registry proof; status unchanged until a real import lands. 28.08 (п. 2.2.2 ответов): прямая интеграция с СОД на MVP **не требуется** — достаточно файлового импорта/экспорта через веб-интерфейс. API-демо остаётся опциональным дифференциатором вне критического пути КТ#3.

^[fn27]: Native `.docx`/`.xlsx` round-trip on committed `samples/office/` fixtures; `package_completeness` accepts declared `docx` and `xlsx`. Legacy `.doc`/`.xls` still fail-closed at ingest. Not customer Office files. Требование заведено как **ТР-64** (28.08) — до этого было в коде без номера ТР.

^[fn28]: Package-vs-package identity compare by `source_id` emits `STAGE_MISMATCH` / `VERSION_MISMATCH` / `DOC_TYPE_MISMATCH` on synthetic inventories. Thin GUID/attribute IFC model-diff (`Tokens.IFC_MODEL_DIFF`) remains an engineering scaffold. **Not** CDE version management, **not** KT#3 II.3 CDE import, **not** customer packages. Требование заведено как **ТР-63** (28.08); в СОД заказчика наложение версий уже работает — ценность не в показе разницы, а в вердикте о нарушении нормы.

^[fn29]: ТЗ «Извлечение» требует инженерные сети из 2D-чертежей третьим пунктом списка; ни одна строка кода это не покрывает. 470 DWG пакета — ровно этот класс. ТР-66, статус MISSING — честный gap, не «частично покрыто».

^[fn30]: Пользовательский критерий ТЗ без порога. ТР-65: метрики из журнала HITL review-events — время до первого подтверждённого замечания, доля принятых без правки, переключения лист↔модель на замечание (третья требует UI-событий). Журнал есть, метрики не посчитаны — MISSING, а не scaffold с цифрой.

^[fn31]: П. 2.1.3 ответов 25.08: «логические коллизии» = несоответствие объёмов в спецификации и графике/BIM — сверка количеств, а не геометрия и не «объёмы из модели в смету». ТР-67: `compare_spec_volumes` на объявленных тройках (фикстура). Не ingest комплекта, не смета, не корпус заказчика. Строка 15 остаётся геометрией.

Customer-corpus `VERIFIED`: **0 / 28**. Checkpoint **NO_GO**.

RT-001 / RT-002 / RT-003 remain **OPEN**. Native DWG remains **MISSING**. MEP system clash remains **NOT_VERIFIED**. CDE import remains **NOT_VERIFIED**. Independent calculation correctness remains **NOT_IMPLEMENTED**.

