<!-- claims-lint: allow-file reason="Demo-day auditor A–F table; TZ 90%/SLA/CDE as non-claims; Checkpoint GO; customer_go false" -->
---
title: "Аудиторский пакет демо-дня — блоки A–F (14.09.2026)"
date: "2026-09-14"
last_updated: "2026-09-15"
status: active
version: "1.1.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: audit_table_not_score
customer_go: false
precision_claim_publishable: false
claim_boundary: >
  Evidence table for TechLab demo day, task Appendix 4 №6, commission №7.
  Not a predicted score. Not pack processed. Census fingerprints are not
  a jury exhibit. Checkpoint GO; customer_go false.
---

# Аудиторский пакет A–F — демо-день 29–30.09.2026

Машина: `python -c "from aerobim.domain.demo_day_auditor_pack import demo_day_auditor_snapshot, render_fact_table"`.

Это **не** карта жюри и **не** exhibit. Счётчики census (обёртка / unpack / IfcSpace пакета A) живут в инженерных пинах, не в `JURY_SURFACES`. PPTX на рабочем столе этим файлом не переписывается — канон слайдов: [`../../submission/03-presentation/demo_day_slides.md`](../../submission/03-presentation/demo_day_slides.md).

Checkpoint **`GO`**; `customer_go` **false**. `PrecisionClaim.publishable` **false**. Строк `VERIFIED_CUSTOMER`: **0** (пакет `processed=false`, dual-rater = 0, акт площадки = NO_DATA). Слабый статус выбран сознательно.

Сводка статусов: VERIFIED_INTERNAL 59; SYNTHETIC 14; NEEDS_CUSTOMER 8; NOT_VERIFIED 3; NO_DATA 10; VERIFIED_CUSTOMER 0. Фактов: 94. На слайд: 67.

Связанные: [замок речи](../demo/DEMO_DAY_SPEECH_LOCK_2026_09.md) · [красная черта деки](DEMO_DAY_DECK_REDLINE_2026_09.md) · [граница заявлений](../pilot-claim-boundary-2026.md) · [CLAIMS_LOCK](../../audit/reports/CLAIMS_LOCK_2026_07_17.md).

## 1) Основная таблица

| ID | утверждение | точное значение | источник (путь + раздел) | статус | можно на слайд | формулировка для слайда |
|---|---|---|---|---|---|---|
| A-01 | Канал комплекта получен | 2026-08-25; hashed pack not in git; names/hashes false | audit/evidence/customer-intake-gate.json §share_received_at; docs/evidence/unpack-census-latest.json names_in_git | VERIFIED_INTERNAL | да | Канал 25.08 получен. Хеш-пакета в git нет. Не говорить «данных нет». |
| A-02 | Файлов в обёртке (вечерний census) | 2552 | docs/evidence/unpack-census-latest.json wrapper_file_count; domain/unpack_census.py | VERIFIED_INTERNAL | нет | счётчик census не на слайд |
| A-03 | Файлов в unpack-дереве (вечерний census) | 6408 | docs/evidence/unpack-census-latest.json unpacked_file_count | VERIFIED_INTERNAL | нет | счётчик census не на слайд |
| A-04 | Уникальные IFC на канале | 15 unique SPF; unpack holds 4 copies of wrapper files | docs/evidence/deep-study-carrier-facts-2026-08.md §IFC; unpack-census-latest.json wrapper_ifc_count=15 unpacked_ifc_count=4 | VERIFIED_INTERNAL | да | 15 уникальных IFC (IFC2X3). 4 IFC в unpack — копии, не новый объём. |
| A-05 | Версия схемы IFC канала | IFC2X3 | docs/evidence/deep-study-carrier-facts-latest.json ifc_schema; unpack-census ifc_schema | VERIFIED_INTERNAL | да | На канале только IFC2X3. Учебный IFC4 помечать «учебный». |
| A-06 | IFC выше SPF-капа 256 МиБ | 1 | docs/evidence/unpack-census-latest.json ifc_over_spf_cap_count; deep-study pack C AR | VERIFIED_INTERNAL | да | Один IFC выше 256 МиБ SPF: инвентарь, не подъём капа. |
| A-07 | Объём комплекта в байтах/ГиБ | NO_DATA in git; tracker «43 ГБ» is the assigned task title, not this measurement | docs/evidence/unpack-census-2026-08.md claim_boundary; DATA_STATEMENT_2026_08.md §2 | NO_DATA | нет | несжатый объём в git не публикуем |
| A-08 | Пакет обработан (processed) | false | docs/evidence/unpack-census-latest.json processed; domain/finding_volume.py is_pack_processed | VERIFIED_INTERNAL | да | Пакет не обработан. Инвентарь носителей, не акт прогона. |
| A-09 | Публикуемое число находок на канале | 0 | backend/src/aerobim/domain/finding_volume.py publishable_finding_count; SIG01_CHANNEL_TRIAGE_2026_08.md | VERIFIED_INTERNAL | да | Публикуемых находок на канале: 0. Фраза: объём находок получен. |
| A-10 | Сырой total / классы находок канала (штуки) | NO_DATA in git (OA-9; totals stay .local) | docs/quality/FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md; SIG01_CHANNEL_TRIAGE_2026_08.md Channel totals stay .local | NO_DATA | нет | сырой total канала не в git |
| A-11 | Лицензированная фраза SIG-01 | объём находок на канале получен | backend/src/aerobim/domain/finding_volume.py REPORT_PHRASE | VERIFIED_INTERNAL | да | Объём находок на канале получен. Это не список дефектов. |
| A-12 | Пример «геометрия» на канале как дефект заказчика | NO_DATA; 837 IfcClash is open IFC-Bench duplex, not the channel | docs/evidence/federated-clash-duplex-2026-08.json clash_count; closes_rt003=false | SYNTHETIC | да | 837 пересечений — открытый duplex, не АР↔ИОС канала. |
| A-13 | Пример «атрибут» на носителе канала | Wall FireRating filled class EI 45 (pack A); unsigned demo expected REI60; not SP fail | docs/evidence/deep-study-carrier-facts-2026-08.md FireRating; IUA CH-09; FINDING_VOLUME_CLAIM_BOUNDARY | VERIFIED_INTERNAL | да | Наблюдаемый FireRating стен EI 45. Это не провал СП. |
| A-14 | Пример «состав комплекта» | Native RVT/NWD/DWG/LIRA unread (fail-closed); 1 IFC over SPF cap | docs/tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md; unpack-census parse_rvt_nwd_lira=false | VERIFIED_INTERNAL | да | RVT/NWD/DWG/LIRA — отказ. Читаем IFC и PDF/A. |
| A-15 | Пример шва модель↔ведомость↔ТЗ как published finding | IfcSpace QTO NetFloorArea=0 on all packs; sheet-vs-IFC area not a published customer finding | docs/evidence/deep-study-carrier-facts-2026-08.md NetFloorArea; space_area_from_geometry=not_implemented | VERIFIED_INTERNAL | да | 16152 IfcSpace; NetFloorArea в QTO = 0. Площадь по геометрии нет. |
| A-16 | Доля находок с нормой + этажом/осью + GUID (канал) | NO_DATA (channel totals not in git; triad engine exists on fixtures) | docs/quality/FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md OA-9; domain/remark_completeness.py; TZ_COMPLIANCE_MATRIX §3.4 | NO_DATA | нет | доля триады на канале в git отсутствует |
| A-17 | Стена FireRating заполнена (пакет A, покрытие) | 3538 of 62033 walls (5.7%), class EI 45 only | docs/evidence/deep-study-carrier-facts-2026-08.md table IFC pack A | VERIFIED_INTERNAL | нет | покрытие FireRating не на слайд как точность |
| A-18 | Оси IfcGrid по пакетам | 0 / 13 / 53 (A / B AR / C AR) | docs/evidence/deep-study-carrier-facts-2026-08.md IfcGrid; domain/deep_study_facts.py | VERIFIED_INTERNAL | да | IfcGrid: 0 / 13 / 53. Нулевые оси только у EDM-экспорта. |
| A-19 | IfcReinforcingBar / воздуховоды-трубы-кабели в IFC канала | 0 / 0 | docs/evidence/deep-study-carrier-facts-2026-08.md IfcReinforcingBar; duct/pipe/cable | VERIFIED_INTERNAL | да | Арматура в IFC = 0. Сети в IFC = 0. Не заявлять проверку ИОС. |
| A-20 | NWD-федерации как носители | 3 present; native NWD fail-closed | docs/evidence/deep-study-carrier-facts-2026-08.md NWD federations; NATIVE_AUTODESK_INGEST_BOUNDARY | VERIFIED_INTERNAL | да | Три NWD как носители. Нативно не читаем. |
| A-21 | Wall-clock прогона канала (пакет / полное / CPU/RAM / профиль) | NO_DATA in git; tool-side elapsed measured locally; totals .local until OA-9 | docs/evidence/deep-study-carrier-facts-2026-08.md §Дополнения 31.08–03.09 Lab journal; TRACKER_EIGHT_TASKS | NO_DATA | нет | время канала в git нет |
| A-22 | Репетиция IFC 26.08 (fixture IDS на локальной копии) | 14 IFC analysed under cap; 1 over cap inventory-only; detected_count=0; not ingested in git | audit/evidence/customer-intake-gate.json owner_machine_engine_rehearsal; TZ_SEAM_COVERAGE_MAP_2026_08.md | VERIFIED_INTERNAL | да | 14 IFC под капом, учебные IDS. detected_count=0. Не акт заказчика. |
| A-23 | SIG-01 rerun 31.08 | EXECUTED locally after ALL/GUID/Qto fixes; pack_volume_not_accuracy; totals not in git | docs/evidence/deep-study-carrier-facts-2026-08.md SIG-01 channel rerun EXECUTED; SIG01_CHANNEL_TRIAGE | VERIFIED_INTERNAL | да | Локальный перегон SIG-01 был. Сырой total не публикуем. |
| A-24 | Повторы канала бит-в-бит | NO_DATA for the NDA pack; DeterminismGate covers verdict on fixtures | docs/architecture/ADR-001-verdict-ownership-2026.md; TZ v2 ТР-27; no channel hash in git | NO_DATA | нет | бит-в-бит канала не доказан в git |
| A-25 | Акт/протокол прогона канала | NO_DATA; M7 site act BLOCKED_CUSTOMER_DATA | docs/partners/MIK_PILOT_COMPLIANCE_2026.md M7; customer-intake-gate.json nda_signed=false | NO_DATA | нет | подписанного акта прогона нет |
| A-26 | Форматы обёртки (suffix/magic, не «прогнаны») | IFC 15, PDF 1208, DWG 551, DXF 67, RVT 27, Navis 21, .lir 20+21 tilde | docs/evidence/unpack-census-latest.json wrapper_*_count | VERIFIED_INTERNAL | нет | поформатный census не «пакет обработан» |
| A-27 | Отчёты слотов канала в git | HTML/JSON/PDF/BCF stay .local-only (OA-9/OA-22); git does not host or send customer reports; processed remains false | docs/quality/FINDING_VOLUME_CLAIM_BOUNDARY_2026_08.md OA-9 | VERIFIED_INTERNAL | да | Отчёты слотов — только .local. Git не шлёт. Пакет не processed. |
| B-R1 | R1 2D drawings | closed_by_code (PDF/OCR/overlay) on fixtures; customer PDFs inventoried, not drawing findings | docs/techlab-alignment-2026.md §3 R1; TZ_COMPLIANCE_MATRIX §3.1; CHANNEL_LOCAL_MAX_PASS PDF HITL | VERIFIED_INTERNAL | да | Чертежи: учебный оверлей. Листы канала — очередь HITL, не CV. |
| B-R2 | R2 BIM models | closed_by_code IFC+IDS; customer: 15 IFC2X3 inventory, processed=false | docs/techlab-alignment-2026.md R2; deep-study-carrier-facts-2026-08.md | VERIFIED_INTERNAL | да | BIM: IFC+IDS в коде. Канал — инвентарь IFC2X3, не акт. |
| B-R3 | R3 TZ + calculations | closed_by_code on fixtures; customer .lir unread (native_lir=not_implemented) | docs/techlab-alignment-2026.md R3; CALCULATION_COMPARE_FOUR_CHECKS; unpack-census parse_rvt_nwd_lira | VERIFIED_INTERNAL | да | Сверка заявленных величин — да. Решатель ЛИРА — нет. |
| B-R4 | R4 Match docs + norms | artifact: public IDS (50 files / 847 specs); customer_approved IDS=false | docs/techlab-alignment-2026.md R4; demo_day_speech_lock PUBLIC_IDS_*; deep-study customer_approved_ids | VERIFIED_INTERNAL | да | Публичные IDS: 50 файлов, 847 spec. Подписи заказчика канала нет. |
| B-R5 | R5 Collisions / clashes | code+planted/open rehearsal; customer MEP IFC entities=0; 837≠channel | docs/techlab-alignment-2026.md R5; federated-clash-duplex-2026-08.json; deep-study mep_duct_pipe_cable_count | SYNTHETIC | да | Clash движка — на фикстуре и открытом duplex. Не их АР↔ИОС. |
| B-R6 | R6 Calculation / dimension / area errors | code on fixtures; channel NetFloorArea=0; geometry area not_implemented | docs/techlab-alignment-2026.md R6; system_capabilities space_area_from_geometry | VERIFIED_INTERNAL | да | Площади канала: QTO пуст. Геометрию IfcSpace не считаем. |
| B-R7 | R7 Logic / missing elements | closed_by_code IDS exists/bounds; channel unsigned ALL is coverage_map, not defects | docs/techlab-alignment-2026.md R7; FINDING_VOLUME_CLAIM_BOUNDARY target_ref=ALL | VERIFIED_INTERNAL | да | IDS exists работает. Unsigned ALL на канале — покрытие, не дефект. |
| B-R8 | R8 Highlight problem zones | closed_by_code+artifact on fixture overlay; not customer sheets | docs/techlab-alignment-2026.md R8; docs/evidence/drawing-overlay-smoke-2026-08/README.md | SYNTHETIC | да | Подсветка зоны — учебный оверлей, не лист заказчика. |
| B-R9 | R9 Prioritize remarks | closed_by_code AEROBIM_PRIORITY_PROFILE=customer; not measured on customer queue | docs/techlab-alignment-2026.md R9; domain/review_priority.py | VERIFIED_INTERNAL | нет | профиль приоритета в коде; замер очереди заказчика нет |
| B-R10 | R10 Designer comments | closed_by_code RU/EN templates + HITL edit + BCF ZIP; no customer HITL log in git | docs/techlab-alignment-2026.md R10; TemplateRemarkGenerator; ADR-001 | VERIFIED_INTERNAL | да | Черновик замечания: норма, этаж/ось, GUID. Пишет не LLM. |
| B-R11 | R11 Faster review | target_metric; fixture SLA only | docs/techlab-alignment-2026.md R11; audit/evidence/sla-fixture-honesty-2026-07-17.json | SYNTHETIC | нет | ускорение ревью на комплекте заказчика не замерено |
| B-R12 | R12 Expert remains accountable | closed_by_artifact ADR-001 DeterminismGate; independent_human_raters=0 | docs/architecture/ADR-001-verdict-ownership-2026.md; accuracy-answer-2026-09.json independent_human_raters | VERIFIED_INTERNAL | да | Вердикт пишет движок. Эксперт подтверждает находки. LLM не rater. |
| B-R13 | R13 MVP + visualization + reports | closed_by_code API/HTML/JSON/BCF + review shell (eight IA screens partial) | docs/techlab-alignment-2026.md R13; UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md | VERIFIED_INTERNAL | да | Отчёт JSON/HTML/BCF есть. Оболочка — review shell, не сданное РМ. |
| B-R14 | R14 Typical error catalog | artifact scaffold ≥20; customer_confirmed_patterns=0 | docs/techlab-alignment-2026.md R14; samples/benchmarks/typical-errors-catalog.json; accuracy-answer typical_error_class_coverage | SYNTHETIC | да | Каталог ≥20 на шаблоне. Подтверждённых заказчиком: 0. |
| B-R15 | R15 ≤30 min package SLA | target_metric; fixture 576.87 ms; customer pack NO_DATA; 25.08 answers do not confirm the criterion | docs/techlab-alignment-2026.md R15; sla-fixture-honesty-2026-07-17.json; TZ_COMPLIANCE_MATRIX §6 | SYNTHETIC | да | 30 минут — цель ТЗ. На комплекте заказчика не замерено. |
| B-IDS-MOEXP | IDS Мособлгосэкспертизы (не профиль назначающей стороны) | 24 files / 389 specifications | backend/src/aerobim/domain/demo_day_speech_lock.py MOEXP_IDS_*; docs/evidence (norm-pack-moexp-coverage) | VERIFIED_INTERNAL | да | 389 спецификаций — 24 файла МОГЭ, не все 50 публичных IDS. |
| C-01 | CI backend tests passed / collected / failed / skipped | 3177 / 3197 / 0 / 20 | docs/evidence/runtime-baseline-latest.json backend.*; attestation.attested_by=ci | VERIFIED_INTERNAL | да | CI: бэкенд 3177 из 3197, 0 упало, 20 skipped. |
| C-02 | CI frontend tests passed / failed | 387 / 0 | docs/evidence/runtime-baseline-latest.json frontend | VERIFIED_INTERNAL | да | CI: фронт 387 / 0. Только из runtime-baseline. |
| C-03 | Quality gates ruff/mypy/pytest/vitest/build | PASS / PASS / PASS / PASS / PASS | docs/evidence/runtime-baseline-latest.json quality_gates | VERIFIED_INTERNAL | да | Пять ворот качества: PASS. Числа файлов mypy в пине нет. |
| C-04 | attested_by / publishable / corpus_kind | ci / true / fixture | docs/evidence/runtime-baseline-latest.json attestation.attested_by, publishable, corpus_kind | VERIFIED_INTERNAL | да | Пин attested_by=ci. Локальный pytest на слайд не ставить. |
| C-05 | Architecture inventory | 48 protocols / 75 adapters / 63 DI tokens | docs/evidence/runtime-baseline-latest.json architecture_inventory | VERIFIED_INTERNAL | нет | инвентарь архитектуры не критерий жюри |
| C-06 | Fixture extraction macro_f1 | 0.86 (fixture; not product accuracy) | docs/evidence/runtime-baseline-latest.json metrics.extraction_macro_f1; accuracy-answer-2026-09.json claim_boundary | SYNTHETIC | да | F1 0,86 — учебный корпус извлечения, не точность продукта. |
| C-07 | Fixture AABB clash P/R | precision=1.0 recall=1.0 n=6; Wilson 95% lower ≈0.61; publishable=false | docs/evidence/accuracy-answer-2026-09.json rows fixture_aabb_clash; clash-measurement-slice-2026-08 | SYNTHETIC | нет | n=6 не exhibit; нижняя Уилсона ≈0,61 |
| C-08 | Defect-injection recall (mini-IFC) | 1/8=0.125; Wilson 95% [0.022; 0.471]; lower <0.50; publishable=false | docs/evidence/accuracy-answer-2026-09.json defect_injection_recall; DEFECT_INJECTION_RECALL_RUN_2026_09.md | SYNTHETIC | нет | нижняя Уилсона 0,022 < 0,50 — не на слайд |
| C-09 | Defect-injection recall (channel IFC mutations) | 0/6 killed; Wilson lower 0.000; synthetic_only | docs/evidence/DEFECT_INJECTION_RECALL_RUN_2026_09.md; TIER0_INDEX row E2 | SYNTHETIC | нет | 0/6 на канальном IFC — синтетика, не recall заказчика |
| C-10 | AECV object counting | macro_extended=0.4325; n_field_scores_extended=585; is_f1=false; publishable=false | docs/evidence/accuracy-answer-2026-09.json aecv_object_counting; aecv-bench-eval-latest.json | SYNTHETIC | да | 0,4325 — macro_extended открытого бенча, не F1. |
| C-11 | Dual-rater simulation | κ=0.705 n=28; independent_human_raters=0; labelled=simulation | docs/evidence/accuracy-answer-2026-09.json dual_rater_simulation; rt001-dual-rater-simulation-2026-09.json | SYNTHETIC | да | κ≈0,70 — симуляция протокола. Живых разметчиков: 0. |
| C-12 | Experiment B KR coverage | 4/24 ≈16.7%; coverage_map_only; not product recall | docs/evidence/weekly-eng-status-latest.json coverage_map; EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md | SYNTHETIC | да | КР ≈16,7% (4/24) — карта покрытия, не recall. |
| C-13 | Pilot n (interval width vs power) | recommended_n=111; power_design n=62; interim precision 0.60 | docs/evidence/weekly-eng-status-latest.json adjudication_corpus_plan | VERIFIED_INTERNAL | да | Размер выборки пилота n=111. 62 — только мощность. |
| C-14 | PrecisionClaim.publishable | false (corpus_kind≠customer; <2 human adjudicators) | docs/evidence/accuracy-answer-2026-09.json precision_claim_publishable; customer-intake-gate.json | VERIFIED_INTERNAL | да | Точность продукта не публикуется. Гейт PrecisionClaim закрыт. |
| C-15 | TRL self-assess / TRL 5 claimed | 4 / False | docs/quality/TRL_GOST_R_58048_SELF_ASSESS_2026.md; domain/mik_commission_scoring.py | VERIFIED_INTERNAL | да | Самооценка ГОСТ Р 58048 — TRL 4. Уровень 5 не заявляется. |
| C-16 | Non-claims in pilot-claim-boundary | 40 numbered items (§Non-claims 1–40) | docs/pilot-claim-boundary-2026.md §Non-claims; CLAIMS_LOCK_2026_07_17.md Pass 14 | VERIFIED_INTERNAL | нет | полный список non-claims — в границе заявлений, не на обложку |
| C-17 | Open duplex IfcClash count | 837 | docs/evidence/federated-clash-duplex-2026-08.json runs[0].clash_count; elapsed_ms=5959.65 | SYNTHETIC | да | 837 — открытый duplex IFC-Bench, 6 с. Не канал заказчика. |
| D-01 | Команда офлайн-развёртывания | python -m aerobim.tools.offline_bundle closed-contour --smoke (from backend/) | docs/offline-deployment-2026.md; audit/evidence/offline-closed-contour-docker-2026-08.json | VERIFIED_INTERNAL | да | Офлайн: Docker load + --network none. Bare-metal — вне скоупа. |
| D-02 | Время до первого прогона (минуты) | NO_DATA; smoke PASS 2026-08-08, wall-clock minutes not recorded | docs/evidence/offline-closed-contour-docker-2026-08.md; offline-closed-contour-docker-2026-08.json | NO_DATA | нет | минут до первого прогона в git нет |
| D-03 | Образ офлайн-бандла | tar 864927744 bytes; tag aerobim-backend:offline-bundle; date 2026-08-08 | docs/evidence/offline-closed-contour-docker-2026-08.md table Image | VERIFIED_INTERNAL | нет | размер tar не SLA |
| D-04 | Ядра CPU / требуемый RAM стенда | NO_DATA (required cores); RAM planning multiplier 10 is literature not appointing-party RSS | docs/quality/IFC_ANALYZE_VS_INGEST_CAP_2026_08.md; KT3_JURY_FAQ RSS на файле заказчика не замерен | NO_DATA | нет | RSS на файле заказчика не замерен |
| D-05 | GPU | not required for deterministic analyze; optional YOLO/VLM advisory | docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md GPU optional; sla-benchmark-protocol-2026.md | VERIFIED_INTERNAL | да | GPU для детерминированного прогона не нужен. |
| D-06 | Интернет на стенде | not required for Docker air-gap smoke (--network none); LLM/VLM default deny | docs/offline-deployment-2026.md smoke path; BUILD_WITHOUT_EXTERNAL_MODELS_2026.md | VERIFIED_INTERNAL | да | Закрытый контур: Docker без сети. Облачный LLM по умолчанию выключен. |
| D-07 | Вход / выход | in: IFC, PDF, Office OOXML; native RVT/NWD/DWG/.lir fail-closed. out: JSON, HTML, PDF, BCF ZIP 2.1/3.0 | README.md Limits; TZ_COMPLIANCE_MATRIX §4; bcf-structural-handoff-2026-07-25.json | VERIFIED_INTERNAL | да | Вход: IFC+PDF/A+Office. Выход: JSON, HTML, BCF ZIP. |
| D-08 | Лимиты объёмов | SPF 256 MiB; model ingest/analyze 1.5 GB RocksDB on customer_pilot/production; Office 500 MB | README.md AEROBIM_MAX_IFC_BYTES / MAX_MODEL_BYTES / MAX_OFFICE_BYTES; IFC_ANALYZE_VS_INGEST_CAP | VERIFIED_INTERNAL | да | Капы: 256 МиБ SPF, 1,5 ГБ диск, 500 МБ Office. |
| D-09 | Ключевые эндпоинты | POST /v1/analyze/project-package, POST /v1/uploads, GET /v1/system/capabilities, export HTML/PDF/BCF, review-events, review-kpi | README.md API table; presentation/http/routes | VERIFIED_INTERNAL | нет | карта API не слайд эффекта |
| D-10 | BCF 2.1 / 3.0 ZIP | T1 structural OK (XSD passed, 2 topics each); cde_import=NOT_VERIFIED | audit/evidence/bcf-structural-handoff-2026-07-25.json; docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md | VERIFIED_INTERNAL | да | BCF ZIP 2.1 и 3.0 — структура T1. Импорт в СОД не доказан. |
| D-11 | BCF API 3.0 push | foundation endpoint POST .../export/bcf-api/push; T2 still NOT_VERIFIED | docs/pilot-claim-boundary-2026.md BCF API 3.0; tests/test_wave2_cde_integration.py; CDE_IMPORT | NOT_VERIFIED | да | Push BCF API есть как фундамент. Журнала импорта в СОД нет. |
| D-12 | SSO / OIDC BFF | default GET /v1/auth/bff = 501_NOT_IMPLEMENTED; JWT validator exists; full SSO post-pilot | docs/pilot-claim-boundary-2026.md Full OIDC; domain/demo_day_speech_lock.py AUTH_BFF_DEFAULT | VERIFIED_INTERNAL | да | GET /v1/auth/bff по умолчанию 501. SSO на их IdP не живой. |
| D-13 | ACL: чужой отчёт | deny → 404 (not 403) | docs/pilot-claim-boundary-2026.md Cross-tenant ACL; tests/test_mutation_kills_http_context.py test_cross_tenant_job_access_is_404; test_oidc_bff_hitl_rbac.py | VERIFIED_INTERNAL | да | Чужой объект — 404, не 403. Перечень не светим. |
| D-14 | SSRF на исходящих URL | JWKS / bSI / OpenCDE URL guard; tests block RFC1918 and loopback | docs/pilot-claim-boundary-2026.md Outbound SSRF; tests/test_outbound_guard_invariant.py; test_defensive_engineering_pass_2026_08.py; test_oidc_bff_phase3.py | VERIFIED_INTERNAL | да | Исходящие URL режутся. Приватные адреса не ходят. |
| D-15 | Сервисный токен не подписывает вердикт HITL | is_service_token cannot append accepted/rejected; even when role gate off | domain/object_acl.py principal_may_append_hitl_event; tests/test_rt_wave3_remediation_2026_08.py HitlRbacTests | VERIFIED_INTERNAL | да | Общий bearer не подписывает accept/reject. Нужен эксперт. |
| D-16 | cde_import machine status | NOT_VERIFIED | audit/evidence/bcf-structural-handoff-2026-07-25.json cde_import.status; BCF_EVIDENCE_LADDER T2 | NOT_VERIFIED | да | Статус импорта в СОД: NOT_VERIFIED. |
| E-01 | Допущение E1 (дословно) | Один лишний круг согласования РД на типовой секции существует | docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E1 | NEEDS_CUSTOMER | да | E1: лишний круг на типовой секции — их факт, не наш замер. |
| E-02 | Допущение E2 (дословно) | Длительность круга — **N рабочих дней** (N задаёт заказчик) | docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E2 | NEEDS_CUSTOMER | да | E2: длительность круга задаёт заказчик. Не спорить «у нас 30 мин». |
| E-03 | Допущение E3 (дословно) | Стоимость дня комплекта — их внутренняя цифра (не публикуем) | docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E3 | NEEDS_CUSTOMER | нет | рубли дня комплекта не публикуем |
| E-04 | Допущение E4 (дословно) | Система снимает **не больше одного** круга на эталонном корпусе после канонической пары ревизий | docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E4 | NEEDS_CUSTOMER | да | E4: не больше одного круга и только на эталоне с парой ревизий. |
| E-05 | Допущение E5 (дословно) | Повторяемость на типовой секции > единичный дефект | docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md table E5 | NEEDS_CUSTOMER | да | E5: эффект на типовой секции, не разовый дефект. |
| E-06 | Что система считает сама (эффект) | HITL review-kpi: opened/triaged/accepted/rejected/acceptance_rate/avg_latency_ms — not CDE cycle days, not pre-expertise share, not re-entry | backend/src/aerobim/application/services/review_kpi.py summarize_review_events; GET /v1/reports/{id}/review-kpi; README.md | VERIFIED_INTERNAL | да | Экран «Эффект» — журнал HITL. Это не дни цикла СОД. |
| E-07 | Число 1 от заказчика канала: календарные дни круга согласования РД | NO_DATA; who: technological-customer director / PMO of the section | docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md E2; DEMO_DAY_SPEECH_LOCK three numbers | NEEDS_CUSTOMER | нет | запросить письмом |
| E-08 | Число 2 от заказчика канала: часы эксперта «до» на эталонном комплекте | NO_DATA; t_manual_s is null; A1–A8 empty; who: chief expert / project office | docs/partners/BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md; ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md | NEEDS_CUSTOMER | нет | запросить письмом |
| E-09 | Число 3 от заказчика канала: сколько лишних кругов они считают нормой на типовой секции | NO_DATA; who: information-modelling lead (typification) + tech-customer | docs/partners/CUSTOMER_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md E1 E5 | NEEDS_CUSTOMER | нет | запросить письмом |
| E-10 | Baseline «до» в репозитории | NO_DATA partner hours; lab t_manual_s=null; fixture SLA 0.0096 min is not baseline-before | docs/evidence/deep-study-carrier-facts-2026-08.md t_manual_s is null; sla-fixture-honesty-2026-07-17.json claim_level=fixture_only | NO_DATA | да | Замера «до» на часах партнёра в git нет. |
| F-01 | Лицензия собственного кода | MIT; third-party under own licenses (IfcOpenShell LGPL; PyMuPDF optional AGPL extra not in runtime lock) | LICENSE; docs/license-policy-2026.md; audit/dependency_license_inventory.json | VERIFIED_INTERNAL | да | MIT — свой код. Сторонние компоненты — свои лицензии. |
| F-02 | ADR | ADR-001 verdict; ADR-002 open-core; ADR-003 DWG/ODA; ADR-004 prize IP; ADR-005 customer data | docs/architecture/ADR-001-verdict-ownership-2026.md … ADR-005-customer-data-handling-2026.md | VERIFIED_INTERNAL | да | Пять ADR. Вердикт — ADR-001. Данные канала — ADR-005. |
| F-03 | Протокол приёмочных испытаний (подписанный) | NO_DATA; protocol drafts exist, site act does not | docs/partners/PROTOCOL_QUALITY_ACCEPTANCE_TASK07_2026_08.md claim_level=protocol_only; MIK_PILOT_COMPLIANCE M6/M7 | NO_DATA | нет | подписанного протокола испытаний нет |
| F-04 | Методика замера | QUALITY_MEASUREMENT_PROTOCOL_2026_08.md + Wilson planner n=111; protocol_only | docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md; weekly-eng-status-latest.json recommended_n | VERIFIED_INTERNAL | да | Методика замера есть. Замера на их корпусе нет. |
| F-05 | Инструкция офлайн-сборки | docs/offline-deployment-2026.md + INSTALL_OFFLINE.md in bundle | docs/offline-deployment-2026.md | VERIFIED_INTERNAL | да | Офлайн-сборка: Docker-бандл. Без Docker не обещаем. |
| F-06 | Передача прав / IP приза | ADR-004 fork path; LICENSE unchanged; п.6.3 prize IP not closed | docs/architecture/ADR-004-prize-ip-mit-fork-2026.md; docs/quality/KT3_DELIVERY_BOM_2026_08.md | NOT_VERIFIED | нет | п.6.3 передачи прав не закрыт |
| F-07 | Что показать жюри без NDA | git fixtures + run_kt3_jury; public IDS; CI pin; speech lock; not NDA tree, not .local totals, not JK names | docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md; docs/evidence/DATA_STATEMENT_2026_08.md; JURY_SURFACES | VERIFIED_INTERNAL | да | Жюри: учебный CLI из git. Файлов заказчика в репозитории нет. |
| F-08 | customer_go / Checkpoint | customer_go=false; CHECKPOINT=GO (regulatory_measurement_mvp) | docs/pilot-claim-boundary-2026.md; domain/checkpoint.py; AGENTS.md | VERIFIED_INTERNAL | да | Checkpoint GO — измерительный MVP. customer_go по-прежнему false. |

## Non-claims (explicit boundaries)

1. AeroBIM is **decision-support** for engineering QA, not a licensed-engineer replacement.
2. AeroBIM does **not** assert full regulatory code compliance across all document types.
3. AeroBIM does **not** claim to outperform Solibri globally — only a bounded open pilot path.
4. Non-deterministic text extraction is **not** used for pilot sign-off; deterministic regex path meets F1 gates in CI.
5. Optional LLM **IDS assist** (if enabled later) is **advisory only** and must never affect `summary.passed` without human-in-the-loop.
6. TZ wording «точность >90%» is an **evaluation target**, not a verified product claim, until precision/recall is published from a labeled customer corpus.
7. AeroBIM does **not** claim that OCR, CV, or VLMs “read drawings like a licensed engineer” (see Claims Lock / this claim boundary).
8. AeroBIM does **not** claim Experiment B coverage percentages (e.g. KR **≈16.7%** of n=24 open-source remarks) as product detection rate on a customer corpus — they are **coverage-map** measurements with explicit out-of-scope classes; see [`evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md`](../evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md).
9. AeroBIM does **not** claim IfcLLM / GraphRAG product capability. I9 is an **advisory scaffold** (port + allowlisted query + fixture QA); multi-hop GraphRAG is unshipped.
10. AeroBIM does **not** claim Hybrid AI is in the verdict path, nor that masking guarantees anonymity — WP-02 wires `HybridRouteGate` as an **advisory pre-gate** only (verdict-neutral, OFF==ON; blocked → no advisory observation).
11. AeroBIM does **not** replace 10D, Tangl, Renga, CDE, or the expert. First sell is a white-box IFC+IDS evidence layer; `customer_go` stays **false** until residual volumes close. Product Checkpoint **GO** is the regulatory-measurement MVP, not customer sign-off.
12. The SPb GAU CGE profile (`samples/profiles/spb-cge/`) is a published rule set (OFFICIAL_PUBLISHED), not a customer-signed acceptance profile. It does **not** close RT-001 or RT-002 and is not an expertise verdict.
13. AeroBIM does **not** SPF-open a 1.5 GB IFC and does **not** treat 1.5 GB as WASM capability, and does **not** treat «5–10 packs/day» as a published SLA.
14. After the 25.08 questionnaire, AeroBIM does **not** say the customer sent no data. The channel is received; a hashed pack is **not** in git; RT-001 stays OPEN. HTTPS / closed-cloud storage is a **stated** target — browser OIDC BFF remains `NOT_IMPLEMENTED`.
15. AeroBIM does **not** treat xlsx/docx declared-field **MATCH** as `calculation_correctness` or a LIRA solver. Native `.lir` is not parsed. PDF table compare stays **fragile**.
16. AeroBIM does **not** treat the IFC streaming / disk R-tree **design** as shipped, and does **not** raise the default **SPF** analyze cap from **256 MiB** because ingest allows 1.5 GB (that path is RocksDB).
17. AeroBIM does **not** treat HTTP upload of `.lir`/`.spr` as a silent skip or a solver path. The closed reason is explicit; ZIP members are rejected the same way as native Autodesk.
18. AeroBIM does **not** treat a JSON dump of `IfcSpatialIndex` as a disk R-tree or a streaming parser, and does **not** wire that dump into analyze.
19. The two numeric TZ criteria (clash recall >90%, pack-check time) are **not customer-confirmed**: the 25.08 answers document never mentions 90%, SLA, or time. AeroBIM neither claims them nor accepts them as agreed until a measurement protocol (golden remark set, corpus size, time endpoints) is answered in writing.
20. The internal-standards and BIM-regulations list was **issued** on 25.08 (two links inside answer 1.2.1 to internal CDE project folders); the norm-pack blocker is **access to the issued material**, not missing data — the ask is to publish the two folders the same way as the dataset. Direct CDE API integration is **not** a customer requirement (п. 2.2.2: file import/export via web UI suffices); it stays an optional differentiator.
21. Typical-node checks are **not** IFC-ready: п. 1.2.3 places the node library as PDF/DWG in the same closed 1.2.1 folders; native DWG stays unread. Cloud is allowed (п. 3.1.1); the requirement is **per-project isolation** of stored data, not on-prem deploy and not “HTTPS equals isolation”. Horizontal scale is an architecture point for later, **not** an MVP deliverable and **not** a load figure at defense (п. 3.2.2).
22. The depersonalization + NDA ask to organizers is **the customer's own clause** (п. 3.1.2), not extra caution from the team. AeroBIM does **not** treat the delivered channel as a depersonalized NDA pack.
23. AeroBIM is an **engineering-compare engine** with a measurement protocol, not a documentation platform and not a replacement for the customer's CDE or BIM-data stack. Version overlay of RD packs is **not** a differentiator (the customer already ships it). TR-67 is spec-volume vs drawing/BIM, **not** model-to-estimate quantities.
24. Benefit speech uses expert-hours per pack, share of remarks caught before production issue, and re-entry count — **not** «innovation» and **not** a multiple of EBITDA. The citation linter (`lint_citation_twins`) is shown as source discipline (fabricated DOI / same-article year twins), not as product accuracy.
25. Catalog questionnaire answers, demo video frames, and slides are **publication** (same gate as git). AeroBIM does **not** treat machine-readable information requirements or RD version overlay as differentiators, and does **not** transfer a competitor's published figure as our metric. Self-assessment against GOST R 72514-2026 (ISO/IEC 42005:2025) is **not** a certification. Mapping onto GOST R 72515-2026 (ISO/IEC 12792:2025) is **not** a conformity declaration.
26. Attributed TechLab **selection** weights (K1=40 / prize floor 50 / arithmetic **mean**) are **not** a predicted AeroBIM score. Application roster is the K1 object; oral advisors are not. MinTsifry bill 166424 is **not** in-force law.
27. Regulation Appendix 3 (final criteria) is **not in git**. B1–B5 in the scoring module are an owner briefing, not that appendix. Final aggregation in the order is a **sum**. Pytest and the fixture SLA pin are **not** Partner validation metrics. Empty A1–A8 hours are required until a partner baseline exists. The vitrine heading 07 is **not** Appendix 4 task №6 (commission №7); do not fight the organizer site.
28. The criterion→git evidence map and the national AI GOST stack are **findability**, not a predicted prize-clearing total. Mapping onto GOST R ISO/IEC 42001-2024 is **not** a certified AI management system.
29. i.moscow/pilot (city grant, legal entity, TRL-ish 6) is **not** the TechLab paid-pilot prize. The K1 role-matrix template in git has empty person cells; the scored roster is the i.moscow application.
30. Ten named people are **not** required for K1 (LETI: 1–10; two competency classes). GOST R 58048 self-assessment is **TRL 4 (lab)**, not TRL 5 and not an independent readiness exam. System A K3 is partner-fit, **not** System B B2 metrics.
31. Russian BIM TAM (GidMarket 10.1 bn RUB, 2022) is **not** AeroBIM SAM. A published analog −72.1% labor cut is **not** our effect. PNST 841-2023 mapping is **not** a SQuaRE certificate. Another MIK product’s «≥500M market» packaging is **not** this TechLab K4.
32. The 16+36.6=52.6 band identity is **not** a predicted AeroBIM total. The public task-page sponsor quote is **not** the attested commission chair. SPbPU 25.1 bn RUB by 2030 is **not** our revenue. The i.moscow paste file is **not** a scored roster.
33. Partner 1H2026 IFRS (revenue −31 %, loss 22.3 bn RUB) is **context**, not an AeroBIM saving. Stand-alone RAS +31 % revenue is **not** group IFRS. K4 does **not** ask CAPEX.
34. Four catalog cards are **not** all applicants. Neighbor-task «46 teams» is a different Partner. Peer catalog claims (15 pilots, 600+ norms, live customer prototype) are **not** audited public fact.
35. Publishable CI counts come only from `docs/evidence/runtime-baseline-latest.json`. Historical blocker-file figures (SHA `019962141606`) are a prior pin, not the current SSOT.
36. Native DWG/RVT/NWD are **not implemented**. Default IFC **SPF** cap stays **256 MiB**. 1.5 GB is ingest + RocksDB analyze, not SPF RAM and not WASM. Experiment B KR headline is **≈16.7 %** (4/24); **≈8.3 %** is the Task-3 waypoint, not the current detected share.
37. Closed Autodesk CAD and `.lir` are **not** an ingest product. KT#3 exchange is IFC + PDF/A. Stock Navisworks does not write IFC. ODA trial is measurement, not a product ([`quality/FORMAT_INGEST_TRIAGE_2026_09.md`](FORMAT_INGEST_TRIAGE_2026_09.md)).
38. Strategy Partners / AO SPG August 2026 notes are **attributed speech**, not SAM and not a digital-twin / FM product. The 8-page construction cut supports machine-readable PD/RD; the 60-page property-IT cut is adjacent. PDFs stay off git. The owner pin is not a TIER0 exhibit.
39. The browser surface is a **review shell**, not a delivered full-cycle expert workplace. UI does **not** write `summary.passed`. Native RVT/NWD/DWG stay fail-closed. 30 minutes / 5–10 packs per day are TZ goals, not measured SLA. No live 10D/Tangl connector ([`quality/UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md`](UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md)).
40. `POST /v1/demo/seed-fixture` is **development-only** and copies git `samples/` walls+IDS, not a customer pack. Two fire-rating fixture findings are **not** product accuracy. The published OpenAPI contract does **not** list the seed. UI CSS does **not** load Google Fonts. The sitting-member KT#3 laptop track stays `run_kt3_jury`. The TZ compliance matrix Web UI row is **partial**, not done.

## 2) ПРОТИВОРЕЧИЯ

| ID | Где | Суть |
|---|---|---|
| X-01 | CLAIMS_LOCK_2026_07_17.md header vs live checkpoint | Header still says Checkpoint verdict NO_GO; live product checkpoint is GO since 2026-09-04. Treat the July file as HISTORICAL_PIN plus Pass 14 wording, not as current SSOT. |
| X-02 | weekly-eng-status-latest.json checkpoint vs TIER0 | CLOSED 2026-09-15: weekly pin regenerated via export_weekly_eng_status; checkpoint GO; runtime_baseline SHA is the attested pin 139896709507. The 2026-08-17 NO_GO snapshot is historical. Do not mix the August file with HEAD. |
| X-03 | techlab-alignment R1–R15 checkmarks vs this pack | Alignment uses ✅ on several rows that this audit marks fixture-only or target_metric (R11/R15 SLA, R5 clash, R14 catalog). Prefer this table’s weaker status. |
| X-04 | Desktop deck 13.09 vs git | Deck (outside git) printed УГТ-5, 837 as partner AR↔MEP, 0.43 as F1, n≥62, KR 17%, 389-in-50, SSO/BCF-ready. Licensed copy is submission/03-presentation/demo_day_slides.md. PPTX itself is still the owner’s file. |
| X-05 | AUDITOR_BRIEF freeze 2026-09-04 vs HEAD docs | Standalone auditor brief is dated 04–08.09 and must not be read as HEAD evidence counts. CI integers live only in runtime-baseline-latest.json. |
| X-06 | System A vs System B weights | Selection 40/20/15/15/10 vs finalist 30/20/20/20/10. Desktop scan 14.09 matches both tables; PDF still not in git. Do not cite as attested_by=ci. |
| X-07 | Intake-gate status vs channel received | customer-intake-gate.json claim_level=not_ready and gates.* = false, but share_received_at=2026-08-25. Do not say «нет данных». Do not say gates are green. |
| X-08 | CLAIMS_LOCK vs live GO formula | Allowed-wording bullet still uses the pre-measurement formula (RF PD+expertise). Residual RT volumes stay OPEN; the product flag is nevertheless GO (measurement MVP). Speak both sentences, never one. |

## 3) ОПАСНЫЕ ВОПРОСЫ

**Q-01. Вы прогнали наш комплект. Сколько дефектов?**
Карта выгрузки снята. Это не акт дефектов объекта. Публикуемых находок как дефектов заказчика: 0. Фраза: объём находок на канале получен.

**Q-02. Какая точность? Вы же писали >90% / 0,43 F1?**
Точность продукта не публикуется. 0,86 F1 — фикстура извлечения. 0,4325 — macro_extended открытого бенча, не F1. n пилота 111.

**Q-03. 837 коллизий АР↔ИОС на наших файлах?**
Нет. 837 — открытый IFC-Bench duplex. В переданных IFC воздуховоды/трубы/кабели = 0.

**Q-04. Почему УГТ-5, если комплект уже у вас?**
Самооценка ГОСТ Р 58048 — TRL 4. Уровень 5 требует контура партнёра в измерении и двух человеческих разметчиков. Их нет.

**Q-05. Укладываетесь в 30 минут на наш пакет?**
На комплекте заказчика время в git отсутствует. Фикстура 577 мс не SLA. Критерий 25.08 не подтверждён.

**Q-06. Замечания уже падают в наш 10D / СОД?**
BCF ZIP структурно T1. Импорт в СОД NOT_VERIFIED. GET /v1/auth/bff = 501.

**Q-07. Вы читаете RVT и NWD? У нас три федерации.**
Нативно нет, fail-closed. Три NWD есть как носители. Обмен — IFC + PDF/A.

**Q-08. Где недобор арматуры относительно ЛИРЫ?**
IfcReinforcingBar = 0. Бинарный .lir не разбираем. Сверка заявленных полей — не пересчёт.

**Q-09. Сколько денег сэкономим на круге согласования?**
Ни один множитель E1–E5 не измерен. Нужны их дни круга, часы «до» и сколько кругов они считают нормой.

**Q-10. Кто отвечает, если машина пропустит дефект?**
Эксперт. summary.passed пишет только детерминированный движок (ADR-001). LLM не rater и не вердикт.

## 4) ЗАПРОС ЗАКАЗЧИКУ

Коллеги, чтобы на демо-дне поставить блок эффекта на ваши цифры, а не на чужую модель, нужны три числа вашего контура.
1) Сколько рабочих дней у вас занимает один круг согласования рабочей документации по типовой секции.
2) Сколько часов эксперт тратит на тот же эталонный комплект без нашей системы (прогон «до»).
3) Сколько лишних кругов на типовой секции вы сами считаете нормальной практикой сегодня.
Цифры можно дать интервалом и без рублей. Их знают директор по техзаказчику, проектный офис и руководитель информационного моделирования.
Отдельно просим письменно подтвердить режим данных по уже переданному каналу 25 августа и порог приёмки пилота: промежуточная точность 0,60 по согласованной методике либо ваш иной порог. Молчание не считаем согласием с цифрой из брифа.
Готовы показать учебный прогон и карту пригодности выгрузки без публикации имён объектов и без записи в вашу СОД.

## 5) СЦЕНАРИЙ ДЕМО 20 СЕКУНД

1. 0–3 с: терминал, каталог backend/, команда python -m aerobim.tools.run_kt3_jury.
2. 3–8 с: дождаться artifacts/kt3-jury/latest.json; не открывать NDA-дерево и не seed-fixture.
3. 8–14 с: открыть report.html из того же прогона; строка IDS-Wall Fire Rating Multi, GUID 1XYVUKGoDDbREfVxRKsHkl (REI60 vs REI30).
4. 14–18 с: не кликать первую REQ-AREA-* (ifc_guid пустой). Показать, что summary.passed=false на учебной фикстуре — сценарий.
5. 18–20 с: указать findings.bcfzip рядом; сказать: файл BCF, не реестр СОД. stderr MEP-CLASH-001 не есть падение демо.

Не открывать NDA-дерево. Не нажимать «Загрузить демонстрационный комплект» (`POST /v1/demo/seed-fixture`) как «их комплект». Не ставить `AEROBIM_SIGNOFF_PROFILE=customer_pilot` на чужом ноутбуке.
