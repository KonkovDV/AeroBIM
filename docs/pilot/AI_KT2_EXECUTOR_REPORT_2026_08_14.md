<!-- claims-lint: allow-file reason="KT#2 engineering brief; forbidden phrases as non-claims per Claims Lock" -->
---
title: "Инженерный бриф — КТ#2 после Wave A (HEAD 005b7bc)"
date: "2026-08-14"
status: active
claim_boundary: >
  Engineering brief only. Checkpoint NO_GO. RT-001/002/003 stay OPEN. Wave A is
  fixture evidence, not customer evidence. Not product accuracy. Not MEP
  delivered. Not CDE-ready. Not native DWG. Local Windows pytest after Wave A:
  2259 passed / 12 skipped / 0 failed — does not replace CI pin tests_passed=2167.
---

# Инженерный бриф AeroBIM (после Wave A)

Операторский отчёт по репозиторию. Не инструкция для языковой модели.  
Авторская оценка владельца 14.08 ~23:51 МСК: инженерно сильнее, стратегический риск тот же.  
**Не начинать новый фичевый слой.** Сначала focused tests → полный pytest → runtime baseline на этот HEAD → claims-lint → vertical slice.

## 0. Стоп-правила (нарушение = стоп)

1. Checkpoint остаётся **`NO_GO`**. Не писать GO / customer-ready / полностью проверено.
2. `closes_rt001` / `closes_rt002` / `closes_rt003` всегда `false`. Не править `tests/test_rt_customer_blocker_honesty_lock.py` под CLOSED.
3. Не изобретать `tests_passed`. Не редактировать README-сниппет руками «на глаз».
4. Новые порты/DI — только atomic: port + adapter + token + wiring + tests + evidence. Предпочитать extra-method.
5. Один заказчик программы Техлаб — **Самолёт**. А101 / Галс как второй заказчик программы запрещены.
6. Не вендорить LibreDWG (GPL-3). Не скрейпить закрытые API ЕГРЗ. Не копировать чужие клиентские BCF.
7. Коммит / пуш — **только по явной команде** пользователя.
8. Не создавать фиктивное видео. Запись 19.08 — человек.
9. Не тратить календарь КТ#2 на AEC-Bench Harbor, ODA trial, live CDE, новый MEP-провайдер.

## 1. Текущий контекст

| Поле | Факт (проверено `git` 14.08 вечер) |
|---|---|
| Репозиторий | https://github.com/KonkovDV/AeroBIM |
| HEAD | `005b7bcb6fb2b9f353cc046b44fe68f1b519b776` |
| Дата коммита | 2026-08-14 23:40:53 +0300 |
| Сообщение | `feat(kt2): Wave A survey XSD, clearance clash, IDS audit (blockers stay OPEN)` |
| Родитель | `dd1a0a70aa1b6328ccfd912820fa88638f72899f` |
| Diff vs parent | 38 files, **+12116 / −80** (git). Основной объём — вендоренные XSD |
| Working tree at brief | clean on `main` tracking `origin/main` |
| GitHub | signed / verified (владелец) |

Инженерная готовность растёт. Контрольная точка **не** снимается.

### Нельзя считать закрытыми

| ID | Что отсутствует |
|---|---|
| **RT-001** | Корпус «российская ПД/РД + фактическое заключение экспертизы» + ≥2 адъюдикатора + κ/α + held-out FN |
| **RT-002** | Подписанный `customer_approved` профиль приёмки Самолёта (`approval` + `pack_hash`) |
| **RT-003** | Федеративный IFC заказчика + signed scope + системный MEP clash с `geometry_verified` |

### Нельзя заявлять

точность продукта >90%; SLA клиентского комплекта ≤30 мин; native DWG; готовый MEP system clash; CDE-ready BCF; независимую проверку корректности расчётов; проверенную УКЭП / полную `trust_chain`; bare-metal offline; интеграцию с Tangl/10D; что fixture = customer evidence; IDS 1.1 certification; «полная поддержка XML Минстроя»; «Wave A полностью проверена suite».

## 2. Что представляет собой AeroBIM сейчас

Open-source ассистент критериев приёмки openBIM-комплектов. Не автономный эксперт.

```text
IFC + IDS + чертежи + расчётные документы
        ↓
детерминированная проверка
        ↓
междокументные противоречия
        ↓
finding с provenance
        ↓
HTML / JSON / BCF ZIP
        ↓
эксперт принимает итоговое решение
```

Сильная сторона: сопоставление документов, provenance, fail-closed, не превращать отсутствие проверки в зелёный `summary.passed`, оставить решение человеку, честные capability states.

**Позиция продукта:** AeroBIM помогает эксперту находить противоречия в комплекте до стройки. Он **не** авторизует Shared → Published и **не** заменяет экспертизу, CDE или специалиста. `summary.passed` = Shared-gate (ADR-001), не контрактная пригодность.

Интерпретатор локально: `backend\.venv-3.12\Scripts\python.exe` (CPython 3.12).  
Windows: `$ProgressPreference = 'SilentlyContinue'` в каждом PowerShell-сеансе.

## 3. Что изменилось в Wave A (`005b7bc` vs `dd1a0a7`)

Полезно для КТ#2 как **доказательная база**. Не закрывает продуктовые блокеры.

### A1. XSD Минстроя (intake)

Вендорено:

- `samples/xsd/minstroy/EngineeringSurveysTask-01-00.xsd` (корень `EngineeringSurveysTask`)
- `samples/xsd/minstroy/GeologicalReport-01-00.xsd` (корень **геологический**, не «все изыскания»)
- fail fixtures `fixtures/empty-survey-*.xml`
- каталог в `egrz_intake_xml_checks.py`; `closes_rt001=false`

**Allowed:** intake format / fail-closed на пустом XML.  
**Forbidden:** поддержка экспертизы; машиночитаемые замечания; RT-001 CLOSED; «все новые схемы Минстроя».

Схемы этапа строительства из новости 07.08.2026 **не** найдены на каталожном срезе 14.08 — файлы не выдумывать (`SOURCE.md`, heading `Construction-stage catalog gap`). PZ/ZnP по-прежнему грузятся XMLSchema11 только после strip `xml:id` на documentation.

### A2. IDS document audit

`XmlIdsDocumentAuditor` + пин `docs/evidence/ids-audit-2026-08.*`:

| Pack | Files | Document issues |
|---|---:|---:|
| MOEXP | 24 | 0 |
| Moscow AGR | 4 | 0 |
| SPb CGE | 22 | 0 |
| **Всего** | **50** | **0** |

Аудитор: well-formedness + вендоренный **IDS 1.0** XSD (`samples/ids-xsd/ids.xsd`) + фасеты AeroBIM.  
**Не** binary buildingSMART IDS-Audit-tool. Часть файлов — IDS 1.1; 0 ошибок ≠ сертификация 1.1.  
`customer_pack_hash=null`. `closes_rt002=false`.  
Тест `tests/test_jurisdiction_ids_audit.py` гоняет **3 hashed samples**, не все 50 (pack-wide — evidence pin).

**Allowed:** 50 официальных IDS прошли самопроверку документа без ошибок.  
**Forbidden:** профиль Самолёта; IDS certified; xbim/IDS-Audit-tool пройден; CIM compliance.

Это **не** IfcTester engine coverage. Coverage МОГЭ отдельно: 389/389 executable на fixture, **0 pass** — тоже не customer acceptance.

### A3. buildingSMART Validation Service

**Не сделано.** Нужен человеческий аккаунт validate.buildingsmart.org. Не подменять локальным schema pre-gate.

### A4. Clearance clash

Extra-methods на существующем `IfcClashDetector` (порт `ClashDetector` по-прежнему только `detect(path)`):

- `detect_between`
- `detect_clearance_between`

IfcClash 0.8.5: federated set **обязан** содержать `check_all` и для intersection — `tolerance`; для clearance — `mode=clearance`, `check_all`, `clearance` (метры).

Fixture: `samples/ifc/clash-clearance-gap-{a,b}.ifc` (~30 мм зазор, стены 0.2 м, centerlines 0.23 м).  
HVAC `samples/mep/hvac-sprinkler-systems.ifc` **без tessellated geometry** — не использовать для live IfcClash.

`AnalyzeProjectPackageUseCase._run_clash_detection` вызывает только `detect()` (self-clash). Clearance **не** в analyze.

Default DI MEP: `UnconfiguredMepSystemGraphProvider`. `mep_system_clash=NOT_VERIFIED`. `geometry_verified=false`.

Генератор `backend/scripts/generate_clash_smoke_ifc.py` **не перезаписывает** существующие planted `clash-federated-box-*.ifc` (хеши evidence).

### A5. Clash → BCF file ingest

Round-trip: planted clash → **наш** `export_bcf` → `consume_bcf_zip` / `ingest_payload`.  
Не native BCF-XML IfcClash.

**Allowed:** file ingest T1; GUID/заголовки на собственном ZIP.  
**Forbidden:** CDE import; BCF API; T2; RT-008 T2; RT-003 CLOSED.  
`cde_import=NOT_VERIFIED`.

PowerShell: GUID с `$` не раскрывать (писать через Python-файл, не через `"$guid"`).

### A6. SP 63 template

`samples/rule-packs/sp63-cover-template.json`: `status=synthetic-template`, 20 мм, `Pset_CoveringCommon.CoveringThickness` на IfcSlab/Column/Beam.

**Forbidden:** solver; таблица 8.1; независимая проверка армирования / несущей способности.  
`calculation_correctness=NOT_IMPLEMENTED`. OpenRebar = сверка источников.

## 4. Архитектурный вывод

Freeze портов снят оператором 14.08 вечер. Это **не** свободная разработка.

Разрешено: extra-method; atomic port unit если протокол требует контракт.  
Запрещено до КТ#2: новые enterprise-слои, BCF API-контуры, KG, CV, новые MEP-провайдеры без данных заказчика, интеграции, рефакторинг «для красоты», удаление адаптеров, перевод fixture в customer claims.

**Приоритет:** доказать существующее → тесты → baseline → демо.

## 5. Главный пользовательский сценарий КТ#2

Вертикальный срез (текстовый слой PDF, не CV):

штамп / экспликация / спецификация / толщина стены → finding → overlay → provenance → HTML/JSON → BCF ZIP.

Не показывать: двери/окна (AECV trap); autonomous CV; native DWG; MEP clash; «AI нашёл все ошибки».

```powershell
$ProgressPreference = 'SilentlyContinue'
cd backend
# предпочтительно: .venv-3.12\Scripts\python.exe
python -m aerobim.tools.run_demo_vertical_slice
```

Артефакты (fail-loud, если нет файла):

| Path |
|---|
| `artifacts/vertical-slice-demo/report.html` |
| `artifacts/vertical-slice-demo/report.json` |
| `artifacts/vertical-slice-demo/overlay-problem-zone.png` |
| `artifacts/vertical-slice-demo/findings.bcfzip` |
| `artifacts/vertical-slice-demo/run-manifest.json` |
| `artifacts/vertical-slice-demo/slice-summary.json` |

В UI обязательно: исходный фрагмент; overlay (`#kt2-overlay`); текстовое доказательство; `finding_id`; `source_id`; `evidence_refs`; страница/координаты; правило; capability states; `summary.outcome`; **`summary.passed=false`**; fixture demo; not customer accuracy; not CDE-ready BCF.

Не открывать snapshot `docs/evidence/kt2-handoff-2026-08-11/vertical-slice/report.html` — там нет `#kt2-overlay`.

Видео: [`docs/demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](../demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md). Человек, 19.08. Не снимать и не подменять mp4 из репозитория.

Называть демо: fixture vertical slice / evidence-first review demo. Не: customer demo / production acceptance / CV product.

## 6. Метрики и данные (честное чтение)

### Runtime baseline (сейчас в git)

Файл: `docs/evidence/runtime-baseline-latest.json`

| Поле | Значение | Смысл |
|---|---|---|
| `commit_sha` | `88e726be20bc…` | **Старше HEAD.** Не утверждать, что pin = `005b7bc` |
| `tests_passed` | **2167** | CI Linux pin. Local Windows Wave A: **2259 passed / 12 skipped / 0 failed** — see `docs/evidence/runtime-baseline-wave-a-windows-2026-08-15.md`. Do not copy 2259 into README |
| `tests_skipped` | 11 (CI pin) | Local run skipped 12 (golden pin skip when ifcclash extra sets clash=failed) |
| `tests_collected` | **2271** | Consistency fix 2026-08-15: was 2178 vs `test_functions=2271` |
| `source_loc` | 73166 | Hand-bump 15.08 (live count; tests_passed stays 2167) |
| `test_loc` | 47587 | Hand-bump 15.08 afternoon (honesty tests + matrix renderer). **Not** a suite re-pin. `tests_passed` stays 2167 |
| `test_functions` | 2271 | Hand-bump |
| `frontend.tests_passed` | 54 | Vitest artifact; таблица README capabilities всё ещё пишет 48 — **не** «чинить» без нового vitest JSON |
| `extraction_macro_f1` | 0.86 | **Только fixture corpus**, не product accuracy |

`--check-readme` сравнивает **LOC ±50**, не требует `commit_sha == HEAD`.  
`export_runtime_baseline` **без CI** пишет в `docs/evidence/local/runtime-baseline-local.json` (N-26: отказ писать committed pin с `attested_by != ci`).

Как честно обновить pin после полного pytest:

1. `python -m pytest tests -q --junitxml=var/reports/pytest-junit.xml`
2. Взять passed/skipped/failed **из этого XML / итога pytest**, не выдумать.
3. `python -m aerobim.tools.export_runtime_baseline --pytest-junit var/reports/pytest-junit.xml` → local JSON.
4. Перенести в committed pin **только измеренные** `tests_*`, live loc, `commit_sha=HEAD`, README-сниппет. Не ставить `publishable=true` локально, если политика N-26 это запрещает.
5. Снова `--check-readme`.

### IFC

IFC2x3 / IFC4 ADD2 / IFC4x3 через `IfcOpenShellValidator` + `IfcTesterIdsValidator`.  
**Запрещены алиасы** IFC4 ↔ IFC4X3 ↔ IFC4X3_ADD2.

Fail-closed `ifcVersion` vs `FILE_SCHEMA`: BSI 0101; SKIPPED под pilot/production → FAILED; FAILED блокирует `summary.passed`.

Матрица трёх релизов (fixture, n=20, CPython 3.12.10, 15.08): [`docs/evidence/ifc-release-matrix-2026-08.md`](../evidence/ifc-release-matrix-2026-08.md) — IFC2X3 findings **5**, IFC4 **4**, IFC4X3 **6** (два `AEROBIM-IDS-IFC-VERSION`), `summary.passed=false`. Не называть точностью и не называть SLA. Трекер: таблица «элементы / правила / время / отказы» + блок Tracker paste.

### IDS МОГЭ (IfcTester)

389/389 executable на fixture, **0 pass**. Не «389 успешных». Не профиль Самолёта.

### Open corpora

| Источник | Как говорить | Как не говорить |
|---|---|---|
| AEC-Bench | inventory 196; Harbor **NOT_RUN**; gold `null_always_clean` 134 FP / 50 TN / 184 ≠ agent | false-pass % продукта |
| IFC-Bench v2 | не смешивать карточку HF и статью; smoke **25/1026**; не 514 false-pass | product accuracy |
| GNI | 224 header / 223 parsed / 1 oversize skip | точность системы |
| BSI IDS TestCases | CC BY-ND unmodified | «мы сертифицированы bSI» |

Публичного «ПД РФ + заключение экспертизы» нет.

## 7. VLM: Qwen и Kimi

Qwen = LIVE на fixture. Kimi = GATED (Yandex Studio egress). comparison = **NOT_RUN**.

VLM не ставит PASS, не снимает блокеры, не подтверждает норму, не меняет deterministic verdict.

Сравнительные метрики без одинаковых input/crop/prompt/schema/repeats/timeout/version/cost/latency/hashes — не публиковать.

## 8. MEP и clearance (ещё раз, коротко)

Есть: graph scaffold, edge_kinds, AABB, planted clash, duplex 837 hits, 654 AABB pairs, clearance-gap, BCF file ingest.  
Нет: системный clash заказчика.

654 AABB ≠ clash. 837 duplex ≠ customer. Gap pair ≠ HVAC validation.

## 9. DWG / DXF

Native DWG = **MISSING / FAILED**. LibreDWG не линковать. ODA trial = человек, КТ#3. CADSoftTools не считать решением.  
DXF = Partial / Not verified, optional `[cad]`.  
PDF/IFC из DWG = derived + provenance, не native DWG.

## 10. Нормы и СП 63

МОГЭ IDS ≠ signed Samolet pack. Loader fail-closed без полного `approval`. SP 63 = synthetic template.

## 11. Безопасность и подписи

Wave A не открыла новый fetch в analyze (catalog URL — статические поля).  
`trust_chain=NOT_VERIFIED`. Не писать «УКЭП проверена».  
Offline: Docker image-track verified; bare-metal deferred.

## 12. Что делать инженеру сейчас

### Фаза 1. Аудит без изменений

```powershell
$ProgressPreference = 'SilentlyContinue'
git rev-parse HEAD   # must be 005b7bcb6fb2b9f353cc046b44fe68f1b519b776 unless user moved HEAD
git status --short
git diff --stat dd1a0a7 HEAD
```

Прочитать (в этом порядке): README.md, README.ru.md, `audit/reports/CRITICAL_BLOCKERS.md`, `audit/reports/TZ_RUNTIME_MATRIX.md`, `docs/pilot/KT2_7DAY_PLAN_2026_08_13.md`, этот файл, `docs/pilot/AI_NEXT_STEPS_PLAN_2026_08_14.md`, `docs/demo/TRACKER_MEETING_2026_08_14.md`, `docs/demo/TRACKER_MEETING_2026_08_14_FOLLOWUP.md`, `docs/quality/RED_TEAM_WAVE_A_KT2_2026_08_14.md`, `docs/evidence/ids-audit-2026-08.md`, `docs/evidence/checkpoint2-evidence-bundle-latest.json`, `docs/pilot-claim-boundary-2026.md`, ADR-001.

Составить claim matrix. **Не коммитить.**

### Фаза 2. Focused Wave A

Из `backend/` (venv 3.12):

```text
python -m pytest tests/test_egrz_intake_xml_checks.py -q
python -m pytest tests/test_jurisdiction_ids_audit.py -q
python -m pytest tests/test_bcf_export_and_clash.py -q
python -m pytest tests/test_norm_rule_pack_loader.py::NormRulePackLoaderTests::test_loads_sp63_cover_template_without_claiming_solver -q
python -m pytest tests/test_samples_manifest_gate.py -q
python -m pytest tests/test_p0_remediation_fail_closed.py -q
python -m pytest tests/test_rt_customer_blocker_honesty_lock.py -q
```

Проверить инварианты:

- empty XSD intake → `RULE_XSD` / `RULE_ROOT`, не pass;
- evidence JSON: 50 files, 0 issues, `closes_rt002=false`;
- clearance test (если `[clash]` есть): 0 hard, ≥1 clearance; skip честный без extra;
- clash→BCF: `cde_import=NOT_VERIFIED`, `closes_rt003=false`;
- SP 63: `synthetic-template`, `advisory_only`;
- RT lock зелёный;
- новых DI token нет.

Затем:

```text
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
```

Ruff line length = 100. Не «чинить» весь репо форматтером без нужды.

### Фаза 3. Полный suite

```text
python -m pytest tests -q --junitxml=var/reports/pytest-junit.xml
```

Не заявлять «полный suite зелёный», пока команда не завершилась.  
Потом baseline (см. §6). Frontend не трогать, если UI не менялся, кроме сверки существующего vitest JSON.

### Фаза 4. Claims lint

```text
python ../scripts/lint_claims.py --matrix-guard
python ../scripts/lint_claims.py --full-docs
python -m aerobim.tools.export_samples_manifest --merge-missing
python -m aerobim.tools.export_runtime_baseline --check-readme
```

Новый md с `allow-file` **обязан** быть в `audit/claims_allow_file_registry.json` (N-29).

### Фаза 5. Vertical slice

`python -m aerobim.tools.run_demo_vertical_slice`  
Exit 0 + все файлы §5. Повторный прогон: дрейф `created_at` / UUID ожидаем; не раздувать архитектуру ради bit-identical HTML.

### Фаза 6. Документация

Править только расхождение с runtime. Не менять RT CLOSED, CDE, DWG, calculation_correctness, VLM comparison, checkpoint.

## 13. Claim matrix (стартовая)

| Claim | Source | Artifact | Status | Allowed | Forbidden |
|---|---|---|---|---|---|
| Wave A landed | git `005b7bc` | 38 files | true | fixture substitutes | product GO |
| Survey XSD | minstroy catalog | `EngineeringSurveysTask-01-00.xsd` | intake | fail-closed format | RT-001 CLOSED |
| GeologicalReport | same zip title «отчёт» | XSD root geological | intake | engineering-geological | all-discipline survey |
| Construction-stage XSD | news 07.08 | catalog gap 14.08 | missing | gap documented | invented files |
| IDS 50/0 | XmlIdsDocumentAuditor | ids-audit-2026-08 | document audit | 0 document issues | Samolet profile / IDS 1.1 cert |
| MOEXP 389/389 | IfcTester | norm-pack-moexp-coverage | engine coverage | executable on fixture | 389 pass / accuracy |
| Clearance gap | IfcClash extra | clash-clearance-gap-* | engine rehearsal | ~30 mm gap pair | MEP delivered |
| Analyze clash | use case | `detect()` only | self-clash | optional extra | federated clearance in product |
| Clash→BCF | export_bcf + consume | test_bcf_export_and_clash | T1 file ingest | structural ZIP | CDE-ready |
| SP 63 pack | NormRulePackLoader | sp63-cover-template.json | synthetic | template 20 mm | solver / table 8.1 |
| tests_passed 2167 | CI runtime-baseline | commit 88e726be | CI pin | «CI pin до Wave A» | «HEAD 005b7bc полностью проверен в README» |
| local pytest 2259/12/0 | pytest -q on Windows 3.12.10 | runtime-baseline-wave-a-windows-2026-08-15.md | local, not publishable | local Wave A suite green | replace README 2167 |
| LOC 73166/47587 | same pin | live count 15.08 | loc only | loc drift updated | suite green |
| macro_f1 0.86 | extraction eval | fixture corpus | fixture | fixture F1 | product accuracy |
| Qwen LIVE | vlm evidence | title/spec fixture | advisory | live fixture | bake-off winner |
| Kimi GATED | same | Studio egress | not compared | gated | Kimi vs Qwen score |
| Duplex 837 | federated-clash-duplex | public IFC-Bench | open bench | engine rehearsal | customer clash |
| AABB 654 | federated-mep-inventory | co-presence | inventory | pairs | clash |
| Native DWG | honesty | MISSING | blocker if claimed | FAILED | DWG-ready |
| Docker offline | И1 | closed-contour smoke | eng | image-track | bare-metal air-gap |
| trust_chain | WP-03 | envelope | NOT_VERIFIED | unknown key untrusted | УКЭП проверена |
| Checkpoint | CRITICAL_BLOCKERS | RT-001/002/003 | **NO_GO** | NO_GO | GO |

## 14. Обязательства трекера (14.08 follow-up)

Источник: [`docs/demo/TRACKER_MEETING_2026_08_14_FOLLOWUP.md`](../demo/TRACKER_MEETING_2026_08_14_FOLLOWUP.md). Утренних минут 08:00 в git **нет**.

1. Доработать продукт к КТ#2 **20.08**.
2. Таблица IFC2x3 / IFC4 / IFC4x3 (элементы, правила, время, отказы) — см. ifc-release-matrix; выложить в чат (человек).
3. Датасеты: поиск + прогон уже скачанного; не подменять RT-001 open-bench F1.
4. Вопросы + демо-ссылка у: [`docs/demo/CONSULTATIONS_2026_08_14.md`](../demo/CONSULTATIONS_2026_08_14.md). Созвон с Михаилом — человек.
5. Коммерция: KPI = **назначенные демо 3–5**, не 50 холодных писем.
6. Следующая встреча: монетизация при открытом коде (человек / владелец).

## 15. Что должно быть в отчёте трекеру

Не «мы добавили 12k строк». А:

1. Что увидеть: одна команда, finding, overlay, evidence, BCF ZIP, `passed=false`.
2. Что независимо: signed commit; IDS document audit; fail-closed version; fixture clash/clearance; BCF file ingest; XSD intake; **после фазы 3 — полный pytest на HEAD**.
3. Что эксперимент: MEP, VLM, SP 63 template, open corpora, CDE import.
4. Что блокирует человек/заказчик: корпус; signed profile; federated IFC; BSI account; видео 19.08; live CDE.
5. Что нужно от программы: Renga IFC; acceptance profile; один раздел ПД/РД; фактическое заключение; закрытый контур; тёплые демо.

## 16. Операционные ловушки (накопленный опыт)

| Ловушка | Правило |
|---|---|
| PowerShell progress / GUID `$` | `$ProgressPreference='SilentlyContinue'`; GUID только из Python |
| IfcClash 0.8.5 | `check_all` + `tolerance` (hard) / `clearance` (soft) |
| `build_payload()` federated MEP | не вызывать в unit-тестах |
| Planted IFC regenerate | generator keeps existing box/pipe files |
| HVAC fixture | нет геометрии → не IfcClash |
| PZ/ZnP XSD | duplicate `xml:id`; strip только в памяти |
| N-26 baseline | local export ≠ overwrite committed pin |
| N-29 claims | header `allow-file` **и** registry path |
| Windows grep | не доверять 0 hits на одном файле |
| `python` vs 3.12 | `.venv-3.12\Scripts\python.exe` |
| Не коммитить | пока пользователь не сказал |
| Не полный pytest | нельзя писать «версия полностью проверена» |

## 17. Итоговый приоритет до 20.08

1. Полный pytest после Wave A.  
2. Claims lint.  
3. Runtime baseline, честно привязанный к HEAD `005b7bc` (измеренный suite, не выдуманный).  
4. Повторный vertical slice.  
5. Полировка HTML/`#kt2-overlay` только если slice сломан.  
6. Скрипт видео для человека (уже есть — не переписывать без нужды).  
7. IFC-таблица трёх релизов — **перегнана 15.08** на 3.12 n=20; Tracker paste в md.  
8. Academic Red Team: [`../quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md`](../quality/RED_TEAM_ACADEMIC_KT2_2026_08_15.md).  
9. Пакет вопросов у (CONSULTATIONS — вопросы 6–7 Kane/Solihin; не выдумывать минуты).  
10. 3–5 назначенных демо вместо холодных касаний (человек / подрядчик).  
11. Не трогать AEC-Bench Harbor, ODA, CDE, MEP сверх зафиксированных fixture-прогонов.

**Победа к КТ#2:** любой человек запускает одну команду, видит доказательное замечание, понимает границы, проверяет каждый claim по артефакту. Не ещё один слой архитектуры.
