<!-- claims-lint: allow-file reason="OSINT on CAD SDK licenses; not a native RVT/NWD claim; NO_GO" -->
---
title: "Native CAD license fork — OSINT (retrieved 2026-08-30)"
date: "2026-08-30"
last_updated: "2026-09-01"
status: active
version: "1.0.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Public price lists and licenses for closed CAD formats. Not a DWG-ready
  product. Not a RVT/NWD reader. Not a purchase. Checkpoint NO_GO.
---

# Лицензионная вилка native CAD (OSINT, 30.08.2026)

Закрытые форматы стоят в п. 1.1.5 ТЗ. Позиция для жюри — **посчитанная**, не оправдательная. Этот файл фиксирует публичные источники; цифры — attributed на дату retrieval. Покупка не совершена. Native ingest остаётся fail-closed ([`NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md`](../tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md); [ADR-003](../architecture/ADR-003-dwg-oda-trial-kt3-2026.md)).

## 1. Open Design Alliance

Источник: [opendesign.com/pricing](https://www.opendesign.com/pricing) и [oda-membership](https://www.opendesign.com/oda-membership); PDF 2026: [ODA Membership & Extension pricing](https://www.opendesign.com/agreements/2026/en/ODA%20Membership%20%26%20Extension%20pricing.pdf). Retrieved **2026-08-30**.

| Уровень | Первый год (USD) | Продление (USD) | Web/SaaS | Распространение |
|---|---|---|---|---|
| Commercial | 3 000 | 2 250 | нет | до 100 копий |
| **Sustaining** | **7 500** | **4 500** | да | unlimited |
| Founding | 37 500 | 18 000 | да | unlimited + source |

Core Sustaining включает Drawings / IFC / Architecture / Publish / Visualize / Open Cloud. Это **DWG-контур**, не Revit и не Navisworks.

**Расширения (Sustaining, annual, attributed):**

| SDK | Формат | Sustaining (USD) |
|---|---|---|
| BimRv | Revit `.rvt` | 6 250 |
| BimNv / BimNw | Navisworks | 6 250 |

**Red Team.** Атака: «Sustaining 7 500 $ закрывает native RVT/NWD». Тормоз: RVT требует Sustaining **плюс** BimRv; NWD — **плюс** BimNv. Нижняя оценка первого года для пары RVT+NWD: 7 500 + 6 250 + 6 250 = **20 000 USD**, затем продление core 4 500 плюс оба расширения. Подписка ежегодная: при прекращении теряется право распространять продукт на SDK (FAQ ODA). Юрлицо — предусловие договора, не git.

## 2. CADSoftTools CAD .NET

Источник: [cadsofttools.com/products/cad-net/buy/](https://cadsofttools.com/products/cad-net/buy/). Retrieved **2026-08-30**: «License prices start at **765 USD**». Издание, число разработчиков и end-user volume задают квоту. Путь — DWG/DXF, **не** Revit/Navisworks.

**Red Team.** Историческая цифра «от 1 660 $» в рабочих заметках **не** подтверждена публичной страницей 2026 и в речь не идёт.

## 3. LibreDWG (GNU)

Источник: [github.com/LibreDWG/libredwg](https://github.com/LibreDWG/libredwg/) — **GPL-3.0 or later**. Динамическая линковка в MIT-ядро делает комбинированное произведение GPL-3 (FSF FAQ; OSArch 2024). Несовместимо с LICENSE этого дерева без смены лицензии ядра. [ADR-002](../architecture/ADR-002-open-core-commercial-boundary-2026.md) такую смену не открывает.

## 4. Autodesk (канал для российского юрлица)

Autodesk News, 4 марта 2022: приостановка бизнеса в России ([adsknews](https://adsknews.autodesk.com/en/views/crisis-in-ukraine/)). Последующие публичные сообщения (2024) о запрете использования продуктов российскими юрлицами — attributed news, не юридическое заключение этого репозитория. Вывод для MVP: **штатный канал Revit API / Navisworks API для российского юрлица не является доступным путём закупки**. Это не доказательство «формат нельзя читать никогда», это доказательство «не купить официально в горизонте КТ#3».

## 5. Обход, который уже заявлен как регламент обмена

IFC 2x3 / IFC4 / IFC4x3 — штатный экспорт authoring tools (в том числе Revit). Native RVT/NWD в MVP закрывается **регламентом передачи IFC**, не SDK. Это не «мы читаем RVT». Сводная NWD → IFC — на стороне назначающей стороны (вопрос заказчику; T2 BCF в их СОД отдельно, NOT_VERIFIED). **Stock Navisworks не пишет IFC** (плагины требуют установленного Navisworks). Карта семи классов решения: [`FORMAT_INGEST_TRIAGE_2026_09.md`](FORMAT_INGEST_TRIAGE_2026_09.md). Retrieved прайса ODA **2026-08-30**; страница pricing жива **2026-09-01**.

buildingSMART Validation Service принимает несжатый `.ifc` **не более 256 MB** ([user guide](https://buildingsmart.github.io/validate/user/index.html); UI: «256mb max»). Default `AEROBIM_MAX_IFC_BYTES` = 256 **MiB** SPF in-memory — сопоставимый порядок, **не** та же единица. До 1,5 ГБ analyze идёт через IfcOpenShell RocksDB, не через SPF RAM. WASM остаётся 256 MiB. Native DWG/RVT — not claimed.

## 6. Что говорить / не говорить

Можно: лицензионная вилка посчитана по публичным прайсам на дату retrieval; native ingest fail-closed; обмен — IFC.

Нельзя: «купим ODA к финалу»; «7 500 $ = RVT»; «CADSoftTools 1 660 $»; «LibreDWG в MIT»; «Autodesk API подключим»; DWG-ready / RVT-ready.

`predicted_aerobim_total() is None`. Checkpoint **NO_GO**.
