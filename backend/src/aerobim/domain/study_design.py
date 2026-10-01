"""Adjudication-corpus planning: Wilson intervals and exact binomial power.

Answers the pilot-protocol question the customer will ask first: **how many
findings must the two experts label** for the interim threshold
TP/(TP+FP) >= 0.60 to be demonstrable rather than anecdotal.

Academic grounding (Jul 2026 practice):

- **Wilson score interval** (Wilson 1927) — the interval recommended by
  Brown, Cai & DasGupta 2001 (Statistical Science) over Wald/Clopper-Pearson
  for essentially all n and p; used both for reporting and for planning the
  half-width.
- **Exact one-sided binomial test** H0: p <= p0 vs H1: p > p0 with the
  conventional conservative critical value (smallest k with
  P(K >= k | p0) <= alpha); power computed exactly from the Binomial tail —
  no normal approximation, pure ``math.comb``.
- **Power analysis for evals**: Miller 2024 (arXiv 2411.00640, "Adding
  Error Bars to Evals") establishes sample-size analysis as a reporting
  norm for model evaluations; we apply it to the human-adjudicated corpus.
- Discreteness note: exact binomial power is sawtoothed in n (Chernick &
  Liu 2002); the planner returns the smallest n reaching the target and
  callers should treat nearby n as equivalent design points.

Claim boundary: the planner sizes the *labeling effort*; it never predicts
the precision itself and never upgrades fixture evidence (RT-001).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

_MAX_PLANNING_N = 1_000_000


@dataclass(frozen=True)
class WilsonInterval:
    """Wilson score interval for a binomial proportion."""

    successes: int
    trials: int
    alpha: float
    point: float
    lower: float
    upper: float
    method: str = "wilson_score"

    @property
    def half_width(self) -> float:
        return (self.upper - self.lower) / 2

    def as_dict(self) -> dict[str, object]:
        return {
            "successes": self.successes,
            "trials": self.trials,
            "alpha": self.alpha,
            "point": round(self.point, 6),
            "lower": round(self.lower, 6),
            "upper": round(self.upper, 6),
            "half_width": round(self.half_width, 6),
            "method": self.method,
        }


def wilson_interval(successes: int, trials: int, *, alpha: float = 0.05) -> WilsonInterval:
    """Wilson 1927 score interval (Brown-Cai-DasGupta 2001 recommendation)."""

    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= successes <= trials:
        raise ValueError("successes must lie in [0, trials]")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly inside (0, 1)")
    z = NormalDist().inv_cdf(1 - alpha / 2)
    p_hat = successes / trials
    z2_n = z * z / trials
    denominator = 1 + z2_n
    center = (p_hat + z2_n / 2) / denominator
    spread = (z / denominator) * math.sqrt(
        p_hat * (1 - p_hat) / trials + z * z / (4 * trials * trials)
    )
    return WilsonInterval(
        successes=successes,
        trials=trials,
        alpha=alpha,
        point=p_hat,
        lower=max(0.0, center - spread),
        upper=min(1.0, center + spread),
    )


def required_n_for_wilson_halfwidth(
    expected_p: float,
    *,
    half_width: float,
    alpha: float = 0.05,
) -> int:
    """Smallest n whose Wilson interval at k ~= expected_p*n is narrow enough.

    Planning variant: assumes the observed rate lands near ``expected_p``
    and asks when the Wilson half-width drops to ``half_width``.
    """

    if not 0.0 < expected_p < 1.0:
        raise ValueError("expected_p must lie strictly inside (0, 1)")
    if not 0.0 < half_width < 0.5:
        raise ValueError("half_width must lie strictly inside (0, 0.5)")
    for n in range(2, _MAX_PLANNING_N + 1):
        k = round(expected_p * n)
        if wilson_interval(k, n, alpha=alpha).half_width <= half_width:
            return n
    raise ValueError("no n within planning cap reaches the requested half-width")


def _binomial_tail_geq(k: int, n: int, p: float) -> float:
    """P(K >= k) for K ~ Binomial(n, p), exact via math.comb."""

    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    total = 0.0
    for i in range(k, n + 1):
        total += math.comb(n, i) * p**i * (1 - p) ** (n - i)
    return min(1.0, total)


@dataclass(frozen=True)
class BinomialPowerResult:
    """Exact one-sided binomial test design for H0: p <= p0 vs H1: p > p0."""

    n: int
    p0: float
    p_true: float
    alpha: float
    critical_k: int
    """Reject H0 when successes >= critical_k."""
    attained_alpha: float
    power: float
    method: str = "exact_binomial_one_sided"

    def as_dict(self) -> dict[str, object]:
        return {
            "n": self.n,
            "p0": self.p0,
            "p_true": self.p_true,
            "alpha": self.alpha,
            "critical_k": self.critical_k,
            "attained_alpha": round(self.attained_alpha, 6),
            "power": round(self.power, 6),
            "method": self.method,
        }


def binomial_power_one_sided(
    *,
    n: int,
    p0: float,
    p_true: float,
    alpha: float = 0.05,
) -> BinomialPowerResult:
    """Exact power of the conservative one-sided binomial test at size <= alpha."""

    if n <= 0:
        raise ValueError("n must be positive")
    if not 0.0 < p0 < 1.0 or not 0.0 < p_true < 1.0:
        raise ValueError("p0 and p_true must lie strictly inside (0, 1)")
    if p_true <= p0:
        raise ValueError("one-sided power needs p_true > p0 (H1 direction)")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly inside (0, 1)")

    critical_k = n + 1  # unreachable => never reject
    for k in range(n + 1):
        if _binomial_tail_geq(k, n, p0) <= alpha:
            critical_k = k
            break
    attained_alpha = _binomial_tail_geq(critical_k, n, p0)
    power = _binomial_tail_geq(critical_k, n, p_true)
    return BinomialPowerResult(
        n=n,
        p0=p0,
        p_true=p_true,
        alpha=alpha,
        critical_k=critical_k,
        attained_alpha=attained_alpha,
        power=power,
    )


def required_n_for_power(
    *,
    p0: float,
    p_true: float,
    alpha: float = 0.05,
    power: float = 0.8,
) -> BinomialPowerResult:
    """Smallest n whose exact one-sided test reaches the target power.

    Exact power is sawtoothed in n; the smallest qualifying n is returned
    and documented as such (nearby n are equivalent design points).
    """

    if not 0.0 < power < 1.0:
        raise ValueError("power must lie strictly inside (0, 1)")
    for n in range(1, _MAX_PLANNING_N + 1):
        result = binomial_power_one_sided(n=n, p0=p0, p_true=p_true, alpha=alpha)
        if result.power >= power:
            return result
    raise ValueError("no n within planning cap reaches the requested power")
