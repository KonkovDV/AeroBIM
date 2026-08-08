"""Anytime-valid sequential regression monitoring via e-values.

The CI regression gate runs at *every* dependency bump / refactor. Treating
each run as an isolated alpha=0.05 test inflates the family-wise error over
the project's history: with T honest-null comparisons the chance of at least
one false alarm approaches 1 - 0.95^T, and the classical fix (pre-specifying
T) is impossible for an open-ended pipeline.

Game-theoretic statistics (Jul 2026 practice) solves exactly this:

- **p-to-e calibration** (Vovk & Wang 2021, Ann. Statist.): any super-uniform
  p-value maps to an e-value via f_kappa(p) = kappa * p^(kappa-1), kappa in
  (0,1), or the mixture calibrator F(p) = (1 - p + p*ln p) / (p * (ln p)^2)
  (integral of f_kappa over kappa) which needs no tuning.
- **E-process by multiplication**: e-values from independent sequential
  tests multiply into a nonnegative supermartingale under the global null
  (each code change is a fresh hypothesis; the sign-flip randomness is
  independent across runs).
- **Ville's inequality** (Ville 1939): P(sup_t E_t >= 1/alpha) <= alpha —
  the running product may be monitored after every run, forever, with the
  overall false-alarm rate still bounded by alpha. Rejections are
  irreversible ("safe testing", Gruenwald, de Heide & Koolen, JRSS-B 2024);
  anytime validity costs nothing extra (arXiv 2501.03982); SAVI survey:
  Ramdas et al. 2023.

Claim boundary: the monitor guards the *fixture* corpus regression history;
it never measures customer accuracy (RT-001). One-sided permutation
p-values from ``paired_permutation_test(..., alternative="less")`` are exact
and super-uniform — valid calibrator inputs.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import cast

_LN_EPS = 1e-15


def calibrate_p_to_e(p_value: float, *, kappa: float = 0.5) -> float:
    """Vovk-Wang power calibrator f_kappa(p) = kappa * p^(kappa - 1).

    Valid (E[e] <= 1 under H0) for any fixed kappa in (0, 1) chosen before
    seeing the data. kappa = 0.5 gives e = 0.5 / sqrt(p) — the customary
    default. p = 0 is clamped to a tiny positive value (permutation p-values
    with the add-one estimator are never zero anyway).
    """

    if not 0.0 < kappa < 1.0:
        raise ValueError("kappa must lie strictly inside (0, 1)")
    if not 0.0 <= p_value <= 1.0:
        raise ValueError(f"p-value out of [0, 1]: {p_value}")
    p = max(p_value, _LN_EPS)
    return cast(float, kappa * p ** (kappa - 1.0))


def calibrate_p_to_e_mixture(p_value: float) -> float:
    """Vovk-Wang mixture calibrator F(p) = (1 - p + p ln p) / (p (ln p)^2).

    The integral of f_kappa over kappa in (0, 1): tuning-free and admissible.
    Limits handled explicitly: F(1) = 1/2 (second-order expansion) and the
    p -> 0 divergence is finite here because p is clamped away from zero.
    """

    if not 0.0 <= p_value <= 1.0:
        raise ValueError(f"p-value out of [0, 1]: {p_value}")
    p = max(p_value, _LN_EPS)
    log_p = math.log(p)
    if abs(log_p) < 1e-9:
        return 0.5
    return (1.0 - p + p * log_p) / (p * log_p * log_p)


@dataclass(frozen=True)
class BettingEvalue:
    """One-sided betting e-value for H0: mean(diff) >= 0 on bounded diffs.

    Test-by-betting (Waudby-Smith & Ramdas, JRSS-B 2024 read paper; Shafer
    2021): wealth W_n = prod_t (1 + lam_t * (x_t - 1/2)) with diffs mapped
    to x = (d + 1)/2 in [0, 1] and only downward bets lam_t <= 0, so W is a
    nonnegative supermartingale under every mean(d) >= 0 and W_n is a valid
    e-value (Markov/Ville). Bets are the truncated aGRAPA rule — the
    log-optimal-in-hindsight bet approximated from prefix mean/variance,
    clipped to [-lambda_cap, 0]. Truncation is deliberate: aggressive
    strategies risk almost-sure null bankruptcy (arXiv 2602.08888, Feb
    2026); capping preserves future power under optional continuation.
    """

    e_value: float
    n: int
    lambda_cap: float
    final_lambda: float
    strategy: str = "truncated_agrapa_one_sided"

    def as_dict(self) -> dict[str, object]:
        return {
            "e_value": self.e_value,
            "n": self.n,
            "lambda_cap": self.lambda_cap,
            "final_lambda": round(self.final_lambda, 6),
            "strategy": self.strategy,
        }


def betting_evalue_one_sided(
    diffs: Sequence[float],
    *,
    lambda_cap: float = 1.0,
) -> BettingEvalue:
    """Truncated-aGRAPA betting e-value against H0: mean(diff) >= 0.

    ``diffs`` are per-fixture metric differences (candidate − baseline),
    each in [-1, 1] (F1-type metrics). Mapping x = (d + 1)/2 puts the null
    boundary at m0 = 1/2. The bet is predictable: lam_t depends only on
    x_1..x_{t-1} (prefix mean and variance, aGRAPA form
    (mu_hat - m0) / (sigma_hat^2 + (mu_hat - m0)^2), clipped to
    [-lambda_cap, 0]); the theoretical positivity bound is |lam| < 2, the
    default cap 1.0 stakes at most half the wealth per round. Deterministic,
    no randomness. E[W] <= 1 under the null, so W plugs directly into the
    Wave O e-process as a per-run e-value. Power profile is *complementary*
    to p-calibration, not dominant: adaptive betting pays a burn-in (no bet
    at t=1), so at tiny n an exact permutation p can calibrate sharper,
    while for sustained shifts the betting wealth grows exponentially in n.
    """

    if not diffs:
        raise ValueError("betting e-value requires at least one diff")
    if not 0.0 < lambda_cap < 2.0:
        raise ValueError("lambda_cap must lie strictly inside (0, 2)")
    for diff in diffs:
        if not math.isfinite(diff) or not -1.0 <= diff <= 1.0:
            raise ValueError(f"diffs must be finite and within [-1, 1], got {diff}")

    m0 = 0.5
    wealth = 1.0
    running_sum = 0.0
    running_sq_sum = 0.0
    lam = 0.0
    for index, diff in enumerate(diffs):
        x = (diff + 1.0) / 2.0
        if index == 0:
            lam = 0.0  # no history -> no bet (predictability)
        else:
            mean = running_sum / index
            variance = max(running_sq_sum / index - mean * mean, 1e-12)
            raw = (mean - m0) / (variance + (mean - m0) ** 2)
            lam = min(0.0, max(-lambda_cap, raw))
        wealth *= 1.0 + lam * (x - m0)
        running_sum += x
        running_sq_sum += x * x
    return BettingEvalue(
        e_value=wealth,
        n=len(diffs),
        lambda_cap=lambda_cap,
        final_lambda=lam,
    )


@dataclass(frozen=True)
class EProcessEntry:
    """One monitored comparison run."""

    run_id: str
    p_value: float
    e_value: float
    wealth_after: float
    """Running product of e-values after this run."""

    def as_dict(self) -> dict[str, object]:
        # RT-D: p/e/wealth are persisted at full precision — the martingale
        # product must survive CLI restarts without rounding drift.
        return {
            "run_id": self.run_id,
            "p_value": self.p_value,
            "e_value": self.e_value,
            "wealth_after": self.wealth_after,
        }


@dataclass(frozen=True)
class EProcessState:
    """Anytime-valid regression monitor state (a test supermartingale).

    ``wealth`` is the running product of calibrated e-values; the alarm
    fires when wealth >= 1/alpha (Ville) and — per safe-testing semantics —
    **never resets**: ``rejected`` is monotone. Restarting the wealth after
    an alarm would silently re-spend alpha.
    """

    alpha: float = 0.05
    calibrator: str = "mixture"
    kappa: float | None = None
    wealth: float = 1.0
    rejected: bool = False
    history: tuple[EProcessEntry, ...] = field(default_factory=tuple)

    @property
    def threshold(self) -> float:
        return 1.0 / self.alpha

    def as_dict(self) -> dict[str, object]:
        return {
            "artifact_type": "sequential_regression_monitor",
            "schema_version": "1.0.0",
            "alpha": self.alpha,
            "calibrator": self.calibrator,
            "kappa": self.kappa,
            # RT-D: full precision — this dict is the persistence format.
            "wealth": self.wealth,
            "threshold": self.threshold,
            "rejected": self.rejected,
            "run_count": len(self.history),
            "history": [entry.as_dict() for entry in self.history],
            "claim_boundary": (
                "anytime-valid alarm over the fixture regression history; "
                "never customer accuracy (RT-001); rejection is irreversible"
            ),
        }


def new_e_process_state(
    *,
    alpha: float = 0.05,
    calibrator: str = "mixture",
    kappa: float | None = None,
) -> EProcessState:
    """Fresh monitor. ``calibrator``: ``mixture`` (default), ``power`` or
    ``betting`` (per-run e-values come from ``betting_evalue_one_sided``
    instead of p-calibration)."""

    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly inside (0, 1)")
    if calibrator not in ("mixture", "power", "betting"):
        raise ValueError(f"unknown calibrator {calibrator!r}")
    if calibrator == "power":
        resolved_kappa = 0.5 if kappa is None else kappa
        if not 0.0 < resolved_kappa < 1.0:
            raise ValueError("kappa must lie strictly inside (0, 1)")
    else:
        if kappa is not None:
            raise ValueError("kappa is only meaningful for the power calibrator")
        resolved_kappa = None
    return EProcessState(alpha=alpha, calibrator=calibrator, kappa=resolved_kappa)


def _append_entry(
    state: EProcessState,
    *,
    run_id: str,
    p_value: float,
    e_value: float,
) -> EProcessState:
    """Shared wealth-update core: latch rejection, forbid duplicate runs."""

    if any(entry.run_id == run_id for entry in state.history):
        raise ValueError(f"duplicate run_id {run_id!r} in monitor history")
    wealth = state.wealth * e_value
    entry = EProcessEntry(
        run_id=run_id,
        p_value=p_value,
        e_value=e_value,
        wealth_after=wealth,
    )
    return EProcessState(
        alpha=state.alpha,
        calibrator=state.calibrator,
        kappa=state.kappa,
        wealth=wealth,
        rejected=state.rejected or wealth >= state.threshold,
        history=(*state.history, entry),
    )


def update_e_process(state: EProcessState, *, run_id: str, p_value: float) -> EProcessState:
    """Fold one comparison run into the monitor (pure, returns new state).

    The e-value multiplies the wealth; the rejection flag latches once
    wealth crosses 1/alpha. Duplicate run_ids are rejected — feeding the
    same evidence twice would double-count it in the martingale.
    """

    if state.calibrator == "power":
        assert state.kappa is not None  # enforced by new_e_process_state
        e_value = calibrate_p_to_e(p_value, kappa=state.kappa)
    elif state.calibrator == "mixture":
        e_value = calibrate_p_to_e_mixture(p_value)
    else:
        raise ValueError(
            "state pins the betting strategy; feed betting e-values via "
            "update_e_process_with_evalue"
        )
    return _append_entry(state, run_id=run_id, p_value=p_value, e_value=e_value)


def update_e_process_with_evalue(
    state: EProcessState,
    *,
    run_id: str,
    e_value: float,
) -> EProcessState:
    """Fold a directly-constructed e-value (e.g. betting) into the monitor.

    Only ``betting`` states accept direct e-values — mixing sources inside
    one martingale would blur which guarantee the wealth carries. The
    recorded p-value is the Markov companion min(1, 1/e) (a valid p by
    Markov's inequality), kept for human-readable history only.
    """

    if state.calibrator != "betting":
        raise ValueError("direct e-values are only valid for a betting-calibrator state")
    if not math.isfinite(e_value) or e_value < 0.0:
        raise ValueError(f"e-value must be finite and nonnegative, got {e_value}")
    p_companion = min(1.0, 1.0 / e_value) if e_value > 0 else 1.0
    return _append_entry(state, run_id=run_id, p_value=p_companion, e_value=e_value)
