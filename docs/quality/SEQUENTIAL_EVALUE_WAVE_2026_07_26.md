---
title: "Anytime-valid sequential regression monitoring (e-values)"
status: done
version: "1.0.0"
last_updated: "2026-07-26"
claim_boundary: "E-process alarm охраняет историю fixture-регрессий; никогда не измеряет customer accuracy (RT-001). Rejection необратим. Checkpoint остаётся NO_GO."
---

# Wave O — Sequential e-value regression monitor (2026-07-26)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| p-to-e calibration | **Vovk & Wang 2021** (Ann. Statist.) — power calibrator f_κ(p) = κ·p^(κ−1), κ∈(0,1), and the tuning-free mixture calibrator F(p) = (1 − p + p·ln p)/(p·(ln p)²) |
| Maximal inequality | **Ville 1939** — P(sup_t E_t ≥ 1/α) ≤ α for nonnegative supermartingales: monitoring after every run is free |
| Safe testing | Grünwald, de Heide & Koolen 2024 (JRSS-B discussion paper) — rejections are irreversible; e-values compose under optional continuation |
| Field survey | Ramdas, Grünwald, Vovk & Shafer 2023 — SAVI (sequential anytime-valid inference); ICML 2025 tutorial; SAVI-2025 workshop (BIRS) |
| Freshest | arXiv 2501.03982 "Sequentializing a Test: Anytime Validity is Free" — exactly the pattern implemented here: turn a fixed-sample test into an anytime-valid sequential one via e-value composition |
| Multiple testing | Xu & Ramdas 2024 (AISTATS) — online multiple testing with e-values as the current norm |

## Gap closed (declared in Wave M "Explicitly NOT claimed")

The `--fail-on-regression` gate is honest for **one** comparison, but it
runs at every dependency bump/refactor. With T honest-null runs the chance
of ≥1 false alarm across history is 1 − 0.95^T (≈40% at T=10, ≈92% at
T=50), and the classical fix — pre-specifying T — is impossible for an
open-ended CI pipeline. Wave M deferred this as "sequential/always-valid
inference is a separate design"; Wave O is that design.

## Delivered (code + test)

- `domain/eval_statistics.py` — `paired_permutation_test` gains
  `alternative` = `two_sided` (default, unchanged) / `less` / `greater`.
  One-sided exact p-values include the identity flip → super-uniform →
  valid calibrator inputs; MC path keeps the add-one estimator.
- `domain/sequential_inference.py`:
  - `calibrate_p_to_e` (power, κ default 0.5 → e = 0.5/√p) и
    `calibrate_p_to_e_mixture` (закрытая форма, лимит F(1)=1/2 обработан
    явно) — оба admissible по Vovk–Wang;
  - `EProcessState` / `update_e_process` — running product ("wealth"),
    Ville-порог 1/α, **необратимый** `rejected`-латч (перезапуск wealth
    после тревоги молча переспендил бы α), запрет дубликатов run_id
    (повторная подача того же сравнения удвоила бы evidence в мартингале),
    чистые функции, детерминизм.
- `tools/sequential_regression_monitor.py` — CLI: state-файл JSON +
  baseline/candidate артефакты → односторонний p (`less`) → e → wealth;
  exit 1 в rejected-состоянии; state создаётся при первом запуске
  (α и калибратор фиксируются в момент создания).
- `tests/test_sequential_inference.py` — 17 тестов с ручными эталонами:
  one-sided p перечислены вручную (n=2: p_less = 1/4, p_greater = 1);
  калибраторы аналитически (p=0.04 → e=2.5; F(1/e) = e−2; F(e⁻²) =
  (e²−3)/4; F(1) = ½); E[e]=1 под U(0,1) численно (сингулярность у нуля
  учтена в допуске); Ville-кроссинг 5·5=25≥20 по шагам; необратимость
  (50→25→12.5 < 20, флаг держится); null-история сжимает wealth (0.5⁵)
  без тревоги; CLI-латч и накопление без тревоги.

## Statistical notes (for the record)

- Независимость e-значений между запусками оправдана тем, что каждый запуск
  тестирует **свою** гипотезу (свежий code change) и permutation-рандомность
  сэмплируется заново; общий фикстурный корпус не нарушает валидность
  произведения под глобальным нулём «ни одна версия ничего не изменила».
- Мониторинг дополняет, не заменяет per-run гейты: Wave L/M отвечают «эта
  версия хуже?», Wave O отвечает «накопила ли история достаточно evidence
  деградации при контроле ошибки на всю (бесконечную) историю».
- Калибровка p→e — консервативный, но универсальный путь (не требует
  модели данных); прямой betting-мартингейл на bounded diffs
  (Waudby-Smith & Ramdas) дал бы больше мощности, но требует выбора
  ставочной стратегии — отложено как отдельное решение.

## Explicitly NOT claimed

- Монитор не сертифицирует «регрессий не было» (это TOST-территория Wave M)
  — отсутствие тревоги ≠ доказательство стабильности.
- Не реализован прямой betting e-process (aGRAPA/ONS) — p-калибровка
  консервативнее; зафиксировано как осознанный трейд-офф.
  **Closed by Wave R:** [`BETTING_EVALUE_WAVE_2026_07_26.md`](BETTING_EVALUE_WAVE_2026_07_26.md)
  (усечённая aGRAPA, `--calibrator betting`).
- Fixture-история ≠ customer evidence (RT-001 неизменен).

## Gate evidence (2026-07-26 local)

`ruff format/check` PASS · `mypy src` 199 files PASS · `pytest tests -q`
**1057 passed, 7 skipped**.
