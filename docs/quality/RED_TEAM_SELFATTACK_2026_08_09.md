# Red Team self-attacks — 2026-08-09 (G5)

Протокол: мутация → прогон → откат → вердикт `KILLED` | `SURVIVED`.

## Выполнено (локально, 09.08)

| id | Мутация | Команда | Ожидание | Вывод | Вердикт |
|----|---------|---------|----------|-------|---------|
| N-18a | `--attested-by ci` локально | `export_runtime_baseline --attested-by ci` | unknown argument | `unrecognized arguments: --attested-by` | **KILLED** |
| N-18b | `GITHUB_ACTIONS=true` без run_id | `GITHUB_ACTIONS=true python -m aerobim.tools.export_runtime_baseline` | `attested_by=local` | `attestation_environment_incomplete` в attestation | **KILLED** |
| 1 | подмена `commit_sha` в baseline | `compare_baseline_snapshots(tampered, generated)` | field mismatch | `baseline_field_mismatch:commit_sha` | **KILLED** |
| 3 | `--frontend-tests-passed 999` под CI env | `GITHUB_ACTIONS=true … --frontend-tests-passed 999` | exit 1 | `not allowed under CI attestation` | **KILLED** |
| 5 | MEP row `done` | `test_matrix_guard_catches_mep_row_marked_done` | violation | тест зелёный | **KILLED** |
| 6 | «точность 95%» в tmp md | `lint_claims` roots=[tmp] | violation | `[forbidden_accuracy_gt_90]` | **KILLED** |
| 7 | `blocked` + forbidden | `test_blocked_word_does_not_suppress` | hit | тест зелёный | **KILLED** |
| 8 | drift committed vs generated | `compare_baseline_snapshots` с подменённым sha | errors | `baseline_field_mismatch` + metrics drift | **KILLED** |
| 9 | локальный `publishable: true` | `export_runtime_baseline` + `publishability_errors` | `attestation_not_ci` | `publishable=False`, attestation local | **KILLED** |
| 11 | uncollected test defs | `publishability_errors` с `test_functions>tests_collected` | uncollected error | `uncollected_test_definitions` | **KILLED** |
| G6 | unframed 95% claim | `test_claim_needs_boundary_flags_unframed_numeric_claim` | violation | тест зелёный | **KILLED** |

**Итого локально: 11/20 KILLED** (цель ≥14 — остальное после CI).

## Требуют CI-ветки (запланировано)

| id | Мутация | Статус |
|----|---------|--------|
| 10 | security-regression красный | needs CI job failure |
| 13–20 | job-order / artifact / merge gates | после открытия PR и green CI |

## SURVIVED → новый P0

| id | Причина |
|----|---------|
| — | нет на 09.08 (локальный блок) |
