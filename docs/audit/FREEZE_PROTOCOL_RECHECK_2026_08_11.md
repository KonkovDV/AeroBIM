<!-- claims-lint: allow-file reason="Freeze protocol recheck evidence; no product GO claims" -->
---
title: "Freeze protocol code recheck — 2026-08-11"
claim_boundary: "Governance evidence only. Checkpoint NO_GO for RT-001/002/003 unchanged. TZ ~35% unchanged."
---

# Перепроверка кода против протокола заморозки (11.08)

## Календарь дня

| Контроль | Требование 11.08 | Статус после перепроверки |
|---|---|---|
| **A4 signing** | Включить оба флага + `state=active` | **DONE** — `enforce_ci=true`, `fail_on_unverifiable_signature=true`, `min_signed_ratio=0.03`, registry `A4-signing-enforcement=active` |
| Dry-run перед flip | Зелёная проверка доли | **18/50** trusted (`ratio=0.36`), `unverifiable=0`, including merges `3489cad` / `1de5649` / `5a75d86` |
| N43 lag=1 | Дата **17.08** | Остаётся `deferred`, `max_commits_behind=50` (ok) |
| RUF100 / CODEOWNERS / FE lint | После 19.08 | `deferred` с датами — не трогать |

## Реестр отсрочек → включённость

| ID | Mechanism exists | Enabled |
|---|---|---|
| A4-signing-enforcement | yes | **yes (11.08)** |
| N43-baseline-one-commit-lag | yes | deferred → 17.08 |
| N47-ruf100 | yes | deferred → 25.08 |
| N49-hitl-role-profile-boundary | yes | **active** |
| N59-trusted-keys… | note | deferred → 25.08 |
| Private paths CI (N-51) | yes | **active** (`private_marker_hits=0`) |
| CodeQL (N-52) | yes | **active** (separate workflow) |

## N-49…N-54 scorecard (код)

| ID | Verdict | Evidence |
|---|---|---|
| N-49 | **CLOSED** | claim-boundary L76 + `test_hitl_role_gate_profile_matrix` |
| N-50 | **PARTIAL** | Review-event `.seq.N` O_EXCL closed; audit store shares lock reclaim, not seq CAS (honest residual) |
| N-51 | **CLOSED** | CI step + live `private_marker_hits=0` + history empty |
| N-52 | **CLOSED** | `.github/workflows/codeql.yml` push/PR/schedule |
| N-53 | **CLOSED** | `ratio_scope=inspect_window`, depth 50 |
| N-54 | **CLOSED** | `.seq.N` = full payload + fsync; reclaim via rename `.stolen.*` |

## Доп. фикс этой перепроверки

`verify_commit_signatures.py` / `import_trusted_signing_keys.py`: `_gpg_bin()` читает `git config gpg.program` (Windows Git path), иначе локальный dry-run ломался при отсутствии `gpg` в PATH.

## Что не закрывать до заморозки

- RT-001/002/003 Checkpoint **NO_GO**
- RUF100 / frontend ESLint / CODEOWNERS (после 19.08)
- N43 lag=1 до репетиции 17.08
- Продуктовые TZ-критерии (коллизии / overlay) — окно 12–16.08; **fixture handoff готов** 11.08 (`docs/evidence/kt2-handoff-2026-08-11/`)

## KT#2 handoff (добавлено 11.08 вечер)

| Артефакт | Статус |
|---|---|
| Wall-guid bundle + verify | **passed** under `docs/evidence/kt2-handoff-2026-08-11/wall-guid` |
| Vertical slice | regenerated in handoff pack |
| Harness synthetic + `--require-publishable` | exit **1** (fail-closed) |
| Clash AABB + overlay PNG | `fixture_measured` / `fixture_rendered` |
| Cover note | [`../demo/KT2_HANDOFF_COVER_2026_08_11.md`](../demo/KT2_HANDOFF_COVER_2026_08_11.md) |
| Tri-source alignment | [`../tz/KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md`](../tz/KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md) |
| Handoff verify gate | `python -m aerobim.tools.verify_kt2_handoff` → [`../evidence/kt2-handoff-2026-08-11/VERIFY.json`](../evidence/kt2-handoff-2026-08-11/VERIFY.json) |
| RT recheck 12.08 | [`../ENGINEERING_STATUS_2026_08.md`](../ENGINEERING_STATUS_2026_08.md) — RT-001/002/003 still OPEN |

## Команды (воспроизводимо)

```text
python scripts/activate_a4_signing_enforcement.py
python backend/scripts/verify_deferred_controls.py --registry governance/deferred_controls_registry.json
python backend/scripts/import_trusted_signing_keys.py --keys-dir governance/trusted_signing_keys
python backend/scripts/verify_commit_signatures.py --policy governance/commit_signing_policy.json
python backend/scripts/verify_no_private_tracked_paths.py
```
