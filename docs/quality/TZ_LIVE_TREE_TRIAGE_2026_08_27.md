<!-- claims-lint: allow-file reason="Live-tree Red Team triage; TZ 90%/SLA/MEP as blocked inferences; NO_GO" -->
---
title: "Live-tree Red Team triage — 2026-08-27"
date: "2026-08-27"
last_updated: "2026-08-30"
status: active
version: "1.25.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  KILL/HOLD/ACCEPT over the live tree after TZ v1 pin and the KT#3 pack.
  Not product accuracy. Not customer SLA. Not MEP delivered. Checkpoint GO; customer_go false.
---

# Live-tree triage (27.08.2026)

PR-diff к `main` на первом проходе 27.08 был пустой. Этот файл — полный триаж живого дерева плюс проходы КТ#3 / OOS / локация замечания / канал 25.08 / таблица LIRA / стриминг IFC / HTTP `.lir` / JSON sidecar индекса / чек-листы типовых замечаний и счётчики страницы MVP (28.08) / адрес СОД заказчика (28.08) / неизмеримость критерия коллизий на поставленном пакете (28.08) / критическое издание ответов 25.08 (28.08) / проход 12: указатель на денилист, ручной список корней, позиционирование, ГОСТ Р 72514, анкета как публикация (28.08) / проход 13: схема замечания, три ворота находки, слои bSI/IDS/движок, RASE-демо СП 63 (28.08). Не закрытие RT.

Машина: `python -c "from aerobim.domain.live_tree_triage import triage_snapshot"`.

Проход 19: система B (прил. 3) Б1=30; pytest ≠ метрики партнёра; fixture SLA не representative; «07» ≠ номер приложения 4.

Проход 20: карта критерий→git — находимость, не прогноз; 42001 не сертификация СМИИ; i.moscow/pilot ≠ приз 2 млн; шаблон К1 без ФИО; таблица ЛЭТИ подтверждает приложение 4 №6.

Проход 21: порог 50 достижим на верху К1-low; 10 человек не требуются; К3 ≠ Б2; УГТ 4 ≠ УГТ 5.

Проход 22: TAM BIM ≠ SAM; −72% аналога не наш; рынок ≥500 млн другого продукта МИК не К4; ПНСТ 841 не сертификат.

Проход 23: identity 52,6 ≠ прогноз балла; цитата спонсора ≠ председатель; 25,1 млрд к 2030 ≠ наша выручка; paste ≠ выставленный балл.

Проход 24: Приложение 3 Положения не в git; финал — сумма, не среднее; К4 не CAPEX; МСФО убыток не наш эффект; РСБУ ≠ МСФО; четыре карточки ≠ все заявители; пилоты соседей не аудированы.

Проход 25: окно КТ#3 — OIDC 501 единственный code-path риск к 21.09; скоуп space-efficiency OPEN; RT-002a ≠ «нет норм»; Wilson n=6 не показывать; ODA Sustaining ≠ BimRv; CADSoftTools 1660 устарело; TBD — подтвердить редакцию v2; производные пакета не в git до письменного режима.

Проход 26: extra README ≠ extra CI; kitchen HMAC-тесты skip на чистом клоне; AST `test_functions` ≠ pytest `tests_collected`; ingest 1,5 ГБ ≠ analyze 256 МиБ. Кап analyze не поднимаем.

Проход 27: SPF RAM ~8–10× диска (IfcOpenShell #7116); 1,5 ГБ ingest ≈ лимит toolkit экспорта Revit. RocksDB wired over SPF cap. WASM 256 МиБ.

Checkpoint **`GO`**; `customer_go` false. `detected_count: 0`.

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
| RT-MIK-K1-GIT | HEAD git или устные консультанты = К1 закрыт | Объект К1 — состав заявки; консультант не балл |
| RT-MIK-PRIZE-50 | Репозиторий прогнозирует проход порога 50 | `predicted_aerobim_total is None`; 50 — порог программы |
| RT-MIK-AVG | Один суровый голос можно отбросить | Итог — среднее арифметическое |
| RT-MIK-TIE-K2 | Новизна ломает равенство итогов | Тай-брейк К3, затем К4 |
| RT-MIK-VITRINE | Готовиться только к витрине каталога | Подписанный приказ старше карточки; 3 кресла партнёра — по согласованию |
| RT-GOST-ORDER-DROP | Снять 64-ст, потому что каталог за март | Карточка фонда: 64-ст / 30.01.2026; совместимость ≠ сертификация |
| RT-GOST-72515-CERT | Карта ГОСТ Р 72515 = сертификат | Таксономия уже стоящей честности; не декларация соответствия |
| RT-AI-BILL-FORCE | Законопроект 166424 как действующий закон | Проект, не в ГД; сила с 01.09.2027; ADR-001 ≠ закон |
| RT-MIK-SYS-B-METRICS | Б2 высокий, потому что есть pytest и протокол | Б2 требует метрики партнёра; `confirmed_partner_validation_metrics=False` |
| RT-MIK-B2-FIXTURE-SLA | Fixture p95 как 30 мин партнёра | Пакет не representative; 30 мин — цель ТЗ |
| RT-MIK-TASK-NUM | Историческое «07» как номер приложения 4 | Приписано: задача №6, комиссия №7 |
| RT-MIK-TIE-B | Тай-брейк системы B = К3 или новизна | Только Б1 |
| RT-MIK-42001-CERT | Карта 42001 = сертифицированная СМИИ | Карточка фонда 1549-ст; `gost_42001_certified=False` |
| RT-MIK-CITY-PRIZE | i.moscow/pilot или 449-ПП = приз Техлаба 2 млн | Городской контур — юрлицо; приз задачи №6 — другой инструмент |
| RT-MIK-EVIDENCE-SCORE | Карта доказательств = прогноз итога | Находимость; `predicted_aerobim_total is None` |
| RT-MIK-K1-NAMES | Заполнить шаблон К1 в git вымышленными ФИО | Ячейки «кто» пустые; состав — заявка i.moscow |
| RT-MIK-K1-TEN | Десять ФИО — единственный путь К1 за 50 | ЛЭТИ: от 1; два класса; верх К1-low + rest-high ≥50 |
| RT-MIK-K3-AS-B2 | К3 системы A = метрики валидации Б2 | К3 = посадка на запрос; `k3_equals_validation_metrics=False` |
| RT-MIK-TRL5 | CI/фикстура = УГТ 5 или независимая ОГТ | Самооценка УГТ 4; `trl_5_claimed=False` |
| RT-MIK-FOREIGN-72 | −72,1% трудозатрат опубликованного аналога как эффект AeroBIM | `foreign_labor_cut_as_ours=False`; A1–A8 пустые |
| RT-MIK-BIM-TAM-AS-SAM | 10,1 млрд ₽ рынка BIM РФ как SAM / продажи AeroBIM | TAM атрибутирован; SAM в рублях пуст |
| RT-MIK-500M | «Рынок ≥500 млн» другого продукта МИК как К4 этой задачи | Другая упаковка; не TechLab K4 |
| RT-MIK-PNST-CERT | Карта ПНСТ 841 = сертификация SQuaRE / ГОСТ Р | Предварительный стандарт; `pnst_841_certified=False` |
| RT-MIK-IDENTITY-AS-SCORE | 16+36,6 или «порог достижим» как наш итог | Идентичность полос; `predicted_aerobim_total is None` |
| RT-MIK-SPONSOR-CHAIR | Цитата спонсора с витрины = председатель / состав К1 | `sponsor_quote_is_commission_chair=False` |
| RT-MIK-25B-REV | 25,1 млрд ₽ к 2030 как выручка / SAM AeroBIM | `tam_horizon_is_our_revenue=False` |
| RT-MIK-PASTE-SCORE | Вставка в заявку = уже выставленный балл / состав | Тексты полей; ячейки «кто» пустые |
| RT-MIK-APP3-UNSEEN | Б1–Б5 в git = Приложение 3 к Положению | `regulation_appendix_3_in_git=False` |
| RT-MIK-FINAL-MEAN | Финал считается средним, как отбор | `FINALIST_AGGREGATION=sum`; знаменатель 50 неизвестен |
| RT-MIK-INVEST-K4 | «Инвестируйте» / CAPEX / лицензионная стена | `k4_asks_customer_capex=False`; нулевой вход |
| RT-MIK-SAVE-PNL | Убыток МСФО 22,3 млрд как наш эффект | `k4_offsets_partner_ifrs_loss=False` |
| RT-MIK-RAS-IFRS | РСБУ +31% как картина группы МСФО | `ras_ifrs_signs_are_the_same=False` |
| RT-MIK-CATALOG-ALL | Четыре карточки = все, кто подал | `catalog_four_are_all_applicants=False` |
| RT-MIK-PEER-PILOTS | «15 пилотов» / «600+ норм» карточки как факт | `peer_card_claims_externally_verified=False` |
| RT-ODA-BIMRV | Sustaining 7 500 $ = native RVT/NWD | BimRv/BimNv — расширения 6 250 $; Drawings = DWG |
| RT-CADSOFT-STALE | CADSoftTools «от 1 660 $» как пол 2026 | Публичная страница 30.08: от 765 USD; не RVT/NWD |
| RT-WILSON-N6 | Показать fixture P/R=1,0 при n=6 жюри | `wilson_interval(6,6)` lower ≈ 0,61; стоп-лист п. 28 |
| RT-SPACE-SCOPE | Space efficiency сдано / заказчику не нужно | Карта: не реализовано; 25.08 назвал критерий; OA-14 OPEN |
| RT-002-NORMS | RT-002 OPEN = нет машиночитаемых норм | 002a CLOSED (MOEXP 06.03.2026); открыт только 002b |
| RT-TBD-FILL | Просить организаторов заполнить пустые TBD с 09.07 | ТЗ v2 уже заполняет пять разделов; подтвердить редакцию |
| RT-OIDC-FREEZE | Фриз 18.09 формальность; lab cookie = production SSO | `auth_bff=NOT_IMPLEMENTED`; default 501 |
| RT-PACK-DERIV | Коммитить производные канала до письменного режима | OA-9; MIT необратим; инвентарь в `.local` |
| RT-CLONE-PYTEST | 13 failed на README-extra клоне = CI pin | skip без pymupdf/секретов; пин = `attested_by=ci` |
| RT-PIN-DRIFT | Исторические счётчики CRITICAL_BLOCKERS или HEAD pytest как живой пин | SSOT: `runtime-baseline-latest.json`; HEAD может быть впереди |
| RT-INGEST-ANALYZE | 1,5 ГБ ingest заказчика = кап WASM / SPF RAM | SPF 256 МиБ; RocksDB до 1,5 ГБ; WASM 256 МиБ |
| RT-SPF-10X | Поднять default SPF cap до 1,5 ГБ — это строка в settings | SPF ~8–10× диск; 1,5 ГБ путь = RocksDB, не `open(.ifc)` |

## HOLD (не чиним в этом коммите)

| ID | Атака | Почему HOLD |
|---|---|---|
| RT-SEAM-HOLD | Карта семи задач = Meets / RT CLOSED | §5 TZ seam уже KILL; критерий Uncertain |
| RT-FULL-D01 | `/v1/validate/ifc` зелёный в production через development | DI берёт `settings.signoff_profile`; soft `passed` не authoritative |
| RT-AGR-002 | `moscow_agr_2026` `status=approved` = профиль Самолёта | RT-002a ≠ RT-002c; профиль не customer-hard |
| RT-INV-HOLD | Счётчики 2383/15/1 = `pack_hash` / RT-001 CLOSED | `coverage_map_only`; имён нет; intake blocked |

## ACCEPT (тормоз уже стоит)

| ID | Атака | Тормоз |
|---|---|---|
| RT-ADR-001 | LLM/VLM пишет `summary.passed` | DeterminismGate: advisory → INFO |
| RT-CAP-IFC | Поднять cap IFC из-за одного АР | default 256 MiB |

Июльский полный аудит (`RT-FULL-*` SSRF/OIDC/locks) не переоткрываем как новые CRITICAL. Не поднимаем IFC cap. Не парсим RVT/NWD/LIRA.

Связанные пины: [`TZ_V1_CONTEST_BRIEF_PIN_2026_08.md`](../tz/TZ_V1_CONTEST_BRIEF_PIN_2026_08.md) · [`TZ_SEAM_COVERAGE_MAP_2026_08.md`](TZ_SEAM_COVERAGE_MAP_2026_08.md) §5 · [`OWNER_AI_PLAN_EXECUTION_2026_08_27.md`](OWNER_AI_PLAN_EXECUTION_2026_08_27.md).
