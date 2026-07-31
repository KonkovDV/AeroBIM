# AeroBIM — независимая верификация после supply-chain / release-integrity

**Тип:** continuation red-team / release verification (независимый цикл).
**Дата:** 2026-07-31. **Метод:** свежий рабочий репозиторий + прямое воспроизведение
(git, ruff, mypy, pytest, Docker 29.5.2, export_release_attestation). Статусы:
VERIFIED/REPRODUCED/REFUTED/STALE/PARTIAL/BLOCKED.

> Дисциплина промта соблюдена: заявленная база аудита `514b2aa` **STALE** —
> проверялось фактическое состояние `main`, а не снапшот.

## 1. Краткий итог

- Audit commit (заявленная база): `514b2aa` — существует, **ancestor** текущего HEAD (STALE).
- Current HEAD: `2c12642` (на 6 коммитов новее базы).
- Tree (до этого отчёта): `452e011f6f893c9c`.
- Working tree: **clean** (REPRODUCED: `git status --porcelain` пуст).
- Freshness: база = предок; HEAD содержит offline (5j/5k/5l), EI-wiring, RT-EI-04, dataset manifest.
- Overall status: все supply-chain/release-integrity тезисы прошлого внешнего red-team
  **REFUTED** на свежем состоянии; найдена **1 реальная дыра (RTV-01)** и закрыта в этом же цикле.
- Checkpoint: **NO_GO** (RT-001/002/003 открыты — внешние данные).
- New blockers: нет (RTV-01/02 закрыты сразу).
- Closed (this cycle): attestation теперь связывает docker_digest/test_run_id; null-семантика дизамбигуирована.
- Unverified/BLOCKED: RT-001/002/003, LIC-001 (legal), bare-metal offline (без Docker),
  полная security-батарея (в этом цикле не прогонялась — см. §8).

## 2. Вердикт по 11 тезисам прошлого red-team (REPRODUCED на HEAD)

| Тезис | Вердикт | Факт |
|---|---|---|
| Docker игнорирует lock-файлы | **REFUTED** | Dockerfile: `COPY requirements-lock.txt` → `--require-hashes` → проект `--no-deps`; offline build воспроизведён (5k) |
| Base image не pinned | **REFUTED** | обе стадии `python:3.12-slim@sha256:57cd7c3a...` |
| CI floating pip installs | **REFUTED** | 0 floating `pip install ruff/mypy`; всюду `--require-hashes` |
| Actions по плавающим тегам | **REFUTED** | 43 `uses:@<40-hex SHA>`, 0 `@vN` |
| Устаревший freeze SHA `8a314d8` | **REFUTED/STALE** | в CRITICAL_BLOCKERS `f2615e7` |
| README DEBUG=true | **REFUTED** | README: `AEROBIM_DEBUG=false`; Dockerfile `false`; prod compose `false` |
| README без NO_GO | **REFUTED** | баннер `## Checkpoint: NO_GO` присутствует |
| README без license disclosure | **REFUTED** | License-секция + SPDX-граница |
| OCI license label = просто MIT | **CONFIRMED→FIXED (ранее)** | `MIT AND LGPL-3.0-or-later AND (AGPL-3.0-only OR LicenseRef-Artifex-Commercial)` |
| fixture SLA как customer SLA | **CONFIRMED→FIXED (ранее)** | job `samolet-fixture-sla-smoke`, artifact `claim_level=fixture_only` |
| release attestation | **PARTIAL→FIXED (this cycle)** | см. RTV-01 |

## 3. Находки этого цикла

| ID | Severity | Находка | Статус | Fix |
|---|---|---|---|---|
| RTV-01 | MEDIUM | `export_release_attestation` захардкоживал `docker_digest=null`, `test_run_id=null` — в т.ч. в CI: attestation не связывал реальный образ и test-run | **FIXED** | CLI `--docker-digest`/`--test-run-id` + env `GITHUB_RUN_ID`; CI openapi-contract биндит run_id; offline-bundle-smoke эмитит полную attestation с digest образа |
| RTV-02 | LOW | `null` перегружен: «файл отсутствует» vs «pipeline-поле не заполнено» | **FIXED** | `field_semantics` в payload структурно разделяет MISSING/NOT_RUN |
| RTV-03 | INFO | dev `docker-compose.yml` по умолчанию `AEROBIM_DEBUG:-true` | **ACCEPTED** | это dev-compose; prod-compose и Dockerfile = `false`; не дефект |

## 4. Reproduction log

| Команда | Exit | Результат |
|---|---|---|
| `git status --porcelain` | 0 | пусто (clean) |
| `git merge-base --is-ancestor 514b2aa HEAD` | 0 | база = предок |
| `ruff format --check src tests` | 0 | без изменений |
| `ruff check src tests` | 0 | All checks passed |
| `mypy src` | 0 | 244 файла, no issues |
| `pytest tests -q` | 0 | **1603 passed / 8 skipped / 0 failed** |
| `check_markdown_links` | 0 | OK |
| `export_runtime_baseline --check-readme` | 0 | drift OK |
| `export_release_attestation` (clean/dirty/subdir) | 0 | clean=True; dirty→clean=False; subdir работает |
| `offline_bundle build/verify/smoke` (Docker 29.5.2) | 0/0/0 | образ из tar через `docker load`, `--network none`, health+caps 200 |

## 5. Release integrity (HEAD `2c12642`, до коммита отчёта)

- commit: `2c12642...`, tree: `452e011f...`, working_tree_clean: **true**.
- requirements-lock: `baae470109372942...` · dev-lock: `202f3994a0f53e1b...`
- sbom: `f151d71c31abc4e3...` · runtime-baseline: `ab7ed8f39ae9bf5b...`
- license-inventory: `4fbad345a36a47fc...` · Claims Lock: `5af0fc0fca3bf530...`
- docker_digest / test_run_id: ранее всегда null → **теперь bindable** (RTV-01); в offline-bundle-smoke
  эмитится полная attestation с реальным image id и `run_id-run_attempt`.
- attestation статус: **generated-per-run** (не коммитится); dirty-tree честно даёт `working_tree_clean=false`.

## 6. Claims Lock audit

Нового drift не найдено. Изменена только формулировка attestation:
`docker_digest/test_run_id всегда null` → `bindable pipeline-полями; null == NOT_RUN в данном контексте`.
Границы NO_GO / RT-001/002/003 / LIC-001 / calc-correctness / MEP / CDE-T2 — на месте.

## 7. Capability honesty (spot-check, не полный ре-деривейт)

VERIFIED дефолты честности сохранены: `extraction_integrity=NOT_VERIFIED` (FAILED блокирует pass),
`mep_system_clash=NOT_VERIFIED`, `calculation_correctness=NOT_IMPLEMENTED`, `dwg_dxf=MISSING`.
DI-wiring не выдаётся за capability; fixture-only не выдаётся за customer.

## 8. Security matrix — ЧЕСТНАЯ ГРАНИЦА

Полная security-батарея ШАГ 9 (path traversal, SSRF, ZIP/XXE, tenant ACL, rate-limit и т.д.)
**в этом цикле не прогонялась заново** — статус `NOT_REPRODUCED_THIS_CYCLE`. Существующие
негативные тесты присутствуют в suite (1603 passed), но независимая мутационная проверка
периметра — отдельная работа. Не заявляю security как заново подтверждённый.

## 9. Customer blockers

- **RT-001 (accuracy):** код даёт fixture-детерминизм + PrecisionClaim-гейт; заказчик даёт corpus + ≥2 экспертов + adjudication. Next: подписанный scope + корпус. Статус `BLOCKED_CUSTOMER_EVIDENCE`.
- **RT-002 (norm pack):** код исполняет approval-boundary; заказчик даёт официальный approved pack (ред./юрисдикция/hash). Статус `BLOCKED`.
- **RT-003 (federated MEP):** provider DI-wired; заказчик даёт federated IFC + clearance matrix + scope memo. Статус `BLOCKED`.

## 10. План работы

- **Сегодня:** (done) RTV-01/02 attestation binding + CI wiring.
- **До контрольной точки:** прогнать полную security-мутационную батарею (§8) и зафиксировать матрицу; document-as-data poisoned-fixtures в CI.
- **До пилота:** bare-metal offline (wheelhouse без Docker); Docker image vuln-scan (trivy) в CI.
- **После данных Самолёта:** RT-001/002/003, BCF T2 в реальной СОД.
- **Не делать сейчас:** новые крупные фичи до закрытия P0/P1 evidence-gap.

## 11. Финальный статус

**NO_GO** (customer sign-off) — RT-001/002/003 открыты.
Release-integrity: Docker build + offline install/runtime **REPRODUCED** локально; attestation
pipeline-биндинг закрыт (RTV-01). Это не RELEASE_VERIFIED для закрытого промышленного
контура без bare-metal offline и legal-clearance LIC-001, но supply-chain/release-гигиена
на свежем `main` существенно сильнее, чем в снапшоте, с которого шёл внешний аудит.
