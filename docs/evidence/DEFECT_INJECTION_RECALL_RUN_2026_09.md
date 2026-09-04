<!-- claims-lint: allow-file reason="Injection recall run; synthetic mutation test; NO_GO" -->
---
title: "Defect-injection recall run — mutation-kill, synthetic-only"
date: "2026-09-03"
last_updated: "2026-09-03"
status: active
version: "1.0.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Mutation-kill recall on injected synthetics. Output-sensitivity proxy, not
  semantic defect confirmation. Not Samolet accuracy. Not product accuracy.
  Checkpoint GO; customer_go false. Two contours: channel IFC (not in git; data regime not agreed)
  and the published inject_defects mini-IFC (git-reproducible).
---

# Recall на инъекциях — прогон E2 (синтетика, не партнёр)

Формула: на замороженном источнике X при коммите
`929a787a8972daffc9d39638163fa5338f62543b` и seed **20260824** получен
mutation-kill recall Z. Не «точность продукта».

CLI склейки: `python -m aerobim.tools.evaluate_injection_recall`
(`backend/src/aerobim/tools/evaluate_injection_recall.py`). Тесты:
`backend/tests/test_evaluate_injection_recall.py`.

Прокси детекции: мутант **убит**, если мультимножество находок контура
(IFC + IDS `samples/ids/wall-fire-rating.ids` + правила
`samples/requirements/techlab-demo-rules.txt`) отличается от CONTROL
(появились или исчезли находки). Исчезнувший сигнал записывается как
сокрытие, не как подтверждение целевого дефекта. CONTROL и классы с
`applied=false` вне знаменателя. Детерминизм:
`analyze(source) ≡ analyze(CONTROL)` — **pass** на всех трёх прогонах.

Поле `source_path_sha256` в JSON — хеш **строки пути** staging-каталога,
не байтов IFC. Содержимое канальной модели в git не коммитится.

Отклонение от плана 2026-08-30: план требовал шовно-чистый пакет с
`summary.passed=true`. По команде дорожной карты 03.09 источник — канальный IFC
(дерево владельца; режим данных не согласован; не публикуется) плюс git-фикстура инжектора. Атрибуция — через
CONTROL-дифф. Recall на синтетике **не** переносится на комплект Самолёта.

## Контур 1 — канальный IFC, секции 1–3 (не в git; режим не согласован; не внешняя репродукция)

Контур не читает sidecar `.txt`; инжектор на больших IFC без
`IFCQUANTITYAREA` падает на первый numeric-токен заголовка STEP
(`5.02` = версия EDM). `MISSING_ELEMENT` / `IDS_VIOLATION` не применились
(`no-element-token` / `no-ids-token`: стены не в форме `^#n=IFCWALL...;$`,
токены `RusSet_Common` / `GrossFloorArea` в модели нет).

| Класс | KR `house_5_s1_3_kr` | AR `house_5_s1_3_ar` |
|---|---|---|
| AREA_MISMATCH | applied, header `5.02→8.520`, не убит | то же |
| LEVEL_MISMATCH | applied, storey Δ≈+1.655, не убит | storey Δ≈+1.655, не убит |
| PD_RD_DIVERGENCE | sidecar, контур не читает, не убит | то же |
| TZ_UNSATISFIED | sidecar, не убит | то же |
| MISSING_ELEMENT | не applied | не applied |
| UNIT_MISMATCH | `.MILLI.` снят с неиспользуемого LENGTHUNIT, не убит | то же |
| CALC_INCONSISTENCY | sidecar, не убит | то же |
| IDS_VIOLATION | не applied | не applied |

| Прогон | CONTROL находок | applied | убито | точечно | Wilson 95% lower | JSON |
|---|---|---|---|---|---|---|
| KR 5.8 MiB | 6 | 6 | **0** | 0.000 | **0.000** | [`defect-injection-recall-run-2026-09-03-house-5-s1-3-kr-blind.json`](defect-injection-recall-run-2026-09-03-house-5-s1-3-kr-blind.json) |
| AR 89.9 MiB | 97 | 6 | **0** | 0.000 | **0.000** | [`defect-injection-recall-run-latest.json`](defect-injection-recall-run-latest.json) |

Wilson 95% на 0/6: [0.000; 0.390]. Публикуется нижняя граница **0.000**.
`claim_level=synthetic_only`.

## Контур 2 — опубликованная mini-IFC фикстура инжектора (git-воспроизводима)

Тот же текст, что `backend/tests/test_inject_defects.py` (`_MINI_IFC` +
`sheet.txt` / `tz.txt` / `calc.txt`). Все 8 классов **applied**. Убит
только `MISSING_ELEMENT` (стена снята → контур перестал видеть IFCWALL:
+1 новая / −2 исчезнувших находки). Площадь `12.5→15.513` контур не
читает: demo-правила смотрят `IFCSPACE.NetFloorArea`, не
`IFCQUANTITYAREA('GrossFloorArea')`. Sidecar-классы контур не видит.
`IDS_VIOLATION` переименовал токен `GrossFloorArea` в тексте STEP — demo
IDS на это не завязан.

| Класс | Инъекция | Новых | Исчезнувших | Убит |
|---|---|---|---|---|
| AREA_MISMATCH | area 12.5→15.513 | 0 | 0 | нет |
| LEVEL_MISMATCH | storey 0.0→1.867 | 0 | 0 | нет |
| PD_RD_DIVERGENCE | sidecar 12.5→16.500 | 0 | 0 | нет |
| TZ_UNSATISFIED | sidecar 4→6.000 | 0 | 0 | нет |
| MISSING_ELEMENT | removed IFCWALL | 1 | 2 | **да** |
| UNIT_MISMATCH | si-prefix-milli-removed | 0 | 0 | нет |
| CALC_INCONSISTENCY | sidecar 10.0→15.000 | 0 | 0 | нет |
| IDS_VIOLATION | ids-token GrossFloorArea | 0 | 0 | нет |

- Mutation-kill: **1/8** (точечно 0.125)
- Wilson 95%: [0.022; 0.471] — публикуется нижняя граница **0.022**
- CONTROL: 9 находок; детерминизм pass
- JSON: [`defect-injection-recall-run-fixture-latest.json`](defect-injection-recall-run-fixture-latest.json)

Репродукция контура 2 (без канальных файлов): тот же mini-IFC, что в
`backend/tests/test_inject_defects.py`, затем:

```text
python -m aerobim.tools.inject_defects --source <mini-pack> --output var/injected --seed 20260824
python -m aerobim.tools.evaluate_injection_recall \
  --manifest var/injected/injection_manifest.json \
  --ids samples/ids/wall-fire-rating.ids \
  --rules samples/requirements/techlab-demo-rules.txt \
  --source-label inject_defects_mini_ifc_fixture
```

Ожидаемый хеш манифеста контура 2: `3eeeeabbccf022fdeeef48269cd2dd2a7b0986b0e13eafbad47890db2047a6ca`
(при том же seed и том же тексте mini-IFC).

## Что это не есть

- Не customer-recall, не RT-001 CLOSED, не «движок не работает».
- Число 0/6 на канальном IFC — **слепота пары инжектор↔контур** на этом IDS/rule
  pack: мутации либо не в наблюдаемом пространстве (sidecar, заголовок
  STEP, неиспользуемый MILLI), либо класс не применился.
- Число 1/8 на фикстуре — единственный класс, который demo-контур умеет
  увидеть (отсутствие IFCWALL). Не переносить на Самолёта.

Следующий замер — отдельный протокол с новым seed-журналом: либо инжектор
бьёт в `IFCSPACE.NetFloorArea` / `Pset_WallCommon.FireRating`, либо контур
читает sidecar ПД/ТЗ/расчёта. Поверх этих цифр пороги не двигаем.

Checkpoint **GO**; customer_go false. RT-001/002/003 остаются OPEN.
