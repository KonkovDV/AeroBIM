# REPO_DEEP_MAP — AeroBIM — 2026-08-09

> **Назначение:** гиперглубокая карта репозитория до любых дальнейших правок кода (промт v5, Раздел 2).  
> **Правило:** любой инженер, прочитав только этот файл, должен найти заявленную возможность и чем она доказана.  
> **Снимок промта (01:14 MSK):** сверка; при расхождении побеждает проверка ниже.

---

## 0. Точка отсчёта (П1)

### Команды

```text
git fetch --all --prune
git rev-parse HEAD
git rev-parse origin/main
git rev-parse HEAD^{tree}
git status --porcelain
git branch -a --format='%(refname:short) %(objectname:short) %(committerdate:iso)'
gh auth status
gh pr list --state open --json number,title,author,headRefName,updatedAt,mergeable,changedFiles
```

### Вывод (факт на момент аудита)

| Поле | Значение | Команда |
| --- | --- | --- |
| `HEAD` | `5a75d866cce256d8b4caa010031683762b8ee162` | `git rev-parse HEAD` |
| `origin/main` | `5a75d866cce256d8b4caa010031683762b8ee162` | `git rev-parse origin/main` |
| `tree` | `0401bdd209f1ad18dd18d6b8949d96716f9efd6f` | `git rev-parse HEAD^{tree}` |
| working tree | **пусто** (`git status --porcelain` → пусто) | |
| ветки | **только** `main` / `origin/main` | `git branch -a` |
| `gh` | Logged in as **KonkovDV** (keyring), scopes `gist,read:org,repo,workflow` | `gh auth status` |
| open PRs | **`[]`** (0) | `gh pr list --state open` |
| merge CI | `31301092314` **success** | `gh run view 31301092314` |

Последние коммиты (фрагмент `git log --oneline -10`):

```text
5a75d86 Merge pull request #12 from KonkovDV/fix/publishable-circular-lock-n24-n26
e443d2b fix(ci): ruff format + shallow-clone safe parent SHA test
9362fdc fix(tests): resolve ruff S607 on git subprocess calls
022c2ce docs(evidence): sync README baseline markers after publishable-gate fix
76e0da0 fix(baseline): break publishable circular lock and harden gates
af6e364 fix(ci): correct download-artifact pin (Set up job) + baseline bootstrap
…
498fd70 style: isort OfficeDocumentIngestor import in DI bootstrap
```

### Расхождения с промтом (Раздел 1) — обязательная фиксация

| Промт (01:14 MSK) | Проверка сейчас | Статус |
| --- | --- | --- |
| `main` = `498fd709…`, tree `08ee7c9a…` | `5a75d86…` / `0401bdd2…` | **расхождение** — после PR #12 и CI-фиксов |
| две ветки: `main` + `red-team/wp-a-p0-gates` | одна ветка `main` | **расхождение** — feature-ветки удалены после merge |
| 7 открытых PR | 0 open | **расхождение** |
| baseline tests `2001/1993` | committed JSON: collected `2006`, passed `1993`, skip `8` | **расхождение collected** |
| `source_loc/test_loc` `61499/41812` | `61634/42020` | **расхождение** (рост после gate-фиксов) |
| `vitest_artifact` = `C:/plans/...` | `frontend/var/vitest-results.json` | **расхождение** — санитайзер N-24 в коде/артефакте |
| `tool` = `C:\Users\Пользователь\...` | `python` | **расхождение** — санитайзер |
| `publishable: false`, `attested_by: local`, `gates_attested: []` | то же | **совпадает** — N-1 / WP-A1b не закрыты |
| `lockfile_sha256` prefix `c70becc6…` | совпадает (`C70BECC6BDDA0B77…`) | совпадает |

Committed baseline (фрагмент проверки):

```text
schema 1.4.0
clean True
publishable False
completeness partial
attested_by local
run_id None
gates_attested []
runner Windows 3.13.7
commit 76e0da0453cede9fce4f93ebcfdcca041829eb07
vitest frontend/var/vitest-results.json
ruff_tool python
gates all PASS
doc_env 79 code_env 60
```

---

## П2. Физический состав

**Команда:** `git ls-files` + группировки PowerShell.

| Метрика | Значение |
| --- | --- |
| Tracked files | **1755** |
| Top extensions | `py` 577 · `md` 321 · `ifc` 302 · `ids` 294 · `json` 148 · `tsx` 11 · `ts` 5 |
| Top dirs | `samples/ids` 589 · `backend/src` 309 · `backend/tests` 263 · `docs/evidence` 69 · `docs/quality` 60 · `frontend/src` 17 |

60 крупнейших `.py` (топ-10):

| LOC (lines) | Path |
| --- | ---: |
| 1536 | `backend/tests/test_api_security.py` |
| 1485 | `backend/src/aerobim/tools/export_runtime_baseline.py` |
| 1082 | `backend/src/aerobim/tools/run_aecv_bench_eval.py` |
| 1073 | `backend/src/aerobim/application/use_cases/analyze_project_package.py` |
| 968 | `backend/src/aerobim/infrastructure/adapters/filesystem_audit_store.py` |
| 961 | `backend/src/aerobim/infrastructure/di/bootstrap.py` |
| 950 | `backend/tests/test_analyze_project_package.py` |
| 882 | `backend/src/aerobim/application/services/compliance_agent_orchestrator.py` |
| 850 | `backend/src/aerobim/application/services/analyze_orchestrators.py` |
| 800 | `backend/src/aerobim/core/config/settings.py` |

---

## П3. Гексагональная целостность

**Команды:** `rg` по `Protocol` / `Adapter|Ingestor|…`; `_live_architecture_inventory`.

| Источник | Число |
| --- | ---: |
| `rg` hits `class …Port|Protocol)` в `backend/src` | 59 (включает private Protocol в infra/adapters) |
| Live inventory `public_domain_protocols` | **48** |
| Live inventory `adapter_modules` | **72** |
| Live inventory `di_tokens` | **63** |
| `rg` hits Adapter/Ingestor/Provider/Repository/Client | 27 (узкий паттерн имён классов) |

**Вывод:** SSOT для отчётности — live inventory **(48/72/63)**, совпадает с ENGINEERING_STATUS. Узкий `rg` Adapter|… занижает адаптеры относительно модулей в `infrastructure/adapters/`.

Порты без адаптера / адаптеры без негативного теста: **полная попарная таблица = отдельная находка N-32** (см. §2.2.2) — автоматический паритетный тест в репозитории не найден как единственный SSOT; требуется отдельный проход `port-adapter-parity` (если появится) или ручной реестр. Статус: **UNVERIFIED** на «ноль orphan ports» без полного матричного скрипта в этом аудите.

---

## П4. Domain vs infrastructure

**Команда:** импорты `backend/src/aerobim/domain` минус stdlib/domain.

Найдены **не-domain** импорты (не infra leak, но за пределами «чистого» фильтра промта):

- `domain/eval_statistics.py:39` → `import random`
- `domain/llm_token_budget.py:8` → `zoneinfo`
- `domain/hybrid/privacy_guard.py:24` → `hmac`
- `domain/package_trace.py:6-7` → `time.perf_counter`, `types.TracebackType`
- `domain/study_design.py:32` → `statistics.NormalDist`
- `domain/stage_timeout.py:6-7` → `time` / `types`

**Импортов `aerobim.infrastructure` / `aerobim.presentation` в domain не обнаружено** в выборке. Вердикт: **DOMAIN CLEAN относительно infra** (с оговоркой stdlib extras выше).

---

## П5. Карта тестов

```text
pytest --collect-only -q  →  2006 tests collected in 1.35s
```

| Метрика | Значение |
| --- | ---: |
| Collected (live) | 2006 |
| Baseline recorded passed/skip/fail | 1993 / 8 / 0 |
| `skipTest` / `unittest.skip` / `importorskip` hits | **90** строк (условные skip с reason) |
| `@pytest.mark.skip` без reason | **0** найдено узким `rg` на mark |

Примеры skip **с reason** (выборка): `test_cad_office_ingest.py:53` «ezdxf optional…»; `test_office_native_ingest.py:33` «python-docx…»; `test_ifc_bench_smoke.py:64` «IFC-Bench checkout…».

Coverage full-run: **не запускался в этом аудите** (длительный прогон). Статус: **UNVERIFIED** (нужен `coverage run -m pytest` + report).

---

## П6. Frontend

| Метрика | Значение | Доказательство |
| --- | ---: | --- |
| `*.ts`/`*.tsx` (без test) | 11 | `Get-ChildItem frontend/src` |
| test files | 4 (`App`, `CapabilityHonesty`, `DrawingEvidence`, `Provenance`) | дерево |
| Vitest | **29 passed / 5 files** | `npm test -- --run` |
| `CoverageMapPanel` dedicated tests | **0** | нет `CoverageMapPanel.test.tsx` |
| `DrawingEvidencePanel` `it(` | **5** | `DrawingEvidencePanel.test.tsx` |
| Без тестов (важные для ТЗ) | `CoverageMapPanel.tsx`, `IfcViewerPanel.tsx` | дерево |

Компоненты без dedicated теста (по важности ТЗ):

1. `frontend/src/components/CoverageMapPanel.tsx` — карта покрытия (критерий ТЗ)
2. `frontend/src/components/IfcViewerPanel.tsx` — IFC viewer
3. `frontend/src/lib/api.ts`, `ifc-scene.ts`, `types.ts` — без unit-тестов

---

## П7. CI

Файл: `.github/workflows/ci.yml` (**738** строк; промт «742» — близко).

| Job | Blocking? | Notes |
| --- | --- | --- |
| `lint` | blocking | ruff/mypy/claims/readme |
| `docs-links` | blocking | |
| `typecheck` | blocking | frontend |
| `test` | blocking | pytest+coverage |
| `frontend` | blocking | vitest + npm audit high |
| `supply-chain-audit` | blocking + **1 advisory step** | `continue-on-error: true` на `pip_audit` **dev** lock (`ci.yml:345`) |
| `sprint-2-1-gates` | blocking | |
| `security-regression` | blocking | |
| `baseline-integrity` | blocking (`needs` vitest) | soft-fail bootstrap если committed local |
| `benchmark-smoke` | blocking (`needs: test`) | |
| `samolet-fixture-sla-smoke` | blocking | |
| `extraction-quality` | blocking | |
| `openapi-contract` | blocking | |
| `offline-bundle-smoke` | blocking | |

Все перечисленные джобы на `push`/`pull_request` к `main`. Отдельный workflow CodeQL на PR — зелёный на #12.

---

## П8. Env vars

Грубый `AEROBIM_[A-Z0-9_]+` по `backend/src`+`frontend/src`+`scripts` vs `docs`+README:

| Множество | Count |
| --- | ---: |
| code | 107 |
| docs | 98 |
| code − docs | 16 |
| docs − code | 7 |

`code − docs` (сырой список; часть — **ложные** из-за обрезки regex на `AEROBIM_LLM_`):  
`AEROBIM_API_BASE_URL`, `AEROBIM_AUDIT_FAIL_CLOSED`, `AEROBIM_BSI_LOCAL_CERT`, `AEROBIM_DOCUMENT_DATA_BEGIN/END`, `AEROBIM_ENFORCE_OBJECT_ACL`, `AEROBIM_HYBRID_DRAWING_ENABLED`, `AEROBIM_KIMI_*`, `AEROBIM_LLM_`, `AEROBIM_MAX_*`, `AEROBIM_ODA_CAD_ENABLED`, `AEROBIM_REQUIRE_BSI_SCHEMA`.

Baseline tool сообщает `documented_env_vars=79` ⊇ `code_env_vars=60` (другой алгоритм извлечения) — `--check-readme` **OK**.

**Находка N-33:** два алгоритма env-учёта расходятся (79/60 vs 107/98) — риск ложного «закрытия» N-20.

---

## П9. CLI tools

| Метрика | Значение |
| --- | ---: |
| `backend/src/aerobim/tools/*.py` modules | **73** |
| Полный `--help` цикл по всем | **UNVERIFIED** (не гонялся целиком в этом проходе) |

Ключевые honesty tools: `export_runtime_baseline`, `offline_bundle`, `measure_package_sla`, `lint_claims` (scripts/), `check_docs_metadata_integrity` (scripts/).

---

## П10. Гигиена

| Проверка | Результат |
| --- | --- |
| TODO/FIXME/HACK/XXX/NotImplementedError count (`backend/src`+`scripts`) | **0** по узкому `rg` |
| Локальные пути `C:\` / `Пользователь` / `AppData` | **много** в `audit/evidence/*.json` + тесты (фикстуры атак) |
| Secrets `sk-|ghp_|AKIA` | только **тестовые** / regex детекторы (`test_hybrid_*`, `sensitive_entities.py`) — не живые ключи |
| Markdown links | **UNVERIFIED** в этом проходе (`check_markdown_links` не гонялся отдельно; CI `docs-links` зелёный на merge) |

**Находка N-34 (И17):** `docs/evidence/runtime-baseline-latest.json` очищен, но **`audit/evidence/**` всё ещё публикует абсолютные Windows-пути** (пример: `audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json:21`).

---

## П11. Лицензии / supply chain

| Проверка | Статус |
| --- | --- |
| `sha256` `requirements-lock.txt` | `C70BECC6BDDA0B774AFD174BCF8B673B19A4251D83873AD43A300C8AADF193EB` |
| `pip-audit --strict` live | **UNVERIFIED** локально; CI `supply-chain-audit` зелёный на merge |
| LGPL/GPL/MPL/AGPL упоминания | см. `docs/license-policy-2026.md` / LIC-001 Option B — полная перечитка **ASSUMED** для деталей N-15 |

---

## П12. Дрейф docs↔code

Команды и вывод:

```text
python -m aerobim.tools.export_runtime_baseline --check-readme --check-complete
→ README markers, documented-env sets, runtime baseline drift, and completeness OK

python -m aerobim.tools.export_runtime_baseline --check-committed-baseline
→ publishable_not_true
  artifact_incomplete
  attestation_not_ci: got 'local'
  attestation_gates_attested_missing: [7 jobs]
  commit_sha_mismatch / tree_sha_mismatch (76e0da0 vs HEAD 5a75d86)

python -m aerobim.tools.export_runtime_baseline --check-publishable
→ committed_baseline_not_publishable: … must have publishable=true

python scripts/lint_claims.py --full-docs --matrix-guard --claim-boundary-guard
→ matrix-guard: OK (0 violations)  (+ claims OK в том же прогоне)

python scripts/check_docs_metadata_integrity.py
→ docs-metadata-integrity: OK
```

---

## 2.2 Обязательные численные ответы

### 1) Файлы / LOC / тесты / test÷src по слоям

| Слой | LOC (approx lines) | Notes |
| --- | ---: | --- |
| domain | 12965 | `backend/src/aerobim/domain` |
| application | 6339 | |
| infrastructure | 13209 | |
| presentation (api) | 2620 | |
| tools | 16965 | |
| backend tests | 36156 | |
| frontend src | 3671 | |
| Tracked files | 1755 | |
| pytest collected | 2006 | |
| frontend vitest | 29 | |
| test/src backend (test_loc/src tools+layers rough) | ~0.68 | 36156 / (12965+6339+13209+2620+16965≈52098) |

Baseline metrics: `source_loc=61634`, `test_loc=42020` (aerobim package counting rules).

### 2) Порты / orphans / негативные тесты адаптеров

| | |
| --- | ---: |
| public_domain_protocols | 48 |
| adapter_modules | 72 |
| di_tokens | 63 |
| ports without adapter | **UNVERIFIED** (нет автоматического отчёта в этом проходе) |
| adapters without negative test | **UNVERIFIED** |

### 3) Возможность → код → тест → артефакт → матрица

> Полная строка по **каждой** ячейке матрицы — обязательный объём; ниже — каркас по gap-направлениям и allowed claims. Строки с дырой помечены **НАХОДКА**.

| Возможность | Код (`path:line`) | Тест (`path:line`) | Артефакт | Матрица | Gap? |
| --- | --- | --- | --- | --- | --- |
| Runtime baseline / publishable | `export_runtime_baseline.py:883` `_compute_publishable` | `tests/test_export_runtime_baseline.py` (CI publishable tests) | `docs/evidence/runtime-baseline-latest.json` | Allowed «Runtime baseline» `:74` | **да** — `publishable:false` / `attested_by:local` |
| Claims Lock linter | `scripts/lint_claims.py:1` | CI lint job | matrix + CLAIMS_LOCK | `:75` | boundary tables skipped `:100` **N-28** |
| Docs metadata integrity | `scripts/check_docs_metadata_integrity.py:17` `_MONITORED` | CI | ENGINEERING_STATUS | — | `_MONITORED` только 4 файла **N-27** |
| Coverage map statuses | `domain/check_coverage.py:85-97` | backend coverage tests (см. suite) | evidence bundle coverage | K4 target | UI `CoverageMapPanel` **0 tests** **N-35** |
| Drawing evidence overlay | `frontend/.../DrawingEvidencePanel.tsx` | `DrawingEvidencePanel.test.tsx` (5× `it`) | — | HITL/drawing | **<12 tests** **N-35** |
| Native DWG | fail-closed ports / cad ingest | `test_week_ifc_llm_extraction` DWG memo; cad tests | CRITICAL_BLOCKERS | Forbidden native DWG | OK fail-closed |
| MEP system clash | `domain/mep.py` + adapters | `test_p2_mep_*` | — | RT-003 OPEN | `geometry_verified=False` |
| BCF structural | BCF exporters | `test_bcf_*` | `audit/evidence/bcf-structural-handoff-2026-07-25.json` | BCF T1 AVAILABLE | T2 CDE NOT_VERIFIED |
| SSRF outbound | `outbound_url` (infra) | security tests | — | Allowed SSRF | ASSUMED path:line точный в этом файле не цитирован → добить в N-реестре |
| Offline closed-contour | `tools/offline_bundle` | CI `offline-bundle-smoke` | — | Offline Docker | bare-metal DEFERRED |
| Extraction F1 fixture | `evaluate_extraction` / baseline metrics | extraction tests | runtime-baseline `extraction_macro_f1` | Allowed F1 | claim_level fixture |
| Hybrid advisory pre-gate | `domain/hybrid/*` | `test_wp02_hybrid_*` | HYBRID reports | Allowed Hybrid | не verdict path |
| УКЭП / trust chain | signature envelope | verify_release tests | — | Forbidden «УКЭП проверена» | presence-only |
| Norm pack customer | NormRulePack loader | pack tests | — | RT-002 OPEN | нет approved pack |
| OpenAPI capabilities | presentation OpenAPI | `openapi-contract` job | openapi artifact | schema 1.3.0 honesty | — |

**Находка N-36:** строка матрицы `:74` всё ещё пишет schema **1.3.0**, baseline факт **1.4.0**.

### 4) Frontend без тестов (сорт. по ТЗ)

1. `CoverageMapPanel.tsx` — 0  
2. `IfcViewerPanel.tsx` — 0  
3. `DrawingEvidencePanel.tsx` — 5 (<12)  
4. `lib/api.ts` / `ifc-scene.ts` — 0  

### 5) CI jobs (blocking / advisory / PR)

См. таблицу П7. Единственный явный `continue-on-error: true`: audit **dev** lock (`ci.yml:345`).

### 6) skip/xfail

90 условных `skipTest`/`skipUnless` **с reason**. Отдельных `@pytest.mark.skip` без reason не найдено. Полный реестр 90 строк — в выводе `rg` аудита (не дублируется целиком здесь из-за объёма; сырой вывод сохранён в сессии).

### 7) Числа docs↔code под охраной

| Число | Охрана |
| --- | --- |
| README baseline snippet | `--check-readme` + artifact `readme_snippet` |
| LOC / test_functions | drift ±50 vs committed baseline |
| documented vs code env (baseline algo) | `--check-readme` sets |
| architecture (48/72/63) | `--check-readme` / inventory |
| ENGINEERING_STATUS version/date | `check_docs_metadata_integrity` |
| Claims forbidden phrases | `lint_claims.py` |
| Matrix blocked ≠ done | `--matrix-guard` |

### 8) `_MONITORED` / `_SCAN_ROOTS` / excludes / boundary

| Константа | Path | Exists? | Rename consequence |
| --- | --- | --- | --- |
| `_MONITORED[0]` | `docs/ENGINEERING_STATUS_2026_08.md` | OK | gate misses file → зависит от fail-open логики (**N-27**) |
| `_MONITORED[1]` | `docs/tz/TZ_COMPLIANCE_MATRIX_2026.md` | OK | то же |
| `_MONITORED[2]` | `docs/capability-claim-matrix-2026.md` | OK | то же |
| `_MONITORED[3]` | `docs/pilot-claim-boundary-2026.md` | OK | то же |
| `_SCAN_ROOTS` | README×2, `frontend/src`, `docs/docs.md`, partners, demo-format, customer | OK (проверены ключевые) | claims-lint не увидит перенос |
| `_EXCLUDE_PATH_FRAGMENTS` | CLAIMS_LOCK, RED_TEAM, baseline JSON, … | OK | исключённые файлы не сканируются |
| `_BOUNDARY_MARKERS` | `claim_level`, `n=`, `RT-001`, … | N/A | широкий `n=` → ложные «границы» (**N-28 related**) |
| `_ALLOW_FILE_RE` | file-wide amnesty | `ENGINEERING_STATUS` line 1 | **N-29 STILL_TRUE** |
| Table skip | `lint_claims.py:100` `startswith("|")` | — | **N-28 STILL_TRUE** |

---

## Новые находки (минимум 3) — N-32…

| ID | Суть | Доказательство |
| --- | --- | --- |
| **N-32** | Промт описывает 2 ветки + 7 PR; реальность: 1 ветка `main`, 0 open PR | `git branch -a`; `gh pr list` → `[]` |
| **N-33** | Два алгоритма env-учёта (baseline 79/60 vs сырой regex 107/98) | П8 вывод |
| **N-34** | Абсолютные пути Windows живут в `audit/evidence/**` (И17 шире baseline) | `rg` hits `samolet-sla-fixture-honesty-*.json` и др. |
| **N-35** | `CoverageMapPanel` = 0 тестов; `DrawingEvidencePanel` = 5 (<12 K4) | дерево + vitest 29 |
| **N-36** | Матрица claims всё ещё указывает baseline schema **1.3.0** при факте **1.4.0** | `capability-claim-matrix-2026.md:74` vs baseline JSON |
| **N-37** | `--check-committed-baseline` / `--check-publishable` красные на чистом `main` при зелёном merge CI | вывод П12; run `31301092314` success |
| **N-38** | Orphan port/adapter parity не сведён автоматическим отчётом в этом аудите | П3 UNVERIFIED |

---

## Предварительные статусы критичных N (до полного реестра Раздела 3)

> Полный реестр N-1…N-31 — следующий артефакт **после** этой карты. Здесь только якорные.

| № | Предварительно | Почему |
| --- | --- | --- |
| N-30 circular self-check | **FIXED_BY_US** (коммиты `76e0da0`…`e443d2b`) | `_compute_publishable` → только `_publishability_core_errors` (`export_runtime_baseline.py:883-893`) |
| N-30 residual / N-1 | **STILL_TRUE** | committed `publishable:false`, `attested_by:local`, нет `run_id` |
| N-24 в committed baseline | **FIXED_BY_US** (пути) | `vitest` относительный, `tool=python`; **но** N-34 в audit/evidence |
| N-25 | **FIXED_BY_US** | `--check-publishable` падает на non-publishable (вывод П12) |
| N-26 | **FIXED_BY_US** (код) | refuse write `export_runtime_baseline.py:1618` — перепроверить тестом на исходном/текущем |
| N-28 / N-29 | **STILL_TRUE** | `lint_claims.py:100`, `ENGINEERING_STATUS:1` allow-file |
| N-31 | **SUPERSEDED / FIXED_BY_US** частично | прямой push был; сейчас политика через PR #12; stale branch удалена; triage «7 PR» устарел (0 open) |

---

## Файлы «прочитать целиком» — статус чтения в этом аудите

| Файл | Статус |
| --- | --- |
| `.github/workflows/ci.yml` | карта джобов + `continue-on-error`; хвост 437–742 **частично** (needs/if) |
| `export_runtime_baseline.py` publishability | прочитаны `:762-893`, `:1618` |
| `test_docs_metadata_integrity` / scripts gate | `_MONITORED` прочитан |
| `pilot-claim-boundary`, TZ matrix, FINDINGS, docs.md §7, CRITICAL_BLOCKERS | **частично / ASSUMED** для полного текста — требуется дочитать до K1 |
| README markers | сверены `--check-readme` OK |

---

## Конец карты / git status

```text
git status --porcelain  → (пусто)
git rev-parse HEAD      → 5a75d866cce256d8b4caa010031683762b8ee162
```

**Следующий шаг по промту:** Раздел 3 — полная пересверка N-1…N-31 со статусами словаря 0.1 и доказательствами. Код пакетов P0 **не начинать**, пока реестр не сдан (кроме уже влитых FIXED_BY_US на `main`).
