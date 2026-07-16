---
title: External standards and mandate check
status: verified-online
checked_at: "2026-07-10T22:00:00+03:00"
---

# External evidence check — 2026-07-10

Проверка выполнена по первичным/официальным страницам. Это engineering note,
не юридическое заключение и не лицензия на автоматическую проверку всех норм.

| Контур | Первичный источник | Наблюдение на 2026-07-10 | Решение AeroBIM |
|---|---|---|---|
| IDS | [buildingSMART: IDS v1.0 Final Standard](https://www.buildingsmart.org/information-delivery-specification-ids-v1-0-is-approved-as-a-final-standard/) | IDS 1.0 объявлен Final 2024-06-04; назначение — machine-readable information requirements и автоматическая проверка delivery | Сохранять IDS 1.0 baseline/IfcTester; JSON norm pack не выдавать за IDS; geometry остаётся отдельным SPATIAL capability |
| IFC | [buildingSMART IFC schema specifications](https://technical.buildingsmart.org/standards/ifc/ifc-schema-specifications/) | Официальный release database остаётся источником schema/errata | Сохранять IfcOpenShell + schema pre-gate; не фиксировать выдуманный «IFC 2026» |
| BCF | [buildingSMART BCF overview](https://technical.buildingsmart.org/standards/bcf/) и [BCF-XML 3.0 Final](https://github.com/buildingSMART/BCF-XML/releases/tag/v3.0) | BCF поддерживает file и REST issue exchange; BCF-XML 3.0 — final release | BCF 2.1 остаётся default для совместимости, 3.0 opt-in; AeroBIM не становится proprietary issue hub |
| OpenCDE / BCF API | [buildingSMART BCF API release 3.0](https://github.com/buildingSMART/BCF-API/blob/release_3_0/README.md) | BCF API 3.0 относится к OpenCDE API family и опирается на Foundation API | Сохранять существующий BCF API push foundation; полный Documents API не объявлять готовым |
| ISO 19650 | [ISO/DIS 19650-1 Edition 2](https://www.iso.org/standard/89703.html) | На 2026-07-10 это **Draft International Standard**, under development, stage 40.60; заменит 2018 edition только после публикации | Не выдавать DIS за действующий final; сохранять `ISO 19650-lite` metadata и отслеживать терминологию EIR/IPR без migration claims |
| РФ: информационная модель | [ПП РФ №331 от 05.03.2021](http://publication.pravo.gov.ru/Document/View/0001202103100026) | Официальный акт о случаях формирования/ведения информационной модели | Использовать как контекст intake; не выводить из него готовность проверки всех обязательных требований |
| РФ: состав/форматы ИМ | [ПП РФ №614 от 17.05.2024](http://publication.pravo.gov.ru/document/0001202405170050) | Официальные правила формирования/ведения ИМ, состав и электронные форматы | Поддерживать traceable exchange artifacts; конкретные обязательные правила переводить только в согласованный pack |
| Task 07 | [TechLab Самолёт](https://i.moscow/techlab/samolet) | Страница по-прежнему требует ПД/РД, 2D, BIM, ТЗ, расчёты, нормы/разделы, замечания, визуализацию; срок анализа до 30 минут; экспертная валидация сохраняется | P1 фокус: norm packs, section pairing, precision/adjudication harness; HITL и claim boundary не ослаблять |

## Что изменилось относительно апрельских incubator packets

1. ISO 19650 Edition 2 теперь видим как DIS 2026 (stage 40.60), но **не** как
   опубликованный International Standard. Поэтому migration EIR→IPR остаётся
   terminology tracking, не нормативной миграцией продукта.
2. IDS 1.0 и BCF 3.0 не требуют смены baseline: их final status подтверждён;
   P1 реализует customer criteria вокруг них, а не новый proprietary format.
3. Российские акты подтверждают необходимость управляемого состава/форматов ИМ,
   но не дают основания claim «полный СП/ГОСТ».
4. Текущий Task 07 mandate подтверждает expert-in-loop; P1 precision gate требует
   двух adjudicators и не публикует synthetic quality.
5. Incubator PPTX/startup packets не восстанавливались и не использовались как
   evidence; SSOT и официальные источники имеют приоритет.

## Re-check trigger

Повторить online check перед pilot scope freeze или при публикации ISO 19650
Edition 2 / нового IDS release. Любое изменение default standard требует tests,
compatibility note и обновления claim boundary.
