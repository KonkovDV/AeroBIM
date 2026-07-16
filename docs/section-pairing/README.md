---
title: PD/RD section pairing scaffold
status: active
last_updated: "2026-07-10"
---

# Детерминированная сверка ПД↔РД по разделу

`SectionDiffAnalyzer` закрывает отдельный Task 07 use case **sections vs
sections**, а не переименовывает generic cross-document поиск. Текущий P1
контракт принимает одну нормализованную пару JSON ПД↔РД (референс: АР).

## Что проверяется

- `project_id`: разные проекты отклоняются как неправильная пара;
- роли стадии: первый документ только `PD/ПД`, второй только `RD/РД`;
- `discipline` сверяется по **каноническому коду** (RU/EN алиасы `АР`↔`AR`,
  `КЖ`↔`KZH` … сводятся к одному коду; `АР` против `AR` больше не даёт ложный
  mismatch), плюс `section_code`;
- `basis.document_id` и `basis.revision` РД относительно ПД;
- сопоставление PD↔RD выполняется по **каноническому ключу** (см. ниже), а не по
  сырой строке ключа — RU-алиас `защитный.слой` (РД) сходится с EN-ключом
  `rebar.cover` (ПД) детерминированно, без fuzzy;
- наличие каждого `required_in_rd` key;
- строковое exact/casefold сравнение;
- числовое сравнение после SI normalization (`mm↔m`, `m2`, углы и т. п.);
- explicit `tolerance_si` либо общая `ToleranceConfig`;
- несовместимые/неизвестные units как `UNIT_MISMATCH`, а не silent equality.

Каждый finding получает стабильный `rule_id`, `FindingCategory.CROSS_DOCUMENT`,
`ConflictKind`, source pair, `target_ref`, `problem_zone`, modality и confidence.
`rule_id` строится из транслитерированного Latin-slug (`КЖ` → `KZH`), поэтому
кириллические коды дают стабильные ASCII-идентификаторы, безопасные для BCF/URL.
Нечёткое сопоставление, OCR/CV и LLM в этом контуре **не используются**.

## Канонизация: дисциплины и ключи (P1, усилено 2026-07-11)

`aerobim.domain.section_pairing` (чистый Domain-слой, без Infrastructure) держит
детерминированный словарь:

- **Реестр дисциплин** — RU/EN марки комплектов (`АР/AR`, `КЖ/KZH`, `КМ/KM`,
  `КР/KR`, `ГП/GP`, `ОВ/OV`, `ВК/VK`, `ЭОМ/EOM`, `СС/SS`, `ПС/ОПС`, `ТХ/TKH`,
  `ПБ/PB`, `ООС/OOS`, `ПЗ/PZ`) → единый canonical code + человекочитаемый label;
- **Реестр канонических ключей** — discipline-scoped + общие (common) ключи с
  RU/EN алиасами (`высота.здания`→`building.height`,
  `защитный.слой.бетона`→`rebar.cover`, `этажность`→`floor.count` …).

Нераспознанные дисциплины/ключи **не отбрасываются**: они нормализуются и
сравниваются как есть, но помечаются `recognized=False`, чтобы capability не
выглядел полным. Если два ключа в одном документе сходятся к одному
каноническому ключу — запрос **fail-closed** (`ValueError`), а не тихое
перекрытие.

Это по-прежнему **scaffold-словарь**, засеянный под синтетическое жильё, а не
заявка на полное покрытие СП/ГОСТ. Заморозка customer canonical-keys остаётся
блокером (см. ниже).

Schema: [`section-pair.schema.json`](../../samples/sections/section-pair.schema.json).
Synthetic fixtures:

- АР (Latin): [`ar-pd-synthetic.json`](../../samples/sections/ar-pd-synthetic.json),
  [`ar-rd-synthetic.json`](../../samples/sections/ar-rd-synthetic.json);
- КЖ (Cyrillic + RU-алиас):
  [`kzh-pd-synthetic.json`](../../samples/sections/kzh-pd-synthetic.json),
  [`kzh-rd-synthetic.json`](../../samples/sections/kzh-rd-synthetic.json).

АР-fixture намеренно создаёт 3 finding: area mismatch, missing RD door criterion
и facade material mismatch. Эквивалентные `30 m↔30000 mm`, `250 mm↔0.25 m` и
`1.2 m↔1200 mm` не должны давать false positive.

КЖ-fixture демонстрирует **вторую дисциплину** и кросс-язычную канонизацию:
стадии `ПД/РД` и марка `КЖ` заданы кириллицей; RU-ключ `защитный.слой` (РД)
сходится с EN-ключом `rebar.cover` (ПД), а SI-эквивалент `25 mm↔0.025 m` не даёт
false positive. Ожидаемые 3 finding: `concrete.class`, `slab.thickness`,
missing `foundation.depth`.

## API

Оба storage-relative path обязательны вместе:

```json
{
  "ifc_path": "uploads/<id>/model.ifc",
  "requirement_text": "...",
  "pd_section_path": "uploads/<id>/ar-pd.json",
  "rd_section_path": "uploads/<id>/ar-rd.json"
}
```

Если задан только один path, запрос завершается `400`; если adapter не
сконфигурирован — `503`. Успешное выполнение отражается в
`capabilities.section_pairing`, чей `reason` теперь честно отражает
**canonical-key coverage** и распознанность дисциплины, например:
`paired KZH [recognized] kzh-pd.json -> kzh-rd.json; canonical-key coverage=5/5;
findings=3`. Наличие finding не маскируется как failure adapter-а.

Порт `SectionDiffAnalyzer` даёт два метода: `compare(...) -> list[ValidationIssue]`
(минимальный findings-only контракт для обратной совместимости) и
`analyze(...) -> SectionPairingReport` (findings + метаданные покрытия для
capability). Use case вызывает `analyze`.

## Ограничения и следующий customer шаг

Это **pairing scaffold**, не универсальный parser ПД/РД. До customer corpus:

- JSON нормализуется из PDF/XML/ведомостей вручную или согласованным ingestion;
- не заявляется покрытие всех разделов;
- нет customer precision;
- требуется реальная пара АР или КЖ, список canonical keys и две adjudicating
  стороны;
- после intake нужно заморозить mapping key↔лист/таблица/GUID и прогнать
  [`DETECTION_PRECISION_PROTOCOL_2026.md`](../evaluation/DETECTION_PRECISION_PROTOCOL_2026.md).
