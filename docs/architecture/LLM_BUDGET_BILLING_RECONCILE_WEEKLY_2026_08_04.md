---
title: "Weekly LLM budget ledger vs Yandex billing reconciliation"
date: 2026-08-04
status: active
version: "1.0.0"
claim_boundary: >-
  Ops procedure only. Does not change Checkpoint NO_GO.
  Do not raise budget ceilings to force a run through.
---

# I.6 — Сверка журнала бюджета с биллингом (еженедельно)

## Зачем

Open-bench CLI и прямые вызовы Studio могут обходить `backend/var/llm_token_budget.json`.
Расхождение `tokens_today` ↔ биллинг Yandex — сигнал «мимо AeroBIM», не повод поднимать потолок.

## Процедура (≤15 мин)

1. **Снять ledger**
   ```powershell
   Get-Content C:\plans\AeroBIM\backend\var\llm_token_budget.json
   ```
   Записать: `day` (Europe/Moscow), `tokens_today`, `tokens_run` (если есть), path.

2. **Снять биллинг** в консоли Yandex Cloud → Billing / AI Studio usage за тот же календарный день (МСК). Записать prompt+completion токены и ₽.

3. **Сверить**

   | Поле | Ledger | Billing | Δ |
   |---|---:|---:|---:|
   | tokens in | | | |
   | tokens out | | | |
   | ₽ | | | |

4. **Классифицировать Δ**
   - Δ ≈ 0 (±5%) → OK
   - Billing ≫ ledger → вызовы мимо ledger (open-bench CLI, ручные curl, другой ключ/folder)
   - Ledger ≫ billing → задержка агрегации вендора или неверный day-roll TZ

5. **Зафиксировать** одну строку в `docs/architecture/YANDEX_STUDIO_GRANT_OPS_REPORT_*.md` или в evidence note:
   `date | ledger_tokens | billing_tokens | delta | explanation | operator`

## Тарифы (ориентир гранта)

Вход 200 ₽/млн · выход 300 ₽/млн · кеш 50 ₽/млн (уточнять в консоли на дату сверки).

## Запрещено

- Поднимать `AEROBIM_LLM_MAX_TOKENS_*`, чтобы «прогнать» упёршийся прогон.
- Печатать API-ключ / kill-switch id в отчёт (id `ajeomh7lns01j2lv3dcc` только для операторского revoke).
