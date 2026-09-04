<!-- claims-lint: allow-file reason="URL verification of open proxies; RT stay OPEN; forbidden phrases as non-claims" -->
---
title: "Проверка открытых прокси на RT-001/002/003 (вечер 23.08.2026)"
date: "2026-08-23"
checkpoint: GO
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Link check + mapping onto pins already in this repo. Open IFC/IDS/BCF
  do not close RT-001 (RF PD + expertise labels), RT-002 (Samolet-signed
  profile), or RT-003 (federated MEP delivered). Not product accuracy.
  Not a customer SLA. Not a published-state CDE. Manual TP/FP on student
  IFC is not dual-expert κ.
---

# Открытые источники: что реально скачивается и чего они не закрывают

Срез поиска 23.08 вечером сверен с пинами репозитория и с живыми URL.  
**Вердикт:** это усиление **L1/L2** (open bench / fixture). Это **не** CLOSED по RT-001/002/003 и не замена комплекта Самолёта.

Смежные описи: [`RT001_002_003_WITHOUT_SAMOLET_2026_08_14.md`](../evidence/kt3-without-customer-2026-08.md) · [`../DATASETS.md`](../DATASETS.md) · [`../dataset/RENGA_PNST909_LOCAL_PIN_2026_08_05.md`](../dataset/RENGA_PNST909_LOCAL_PIN_2026_08_05.md).

## Исправления URL (не копировать из черновика поиска вслепую)

| Как было в черновике | Рабочий URL | Статус |
|---|---|---|
| «GNI BIM» Zenodo `19722012` | **GNI** BIM, [10.5281/zenodo.19722012](https://doi.org/10.5281/zenodo.19722012) · GitHub [ZijianWang-ZW/GNI-BIM-Dataset](https://github.com/ZijianWang-ZW/GNI-BIM-Dataset) | **Уже в `.local/gni-bim`**: 224 header / 223 parse |
| `buildingSMART/Sample-Test-Files` | [buildingSMART/Sample-Test-Files](https://github.com/buildingSMART/Sample-Test-Files) (Schependomlaan subset: `IFC 2x3/Schependomlaan`) | Частично в IFC-Bench / Sample-Test-Files pin |
| `huggingface.co/datasets/sylvainHellin/ifc-bench` | [sylvainHellin/ifc-bench](https://huggingface.co/datasets/sylvainHellin/ifc-bench) | **Уже запинен**, smoke 27/1026 |
| `github.com/IfcOpenShell/files` | [IfcOpenShell/IfcOpenShell-files](https://github.com/IfcOpenShell/IfcOpenShell-files) (issue-referenced fixtures) | Регресс парсера, не экспертиза |
| `openBIMstandards/DataSetSchependomlaan/releases` | Репо **переехал**. Полный zip: [releases на Archive-DataSetSchependomlaan](https://github.com/openBIMstandards/DataSetSchependomlaan/releases) (форк [jakob-beetz](https://github.com/jakob-beetz/DataSetSchependomlaan) указывает на тот zip). Канон bSI: Sample-Test-Files | **Не вендорить целиком в git**; pin в `.local/` |
| `rengabim.com/shablons/` | [rengabim.com/shablons/](https://rengabim.com/shablons/) · Я.Диск пина: см. `RENGA_PNST909_LOCAL_PIN` | ПНСТ **909-2024**, не «909». ToS: не вендорить бинарники |
| `github.com/EdvardGK/ifcfast/issues/141` | [EdvardGK/ifcfast#141](https://github.com/EdvardGK/ifcfast/issues/141) | Issue **есть**. Архив TMK **не публикуется** (клиент, `scratch/g55`) |
| `github.com/devkon-at/ifc-clash-experiments` | [devkon-at/ifc-clash-experiments](https://github.com/devkon-at/ifc-clash-experiments) (`column_duct_touching.ifc`) | Smoke clash, MIT-adjacent experiments |
| `github.com/clashcontrol-io/ClashControl` | [clashcontrol-io/ClashControl](https://github.com/clashcontrol-io/ClashControl) | **SSPL** — не копировать в MIT-дерево; только внешняя ссылка |
| PDF Мосэкспертизы / СПб ЦГЭ с разовыми `upload/iblock` | Живые комплекты IDS: МОГЭ, АГР «СтроимПросто», СПб ГАУ ЦГЭ — уже в `samples/ids/` | Разовые PDF на `mos.ru/upload` проверять перед цитированием; не = подпись Самолёта |

## RT-001 — корпус точности

Нужно для CLOSED: комплект ПД/РД + заключение экспертизы + ≥2 разметчика + κ/α + held-out.  
Публичного «ПД РФ + заключение» по-прежнему **нет**.

| Источник | Что даёт | Закрывает RT-001? | Уже у нас |
|---|---|---|---|
| GNI BIM (CC BY 4.0), 224 IFC | Студенческие модели, 7 пар AR+KR | **Нет.** Нет заключения. Своя разметка TP/FP одним автором ≠ dual-rater κ | Да, `.local/gni-bim` |
| IFC-Bench v2 | 1027 QA, не замечания экспертизы | **Нет.** QA по модели | Да, pin + smoke |
| Sample-Test-Files | Референс IFC | **Нет.** Эталон схемы, не ошибки ПД | Да |
| IfcOpenShell-files | Issue-привязанные баги парсера | **Нет.** Баги тулинга | Нет нужды вендорить |
| Schependomlaan + BCF | Реальный NL-проект, clash topics | **Нет.** Коллизии ≠ замечания экспертизы РФ | Partial (IFC-Bench / BatchPlan examples) |

**Честный ход до 30.08:** не качать 10 ГБ заново, если GNI уже на диске. Взять **20–30** уже распарсенных IFC, заложить дефект *или* разметить IDS-fail как engine regression. Публиковать только как **fixture / open-bench**, с `n`, протоколом и «не точность Самолёта».

## RT-002 — подписанный профиль приёмки

Нужно для CLOSED: подпись **заказчика программы** + `pack_hash`.

| Источник | Что даёт | Закрывает RT-002? |
|---|---|---|
| ПНСТ 909 + комплект Renga (22 сценария IDS) | RU IDS + IFC; ToS «ознакомительные» | **Нет.** Издательский pack ≠ профиль Самолёта. У нас runtime **18/22**, 4 без IDS в pack |
| IDS МОГЭ / АГР / СПб ЦГЭ в `samples/ids/` | Официальные гос. IDS | **Нет.** Уже было. Не `pack_hash` Самолёта |
| SmartIDS / ValidBIM (ИСП РАН) | Редактор/сервис | Инструмент, не подпись |
| Pilot-BIM trial | Чужая СОД с IDS | **Не** наше CDE-proof, не T2 импорт Самолёта |

«Адаптировать IDS ПНСТ под Самолёта и назвать signed profile» — **запрещено**. Подпись ставит организация, отдавшая корпус, своим `pack_hash`.

## RT-003 — федеративный MEP clash

Нужно для CLOSED: федерация заказчика + signed scope + геометрический clash ≠ AABB.

| Источник | Что даёт | Закрывает RT-003? |
|---|---|---|
| Schependomlaan BCF (Solibri/Tekla) | Размеченные коллизии NL-проекта | **Нет.** Не MEP delivered Самолёта. Можно как **L2 rehearsal**, если zip уйдёт в `.local/` |
| G55 / TMK12–15 ([ifcfast#141](https://github.com/EdvardGK/ifcfast/issues/141)) | Оракул vs Solibri BCF | **Не датасет.** Клиентские IFC+BCF вне GitHub. **Не копировать** |
| `column_duct_touching.ifc` | 1 касание колонна↔воздуховод | Smoke. Уже есть посаженные пары в evidence |
| ClashControl (SSPL) | Пример UI clash | Не вендорить; IfcClash уже в контуре |
| COMPAS IFC Duplex | Граф портов | Advisory, не GT clash |

Цифра «RT-003 на 70%» **не публикуется**. Нет такого замера.

## Что делать на этой неделе (без 12 ГБ сюрприза)

1. **Не** качать GNI повторно — он уже в `.local/gni-bim`. Зафиксировать subset-манифест 20 файлов для ручной разметки (один разметчик = protocol rehearsal, не κ).
2. **Pin Schependomlaan** в `.local/schependomlaan/` с NOTICE (полный zip с releases **или** bSI Sample-Test-Files subset). Не в git.
3. **ПНСТ 909:** не обещать 22/22. Цитировать 18/22 EXECUTED / 4 без IDS, как в evidence.
4. **G55 не трогать.**
5. ClashControl / SSPL — только ссылка.
6. Речь на КТ#3: «open-bench + гос. IDS + честный NO_GO», не «блокеры закрыты открытыми данными».

## Лицензии (коротко)

| Pack | Лицензия | В MIT-git |
|---|---|---|
| GNI BIM | CC BY 4.0 | Нет (объём); pin + атрибуция |
| IFC-Bench QA | CC BY 4.0; часть IFC GPLv3 | QA pin; GPL IFC только `.local/` |
| Sample-Test-Files | per-file / bSI | Уже с NOTICE |
| Schependomlaan | scientific/open per README владельцев | `.local/` + NOTICE, не vendor |
| Renga ПНСТ | ToS издателя | `.local/` only |
| ClashControl | SSPL | Нет |
| G55 | клиент ifcfast | Нет |
