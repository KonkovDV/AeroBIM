# Red Team self-attacks — 2026-08-09 (G5)

Протокол: мутация → прогон → откат → вердикт `KILLED` | `SURVIVED`.

## Выполнено (локально, 09.08)

| id | Мутация | Команда | Ожидание | Вывод | Вердикт |
|----|---------|---------|----------|-------|---------|
| N-18a | `--attested-by ci` локально | `export_runtime_baseline --attested-by ci` | unknown argument | `unrecognized arguments: --attested-by` | **KILLED** |
| N-18b | `GITHUB_ACTIONS=true` без run_id | `GITHUB_ACTIONS=true python -m aerobim.tools.export_runtime_baseline` | `attested_by=local` | `attestation_environment_incomplete` в attestation | **KILLED** |
| 6 | «точность 95%» в tmp md | `lint_claims` roots=[tmp] | violation | `[forbidden_accuracy_gt_90]` | **KILLED** |
| 7 | `blocked` + forbidden | `test_blocked_word_does_not_suppress` | hit | тест зелёный | **KILLED** |
| 5 | MEP row `done` | `test_matrix_guard_catches_mep_row_marked_done` | violation | тест зелёный | **KILLED** |
| G6 | unframed 95% claim | `test_claim_needs_boundary_flags_unframed_numeric_claim` | violation | тест зелёный | **KILLED** |

## Требуют CI-ветки (запланировано)

| id | Мутация | Статус |
|----|---------|--------|
| 1 | подмена `commit_sha` в baseline | ASSUMED → ветка `red-team/attack-1` + push |
| 3 | `--frontend-tests-passed 999` | KILLED кодом (запрет при CI attestation без vitest json) |
| 10 | security-regression красный | needs CI job failure |
| 11 | удаление test file | needs `uncollected` gate on baseline export |

## SURVIVED → новый P0

| id | Причина |
|----|---------|
| — | нет на 09.08 (локальный блок) |
