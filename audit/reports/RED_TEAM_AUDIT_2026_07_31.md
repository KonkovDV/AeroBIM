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

## 5d. Addendum (Level B, волна 3 — adversarial IDS + GUID)

- LB-008/009/010 VERIFIED fail-closed: malformed / чужой namespace / пустой IDS дают `ids=FAILED` и passed=False (AEROBIM-IDS-AUDIT / AEROBIM-IDS-XSD-INVALID) — сломанный источник правил не может зелёно пройти.
- **LB-011 VERIFIED known-undetected:** два IFCWALL с одним GlobalId (оба pset-корректные) → passed=True / 0 issues — уникальность GUID нигде не проверяется, при том что GUID — якорь BCF-топиков, revision diff и трассируемости. Кандидат: ingestion/ifc_schema GUID-uniqueness WARNING (P1). До реализации — honesty-якорь в test_adversarial_ids_guid_level_b.

## 5e. Addendum (LB-011 закрыт)

- Реализована GUID-uniqueness проверка в `BasicIfcSchemaValidator` (streaming-скан rooted-сущностей, WARNING `AEROBIM-GUID-DUPLICATE`, cap 10, verdict-neutral). LB-011 переведён known_undetected → detected; якорь-тест обновлён осознанно вместе с каталогом и Claims Lock — ровно тот workflow, ради которого якоря вводились.

## 5f. Addendum — triage внешней перепроверки (raw main)

| Утверждение внешней проверки | Вердикт | Факты |
|---|---|---|
| «CI ставит зависимости обычным pip install без --require-hashes» | **ОПРОВЕРГНУТО** | все 9 джобов ci.yml + release-readiness + academic-benchmark используют `pip install --require-hashes -r requirements-dev-lock.txt` (lock: 1453 sha256-хеша), pinned `pip==25.2`, `-e . --no-deps`, отдельный pip-audit 2.9.0; residual (floating pip bootstrap, unhashed uv) задокументирован в комментариях workflow |
| «PyMuPDF всё ещё обязательный Core при license=MIT» | ПОДТВЕРЖДЕНО (известный LIC-001) | решение Artifex/миграция/extra — за владельцем; disclosure в README/README.ru; pyproject получил pointer-комментарий |
| «license/SBOM/offline-гейты не видны» | ЧАСТИЧНО | license-gate есть (pytest в CI: test_dependency_license_gate + isolation guard); **SBOM добавлен этой волной** (`docs/evidence/sbom-backend-latest.json`, CycloneDX-format, venv-scoped, генератор `export_dependency_sbom` без сторонних инструментов + pytest-гейт покрытия core-зависимостей); offline-гейты честно остаются NOT VERIFIED (P-002, F-108) |

## 5g. Addendum — triage второго внешнего red-team (P0-регресс supply-chain)

| Утверждение | Вердикт | Факты (проверено 2026-07-31) |
|---|---|---|
| Docker игнорирует lock, нет --require-hashes | **ОПРОВЕРГНУТО** | Dockerfile L6-9: COPY requirements-lock.txt; pip install --require-hashes -r lock; проект --no-deps |
| Base image не pinned по digest | **ОПРОВЕРГНУТО** | обе стадии: python:3.12-slim@sha256:57cd7c3a... |
| CI: pip install ruff / -e .[dev,raster] без хешей; actions по тегам @v4/@v5 | **ОПРОВЕРГНУТО** | grep по всем workflow: 0 floating installs, 0 тегов; всё --require-hashes + SHA-pinned |
| freeze SHA 8a314d8 устарел | **ОПРОВЕРГНУТО** (факт не совпадает) | в CRITICAL_BLOCKERS operational freeze = f2615e7 |
| README: DEBUG default true, нет NO_GO, MIT без disclosure | **ОПРОВЕРГНУТО** | NO_GO-баннер L9; AEROBIM_DEBUG=false; disclosure в License-секции |
| OCI label licenses=MIT вводит в заблуждение | **ПОДТВЕРЖДЕНО → исправлено** | label заменён SPDX-выражением MIT AND LGPL-3.0-or-later AND (AGPL-3.0-only OR LicenseRef-Artifex-Commercial) |
| Job samolet-sla-smoke читается как customer evidence | **ПОДТВЕРЖДЕНО → исправлено** | переименован в samolet-fixture-sla-smoke (job, step, artifact); сам артефакт всегда нёс claim_level=fixture_only |
| Нет RELEASE_ATTESTATION | **ПОДТВЕРЖДЕНО → закрыто инструментом** | export_release_attestation (commit/tree/locks/ClaimsLock/SBOM/baseline sha256; docker_digest и test_run_id честно null вне release-пайплайна) + 2 теста |
| EXTRACTION_INTEGRITY gate отсутствует в вердикт-пайплайне | ПОДТВЕРЖДЕНО (известная граница) | сигнальное ядро есть (5a), wiring в capability — P2; не заявляется |
| Offline NOT VERIFIED; dataset manifest; semantic-injection fixtures | ПОДТВЕРЖДЕНО (известные P1/P2) | см. F-108, P-010/011, план P1 |

Вывод triage: заявленный «P0-регресс supply-chain» не подтверждён текущим main (вероятно, устаревший снапшот — второй подобный случай); реальные остатки — label/имя job/attestation — закрыты этой волной.

## 5h. Addendum — EXTRACTION_INTEGRITY wired (P1 обоих внешних отчётов)

- `ReportCapabilities.extraction_integrity`: default NOT_VERIFIED (честно: сигналы не производятся ingestion-слоем), FAILED входит в pass-blocking список во всех профилях; персистентные отчёты без поля реконструируются в NOT_VERIFIED. Golden reproducibility hash обновлён осознанно (capability digest вырос на поле). Producer сигналов (hidden-text скан PDF) — P2.

## 5i. Addendum — RT-EI-04 закрыт (digest drift)

- Подтверждён pre-existing дефект из ревью 5h: `_CAPABILITY_FIELDS` содержал фантомные имена (`quantity_consistency`, `load_evidence`), которые getattr молча отбрасывал — pass-blocking `quantity`, `raster`, `ifc_schema`, `norm_rule_packs`, `section_pairing` НЕ входили в reproducibility digest. Список приведён к точному зеркалу `_PASS_BLOCKING_FAILED_FIELDS` (13 полей); синхронизацию и отсутствие фантомов держит guard-тест (test_run_manifest_capability_digest, 3 теста). Golden hash обновлён осознанно второй раз за день; trace-evidence регенерирован.

## 5j. Addendum — offline runtime smoke (F-108 частично закрыт)

- **VERIFIED:** production-образ (lock+hashes, digest-pinned base) запускается и обслуживает API при `--network none`: health 200, capabilities 200 (bearer), 401 без bearer, healthy-healthcheck; ни DNS, ни outbound, ни загрузки моделей на старте. Evidence: `audit/evidence/offline-runtime-smoke-2026-07-31.json` (claim_level=runtime_smoke_only).
- **Реальный дефект, пойманный первым прогоном:** образ вообще не стартовал — LoinMetadataResolver падал на import-time чтении samples-манифеста, которого нет в образе (контейнер ни разу не запускали до этого smoke). Исправлено fail-soft деградацией (enrichment verdict-neutral) + 3 regression-теста.
- Граница честности: offline INSTALL/BUILD (wheelhouse, установка без сети) остаётся NOT VERIFIED — P-002 закрыт только в runtime-части.

## 5k. Addendum — offline INSTALL bundle (P-002 image-track закрыт)

- **VERIFIED:** `aerobim.tools.offline_bundle` build/verify/smoke. Образ собран из hash-lock wheels + digest-pinned base, сохранён в tar (~850 МБ, sha256 в манифесте), локальный тег **удалён**, образ восстановлен **только из tar** (`docker load`) и обслужен при `--network none`: health 200, capabilities 200. Т.е. доказан offline INSTALL (не только runtime из 5j). Evidence: `audit/evidence/offline-bundle-smoke-2026-07-31.json`.
- Инструмент: build → `docker save`; verify → пересчёт sha256 каждого файла против BUNDLE_MANIFEST; smoke → `rmi` тега + `load` + `--network none` API. Docker-free логика манифеста (build_manifest/verify_manifest: детект подмены и пропажи файла) покрыта 4 unit-тестами.
- Граница честности: **bare-metal / no-Docker** установка (wheelhouse на хосте без Docker) остаётся NOT VERIFIED; tar (851 МБ) gitignored, регенерируется инструментом.

## 5l. Addendum — offline bundle в CI (непрерывная проверка)

- Джоб `offline-bundle-smoke` в ci.yml: на каждый push/PR в main прогоняет `offline_bundle build/verify/smoke` на `ubuntu-latest` (GitHub-hosted раннер уже несёт Docker — self-hosted не требуется; для air-gapped меняется только `runs-on`). Так offline install+runtime доказывается непрерывно, а не одноразово (evidence 5k). Artifact — только BUNDLE_MANIFEST.json; tar (~850 MiB) намеренно не выгружается.
- Граница честности неизменна: доказан контур С Docker; bare-metal без Docker остаётся NOT VERIFIED. Зелёный статус джоба производит сам GitHub Actions — локально проверены YAML и работоспособность инструмента (5k).

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
