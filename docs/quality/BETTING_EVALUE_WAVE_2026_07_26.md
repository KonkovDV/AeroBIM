---
title: "Betting e-values for the sequential regression monitor"
status: done
version: "1.0.0"
last_updated: "2026-07-26"
claim_boundary: "Betting-вердикты охраняют историю fixture-регрессий; никогда не измеряют customer accuracy (RT-001). Checkpoint остаётся NO_GO."
---

# Wave R — Test-by-betting e-values (2026-07-26)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Core method | **Waudby-Smith & Ramdas, JRSS-B 2024 read paper** («Estimating means of bounded random variables by betting», 367+ цитирований) — capital process W = Π(1 + λ_t(x_t − m)) как e-process для bounded наблюдений |
| Betting paradigm | Shafer 2021 (JRSS-A, «Testing by betting») |
| Bet sizing | aGRAPA — приближённо лог-оптимальная ставка из префиксных mean/variance |
| **Свежайший (Feb 2026)** | **arXiv 2602.08888 «Almost sure null bankruptcy of testing-by-betting»** — агрессивные стратегии почти наверное банкротятся под нулём; прямое обоснование усечения λ (cap 1.0 = максимум половина капитала за раунд) |
| Related | Fischer 2025 (sequential Monte-Carlo testing by betting); Duan et al. 2022 (one-sided betting) |

## Gap closed (задекларирован в Wave O и повторён в Wave Q)

Wave O: «прямой betting-мартингейл дал бы больше мощности, но требует выбора
ставочной стратегии — отложено как отдельное решение». Wave R и есть это
решение: усечённая aGRAPA, односторонняя (только «вниз»), детерминированная.

## Delivered (code + test)

- `domain/sequential_inference.py`:
  - `betting_evalue_one_sided(diffs, lambda_cap=1.0)` — per-fixture разности
    метрик d∈[−1,1] отображаются в x=(d+1)/2 с нулевой границей m₀=½;
    ставка predictable (λ_t из префикса, при t=1 ставка запрещена);
    только λ≤0 (улучшение никогда не создаёт evidence регрессии);
    усечение к [−cap, 0] против null-банкротства; чистая функция, без
    случайности;
  - `update_e_process_with_evalue` — прямые e-значения принимает **только**
    betting-state: смешение источников в одном мартингейле размыло бы
    гарантию; p-компаньон min(1, 1/e) (валиден по Маркову) — для
    читаемости истории;
  - калибратор `betting` в `new_e_process_state` (kappa запрещена).
- `tools/sequential_regression_monitor.py` — `--calibrator betting`:
  per-fixture macro-F1 разности → betting e-value → Ville-монитор;
  evidence-блок шага содержит стратегию, cap и финальную ставку.
- `tests/test_betting_evalues.py` — 13 тестов:
  - **точный мартингейл-тест**: все 8 последовательностей d∈{−1,+1}³
    просчитаны вручную → wealth (1,1,1,1,0.5,0.5,0.75,2.25), среднее
    **ровно 1** — supermartingale-свойство проверено перебором, не
    симуляцией;
  - worst-case регрессия: W = 1.5^(n−1) (ставка насыщается на cap);
    равномерная −1/3: W = (7/6)^(n−1);
  - **нулевая эрозия на чистых прогонах**: d=0 → W=1 точно (mixture
    калибратор на p=1 умножает на ½) — ключевое операционное преимущество;
  - запрет смешения источников в обе стороны; CLI-траектория
    (7/6)⁹ → латч на третьем прогоне; валидации.

## Honest power note (записано и в docstring)

Профили мощности **комплементарны, не доминируют**: на равномерной −1/3
регрессии с n=10 mixture-калибровка exact-p (1/1024 → e≈21) тревожит с
первого прогона, а betting (адаптивная ставка платит burn-in) даёт e≈4.03 и
тревожит с третьего. Зато betting не тратит капитал на чистых прогонах
(W=1 против ×½) и растёт экспоненциально на затяжных дрейфах. Выбор
стратегии пинится при создании state и не переключается задним числом.

## Explicitly NOT claimed

- Betting не «лучше всегда» — комплементарность зафиксирована численно.
- Двусторонний betting и mixture-over-λ (LBOW/ONS-портфели) не реализованы —
  усечённая aGRAPA выбрана за детерминизм и проверяемость перебором.
- Fixture-история ≠ customer evidence (RT-001).

## Gate evidence (2026-07-26 local)

`ruff format/check` PASS · `mypy src` 202 files PASS · `pytest tests -q`
**1100 passed, 7 skipped**.
