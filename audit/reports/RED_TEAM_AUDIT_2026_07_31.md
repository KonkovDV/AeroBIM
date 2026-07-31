---
title: "Red Team audit 2026-07-31 — факты, классификация P-001…P-020"
status: final-for-session
version: "1.0.0"
date: "2026-07-31"
repo_snapshot: "main @ 33456de + wave-1 changes"
claim_boundary: "Инженерный аудит; юридические пункты — «требуется юридическая проверка», не заключение."
---

# RED TEAM AUDIT 2026-07-31

Классификация: VERIFIED / PUBLIC CLAIM / INFERRED / UNKNOWN / NOT VERIFIED / BLOCKED.
Метод: только код, установленные метаданные, воспроизводимые команды. Дата проверки: 2026-07-31.

## 1. Executive summary (главные выводы)

| ID | Вывод | Статус | Доказательство | Риск | Действие | Приоритет |
|---|---|---|---|---|---|---|
| F-101 | `pymupdf==1.27.2.3` — dual «AGPL-3.0 or Artifex Commercial», ОБЯЗАТЕЛЬНАЯ core-зависимость, серверный путь (6 импортов: raster_drawing_analyzer, filesystem_audit_store, region cropper, tools) | **VERIFIED** | `importlib.metadata` в venv; pyproject L26; grep `import pymupdf` | HIGH (лицензионный) | LIC-001 в CRITICAL_BLOCKERS; юр. проверка; план миграции (pypdfium2/pdfminer.six) или коммерческая лицензия | P0 |
| F-102 | ifcopenshell/ifctester 0.8.5 — LGPL-3.0+ (classifier) | **VERIFIED** | wheel classifiers | MEDIUM | disclosure (сделано в README); юр. проверка динамического связывания | P1 |
| F-103 | README заявлял «MIT» без сторонних оговорок | **VERIFIED (исправлено)** | README L7/L403 до правки | HIGH (P-015) | disclosure добавлен в оба README; Claims Lock v3 запрещает «MIT целиком» | P0 done |
| F-104 | Аффирмативных заявлений «интеграция с 10D»/«российское ПО»/«S.Project» в репо НЕТ | **VERIFIED** | grep по *.md (единственное упоминание — отрицание в samolet.md L418) | LOW | границы добавлены в Claims Lock v3 превентивно | done |
| F-105 | Capability honesty (P-016): FAILED блокирует pass; advisory OFF==ON; статусы в API/отчёте | **VERIFIED** | `capability_policy.py` + существующие тесты (1560) | — | поддерживать мутационные тесты | — |
| F-106 | Prompt-injection (P-004): hybrid-контур не wired в verdict; LLM не в пайплайне вердикта | **VERIFIED** (границы), полный adversarial-набор — частично | bootstrap «DELIBERATELY NOT consumed»; OFF==ON | MEDIUM | fixtures-набор расширять в P3 (когда LLM появится в advisory-проде) | P3 |
| F-107 | УКЭП (P-005): криптографической проверки подписи НЕТ; есть только hash-provenance (sha256 входов в bundle/report) | **VERIFIED (отсутствие)** | нет крипто-адаптера в src; source_files sha256 есть | HIGH при заявлении | Claims Lock v3: «УКЭП проверена» запрещено; capability = missing | P2/customer |
| F-108 | Offline-развёртывание (P-002): hashed locks и pinned toolchain есть; полный offline bundle/verify/install/smoke — НЕТ | **NOT VERIFIED** | requirements-lock с hashes; скриптов bundle нет | MEDIUM | отдельный трек; не заявлять offline-ready | P2 |
| F-109 | Extraction integrity (P-003): скрытый/невидимый текст PDF не детектируется отдельной capability | **NOT VERIFIED** (capability отсутствует честно) | нет EXTRACTION_INTEGRITY в моделях | MEDIUM | scaffold в P2; до тех пор — не заявлять | P2 |
| F-110 | SLA (P-014): манифест/шкала пакета реализованы (package_scale, representative_scale, cold/warm, fingerprint); параллельные/ресурсные профили — нет | VERIFIED (частично) | measure_package_sla 1.3.0 + артефакт 2026-07-30 | — | p50/p95, память/CPU — P2 | P2 |
| F-111 | Расчёты (P-007): только сверка (OpenRebar digest); AnalysisModelIngestor/SAF — отсутствуют | **VERIFIED (границa)** | Claims Lock; capability calculation_match | — | порт — P3+, не заявлять | P3 |
| F-112 | IDS (P-009): IfcTester-путь и XSD-аудит есть; сравнение с независимым валидатором — нет | VERIFIED (частично) | ids_official_xsd_audit test | MEDIUM | внешний regression-suite — P2 | P2 |
| F-113 | Datasets/corpus (P-010…P-013): фикстуры synthetic/fixture, маркированы; внешний каталог — не собран | UNKNOWN/BLOCKED | corpus_kind везде fixture | — | каталог + sizing — отдельный research-трек | P4 |
| F-114 | Реестр российского ПО (P-019) | **BLOCKED (юр.)** | нет юр. gap-анализа | HIGH при заявлении | Claims Lock v3 запрещает заявление; gap analysis с юристом | P2 |
| F-115 | Конкуренты (P-020) | PUBLIC CLAIM | публичные материалы не верифицированы | — | матрица в TZ v3 с оговоркой «vendor claim» | — |

## 2. Что оказалось ошибочным (проверка исходных гипотез промта)

- «PyMuPDF может быть optional» — НЕТ: обязательная core-зависимость (pyproject dependencies).
- «Возможно перепутаны pypdf/pdfminer» — НЕТ: используется именно `pymupdf` (6 прямых импортов); других PDF-бэкендов в src нет.
- «В репо могут быть заявления об интеграции с 10D» — НЕ подтвердилось (только отрицание).

## 3. Что осталось UNKNOWN (не заполнено догадками)

- Применимость AGPL к конкретному способу использования (network use, SaaS) — юридический вопрос.
- Лицензии npm-дерева фронтенда и Docker base images — нужен отдельный SBOM-скан.
- Требования 10D API, УКЭП-правила заказчика, актуальные редакции ПП РФ на 31.07.2026 — нужны официальные источники/заказчик; в этой сессии не проверялись.

## 4. Изменения в репозитории (эта волна)

| path | change | reason | tests |
|---|---|---|---|
| audit/dependency_license_inventory.json | НОВЫЙ: machine-readable реестр лицензий (verified/declared, risk_class, legal_review_required) | P-001 | test_dependency_license_gate |
| backend/tests/test_dependency_license_gate.py | НОВЫЙ: CI-гейт — каждая shipped-зависимость классифицирована; unknown блокирует; pymupdf dual-license не может «потеряться» | P-001 acceptance | 4 теста |
| README.md / README.ru.md | License-раздел: MIT только для собственного кода + disclosure PyMuPDF/LGPL + ссылка на inventory | P-015/P-001 | claims guard остаётся зелёным |
| audit/reports/CLAIMS_LOCK_2026_07_17.md | v3: запрещены «MIT целиком», «интеграция с 10D» (<T5), «российское ПО» (без юр. анализа), «УКЭП проверена»; разрешена формула disclosure; BCF-лестница T0–T5 | P-005/P-006/P-015/P-019 | guard |
| audit/reports/CRITICAL_BLOCKERS.md | LIC-001 (HIGH, OPEN — legal review required) | P-001 | — |
| docs/cde-integration-questionnaire-2026.md | НОВЫЙ: T0–T5 лестница + 13 вопросов заказчику по СОД/10D | P-006 | — |
| audit/reports/RED_TEAM_AUDIT_2026_07_31.md | этот отчёт | формат | — |

## 5. Не реализовано в эту волну (честно, без фальшивых scaffold'ов)

P-002 offline bundle scripts; P-003 EXTRACTION_INTEGRITY capability + red-team PDF corpus;
P-005 крипто-адаптер УКЭП; P-007 AnalysisModelIngestor/SAF; P-009 независимый IDS-валидатор;
P-010…P-013 dataset catalog + corpus sizing; P-018 полный data-governance пакет;
P-019 юридический gap-анализ; P-020 верифицированная конкурентная матрица.
Каждый требует внешних данных/юриста/времени; статусы — в §1. Добавление пустых
файлов-заглушек противоречило бы правилу «не создавай фиктивные evidence files».

## 5a. Addendum (та же дата, после публикации отчёта)

- F-109 частично закрыт: добавлено сигнальное ядро `domain/extraction_integrity.py` (+ адверсариальные фикстуры и тесты). Статус P-003 повышен до «signal-core done»; render-vs-extract адаптер и PDF red-team corpus остаются NOT VERIFIED (P2).

## 5b. Addendum (продолжение той же даты)

- P-012 Level B засеян: каталог injected defects (`samples/benchmarks/injected-defects-level-b.json`) + тесты. Обнаружена и закреплена как honesty-граница VERIFIED-находка probe: **числа в free-text расчёте не сверяются** (пустая delta findings при мутации 16.8→1.0 на пилот-паке); сверка работает только по каноническим LOAD-строкам/JSON. Формулировка «сверка расчётов» обязана уточнять формат.
- P-014: docs/sla-benchmark-protocol-2026.md; P-017/P-018/P-004: outbound guard + governance/AI-safety доки (см. коммиты 7c3b85a, d55d617).

## 5c. Addendum (Level B, волна 2 — IFC-мутации)

- LB-005/006 (missing pset relation, wrong FireRating) детектируются IDS-путём.
- **LB-007 VERIFIED vacuous pass:** подмена класса IFCWALL→IFCCOLUMN даёт passed=True / 0 issues в IDS-only прогоне — «нет элемента» читается как «соответствует». Компенсирующий контроль VERIFIED: structured requirement с ожиданием сущности даёт ERROR «No elements found for entity IFCWALL». Пилот-паки обязаны сочетать IDS с entity-presence требованиями; закреплено honesty-якорем в test_injected_ifc_defects_level_b.

## 6. Что запросить у Самолёта (сводно)

Состав эталонного комплекта; IFC + PDF + ТЗ + нормы + расчёты + ревизии; два эксперта;
каталог типовых ошибок; baseline ручной проверки; BCF sample из их СОД; API СОД + тестовый
контур (опросник: docs/cde-integration-questionnaire-2026.md); правила УКЭП; ограничения
хранения/размещения; NDA; критерии успеха.

## 7. Go/No-Go

**NO_GO** (без изменений): RT-001/002/003 открыты + новый **LIC-001** (лицензионный блокер
уровня release: обязательная AGPL/commercial-dual зависимость при MIT-позиционировании).
Статус изменится на GO_WITH_BLOCKERS после: юридического заключения по LIC-001 (или миграции
PDF-бэкенда), и на GO — после customer evidence по RT-001/002/003 и BCF T2.
