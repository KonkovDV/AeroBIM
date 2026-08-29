<!-- claims-lint: allow-file reason="Live-tree Red Team triage; TZ 90%/SLA/MEP as blocked inferences; NO_GO" -->
---
title: "Live-tree Red Team triage — 2026-08-27"
date: "2026-08-27"
last_updated: "2026-08-29"
status: active
version: "1.15.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  KILL/HOLD/ACCEPT over the live tree after TZ v1 pin and the KT#3 pack.
  Not product accuracy. Not customer SLA. Not MEP delivered. Checkpoint NO_GO.
---

# Live-tree triage (27.08.2026)

PR-diff к `main` на первом проходе 27.08 был пустой. Этот файл — полный триаж живого дерева плюс проходы КТ#3 / OOS / локация замечания / канал 25.08 / таблица LIRA / стриминг IFC / HTTP `.lir` / JSON sidecar индекса / чек-листы типовых замечаний и счётчики страницы MVP (28.08) / адрес СОД заказчика (28.08) / неизмеримость критерия коллизий на поставленном пакете (28.08) / критическое издание ответов 25.08 (28.08) / проход 12: указатель на денилист, ручной список корней, позиционирование, ГОСТ Р 72514, анкета как публикация (28.08) / проход 13: схема замечания, три ворота находки, слои bSI/IDS/движок, RASE-демо СП 63 (28.08). Не закрытие RT.

Машина: `python -c "from aerobim.domain.live_tree_triage import triage_snapshot"`.

Checkpoint **`NO_GO`**. `detected_count: 0`.

## Этот проход (KILL, затор в коде)

| ID | Атака | Тормоз |
|---|---|---|
| RT-V1-01 | Цифра точности из ТЗ v1 как замер AeroBIM | `mik_act_may_cite_tz_v1_accuracy_as_measured()==False` · `SAM-10` |
| RT-V1-02 | Четыре бумаги Самолёта — один документ | `PAPER_OBJECTS` |
| RT-V1-03 | Бинарь PDF в git / sha256 брифа = NDA `pack_hash` | `binary_in_git=false`; в снимке нет `pack_hash` |
| RT-V1-04 | Акт МИК цитирует v1 вместо interim 0.60 | горизонт `interim_tp_fp_ge_0_60` |
| RT-INJ-NEST | `inject_defects` output внутри source → `rmtree` пакета | деревья не равны и не вложены |
| RT-INJ-NDA | source = `samples/customer` или `files/` | posix-маркеры |
| RT-KIT-01 | Защищённые локаторы снова в публичном дереве | `lint_claims` kitchen denylist (HMAC-пин; литералы вне git) |
| RT-KT3-01 | `passed=false` на фикстуре = Checkpoint GO | `require_kt3_jury_gate` |
| RT-KT3-02 | Первая строка жюри = `REQ-AREA` без GUID | `select_jury_finding` |
| RT-KT3-03 | Fixture MEP `OK` = MEP delivered | gate rejects `OK`/`DELIVERED` |
| RT-TRK-05 | KPI 3–5 демо как факт git | `scheduled_demos_in_git=false` |
| RT-TRK-GO | `agent_done_count` = шесть задач закрыты у заказчика | `owner_blocked_count≥4`; NO_GO |
| RT-OOS-01 | Unsigned OOS = skip / signed OOS = RT CLOSED | `evaluate_oos` |
| RT-INV-01 | Имена/хэши `files/` в `docs/` | `require_local_only_output` |
| RT-OOS-MANIFEST | `samples/oos` на диске, но нет в `DATASET_MANIFEST` | `test_samples_manifest_gate` |
| RT-REMARK-LOC | Этаж/ось из OCR или LLM | `IfcSpatialIndex` + шаблон «нет в индексе» |
| RT-PACKS-SLA | «5–10 комплектов/день» как замер SLA | `publishable_sla=false` в порогах |
| RT-NODATA-SPEECH | «Нет данных» после канала 25.08 | `speech_forbid_no_customer_data` |
| RT-IFC-RAISE | Default analyze = 1.5 ГБ | 256 МиБ analyze; ingest отдельно |
| RT-AXIS-NEAR | Ближайшее пересечение осей | Только `IfcGridAxis.AxisTag` |
| RT-CLOUD-OIDC | HTTPS = живой OIDC BFF | `auth_bff` 501 |
| RT-002-SPPACK | Unsigned СП 63 = RT-002b | `closes_rt002=false` |
| RT-LIRA-SOLVER | MATCH таблицы = solver | `compare_declared_tables` `solver=not_implemented` |
| RT-PDF-LIRA | PDF LIRA как таблица | `pdf_fragile`; `AEROBIM-LIRA-PDF` |
| RT-IFC-STREAM | Дизайн = живой disk R-tree / cap 1.5 ГБ | `raises_default_cap=false`; 256 МиБ |
| RT-ZIP-SNIFF | Namelist ZIP на sniff-префиксе = 415 вместо zip-bomb 422 | sniff = magic; `inspect_zip_path` затем Autodesk/LIRA |
| RT-LIRA-HTTP | `.lir`/`.spr` как «disallowed extension» без честной причины | `NATIVE_LIRA_CLOSED_REASON`; ZIP-члены после inspect |
| RT-SIDECAR-RTREE | JSON sidecar индекса = live disk R-tree | `dump_only`; `disk_r_tree=designed_not_implemented` |
| RT-TYP-CATALOG | «Каталог типовых ошибок принят», пока `customer_confirmed_patterns=0` и 2 чек-листа приёмки лежат неразобранными | `customer_share_ingested=false`; `acceptance_checklists_local.ingested_into_patterns=0`; detected 2 ≠ ingested |
| RT-PAGE-DRIFT | Строки страницы MVP (11 Autodesk, 1133 скан-PDF, 51 ТЗ) перекрывают пин инвентаря | `PUBLIC_REHEARSAL`: 27 rvt + 21 navis, 1127 pdf; `rehearsal_differs` ловит дрейф |
| RT-CDE-IDENT | Адрес ссылки назвал СОД заказчика → «импорт/интеграция доказаны» | `cde_import=NOT_VERIFIED` до T2-пакета (log+screenshot+hashes); демо-пуш на синтетике ≠ реестр заказчика |
| RT-CLASH-MEASURE | «Коллизии >90% измеримы/закрыты на поставленном пакете» | `PUBLIC_REHEARSAL`: `federated_mep_ifc_present=false`, `rd_ifc_present=false` — критерий неизмерим на пакете математически; речь: «проверено на синтетике; сводная модель у заказчика в NWD — запрошена выгрузка NWD→IFC по одному корпусу» |
| RT-NORM-ACCESS | «Нормативный блокер = заказчик не дал данных» | Перечень стандартов и регламентов **выдан 25.08** (две ссылки в 1.2.1); блокер — доступ к внутренним папкам; просим публикацию тем же способом, что датасет |
| RT-NWD-FED | «Ждём от заказчика федеративный IFC» | Сводная модель существует в NWD (п. 1.1.5); просим выгрузку NWD→IFC штатным пакетным экспортом по одному корпусу |
| RT-SPEC-VOL | «Логические коллизии» = геометрия / пропустить их | П. 2.1.3: сверка объёмов спецификации с графикой/BIM; ТР-67, `compare_spec_volumes` на объявленных тройках; не смета |
| RT-INTEGRATION-OWN | Прямая интеграция с СОД как требование заказчика | П. 2.2.2: на MVP не требуется, достаточно файлового обмена; API-демо — опциональный дифференциатор вне критического пути |
| RT-90-SILENCE | Критерии >90% и время как подтверждённые заказчиком | В документе ответов ноль вхождений 90%/SLA/минут; критерии не подтверждены и не сняты — ушёл вопрос о протоколе измерения |
| RT-CLASS-TERM | «Марка бетона/стали» в наших материалах и интерфейсе | Нормативно — «класс» (СП 63); «марка» остаётся только входным алиасом парсера чужих документов |
| RT-TYP-NODES | Проверка типовых узлов как IFC-готовой или как пробел заказчика | П. 1.2.3: база узлов — PDF/DWG в тех же закрытых папках 1.2.1; узлов в IFC нет; DWG не читается |
| RT-CLOUD-ISO | On-prem как требование или HTTPS как изоляция | П. 3.1.1: облако допустимо; требуется изоляция **по проектам** (модель доступа, не шифрование) |
| RT-SCALE-MVP | Нагрузочные цифры / горизонтальный масштаб как поставка MVP | П. 3.2.2: заложить архитектурно, не реализовывать на MVP; на защите — точки расширения, не SLA |
| RT-NDA-STATED | Запрос об обезличивании/NDA как наша осторожность | П. 3.1.2 — условие **самого заказчика**; к организаторам: исполнить этот пункт и сказать, что делать с файлами, которые обезличенными не являются |
| RT-KIT-PTR | Описать состав внешнего списка запретов так, что поиск потом его восстанавливает | Инвариант гвардов: без речи о составе; литералы вне git |
| RT-KIT-ROOTS | Ручной список каталогов содержания → новый каталог гварда слепой | `git ls-files`; перечень корней — дефект класса |
| RT-KIT-SCAN-SIZE | Пропуск файла больше окна скана (полоса до карантина по размеру) | Скользящие окна по байтам; пропуск — fail-open |
| RT-KIT-SCAN-BIN | Пропуск не-UTF-8 и документных форматов пакета | Байты плюс извлечение текста PDF/Office/ZIP |
| RT-KIT-GUARD-LIST | Ручной список файлов гвардов → новый импортёр вне инварианта | Гварды = модуль денилиста плюс отслеживаемые импортёры |
| RT-KIT-PLAINTEXT | Запасной многострочный секрет списка после уже потерянных строк | Только B64; пин по счётчику |
| RT-POS-VERDIFF | Сравнение версий комплектов как преимущество | Запрещённые формулировки; у заказчика своё решение с 2024 |
| RT-POS-IDSADV | Машиночитаемые требования как преимущество рынка | Входной билет, не дифференциатор |
| RT-POS-FOREIGN-METRIC | Чужие проценты как наши | Только с атрибуцией источника; без переноса на себя |
| RT-AI-IMPACT | Нет оценки воздействия при действующем ГОСТ Р 72514-2026 | [`AI_SYSTEM_IMPACT_ASSESSMENT_GOST_R_72514_2026.md`](AI_SYSTEM_IMPACT_ASSESSMENT_GOST_R_72514_2026.md); совместимость ≠ сертификация |
| RT-NORM-MARKET | Ожидание папок заказчика как единственный путь к правилам | Licensed classified-requirements registry; подпись под профилем |
| RT-PUB-SURFACE | Анкета и съёмка вне гейта публикации | [`PUBLIC_SURFACES_PROTOCOL_2026.md`](PUBLIC_SURFACES_PROTOCOL_2026.md); шесть проверок кадра |
| RT-GATE-90 | Счётчики schema/quality/regulatory как точность >90% | HTML `finding-gates`: группировка-аналог, не 90% |
| RT-SP63-APPR | Шаблон `SP63-COVER-SLAB-001` = `customer_approved` | `approval` null; пункт 8.3 (template); не таблица 8.1 |
| RT-BSI-REPL | AeroBIM заменяет bSI Validation Service | [`VALIDATION_LAYERS_BSI_IDS_ENGINE_2026.md`](VALIDATION_LAYERS_BSI_IDS_ENGINE_2026.md); совместимость ≠ замена |
| RT-REMARK-SHAPE | Замечание заказчику = title+body без сути/пункта/локации | `validate_remark_shape`; генератор шаблона отвергает |
| RT-SOTA-PQ-MIX | Смешать PQ FloorPlanCAD между статьями / назвать VecFormer/DPSS нашими | PQ несравнимы между протоколами; Luo F1 87.8 ≠ PQ 70.6; не AeroBIM |
| RT-SOTA-CLASH-ML | Lin 0.96 или Ailem 60% FP как наш фильтр коллизий | Детерминированный triage не выкидывает коллизии; модели релевантности нет |
| RT-SOTA-VLM-LIT | VLM/AECV как drawing literacy или подпись листа | `cv_human_level=MISSING`; DrawingVQA/AECV = `open_bench_only` |
| RT-SOTA-DWG-LAYER | Слои/блоки DWG из SOTA = нативное чтение DWG | `dwg_dxf` MISSING; ODA не на пути analyze |
| RT-SOTA-SUPPL | Supplementary Gemini-3 77.2 как основная таблица DrawingVQA | Основная таблица: Gemini-2.5-pro 71.7 vs профессионалы 94.9 |
| RT-SOTA-OCR-PROXY | OmniDocBench / штамп ~0.95 как OCR строительных листов | RapidOCR extra; layout-корпуса не AEC; не ГОСТ-штамп |
| RT-SOTA-FT4B | MechVL-4B обгоняет frontier = модель в поставке | Domain-FT 4B нет в runtime; VLM advisory |
| RT-SOTA-RTREE-LIT | Обсуждение SQLite R-tree в IfcOpenShell = наш disk index | `disk_r_tree=designed_not_implemented`; sidecar `dump_only` |

## HOLD (не чиним в этом коммите)

| ID | Атака | Почему HOLD |
|---|---|---|
| RT-SEAM-HOLD | Карта семи задач = Meets / RT CLOSED | §5 TZ seam уже KILL; критерий Uncertain |
| RT-FULL-D01 | `/v1/validate/ifc` зелёный в production через development | DI берёт `settings.signoff_profile`; soft `passed` не authoritative |
| RT-AGR-002 | `moscow_agr_2026` `status=approved` = профиль Самолёта | RT-002a ≠ RT-002b; профиль не customer-hard |
| RT-INV-HOLD | Счётчики 2383/15/1 = `pack_hash` / RT-001 CLOSED | `coverage_map_only`; имён нет; intake blocked |

## ACCEPT (тормоз уже стоит)

| ID | Атака | Тормоз |
|---|---|---|
| RT-ADR-001 | LLM/VLM пишет `summary.passed` | DeterminismGate: advisory → INFO |
| RT-CAP-IFC | Поднять cap IFC из-за одного АР | default 256 MiB |

Июльский полный аудит (`RT-FULL-*` SSRF/OIDC/locks) не переоткрываем как новые CRITICAL. Не поднимаем IFC cap. Не парсим RVT/NWD/LIRA.

Связанные пины: [`TZ_V1_CONTEST_BRIEF_PIN_2026_08.md`](../tz/TZ_V1_CONTEST_BRIEF_PIN_2026_08.md) · [`TZ_SEAM_COVERAGE_MAP_2026_08.md`](TZ_SEAM_COVERAGE_MAP_2026_08.md) §5 · [`OWNER_AI_PLAN_EXECUTION_2026_08_27.md`](OWNER_AI_PLAN_EXECUTION_2026_08_27.md).
