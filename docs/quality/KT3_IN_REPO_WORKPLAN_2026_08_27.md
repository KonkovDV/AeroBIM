<!-- claims-lint: allow-file reason="In-repo KT#3 workplan; 25.08 caps/cloud as non-claims; NO_GO; RT stay OPEN" -->
---
title: "In-repo workplan after 25.08 customer answers"
date: "2026-08-27"
last_updated: "2026-08-31"
status: active
version: "1.8.2"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Repo work split after the 25.08 questionnaire. Channel received is not a
  hashed pack in git. Not product accuracy. Not customer SLA. Not native
  RVT/NWD. Not OIDC BFF live. Not LIRA solver. Streaming IFC not shipped.
  Checkpoint NO_GO.
---

# In-repo workplan (after 25.08 answers)

Customer answers 25.08 named formats, size caps, HTTPS/closed storage, LIRA **compare**, remark shape, two roles. That **does not** close RT-001/002b/003.

**Speech:** do not say «нет данных заказчика». Say: channel received; hashed pack **not** in git; machine intake status stays `BLOCKED_NO_CUSTOMER_DATA` (meaning git pack absent).

Owner-machine inventory (byte counts, file-type shares, pack hashes) stays **outside** this tree.

## Already in `main` (do not re-sell as a plan)

| Item | Where |
|---|---|
| Native RVT/NWD/DWG fail-closed | `validate_native_autodesk_toolchain`; upload/analyze/ZIP members |
| Ingest caps 500 MB office / 1.5 GB model | `SAMOLET_STATED_*`; SPF/WASM **256 MiB**; RocksDB to 1.5 GB under `samolet_pilot` |
| LIRA = compare, not solver | `calculation_compare`; `native_lir=not_implemented` |
| xlsx/docx declared-field compare | `compare_declared_tables` + office adapter; PDF fragile; `.lir` closed |
| HTTP `.lir`/`.spr` honesty 415 | `NATIVE_LIRA_CLOSED_REASON`; ZIP members after zip-bomb inspect |
| IFC streaming / disk R-tree **design** | `streaming_design_snapshot`; parser not implemented; cap unchanged |
| Spatial index JSON sidecar | dump of in-memory `IfcSpatialIndex`; not disk R-tree; not analyze |
| Remark essence + clause + storey/axis | Storey from `IfcBuildingStorey`; axis = `IfcGridAxis.AxisTag` only — **not** nearest grid intersection |
| Two role aliases | `expert` HITL; `user` viewer |
| HTTPS required flag | `https_required` on capabilities payload |
| OIDC BFF | `auth_bff=NOT_IMPLEMENTED` (default 501) |
| Speech/docs parity with 25.08 | Jury/tracker cards forbid «нет данных»; cloud ask ≠ OIDC live |

## In-repo next (this tree)

| Pri | Task | Done when | Forbidden |
|---|---|---|---|
| 0 | Keep CI green; commit **CI-attested** runtime pin only | typecheck + pytest + frontend vitest + `attested_by=ci` artifact | Minting a runtime pin from local pytest |
| 2 | Unsigned SP 63/20 **template** only if needed | `closes_rt002: false`; not `customer_approved` | Relabel as RT-002b CLOSED |
| 4 | Persist disk AABB R-tree / stream2 (not SPF raise) | Parser + RSS measurement; SPF default still 256 MiB | Silent raise of `AEROBIM_MAX_IFC_BYTES` |
| 5 | Browser OIDC BFF | Explicit 501 until implemented | Demo login as production SSO |

### Добавлено 28.08 (построчный разбор ТЗ + снимок пакета)

| Pri | Task | Done when | Forbidden |
|---|---|---|---|
| 6 | DXF-маршрут на 57 реальных файлах пакета (локально, не в git) | Строка 4 матрицы прогнана на данных заказчика; агрегат без имён | Коммитить имена/хеши; говорить «DWG покрыт» |
| 7 | Комплектность по ПП 87 на реальном комплекте ПД | Прогон на ПД пакета, verdict на файлах заказчика | Называть это точностью: без разметки это обход, не измерение |
| 8 | ТР-65: три метрики когнитивной нагрузки из review-events | Две метрики из журнала посчитаны; третья помечена missing (UI-события) | Выдумать цифру без журнала |
| 9 | Зонд пакета (`pack_probe`) оператором локально | `pack-aggregate.json` без имён получен; три недостающие цифры известны | Публиковать агрегат до ответа организаторов |

Owner-запросы (не код), редакция 28.08 после критического издания ответов 25.08:

1. **Публикация двух папок из ответа 1.2.1** (стандарты компании; регламенты BIM) тем же способом, что датасет, либо одним архивом; для старта достаточно двух документов (СТО по КЖ/КР + регламент BIM). Перечень **выдан** — просим переключатель доступа, не подборку. Каждое правило вернём на подтверждение с точной цитатой. В тех же папках — база типовых узлов (п. 1.2.3, только PDF/DWG).
2. **Выгрузка сводной NWD в IFC** штатным пакетным экспортом СОД по одному корпусу — федерация существует в NWD (п. 1.1.5); без неё критерий коллизий ТЗ неизмерим (RT-CLASH-MEASURE).
3. **Протокол измерения двух числовых критериев** (>90% коллизии; время комплекта): эталонный перечень замечаний и кто его утверждает; репрезентативный объём; от какого момента считать время. В ответах 25.08 эти критерии не упомянуты — без протокола цифры не заявляем.
4. DXF-выгрузка остальных чертежей тем же маршрутом, что 57 вложенных; отчёты по армированию и **нагрузкам/площадям** в xlsx/docx (источник сверки — расчётные записки, п. 2.1.1).
5. Исполнение **п. 3.1.2 самих ответов** (RT-NDA-STATED): обезличенные комплекты в рамках NDA — что делать с файлами, которые обезличенными не являются. Это не наша осторожность, а условие заказчика.
6. Тип доступа ссылки на датасет (только авторизованные / по ссылке) и её срок жизни.
7. Организаторам: письменный режим обращения с пакетом; можно ли публиковать агрегированные счётчики без имён/путей/хешей (они уже в репо — назвать это самим); знакомство с городским контуром проверки оформления ПД/РД (соседний слой, не замена инженерной сверки).
8. Альтернативный источник правил (RT-NORM-MARKET): licensed classified-requirements registry on the market; quote terms and price next week; ask the customer for one signature on a profile rather than months of folder access. Do not copy a vendor's published counts as our metric.

Позиционирование: компонент/движок, не платформа. Выгода — человеко-часы эксперта на комплект, доля замечаний до выдачи в производство, повторные заходы; без «инновации» и без кратного эффекта.

Публичные поверхности: анкета каталога и кадры съёмки — та же публикация, что git ([`PUBLIC_SURFACES_PROTOCOL_2026.md`](PUBLIC_SURFACES_PROTOCOL_2026.md)). Оценка воздействия ИИ: [`AI_SYSTEM_IMPACT_ASSESSMENT_GOST_R_72514_2026.md`](AI_SYSTEM_IMPACT_ASSESSMENT_GOST_R_72514_2026.md) — совместимость не сертификация.

Снято с плана по воле заказчика: разбор бинарных файлов расчётного комплекса (п. 2.1.1 — сверка с читаемыми записками) и прямая интеграция с СОД как требование (п. 2.2.2 — достаточно файлового обмена; API-демо остаётся опциональным дифференциатором).

### Добавлено 30.08 (план окна КТ#3 03–21.09, три правки владельца)

| Pri | Task | Done when | Forbidden |
|---|---|---|---|
| 1 | Внешний контур: production OIDC BFF вместо 501 | Две роли (Эксперт/Пользователь) работают через аутентификацию, негативные RBAC-тесты зелёные; фича-фриз **18.09** обязательный | Выдавать lab cookie-путь за production SSO; фриз как формальность. Единственная из 8 задач трекера с реальным риском не успеть к 21.09 — блокер в auth, не в UI |
| 3 | «Неэффективное использование пространства»: решение владельца | Позиция «в скоупе КТ#3» (advisory по внутреннему нормативу продаваемой площади/МОП/коридоров) или явное «вне MVP» зафиксирована до репетиции защиты (OA-14) | Оставить единственное «не реализовано» в карте покрытия без позиции — жюри поднимет само |
| — | Речь про RT-002 | Всегда split: 002a CLOSED (публичные IDS Мособлгосэкспертизы/АГР/СПб ЦГЭ + `pack_hash`), 002b OPEN (нет подписи Самолёта) | «RT-002 открыт целиком» = «нет норм»; «RT-002 CLOSED» без split |

Критерии приёмки: [`TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md`](TRACKER_EIGHT_TASKS_SIGINEVICH_2026_08.md). Подъём SPF 256 МиБ → 1,5 ГБ ingest — RocksDB и RSS, не rewrite in-memory. Имена и хеши канала в git **не** пишем. Fixture P/R=1,0 при n=6 жюри не показывается (Wilson 6/6 lower ≈ 0,61). TBD в ТЗ — подтвердить редакцию v2. OSINT: Sustaining ≠ BimRv. Критический путь: [`KT3_WINDOW_CRITICAL_PATH_2026_09.md`](KT3_WINDOW_CRITICAL_PATH_2026_09.md).

### Добавлено 31.08 (максимум на unpack-дереве + Red Team семейств)

| Pri | Task | Done when | Forbidden |
|---|---|---|---|
| 9b | `pack_probe` + hashed TSV **локально**; пин семейств в git (счётчики, без байт-итогов) | `pack_family_snapshot()`; live walk = 6408; `lira_named_ext=235` | Несжатые байт-итоги в git; «43 ГБ обработаны»; txt-stub `.local/pack` как комплект |
| 6b | CC-2/CC-4 shortlist: 6 docx «класс бетона», 46 xlsx нагрузок | Кандидаты в `.local/`; `is_cc2_match=false` | Токен = MATCH; разбор `.lir` |
| — | Триаж семейств | [`CHANNEL_PACK_TRIAGE_2026_08.md`](CHANNEL_PACK_TRIAGE_2026_08.md) 18 KILL / 3 HOLD / 4 ACCEPT | Meets/Does-not семи задач; OCR сдан |

## Owner-only (not git)

Hashed inventory of the customer channel; dual raters; Samolet signature on an acceptance profile; federated MEP IFC for RT-003; written data-handling order; catalog questionnaire / legal entity.

## KT#3 still FAILED (say so)

Native RVT/NWD/DWG, calculation **correctness**, signed Samolet profile, CDE import T2, product accuracy >90% on their packs.
