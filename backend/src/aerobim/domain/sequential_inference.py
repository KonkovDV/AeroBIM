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
from dataclasses import dataclass, field

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
    return kappa * p ** (kappa - 1.0)


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
    """Fresh monitor. ``calibrator``: ``mixture`` (default) or ``power``."""

    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly inside (0, 1)")
    if calibrator not in ("mixture", "power"):
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


def update_e_process(state: EProcessState, *, run_id: str, p_value: float) -> EProcessState:
    """Fold one comparison run into the monitor (pure, returns new state).

    The e-value multiplies the wealth; the rejection flag latches once
    wealth crosses 1/alpha. Duplicate run_ids are rejected — feeding the
    same evidence twice would double-count it in the martingale.
    """

    if any(entry.run_id == run_id for entry in state.history):
        raise ValueError(f"duplicate run_id {run_id!r} in monitor history")
    if state.calibrator == "power":
        assert state.kappa is not None  # enforced by new_e_process_state
        e_value = calibrate_p_to_e(p_value, kappa=state.kappa)
    else:
        e_value = calibrate_p_to_e_mixture(p_value)
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
