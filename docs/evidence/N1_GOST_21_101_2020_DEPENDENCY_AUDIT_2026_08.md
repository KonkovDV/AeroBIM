---
title: "N-1 audit — dependencies on GOST R 21.101-2020 / year-less 21.101"
date: 2026-08-05
status: AUDIT_ONLY
claim_boundary: >-
  Inventory of citations and related completeness/revision/cipher surfaces.
  No code or norm-pack edits in this step. Not a claim of compliance with
  GOST R 21.101-2026. Standard text not yet cited by clause number.
---

# N-1 · Аудит зависимости от ГОСТ Р 21.101-2020

**Шаг протокола:** 1 — список до правок. **Правки запрещены до подтверждения владельцем.**

**Дельта этого шага:** порты/адаптеры/DI **+0/+0/+0** (только документ аудита). Живая инвентаризация остаётся 46 / 71 / 59.

**Оговорка:** полный PDF/текст ГОСТ Р 21.101-2026 в репозитории **нет**. Пункты стандарта в этом файле **не** цитируются. Для N-2 нужен текст стандарта (владелец / правовой доступ).

---

## A. Прямые упоминания `21.101` / `21.101-2020` / `21.101-2026`

| # | Путь | Строки / место | Что написано | Риск |
|---:|---|---|---|---|
| A1 | `docs/evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md` | ~142, ~201 | «ГОСТ Р 21.101» **без года** + пометка сверить с 2026 | Эксперт слышит «по 21.101» без редакции |
| A2 | `docs/research/EXTERNAL_SOURCES_P1_P4_GOST_2026_08_05.md` | frontmatter, § GOST | 2026 заменяет 2020; риск edition | Research only; даты по обзорам/ГАРАНТ, **не** по пункту стандарта |
| A3 | `docs/norm-pack-governance-2026.md` | ~19 | P0 edition risk 2026 vs 2020 | Governance flag; нет поля выбора редакции в рантайме |
| A4 | `docs/ENGINEERING_STATUS_2026_08.md` | ~31 | «21.101-2026 risk flagged» | Статус, не runtime |
| A5 | `docs/evidence/weekly-eng-status-latest.json` | blockers list | «Norm-pack edition: …2026 supersedes 2020» | Сгенерированный статус |
| A6 | `backend/src/aerobim/tools/export_weekly_eng_status.py` | ~78 | та же строка в коде экспорта | Хардкод риска в weekly export |

**В коде домена / адаптерах / fixture rule-packs явной строки `21.101` / `21.101-2020` не найдено** (поиск по `samples/rule-packs/`, `backend/src/`).

---

## B. Поверхности, которые *ведут себя* как правила 21.101 (без явной цитаты)

Это не доказательство «реализован 21.101-2020», а места, где смена редакции 2026 затронет поведение или заявления.

### B1. Шифры / марки разделов (комплектность + pairing)

| # | Путь | Содержание | Замечание vs N-1 задачи |
|---:|---|---|---|
| B1.1 | `backend/src/aerobim/domain/section_pairing.py` | `_DISCIPLINE_DEFS`: AR, KZH, KM, KR, GP, OV, VK, EOM, SS, **PS**, TKH, **PB**, OOS, PZ | **ПБ** и **ПС** уже есть (ПС = fire alarm). Марки **ОС** и новых разделов (благоустройство / ОДД) **нет** |
| B1.2 | `backend/src/aerobim/domain/package_completeness.py` | `DEFAULT_RESIDENTIAL_MANDATORY_PD = (PZ, AR, KZH)`; cipher match для AR/KZH | Fixture-grade; claim_boundary отрицает полноту ПП-87 / статутный 21.101 |
| B1.3 | `backend/src/aerobim/domain/package_completeness.py` | rules: `MISSING-SECTION`, `UNPAIRED-SECTION`, `MISSING-CIPHER`, `CIPHER-MISMATCH`, … | Любая устаревшая/неполная таблица марок → ложные срабатывания на свежих комплектах |
| B1.4 | `samples/packages/*-inventory.json` | объявленные дисциплины/шифры | Фикстуры под текущий scaffold, не под 2026 |
| B1.5 | `docs/ENGINEERING_STATUS_2026_08.md` | WP-05 cipher/specs/PD↔RD | Документирует поведение B1.2–B1.3 |
| B1.6 | `docs/evidence/TASK3_COMPLETENESS_DEMONSTRATOR_2026_08_05.md` | #9/#10 `drawing_purpose` / роли листа | MISSING_ATTRIBUTE — смежно с ролями листов 21.101-класса |

### B2. Ревизионный контроль / версии документов

| # | Путь | Содержание | Замечание |
|---:|---|---|---|
| B2.1 | `backend/src/aerobim/domain/ingestion.py` | `revisions_conflict`, `detect_revision_merge_conflicts` | Строковый `revision` + VERSION_MISMATCH / AMBIGUOUS; **не** порядок изменений ПД/РД и GUID-изменений по 21.101 |
| B2.2 | `backend/src/aerobim/application/services/analyze_orchestrators.py` | вызывает revision-merge | Тот же контракт |
| B2.3 | `backend/tests/test_p0_remediation_fail_closed.py` | one-sided revision | Тесты текущей логики |
| B2.4 | `docs/dataset/IFCDIFF_TZ_GAP_NOTE_2026_08_04.md` | STAGE/VERSION_MISMATCH ≠ multi-package CDE | Честный gap |
| B2.5 | `docs/architecture/KIMI_K3_SCENARIO_MATRIX_2026_07_27.md` | SAM-TYP-015 VERSION_MISMATCH | Сценарий, не ГОСТ |

### B3. Норм-пак: поля редакции (есть каркас, нет 21.101)

| # | Путь | Содержание | Замечание |
|---:|---|---|---|
| B3.1 | `samples/rule-packs/norm-rule-pack.schema.json` | `edition`, `norm_edition`, `norm_edition_date` | Pack-level edition есть; **нет** поля «проверять комплектность по 21.101-2020 vs 2026» |
| B3.2 | `backend/src/aerobim/infrastructure/adapters/json_norm_rule_pack_loader.py` | schema 2.0 требует `norm_edition` + date | Механика готова к N-1.4; контента 21.101 нет |
| B3.3 | `backend/src/aerobim/domain/models.py` | `NormRulePack.norm_edition*` | То же |
| B3.4 | `samples/rule-packs/norm-pack-v2-draft-example.json` | draft SP-54 / прочее | **Нет** строк `21.101` |
| B3.5 | `samples/rule-packs/customer-norm-pack-intake-template.json` | placeholders | То же |
| B3.6 | `docs/norm-pack-governance-2026.md` | lifecycle + P0 21.101 risk | Уже знает о смене редакции |

### B4. Электронная подпись / удостоверяющий лист (смежно N-1.5, не 21.101-код)

| # | Путь | Содержание |
|---:|---|---|
| B4.1 | `docs/signature-and-immutability-2026.md` | граница: не УКЭП |
| B4.2 | `backend/src/aerobim/infrastructure/adapters/json_detached_signature_auditor.py` | envelope only |
| B4.3 | `docs/research/SOURCE_VERIFICATION_REPORT_2026_08_04.md` | УКЭП vs ИУЛ; Минстрой 4420-КМ/14 |
| B4.4 | `audit/reports/CLAIMS_LOCK_2026_07_17.md` | запрет «УКЭП проверена» |

Новый 21.101-2026 (удостоверяющий лист / ЭП) **не** отражён в коде; Claims Lock уже запрещает overclaim — сохранить при любых правках.

### B5. Терминология / демо / питч (заявления)

| # | Путь | Риск |
|---:|---|---|
| B5.1 | Exp B AR row «состав томов ≠ ГОСТ Р 21.101» | Год редакции не в формулировке замечания |
| B5.2 | Weekly / ENGINEERING_STATUS | Уже флагуют 2026, но могут читаться как «мы уже по 2026» |

---

## C. Чего в репо **нет** (пробелы к N-1.2–N-1.5)

1. Официальный текст / оглавление ГОСТ Р 21.101-2026 с номерами пунктов (блокер для N-2 и для правок «по пункту»).  
2. Конфигурируемый переключатель редакции комплектности `21.101-2020` ↔ `21.101-2026` (дата введения 01.04.2026).  
3. Canonical mark **ОС** и новые разделы (благоустройство / организация дорожного движения) в `_DISCIPLINE_DEFS`.  
4. Логика «разрешение на изменение / выпуск новой версии / GUID изменения» по 21.101 — только generic revision strings.  
5. Rule-pack rows, явно ссылающиеся на 21.101 любой редакции.  
6. Файл `docs/regulatory-baseline-2026.md` (N-3) — ещё не создан (следующий шаг после N-1 правок / параллельно).

---

## D. Вывод аудита (без правок)

| Класс | Вердикт |
|---|---|
| Жёсткая привязка кода к **21.101-2020** | **Не найдена** (нет year-pinned правил в Python/JSON packs) |
| Year-less / prose риск | **Есть** (Exp B + governance + weekly) |
| Scaffold марок, затронутый 2026 | **Есть** (`section_pairing` + `package_completeness`) — ПБ/ПС уже; **ОС и новые разделы** — нет |
| Ревизии как 21.101 process | **Нет** — только merge-guard по строке revision |
| Поле редакции стандарта для прогона | **Частично** — `norm_edition` есть, семантика 21.101 cutoff — нет |

---

## E. Что требуется от владельца перед шагом N-1 правок

1. **ТРЕБУЕТСЯ ОТ ВЛАДЕЛЬЦА:** доступ к полному тексту ГОСТ Р 21.101-2026 (PDF/СПС) для цитирования пунктов (N-2 запрещает пересказ по новостям).  
2. Подтвердить, что список выше полный для старта правок, или дополнить путями вне репо (локальные PDF, `.local/`).  
3. Не заявлять «соответствуем 21.101-2026» до пункта N-2 с номером пункта.

**Стоп.** Следующий шаг по порядку протокола — **R-5 (гейты)** или подтверждение владельца идти сразу к N-1 правкам после получения текста стандарта.
