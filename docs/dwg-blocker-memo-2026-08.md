<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# DWG: где затыки и сколько стоит платный путь (2026-08)

**Status:** TZ_MANDATORY_UNSUPPORTED (fail-closed FAILED; not silently out of scope)  
**Checkpoint:** NO_GO  
**claim_boundary:** Native DWG remains **Missing/Failed** (fail-closed). Tracker 07.08: DWG is in the Samolet TZ — do not delete the requirement. This memo is engineering + legal framing — **not** a DWG-ready product claim. Budget for SDK = 0.  
**Code path today:** `EzdxfCadModelIngestor` returns `supported=False` for `.dwg`; honesty surface `native_dwg=missing` / `dwg_dxf=FAILED` when DWG is requested; FAILED CAD capability blocks `summary.passed` (ADR-001).  
**Related:** [`docs/tz/DWG_DECISION_OPTIONS_ABC_2026_08.md`](tz/DWG_DECISION_OPTIONS_ABC_2026_08.md)

---

## 1. Нормативная рамка

DWG **не входит** в обязательный контур приёмки.

| Источник | Что требует |
|---|---|
| Приказ Минстроя **783/пр** от 12.05.2017 | Документы для госэкспертизы: XML; до ввода схемы — doc/docx/odt, **PDF** (в т.ч. графика), xls/xlsx/ods. **DWG в перечне нет.** |
| **ПП РФ 614** от 17.05.2024 (заменило ПП 1431; действует до 01.09.2030), **приложение о составе электронных документов, п. 7 подп. «б», «г», «д»** (не п. 7 Правил про ссылки на ГИС) | **PDF/A**; LandXML или open-spec — местность; **IFC** или open-spec — ЦИМ. **DWG в перечне нет.** |
| ГОСТ Р 10.0.02-2019 / ИСО 16739-1:2018 | IFC как национальный стандарт |

**Итог:** юридически значимая приёмка строится на **PDF/A + IFC + XML**. DWG — внутренний рабочий формат подрядчика / требование заказчика, **не** регулятора.

---

## 2. Технический затык

| Фактор | Почему ломает «просто распарсить DWG» |
|---|---|
| Закрытый формат | Открытой спецификации нет. Свободная реализация **GNU LibreDWG** (0.14, 27.06.2026, beta): часть объектов R2010+ пропускается; `ACAD_PROXY_OBJECT`, Layout, PlotSettings не переносятся; запись R2010–R2018 даёт ошибки CRC. Лицензия **GPL-3 несовместима** с MIT AeroBIM. |
| Российская специфика | nanoCAD / SPDS / GraphiCS → набор **прокси-объектов**: без родного приложения доступна кэшированная графика; семантика выносок, осей, размерных цепей и спецификаций теряется. Плюс xref, блоки с атрибутами вне файла, **CP1251**, шрифты SHX (ISOCPEUR, ГОСТ тип А/Б), аннотативные масштабы. |
| Растр / OCR ≠ CAD | OCR даёт текст без слоя, координат в модельном пространстве и связи «выноска ↔ элемент». Без этого нельзя сформировать `evidence_refs` и сверить аннотацию с IFC. Это **деградация**, не поддержка формата. |
| Постулат продукта | Без лицензированного Drawings SDK мы **отказываемся** зелёным путём: capability остаётся non-OK, Shared-gate fail-closed. |

**DXF path:** optional `ezdxf` может извлечь TEXT/MTEXT при **экспорте DXF заказчиком**. Это не claim native DWG.

**Показ Самолёту (14.08):** лицензия GPL-3 — не повод прятать *входные* GPLv3 IFC в `.local/`. LibreDWG в процесс AeroBIM **не линкуем** (неполнота + нельзя отдать GPL-сборку другим). Демо DWG = IFC + PDF/A. Полоса: [`pilot/SAMOLET_DEMO_COPYLEFT_LANE_2026_08_14.md`](pilot/SAMOLET_DEMO_COPYLEFT_LANE_2026_08_14.md).

---

## 3. Стоимость (ориентиры Aug 2026)

Источники: [ODA Pricing](https://www.opendesign.com/pricing), [ODA membership](https://www.opendesign.com/oda-membership), [CADSoftTools CAD DLL buy](https://cadsofttools.com/products/cad-dll/buy/), [libcad.so](https://cadsofttools.com/products/libcadso/).

| Опция | Год 1 | Продление | SaaS/Web | Fit |
|---|---:|---:|---|---|
| **ODA Commercial** | 3 000 $ | 2 250 $ | **Нет** (≤100 копий) | Непригоден для hosted Shared-gate |
| **ODA Sustaining** | 7 500 $ | 4 500 $ | **Да** | Минимум для SaaS native DWG |
| **ODA Founding** | 37 500 $ | 18 000 $ | Да + source | Избыточно |
| ODA extensions (Civil / BimRv / BimNv) | +6 250–12 500 $ | same class | Да | На пилоте не нужны |
| **CADSoftTools CAD DLL / libcad.so** | **от 1 660 $** | по прайсу | серверные лицензии | Практичный кандидат для RU-юрлица; DWG до 2027 |
| LibreDWG | 0 $ | 0 $ | GPL-3 | Неполнота + токсична для MIT |
| **Autodesk APS** Model Derivative | ~0,30 $/файл (0,1 Flex × 3 $); мин. закупка ~500 токенов ≈ 1 500 $/год | variable | cloud | **Закрыт для RF-юрлица** (см. §4) |
| Экспорт заказчиком DXF/IFC/PDF/A | 0 $ | 0 $ | N/A | **Пилот по умолчанию** |

**TCO ODA Sustaining:** 7 500 $ + 4 500 $ = **12 000 $ за два года** без интеграции (оценка интеграции 3–4 недели инженера).

---

## 4. Ограничение важнее цены

- Autodesk с **20.03.2024** запретила российским юридическим лицам использование своих продуктов и услуг (рамка 12-го пакета санкций ЕС / ст. 5n ПО для industrial design); с июля 2024 отключала доступ к облаку BIM 360 (публичные сообщения рынка).  
- **Канал APS не рассматриваем:** юридически недоступен для RF-юрлица и неприемлем по конфиденциальности (выгрузка ПД в зарубежное облако).  
- **ODA:** возможность приёма российского юрлица в члены — **отдельная проверка**; до подтверждения считаем **риском**.  
- Практически исполнимо сегодня: **CADSoftTools** либо **отказ от DWG**.

---

## 5. Решение на пилот (после замечания трекера 07.08)

**DWG не вычёркивается из ТЗ.** Требование остаётся обязательным и **неподдержанным**: код отдаёт FAILED и роняет `summary.passed`, а не «почти работает».

Принимаем **IFC + PDF/A** как подтверждённый контур. Файл, полученный экспортом из DWG, проходит как **производный** вход с provenance, не как native DWG. **DXF** — Partial / Not verified; в критерии приёмки не ставить, пока нет измеренного прогона. Согласование ограниченного сценария ушло заказчику через AM 07.08; ответа в командном контуре на 14.08 нет.

| Триггер к покупке | Первый шаг |
|---|---|
| ≥ **30 %** пакетов приходят **только** в DWG **и** DWG зафиксирован в критериях приёмки заказчика | **CADSoftTools** (от 1 660 $), обкатка на ≥20 реальных файлах |
| Прокси-объекты SPDS не разбираются CADSoftTools | Тогда рассматривать **ODA Sustaining** (если членство для RF-юрлица подтверждено) |

---

## 6. Кратко (трекер)

- **Затык:** формат закрытый; LibreDWG неполна и GPL-3; nanoCAD/SPDS → прокси, семантика теряется; OCR не даёт геометрической привязки / `evidence_refs`.  
- **Цена:** ODA Sustaining 7 500 $ / 4 500 $ (12 000 $ / 2 года); альтернатива CADSoftTools от 1 660 $; APS для RF-юрлица закрыт.  
- **Решение:** DWG **остаётся в ТЗ** и остаётся FAILED; приёмка пилота через IFC + PDF/A (ПП 614, 783/пр); закупка SDK только по триггеру заказчика. Не объявлять native DWG и не вычёркивать требование молча.  
- **Код:** DWG не подключаем; регрессия — запрошенный DWG → `dwg_dxf=FAILED` и `summary.passed=false`.

---

## 7. Code honesty (no DWG feature)

Regression (must stay green):

- `tests/test_four_direction_honesty.py::test_requested_dwg_path_fails_and_blocks_summary_passed`  
- `tests/test_cad_office_ingest.py::test_dwg_fail_closed_without_oda`  
- `tests/test_four_direction_honesty.py` — FAILED `dwg_dxf` / native DWG never OK  
- `tests/test_red_team_signoff_remediation.py::test_rt_d_mixed_dwg_dxf_capability_failed`
