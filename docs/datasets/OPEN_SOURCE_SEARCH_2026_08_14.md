<!-- claims-lint: allow-file reason="Open-source dataset search 14.08; counts as citations; NO_GO" -->
---
title: "Поиск открытых датасетов — 14.08.2026"
date: "2026-08-14"
claim_boundary: "Inventory. Open corpora ≠ RF PD+expertise. Not product accuracy. Checkpoint NO_GO."
---

# Поиск и прогон открытых комплектов (14.08)

Публичного корпуса «ПД РФ + заключение экспертизы» по-прежнему **нет**. Это не закрывает RT-001.

## Поиск 14.08 (GitHub, Hugging Face, госэкспертизы)

| Источник | Статус | Что делать |
|---|---|---|
| IFC-Bench v2 (HF `sylvainHellin/ifc-bench`) | Уже в `.local/ifc-bench-v2`. Card: 22 проекта / 51 IFC / 1027 QA. Paper: 37 IFC / 21 проект — **не смешивать**. GPLv3 модели вне git | Не вендорить GPL |
| GNI BIM (Zenodo 10.5281/zenodo.19722012) | `.local/gni-bim` на диске | Student models, не accuracy |
| AEC-Bench (HF `nomic-ai/aec-bench`) | `.local/aec-bench` | Harbor **NOT_RUN** до 17.08 |
| IDS МОГЭ (moexp.ru ТИМ) | В git `samples/ids/moexp/` | Не профиль Самолёта |
| Москомэкспертиза / АГР IFC4 RV | Распоряжение ДГП-Р-1/26/64-16-6/26 с 02.04.2026: ЦИМ IFC4 Reference View обязателен для АГР Москвы | Норма, не датасет пар remark↔IFC |
| ЕГРЗ / Главгосэкспертиза | Metadata only | DEAD_CHANNEL для файлов |
| buildingSMART IDS TestCases | В git, 290, CC BY-ND | Регресс, не экспертиза |

Новых лицензионно чистых пар «чертёж+IFC+замечание экспертизы» не появилось.

## Прогон уже скачанного (эта машина, 14.08)

| Комплект | Команда | Результат | Ошибка → фикс |
|---|---|---|---|
| Schema-suite IFC2X3/4/4X3 | `export_ifc_release_matrix` | Живая таблица в [`../evidence/ifc-release-matrix-2026-08.md`](../evidence/ifc-release-matrix-2026-08.md) | IFC2X3 wall GlobalId был **23** символа → урезан до 22; `AEROBIM-IFC-GUID-INVALID` снят |
| Open corpora smoke | `run_open_corpora_profiles --mode smoke` | SHA pins **ok** | нет |
| MOEXP IDS × 1 GNI IFC | `run_moexp_on_gni_sample` | 389 executable, **0 pass / 389 fail** | не баг: студенческая модель ≠ ЦИМ МОГЭ; **не** зеленую |
| Renga ПНСТ 909 pin | `.local/renga-pnst909` | ранее `run_renga_export_probe` | не Самолёт |

## Что не прогоняли повторно сегодня

Полный GNI 223 IfcOpenShell (уже в [`../evidence/open-ifc-stress-2026-08.md`](../evidence/open-ifc-stress-2026-08.md)). IFC-Bench 1026 QA (smoke 25/1026). Harbor 160 — календарь 17.08.
