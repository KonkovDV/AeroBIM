<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Четыре направления вне подтверждённого контура — инженерный gap-анализ"
status: active
version: "1.0.0"
last_updated: "2026-07-24"
claim_boundary: "Ни одно из четырёх направлений не является промышленно подтверждённым. Checkpoint NO_GO. Этот документ — roadmap/gap, не capability claim."
tags: [aerobim, samolet, techlab, gap, dwg, mep, calc, bcf, cde]
---

# Инженерная проработка ограничений: DWG · MEP system-aware · расчёты · BCF→СОД

**Программа:** Самолёт × Техлаб Москва, Задача №7  
**Финальная КТ:** 21 сентября 2026  
**Принцип:** порт / DI / fixture ≠ промышленная возможность. LLM не выставляет вердикт.

Связанные SSOT: [`PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md`](PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md), [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md), [`../../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md), [`../roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md`](../roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md), [`../architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md`](../architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md).

---

## Единая шкала статусов

| Статус | Значение |
|--------|----------|
| `AVAILABLE` | Реализовано и подтверждено тестами |
| `AVAILABLE_FIXTURE_ONLY` | Работает на фикстурах, не подтверждено заказчиком |
| `EXPERIMENTAL` | Рабочая заготовка без достаточной валидации |
| `PARTIAL` | Часть сценария |
| `BLOCKED_CUSTOMER_DATA` | Нужны данные / правила / доступ заказчика |
| `MISSING` | Реализации нет |
| `ROADMAP` | Описано, не реализовано |
| `FAILED` | Проверка запрошена, завершилась ошибкой |
| `SKIPPED` | Не запускалась из‑за отсутствия входов |

Слово **«готово»** не используется для `EXPERIMENTAL` / `PARTIAL` / `BLOCKED_CUSTOMER_DATA` / `MISSING` / `ROADMAP`.

---

# 1. Нативная работа с DWG

## 1.1 Текущий статус

| Вопрос | Факт |
|--------|------|
| Реальный DWG-парсер | **Нет.** `EzdxfCadModelIngestor` на `.dwg` сразу `supported=False` |
| DXF-адаптер | **PARTIAL:** optional `[cad]` → `ezdxf`; TEXT/MTEXT → annotations; EntityGraph в DI, не в analyze UC |
| Слои / блоки / XREF / штриховки | **Не покрыты** как product contour |
| Геометрия + семантика DWG | **MISSING** |
| Порт / stub | `OdaCadModelIngestor` = `@sota-stub` STUB-ODA-CAD-001; **не** на analyze path |
| При отсутствии DWG-модуля | Capability `dwg_dxf`: `MISSING` / `FAILED` / `NOT_VERIFIED` |
| Блокирует ли positive verdict | **Да (fail-closed honesty):** `dwg_dxf=ok` **запрещён** honesty gate; unparsed DWG → `FAILED` даже при успешном sibling DXF |
| PDF/IFC как замена | **Честная временная замена 2D:** PDF/OCR + structured TXT/JSON; IFC = BIM-контур, не DWG |

**Статус направления:** `MISSING` (native DWG) + `PARTIAL` (DXF never OK) + stub ODA.

Код: `ezdxf_cad_model_ingestor.py`, `oda_cad_model_ingestor.py`, `enforce_honesty_capabilities`, `test_cad_office_ingest.py`.

## 1.2 Варианты реализации

| Критерий | A. DWG→IFC/PDF | B. DWG→DXF→ezdxf | C. Native ODA/Teigha SDK |
|----------|----------------|------------------|-------------------------|
| Возможности | Проверка уже живым PDF/IFC контуром | Текст/частичная геометрия DXF | Полный DWG (теоретически) |
| Покрытие сущностей | Зависит от конвертера; XREF/блок часто теряются | Слои/текст частично; блоки/XREF слабо | Высокое при лицензии |
| Точность координат | Средняя; нужна QA конвертации | Средняя | Высокая |
| Слои | Часто теряются / flatten | Частично | Сохраняются |
| Стоимость | Низкая–средняя (трудозатраты + tool) | Низкая (ezdxf MIT) | **Высокая** (ODA commercial) |
| Лицензирование | Зависит от tool (ODA File Converter / иной) | MIT | ODA — коммерческий, юридический gate |
| Локальный контур | Да, если конвертер on-prem | Да | Да при лицензии |
| Юр./экспл. риск | Потеря данных без provenance | Ограниченная семантика | Лицензия + поддержка SDK |
| Срок до 21.09 | **Реалистичен** как pipeline | Уже частично есть | **Нереалистичен** как product |
| Тестирование | Hash исходник↔производный + diff слоёв | Fixture DXF | Нужен SDK + корпоративный DWG corpus |
| Закрытый контур Самолёта | Приемлем при on-prem конвертере | Приемлем | Только после закупки ODA |

**Рекомендация:** до 21.09 — **вариант A (+ B как opt-in)**, не C.

## 1.3 Минимальный MVP до 21.09 (без «native DWG»)

1. Приём `.dwg` как **входного артефакта** (ingest + hash).  
2. Обязательная **внешняя** конвертация (заказчик или согласованный tool) → PDF и/или DXF/IFC.  
3. Регистрация пары `source_dwg_sha256` ↔ `derived_*_sha256` в provenance. **ЗАКРЫТО 2026-07-27** — hash-верифицируемый sidecar + CLI `aerobim-register-dwg-conversion`.  
4. QA конвертации: список ожидаемых листов/слоёв; фиксация loss report. **ЗАКРЫТО 2026-07-27** — `cad_conversion_qa` diff + пороги §1.4; вердикт пересчитывается, не читается из sidecar (Wave S).  
5. При неуспехе конвертации / отсутствии derived → capability `FAILED`, **блокировка** `summary.passed` в pilot/production. **ЗАКРЫТО 2026-07-27** — невалидный/tampered sidecar строже отсутствующего (Wave S).  
6. В UI/отчёте: «результат относится к производному файлу; исходный DWG = N». **ЗАКРЫТО 2026-07-27** — INFO-issue `AEROBIM-CAD-DWG-DERIVED` с обоими sha256 в evidence_refs (Wave S).  
7. **Не** ставить `dwg_dxf=ok`.

## 1.4 Критерии приёмки MVP

| Критерий | Порог |
|----------|-------|
| Версии DWG | Зафиксировать в scope (например AutoCAD 2018–2024); иные → `FAILED` + reason |
| Проверяемые объекты | Только то, что есть в derived (PDF text / IFC / DXF text) |
| Сохранение геометрии | Для IFC-derived: ≥ согласованной доли GUID/объёма vs эталон (если эталон есть); иначе qualitative loss log |
| Потеря слоёв | Diff layer count / names; >N% loss → WARNING escalate или FAILED по политике |
| Ошибка конвертации | Явный issue + capability FAILED |
| Unsupported | Status `FAILED` или `MISSING` с reason; не silent skip |
| Эксперту показывают | Derived findings + link to source DWG hash; запрет формулировки «DWG проанализирован нативно» |

## 1.5 Бизнес-сценарий Самолёта / пилот

- **В пилот:** DWG только как исходник + конвертация + fail-closed.  
- **Вне пилота:** native ODA, полный EntityGraph по блокам/XREF, «DWG-ready».

**Приоритет:** `OUT` native · `P1` conversion MVP (если Самолет даёт DWG + tool) · иначе `зафиксировать как ограничение`.

**Допустимая формулировка:** «DWG рассматривается через конвертацию или отдельный лицензируемый адаптер; нативная поддержка отсутствует.»

---

# 2. Полный MEP system-aware clash

## 2.1 Геометрия vs системная семантика

| Проверка | Только геометрия | Нужен system graph / семантика |
|----------|------------------|--------------------------------|
| Пересечение solid | ✓ `IfcClashDetector` hard | — |
| Min distance / clearance | Частично (модель поддерживает `clearance`; detector сейчас hard) | Матрица пар систем |
| Пересечение трасс разных систем | Геометрия даёт пару GUID | Нужны `IfcSystem` / классификация |
| Зона обслуживания оборудования | Слабо / нет | Семантика + clearance rules |
| Направление потока / разрыв / нет connection | Нет | Connectivity graph |
| Неверный тип системы / классификация | Нет | Property + classifier |
| ОВиК↔ВК↔ЭОМ↔СС↔АР | Гео-clash между файлами | Federated scope + matrix |

**Статус:** geometric clash = `AVAILABLE` (opt-in extra, capability-gated).  
System-aware product = `AVAILABLE_FIXTURE_ONLY` / `EXPERIMENTAL` eng scaffold + `BLOCKED_CUSTOMER_DATA` (RT-003).  
Honesty: `mep_system_clash` **никогда OK**.

## 2.2 Необходимые данные от заказчика

- Федеративный IFC (отдельные модели разделов) с реальными `IfcSystem`  
- Signed scope memo + expert_signoff  
- Signed clearance / allowed-intersection matrix (не template)  
- Классификаторы, диаметры, типы сетей, зоны обслуживания (если в правилах)  
- Согласованная CRS / геопривязка  
- Стабильность GUID между ревизиями  
- ≥ N размеченных коллизий для FP/TP

## 2.3 Архитектура (как есть → как должно)

**Сейчас:**

```text
FederatedIfcMepSystemGraphProvider  →  узлы из IfcSpatialIndex
                                     →  рёбра = co-presence (не geometry intersection)
evaluate_matrix_against_graph      →  findings с geometry_verified=False
                                     →  TEMPLATE / unclassified = WARNING
IfcClashDetector                   →  hard intersection (отдельный capability.clash)
IfcSystemAwareClash                →  advisory name-pair probe (opt-in env)
```

**Целевой MVP (после RT-003 данных):**

1. `MepSystemGraphProvider` строит граф: system → elements → ports/connections (где есть в IFC).  
2. Spatial reasoning: bbox/AABB index → candidate pairs → geometry intersection **или** distance.  
3. Clearance rules: (sysA, sysB) → min_gap / forbid.  
4. Incomplete data → `NOT_VERIFIED` / `FAILED`, не ERROR «изобретённый».  
5. Evidence: GUID pair, systems, rule_id, distance, matrix_hash, scope_hash.  
6. `summary.passed`: только при политике + capability OK; **сейчас OK запрещён** до customer evidence.  
7. HITL: спорные пары → review-event, не auto Critical.

## 2.4 Пять сценариев (пилот / демо)

| # | Сценарий | Вход | Правило | Ожидание | Severity | Evidence | Эксперт |
|---|----------|------|---------|----------|----------|----------|---------|
| 1 | Воздуховод ∩ балка | HVAC IFC + AR IFC | Hard clash | Issue + GUIDs | ERROR если `clash_affects_pass` | ClashResult | Подтвердить/отклонить |
| 2 | Труба ∩ кабель-трасса | ВК + ЭОМ + matrix forbid | System pair forbid + geo | Finding только если geo_verified | Critical/Warning | matrix + GUIDs | Adjudicate FP |
| 3 | Зона обслуживания | Equipment + clearance zone | Customer rule | **Часто OUT** без правил | — | — | Нужны правила |
| 4 | Разрыв системы | IfcSystem без connectivity | Connectivity | **OUT** до графа connections | — | — | — |
| 5 | IFC vs спецификация vs чертёж | IFC + PDF + spec | Cross-doc + MEP | Cross-doc / attribute | Warning/Error | provenance | Сверка марок |

До 21.09 реалистичны **1** (уже) и ограниченно **2** (при federated + signed matrix + geo). **3–4** — roadmap. **5** — частично через cross-doc без «system clash».

## 2.5 Критерии приёмки (когда можно писать больше, чем сейчас)

| Критерий | Порог |
|----------|-------|
| Федеративный комплект | ≥2 дисциплины IFC + memo |
| Системы | Список в scope (HVAC, SPRINKLER, …) |
| Тестовые коллизии | ≥10 размеченных (TP/FP) |
| FP-rate | Согласовать; interim ≤40% на Critical |
| Provenance | 100% findings с GUID/rule/matrix_hash |
| Повторяемость | Golden hash на freeze |
| Время | В общем ≤30 мин пакета (если в SLA scope) |
| Capability | `ok` только после RT-003 close + honesty lift; иначе `not_verified`/`failed`/`missing` |

## 2.6 Приоритет

**P2** ограниченный эксперимент при данных; **полный system-aware = OUT / ROADMAP** после пилота.  
В промежуточную версию: честный generic clash + eng fixture graph **как демо ограничений**, не как «MEP delivered».

**Допустимая формулировка:** «Геометрический clash доступен; системно-семантический MEP-анализ требует отдельной конфигурации и данных заказчика.»

---

# 3. Проверка корректности расчётов

## Ключевое разделение

| Класс | AeroBIM сейчас | Статус |
|-------|----------------|--------|
| **Сверка результатов** | Cross-doc numbers, load expected↔observed, qty vs IFC, OpenRebar provenance, logic gaps | `PARTIAL` / `AVAILABLE` на fixture |
| **Независимая корректность** | Решатель + матмодель + нагрузки + эталон | `MISSING` / `NOT_IMPLEMENTED` (`calculation_correctness`) |

## 3.1 Границы ответственности

| Что | Кто |
|-----|-----|
| Сопоставить отчёт↔ТЗ↔IFC, версии, checksums, марки | **AeroBIM** |
| Пересчёт конструкций / сетей | **Внешний решатель** + профильный инженер |
| Подтвердить, что формула/норма применены верно | **Только эксперт** (или внешний solver + peer review) |
| В пилот | Evidence-сверка + fail-closed при отсутствии расчёта (если в scope) |
| В claims | Только «сверка»; **не** «проверяет корректность расчётов» |

## 3.2 Форматы (факт кода)

- LOAD rows: tabular text / JSON (`SpreadsheetLoadEvidenceAdapter`) — **не** полноценный openpyxl path в live adapter  
- Office hydrate: Docling для docx/xlsx/… → текст  
- OpenRebar: `*.result.json` + digest  
- Narrative calc TXT fixtures  
- IFC quantities для qty consistency

## 3.3 Архитектура портов (есть)

```text
LoadEvidenceVerifier          → SpreadsheetLoadEvidenceAdapter
QuantityConsistencyChecker    → IfcQuantityConsistencyAdapter
LogicConsistencyAnalyzer      → ManifestLogicConsistencyAdapter
ExternalEvidenceVerifier      → OpenRebarEvidenceVerifier
```

Эскалация: hard sign-off → cross-doc ERROR; OpenRebar provenance enforce optional.

**Не строить** до 21.09 порт «StructuralSolver» как product claim.

## 3.4 Сценарии

| Сценарий | Поведение AeroBIM | Не является |
|----------|-------------------|-------------|
| Отчёт отсутствует | Logic / capability gap; FAILED если required | — |
| Расчёт ≠ версия IFC | Provenance / hash / projectCode mismatch | — |
| Марка не в модели | Cross-doc / missing | — |
| Площадь/объём расходятся | QTY mismatch (ε) | Не «ошибка расчёта» |
| Нагрузка ≠ ТЗ | LOAD-MISMATCH | Не пересчёт |
| Ревизия изменила числа | Diff + provenance | — |
| Внешний solver без подтверждения | Match OK ≠ correctness | **Не** verification |

## 3.5 Критерии приёмки сверки (не correctness)

| Поле | Правило |
|------|---------|
| Числа | SI + согласованный ε (уже в cross-doc) |
| Единицы | Normalize; mismatch → WARNING/ERROR |
| Версия источника | Hash / contractId / path |
| Нет evidence | `FAILED`/`MISSING` при required; иначе SKIPPED |
| Warning vs block | Policy profile |
| Почему не correctness | Нет независимого решателя и эталонной модели |

**Приоритет:** усиление сверки = `P0/P1` в основном контуре; независимая корректность = `OUT` / `ROADMAP`.

**Допустимая формулировка:** «AeroBIM выполняет сверку переданных результатов расчётов, но не заменяет расчётный решатель.»

---

# 4. Импорт BCF в СОД

## 4.1 Текущий статус

| Слой | Статус |
|------|--------|
| Экспорт BCF 2.1 ZIP | `AVAILABLE` (T0) |
| Экспорт BCF 3.0 | `EXPERIMENTAL` |
| Structural ZIP + dual consumer | `AVAILABLE` (T1 evidenced) |
| Независимый consumer ≠ СОД | T1 ≠ T2 |
| OpenCDE topic push HTTP | `EXPERIMENTAL` foundation (real HTTP if configured; else fail-closed) |
| Импорт в СОД заказчика | `BLOCKED_CUSTOMER_DATA` / `NOT_VERIFIED` (T2 empty) |
| Двусторонняя sync / status return | `MISSING` / `ROADMAP` |

**Почему экспорт ≠ готовность к СОД:** другая схема полей, GUID, auth, viewpoint/camera, вложения, статусы, deep links; нужны screenshot + import log + hashes (`audit/evidence/cde-import-proof/`).

## 4.2 Запрос к заказчику

Название/версия СОД · BCF 2.1 vs 3 · ZIP vs API · OAuth/token · тестовый проект · права · GUID policy · viewpoint/markup support · статусы/приоритеты · пользователи · ИБ · audit log.

## 4.3 Цикл проверки T2

```text
AeroBIM → BCF 2.1 ZIP → импорт в СОД →
тема → viewpoint → IFC GUID → назначение →
смена статуса → (опц.) re-export → сопоставление с исходным finding
```

Поля совпадения: GUID topic, title, description, author, created, priority, status, type, viewpoint/camera, component IFC GUID, snapshot (если есть), document ref.

## 4.4 Критерии «проверено в СОД»

| Метрика | Мин. порог (предложение) |
|---------|--------------------------|
| Тестовых topics | ≥10 |
| Успешный импорт тем | ≥90% |
| Сохранившиеся IFC GUID | ≥80% (или согласованный) |
| Viewpoint usable | ≥70% «открывается у элемента» |
| Статусы | Маппинг задокументирован |
| Вложения | Если в scope — 100% или explicit skip |
| Время импорта | Зафиксировать |
| Evidence pack | log + screenshot + hashes → `VERIFIED` |
| До этого | **Нельзя** писать «BCF готов для СОД» / «CDE interoperable» |

**Приоритет:** `P1` если доступ к СОД до сентября; иначе `P2`/`зафиксировать ограничение`. Экспорт уже в пилоте.

**Допустимая формулировка:** «Доступен экспорт BCF 2.1; импорт в конкретную СОД требует отдельной проверки (T2).»

---

# 5. Итоговая матрица результатов

| Направление | Текущий статус | Что работает | Чего не хватает | Зависимость | MVP до 21.09 | Критерий приёмки | Метрики | Риск | Приоритет | Допустимая формулировка |
|-------------|---------------|--------------|-----------------|-------------|--------------|------------------|---------|------|-----------|-------------------------|
| Native DWG | `MISSING` (+ DXF `PARTIAL`) | Fail-closed; DXF text; PDF/OCR/IFC substitutes; ODA stub | ODA product; слои/XREF; `dwg_dxf=ok` | Лицензия ODA **или** конвертер + DWG corpus | Conversion pipeline + provenance + block on fail | Derived QA + hashes; never native claim | Loss %, convert fail rate | Высокий при native | **OUT** native; **P1** convert MVP | «Через конвертацию / лицензируемый адаптер» |
| MEP system-aware | `AVAILABLE_FIXTURE_ONLY` + `BLOCKED_CUSTOMER_DATA` | Hard clash; eng graph co-presence; template matrix honesty | Geo intersection + signed matrix + customer federated | RT-003 pack | Demo honesty + optional limited geo+matrix experiment | RT-003 evidence ladder | FP-rate, κ, time | Срыв при overclaim | **P2** limited; full **OUT** | «Гео-clash да; system-aware — отдельная конфигурация» |
| Calc correctness | `MISSING` (`NOT_IMPLEMENTED`) | Сверка: load/qty/cross-doc/OpenRebar | Solver, нормы, эталон | Проф. инженер + ПО | Усилить сверку only | Match ε + provenance; correctness never OK | Match precision | Путаница терминов | Сверка **P0**; correctness **OUT** | «Сверка результатов, не решатель» |
| BCF→СОД | Export `AVAILABLE`; T2 `NOT_VERIFIED` | BCF 2.1 ZIP; T1 structural; OpenCDE push scaffold | Customer CDE import proof | Доступ к СОД | T2 test если доступ; иначе ограничение | log+screenshot+hashes | Import %, GUID retention | Низкий для export; высокий для claim | **P1** T2 / else constrain | «Экспорт есть; импорт в СОД — отдельный тест» |

---

# 6. Матрица запросов к «Самолёту»

| Запрос | Для чего | Мин. объём | Ответственный | Дедлайн | Блокирует |
|--------|----------|------------|---------------|---------|-----------|
| Scope memo (дисциплины, in/out DWG/MEP/calc/CDE) | Границы пилота | 1–2 стр | Sponsor Самолёта | **до 3 авг** | Overclaim |
| NDA + канал ИБ | Customer data | Подпись | Юр./ИБ | до 3 авг | Корпус |
| 2 эксперта-adjudicators | TP/FP, κ | Имена + часы | Проектный офис | 4–10 авг | RT-001 |
| Пилотный комплект ПД/РД/IFC/ТЗ | Основной KPI | 1 объект ≤30 мин | BIM lead | 4–10 авг | Pilot |
| Norm pack approval | RT-002 | Signed pack + hash | Нормоконтроль | 4–10 авг | Norms verdict |
| DWG + версия AutoCAD + tool конвертации | DWG MVP | 3–5 листов + процедура | CAD lead | 4–10 авг | DWG MVP |
| Федеративный MEP IFC + signed clearance matrix | RT-003 | ≥2 файла + matrix | MEP lead | 4–20 авг | System-aware |
| Расчётные отчёты + версии + список решателей | Сверка | На тот же объект | ГИП / расчётчик | 4–10 авг | Calc match |
| Тестовая СОД + проект + права + BCF version | T2 | 1 sandbox | CDE admin | **до 20 авг** | «проверено в СОД» |
| Baseline часов ручной проверки | Экономический эффект | Таблица | Эксперты | 4–10 авг | ROI claim |

---

# 7. План-график

### До 3 августа

- [x] Gap-анализ (этот документ)  
- [ ] Подтвердить границы 4 направлений с командой (Claims Lock sync)  
- [ ] Отправить матрицу запросов Самолёту  
- [ ] Зафиксировать тестовые сценарии (MEP 1–2, calc match, BCF T2 checklist, DWG convert)  

### 4–20 августа (КТ2)

- Принять данные; intake quality gate  
- Ограниченный прогон: **основной контур** + сверка расчётов + BCF export  
- MEP/DWG/CDE — только если данные пришли; иначе явный blocker в промежуточном отчёте  
- Не включать недоказанное в «промежуточную версию» как feature  

### 21 августа – 2 сентября

- T2 BCF при доступе к СОД  
- MEP experiment при federated+matrix  
- Calc match на customer numbers  
- Решение: DWG convert MVP **или** formal OUT  

### 3–21 сентября (КТ3)

- Закрыть только доказанное  
- Финальный отчёт + ограничения + capability matrix update  
- Недоказанное → roadmap  
- Запрет неподтверждённых claims в презентации  

---

# 8. Приоритизация (сводка рекомендаций)

| Направление | Рекомендация |
|-------------|--------------|
| DWG native | **Перенести после пилота** / OUT |
| DWG convert MVP | **Делать только ограниченный MVP** при данных; иначе ограничение |
| MEP full system-aware | **Проверять как отдельный эксперимент**; полный контур OUT |
| Generic clash | Уже в основном контуре — **делать сейчас** (не путать с MEP) |
| Calc сверка | **Делать сейчас** (усиление) |
| Calc correctness | **Зафиксировать как ограничение** / ROADMAP |
| BCF export | Уже **AVAILABLE** — в пилоте |
| BCF→СОД T2 | **Отдельный эксперимент** при доступе; иначе ограничение |

---

# 9. Управленческое заключение

1. **Обязательно до 20 августа:** основной openBIM-контур (IFC/IDS/cross-doc/clash/OCR/provenance/HITL/BCF export), протокол разметки, intake, усиленная **сверка** расчётов, честный Claims Lock по четырём направлениям, список запросов Самолёту.  

2. **Реально подтвердить до 21 сентября:** воспроизводимый сценарий проверки согласованного комплекта; interim TP/(TP+FP) при корпусе+экспертах; BCF ZIP; optionally T2 в СОД и ограниченный MEP experiment — **только с evidence**.  

3. **Не пытаться полностью закрыть в пилоте:** native DWG (ODA), полный MEP connectivity/flow/service zones, независимый расчётный решатель, двусторонний CDE sync.  

4. **Критически запросить у Самолёта:** комплект + norm pack + 2 экспертов + baseline часов; при амбициях по направлениям — DWG+конвертер, federated MEP+matrix, calc files, sandbox СОД.  

5. **Минимальный честный защитный результат:** «AeroBIM проверяет согласованный openBIM-комплект детерминированно, с provenance и HITL; границы DWG/MEP-system/calc-correctness/CDE-import явные; эффект измерен на размеченном срезе.»  

6. **Формулировки для презентации:** см. столбец «Допустимая формулировка» + claim boundary.  

7. **Исключить полностью:** «DWG-ready», «полный MEP clash», «проверяет корректность расчётов», «BCF готов для СОД», «CDE interoperable», «>90%», «AI заменяет эксперта», «полное покрытие СП».

**Главная цель до 21.09 — не максимум функций, а доказанный воспроизводимый сценарий с понятными границами ответственности.**
