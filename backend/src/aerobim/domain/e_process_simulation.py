"""Null trajectories for the fixture regression monitor.

Ville's inequality bounds the probability that a path ever crosses
``1/alpha``. One path may cross. The check is the crossing rate over a
fixed-seed ensemble, set next to the naive per-step alpha rule, which
spends alpha at every step.

This is a simulation under a synthetic null. It is not a customer-pack
measurement and it does not write ``summary.passed``.
"""

from __future__ import annotations

import math
from typing import Final

from aerobim.domain.sequential_inference import (
    betting_evalue_one_sided,
    new_e_process_state,
    update_e_process,
    update_e_process_with_evalue,
)

DEFAULT_SEED: Final = 20261018
DEFAULT_PATHS: Final = 400
DEFAULT_STEPS: Final = 30
DEFAULT_ALPHA: Final = 0.05
_NULL_DIFFS_PER_STEP: Final = 8


def simulate_null_trajectories(
    *,
    seed: int = DEFAULT_SEED,
    n_paths: int = DEFAULT_PATHS,
    n_steps: int = DEFAULT_STEPS,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, object]:
    """Run mixture, power and truncated-aGRAPA monitors on one null stream.

    Draws come from a fixed 32-bit linear congruential generator, so the
    ensemble does not depend on the language runtime. p-values are uniform
    on ``[0, 1)``. Betting diffs are uniform on ``[-1, 1]`` (mean zero, the
    boundary of ``H0: mean >= 0``). The naive rule alarms when any single
    p-value is below alpha.
    """

    if n_paths < 1 or n_steps < 1:
        raise ValueError("n_paths and n_steps must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly inside (0, 1)")
    state = seed & 0xFFFFFFFF
    mixture_crosses = 0
    power_crosses = 0
    betting_crosses = 0
    naive_alarms = 0
    mixture_wealth = 0.0
    power_wealth = 0.0
    betting_wealth = 0.0
    for path in range(n_paths):
        mixture = new_e_process_state(alpha=alpha, calibrator="mixture")
        power = new_e_process_state(alpha=alpha, calibrator="power")
        betting = new_e_process_state(alpha=alpha, calibrator="betting")
        naive = False
        for step in range(n_steps):
            p_value, state = _unit(state)
            naive = naive or p_value < alpha
            run_id = f"p{path}-s{step}"
            mixture = update_e_process(mixture, run_id=run_id, p_value=p_value)
            power = update_e_process(power, run_id=run_id, p_value=p_value)
            diffs: list[float] = []
            for _ in range(_NULL_DIFFS_PER_STEP):
                unit, state = _unit(state)
                diffs.append(2.0 * unit - 1.0)
            bet = betting_evalue_one_sided(diffs)
            betting = update_e_process_with_evalue(betting, run_id=run_id, e_value=bet.e_value)
        mixture_crosses += int(mixture.rejected)
        power_crosses += int(power.rejected)
        betting_crosses += int(betting.rejected)
        naive_alarms += int(naive)
        mixture_wealth += mixture.wealth
        power_wealth += power.wealth
        betting_wealth += betting.wealth
    return {
        "artifact_type": "e_process_null_simulation",
        "claim_level": "fixture_only",
        "corpus_kind": "synthetic_null",
        "publishable": False,
        "seed": seed,
        "n_paths": n_paths,
        "n_steps": n_steps,
        "alpha": alpha,
        "ville_threshold": 1.0 / alpha,
        "crossing_rate_bound": _crossing_rate_bound(alpha, n_paths),
        "mixture_crossing_rate": mixture_crosses / n_paths,
        "power_crossing_rate": power_crosses / n_paths,
        "betting_crossing_rate": betting_crosses / n_paths,
        "naive_alarm_rate": naive_alarms / n_paths,
        "mixture_mean_terminal_wealth": mixture_wealth / n_paths,
        "power_mean_terminal_wealth": power_wealth / n_paths,
        "betting_mean_terminal_wealth": betting_wealth / n_paths,
        "note": (
            "A single null path may cross 1/alpha. The bound is on the "
            "ensemble rate. The naive rule spends alpha at every step."
        ),
    }


def _unit(state: int) -> tuple[float, int]:
    """One uniform in ``[0, 1)`` from a fixed 32-bit LCG. Not a secret stream."""

    nxt = (1664525 * state + 1013904223) & 0xFFFFFFFF
    return (nxt / 0xFFFFFFFF, nxt)


def _crossing_rate_bound(alpha: float, n_paths: int) -> float:
    """Ville's alpha plus a Hoeffding deviation at delta = 0.01.

    Sample crossing rates are allowed up to this number. A larger rate
    means the monitor is not behaving like a level-alpha e-process on
    this null.
    """

    deviation = math.sqrt(math.log(2.0 / 0.01) / (2.0 * n_paths))
    return min(1.0, alpha + deviation)
