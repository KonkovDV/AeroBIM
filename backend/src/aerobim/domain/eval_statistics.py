"""Deterministic evaluation statistics — CIs and inter-annotator agreement.

Academic-grade uncertainty quantification for AeroBIM benchmark artifacts
(Jul 2026 reporting norms):

- **Cluster bootstrap CIs** (percentile method; Efron & Tibshirani 1993) for
  micro/macro P/R/F1. Resampling unit is the *fixture* (document cluster),
  matching the sampling design — instances within a document are not i.i.d.
  ACL Responsible-NLP / NeurIPS checklists: report error bars, state the
  method; default B=1000 resamples, 95% CI, fixed seed for reproducibility.
- **Paired sign-flip permutation test** for system comparison over the same
  fixture set (Noreen 1989; Dror et al. 2018; Zmigrod et al. 2022 exact
  variant). Exact enumeration for small n, Monte-Carlo otherwise with the
  Phipson & Smyth (2010) add-one estimator — permutation p-values are never
  zero. Two-sided.
- **Paired cluster-bootstrap CI of the metric difference** (joint resampling
  of fixture indices preserves pairing).
- **Equivalence TOST** (Schuirmann 1987; Berger & Hsu 1996 CI-inclusion;
  Lakens 2017 SESOI margins; Robinson & Froese 2004 bootstrap variant) —
  non-rejection of "no difference" can never certify equivalence, so the
  refactoring-safety gate needs its own test with a pre-specified margin.
- **Holm-Bonferroni step-down** (Holm 1979) FWER control for metric
  families, following Dror et al. 2017 (TACL) replicability practice for
  multiple comparisons in NLP evaluation.
- **Cohen's kappa** (Cohen 1960) for two annotators, nominal labels.
- **Krippendorff's alpha** (nominal; Krippendorff 2019, coincidence-matrix
  formulation) for >=2 annotators with missing labels.
- **Gwet's AC1** (Gwet 2008) for two annotators — chance-corrected agreement
  that is robust to the kappa paradox under high class imbalance (RT-026).

Claim boundary: statistics quantify *fixture-corpus* uncertainty; they never
upgrade fixture evidence to customer evidence (RT-001). All computations are
pure stdlib and deterministic given the seed.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

_MIN_CLUSTERS_FOR_STABLE_CI = 5


@dataclass(frozen=True)
class FixtureCounts:
    """Per-fixture confusion counts (the bootstrap resampling unit)."""

    true_positives: int
    false_positives: int
    false_negatives: int


@dataclass(frozen=True)
class BootstrapCI:
    """Percentile bootstrap confidence interval for one metric."""

    metric: str
    point: float
    lower: float
    upper: float
    replicates: int
    alpha: float
    seed: int
    n_clusters: int
    method: str = "cluster_percentile_bootstrap"
    stable: bool = True
    """False when n_clusters is too small for a trustworthy interval."""

    def as_dict(self) -> dict[str, object]:
        return {
            "metric": self.metric,
            "point": round(self.point, 6),
            "lower": round(self.lower, 6),
            "upper": round(self.upper, 6),
            "replicates": self.replicates,
            "alpha": self.alpha,
            "seed": self.seed,
            "n_clusters": self.n_clusters,
            "method": self.method,
            "stable": self.stable,
        }


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def _micro_metrics(sample: Sequence[FixtureCounts]) -> tuple[float, float, float]:
    tp = sum(item.true_positives for item in sample)
    fp = sum(item.false_positives for item in sample)
    fn = sum(item.false_negatives for item in sample)
    return _prf(tp, fp, fn)


def _macro_metrics(sample: Sequence[FixtureCounts]) -> tuple[float, float, float]:
    if not sample:
        return 0.0, 0.0, 0.0
    triples = [
        _prf(item.true_positives, item.false_positives, item.false_negatives) for item in sample
    ]
    n = len(triples)
    return (
        sum(t[0] for t in triples) / n,
        sum(t[1] for t in triples) / n,
        sum(t[2] for t in triples) / n,
    )


def _percentile(sorted_values: list[float], q: float) -> float:
    """Linear-interpolation percentile on a pre-sorted list (q in [0, 1])."""

    if not sorted_values:
        return 0.0
    position = q * (len(sorted_values) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return sorted_values[low]
    fraction = position - low
    return sorted_values[low] * (1 - fraction) + sorted_values[high] * fraction


def cluster_bootstrap_cis(
    fixtures: Sequence[FixtureCounts],
    *,
    replicates: int = 1000,
    alpha: float = 0.05,
    seed: int = 20260725,
) -> dict[str, BootstrapCI]:
    """Percentile cluster-bootstrap CIs for micro/macro P/R/F1.

    Fixtures (documents) are resampled with replacement B times; metrics are
    recomputed per replicate. Deterministic given ``seed``. With fewer than
    ``_MIN_CLUSTERS_FOR_STABLE_CI`` clusters the interval is flagged
    ``stable=False`` — report but do not lean on it.
    """

    n = len(fixtures)
    if replicates < 1:
        raise ValueError("bootstrap requires at least one replicate")
    rng = random.Random(seed)
    metric_names = (
        "micro_precision",
        "micro_recall",
        "micro_f1",
        "macro_precision",
        "macro_recall",
        "macro_f1",
    )
    point_values = dict(
        zip(
            metric_names,
            (*_micro_metrics(fixtures), *_macro_metrics(fixtures)),
            strict=True,
        )
    )

    replicate_values: dict[str, list[float]] = {name: [] for name in metric_names}
    if n > 0:
        for _ in range(replicates):
            sample = [fixtures[rng.randrange(n)] for _ in range(n)]
            sample_values = (*_micro_metrics(sample), *_macro_metrics(sample))
            for name, value in zip(metric_names, sample_values, strict=True):
                replicate_values[name].append(value)

    results: dict[str, BootstrapCI] = {}
    for name in metric_names:
        sorted_replicates = sorted(replicate_values[name])
        lower = (
            _percentile(sorted_replicates, alpha / 2) if sorted_replicates else (point_values[name])
        )
        upper = (
            _percentile(sorted_replicates, 1 - alpha / 2)
            if sorted_replicates
            else (point_values[name])
        )
        results[name] = BootstrapCI(
            metric=name,
            point=point_values[name],
            lower=lower,
            upper=upper,
            replicates=replicates,
            alpha=alpha,
            seed=seed,
            n_clusters=n,
            stable=n >= _MIN_CLUSTERS_FOR_STABLE_CI,
        )
    return results


def scalar_cluster_bootstrap_ci(
    values: Sequence[float],
    *,
    metric: str,
    replicates: int = 1000,
    alpha: float = 0.05,
    seed: int = 20260726,
) -> BootstrapCI:
    """Percentile cluster-bootstrap CI for the mean of per-cluster scalars.

    Generic companion to :func:`cluster_bootstrap_cis` for metrics that are
    already one number per cluster (e.g. per-case tie-aware nDCG). Same
    percentile method, same stability floor, deterministic given ``seed``.
    """

    n = len(values)
    if n == 0:
        raise ValueError("scalar_cluster_bootstrap_ci requires at least one cluster")
    if replicates < 1:
        raise ValueError("bootstrap requires at least one replicate")
    point = sum(values) / n
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(replicates):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    return BootstrapCI(
        metric=metric,
        point=point,
        lower=_percentile(means, alpha / 2),
        upper=_percentile(means, 1 - alpha / 2),
        replicates=replicates,
        alpha=alpha,
        seed=seed,
        n_clusters=n,
        stable=n >= _MIN_CLUSTERS_FOR_STABLE_CI,
    )


_MetricFn = Callable[[Sequence[FixtureCounts]], float]
_METRIC_FNS: dict[str, _MetricFn] = {
    "micro_precision": lambda sample: _micro_metrics(sample)[0],
    "micro_recall": lambda sample: _micro_metrics(sample)[1],
    "micro_f1": lambda sample: _micro_metrics(sample)[2],
    "macro_precision": lambda sample: _macro_metrics(sample)[0],
    "macro_recall": lambda sample: _macro_metrics(sample)[1],
    "macro_f1": lambda sample: _macro_metrics(sample)[2],
}

_EXACT_ENUMERATION_MAX_N = 12


@dataclass(frozen=True)
class PairedTestResult:
    """Paired sign-flip permutation test outcome (two- or one-sided)."""

    metric: str
    observed_diff: float
    """metric(B) − metric(A) on the aligned fixture set."""
    p_value: float
    exact: bool
    permutations: int
    seed: int | None
    n_pairs: int
    alternative: str = "two_sided"
    method: str = "paired_sign_flip_permutation"

    def as_dict(self) -> dict[str, object]:
        return {
            "metric": self.metric,
            "observed_diff": round(self.observed_diff, 6),
            "p_value": round(self.p_value, 6),
            "exact": self.exact,
            "permutations": self.permutations,
            "seed": self.seed,
            "n_pairs": self.n_pairs,
            "alternative": self.alternative,
            "method": self.method,
        }


def _metric_diff(
    system_a: Sequence[FixtureCounts],
    system_b: Sequence[FixtureCounts],
    metric: str,
) -> float:
    metric_fn = _METRIC_FNS[metric]
    return metric_fn(system_b) - metric_fn(system_a)


def paired_permutation_test(
    system_a: Sequence[FixtureCounts],
    system_b: Sequence[FixtureCounts],
    *,
    metric: str = "macro_f1",
    replicates: int = 10000,
    seed: int = 20260725,
    alternative: str = "two_sided",
) -> PairedTestResult:
    """Paired sign-flip permutation test on aligned fixtures.

    Under H0 (systems interchangeable) the A/B assignment within each fixture
    pair is exchangeable; we flip pairs and recompute the metric difference.
    Exact enumeration of all 2^n flips when n <= 12 (Zmigrod et al. 2022
    motivation); otherwise Monte-Carlo with the Phipson & Smyth (2010)
    add-one estimator so the p-value is never zero.

    ``alternative``: ``two_sided`` (|diff| >= |observed|), ``less`` (diff <=
    observed; evidence that B is *worse*), ``greater`` (diff >= observed).
    One-sided exact p-values include the identity flip, hence are
    super-uniform — safe inputs for e-value calibration (Vovk & Wang 2021).
    """

    if metric not in _METRIC_FNS:
        raise ValueError(f"unknown metric {metric!r}")
    if alternative not in ("two_sided", "less", "greater"):
        raise ValueError(f"unknown alternative {alternative!r}")
    if len(system_a) != len(system_b):
        raise ValueError("paired test requires equal-length aligned fixture lists")
    n = len(system_a)
    if n == 0:
        raise ValueError("paired test requires at least one fixture pair")
    if replicates < 1:
        raise ValueError("paired test requires at least one replicate")

    observed = _metric_diff(system_a, system_b, metric)
    tolerance = 1e-12

    def is_extreme(diff: float) -> bool:
        if alternative == "two_sided":
            return abs(diff) >= abs(observed) - tolerance
        if alternative == "less":
            return diff <= observed + tolerance
        return diff >= observed - tolerance

    def diff_for_mask(mask: int) -> float:
        flipped_a = [system_b[i] if (mask >> i) & 1 else system_a[i] for i in range(n)]
        flipped_b = [system_a[i] if (mask >> i) & 1 else system_b[i] for i in range(n)]
        return _metric_diff(flipped_a, flipped_b, metric)

    if n <= _EXACT_ENUMERATION_MAX_N:
        total = 1 << n
        extreme = sum(1 for mask in range(total) if is_extreme(diff_for_mask(mask)))
        return PairedTestResult(
            metric=metric,
            observed_diff=observed,
            p_value=extreme / total,
            exact=True,
            permutations=total,
            seed=None,
            n_pairs=n,
            alternative=alternative,
        )

    rng = random.Random(seed)
    extreme = 0
    for _ in range(replicates):
        mask = rng.getrandbits(n)
        if is_extreme(diff_for_mask(mask)):
            extreme += 1
    # Add-one: the observed labelling is itself a valid permutation.
    p_value = (extreme + 1) / (replicates + 1)
    return PairedTestResult(
        metric=metric,
        observed_diff=observed,
        p_value=p_value,
        exact=False,
        permutations=replicates,
        seed=seed,
        n_pairs=n,
        alternative=alternative,
    )


def paired_bootstrap_diff_ci(
    system_a: Sequence[FixtureCounts],
    system_b: Sequence[FixtureCounts],
    *,
    metric: str = "macro_f1",
    replicates: int = 1000,
    alpha: float = 0.05,
    seed: int = 20260725,
) -> BootstrapCI:
    """Percentile CI for metric(B) − metric(A) with joint fixture resampling.

    Sampling fixture *indices* keeps the pairing intact (paired cluster
    bootstrap); a CI excluding zero corroborates the permutation verdict.
    """

    if metric not in _METRIC_FNS:
        raise ValueError(f"unknown metric {metric!r}")
    if len(system_a) != len(system_b):
        raise ValueError("paired CI requires equal-length aligned fixture lists")
    n = len(system_a)
    if n == 0:
        raise ValueError("paired CI requires at least one fixture pair")
    if replicates < 1:
        raise ValueError("bootstrap requires at least one replicate")

    point = _metric_diff(system_a, system_b, metric)
    rng = random.Random(seed)
    diffs: list[float] = []
    for _ in range(replicates):
        indices = [rng.randrange(n) for _ in range(n)]
        sample_a = [system_a[i] for i in indices]
        sample_b = [system_b[i] for i in indices]
        diffs.append(_metric_diff(sample_a, sample_b, metric))
    diffs.sort()
    return BootstrapCI(
        metric=f"diff_{metric}",
        point=point,
        lower=_percentile(diffs, alpha / 2),
        upper=_percentile(diffs, 1 - alpha / 2),
        replicates=replicates,
        alpha=alpha,
        seed=seed,
        n_clusters=n,
        method="paired_cluster_percentile_bootstrap",
        stable=n >= _MIN_CLUSTERS_FOR_STABLE_CI,
    )


@dataclass(frozen=True)
class EquivalenceTestResult:
    """Paired cluster-bootstrap TOST verdict for metric(B) − metric(A).

    ``equivalent`` is fail-closed: it is True only when the interval is
    stable (enough clusters) **and** the (1 − 2α) CI lies strictly inside
    (−margin, +margin) — the Berger & Hsu (1996) CI-inclusion rule.
    """

    metric: str
    observed_diff: float
    margin: float
    alpha: float
    ci_lower: float
    ci_upper: float
    ci_level: float
    p_lower: float
    """Bootstrap p for H0: diff <= −margin (add-one estimator, never zero)."""
    p_upper: float
    """Bootstrap p for H0: diff >= +margin (add-one estimator, never zero)."""
    p_tost: float
    """max(p_lower, p_upper) — the TOST decision p-value."""
    equivalent: bool
    stable: bool
    replicates: int
    seed: int
    n_pairs: int
    method: str = "paired_cluster_bootstrap_tost"

    def as_dict(self) -> dict[str, object]:
        return {
            "metric": self.metric,
            "observed_diff": round(self.observed_diff, 6),
            "margin": self.margin,
            "alpha": self.alpha,
            "ci_lower": round(self.ci_lower, 6),
            "ci_upper": round(self.ci_upper, 6),
            "ci_level": self.ci_level,
            "p_lower": round(self.p_lower, 6),
            "p_upper": round(self.p_upper, 6),
            "p_tost": round(self.p_tost, 6),
            "equivalent": self.equivalent,
            "stable": self.stable,
            "replicates": self.replicates,
            "seed": self.seed,
            "n_pairs": self.n_pairs,
            "method": self.method,
        }


def equivalence_tost(
    system_a: Sequence[FixtureCounts],
    system_b: Sequence[FixtureCounts],
    *,
    metric: str = "macro_f1",
    margin: float,
    replicates: int = 2000,
    alpha: float = 0.05,
    seed: int = 20260726,
) -> EquivalenceTestResult:
    """Two one-sided tests via paired cluster bootstrap (CI-inclusion form).

    H0 (non-equivalence): |metric(B) − metric(A)| >= margin. Equivalence is
    declared at level ``alpha`` iff the (1 − 2α) percentile CI of the paired
    cluster-bootstrap difference lies strictly inside (−margin, +margin)
    (Berger & Hsu 1996; Lakens 2017 uses the same 90%-CI form at α=0.05;
    bootstrap variant per Robinson & Froese 2004). The ``margin`` is the
    smallest effect size of interest (SESOI) and must be pre-specified —
    there is no defensible default, so none is provided.

    One-sided p-values are the bootstrap tail fractions beyond each margin
    with the Phipson & Smyth (2010) add-one estimator (never zero); the TOST
    p-value is their maximum. Fewer than ``_MIN_CLUSTERS_FOR_STABLE_CI``
    pairs → ``stable=False`` and the verdict is withheld (``equivalent`` is
    forced False): too few clusters cannot certify equivalence.
    """

    if metric not in _METRIC_FNS:
        raise ValueError(f"unknown metric {metric!r}")
    if margin <= 0:
        raise ValueError("equivalence margin (SESOI) must be positive")
    if not 0 < alpha < 0.5:
        raise ValueError("alpha must be in (0, 0.5) for a (1-2a) CI")
    if len(system_a) != len(system_b):
        raise ValueError("TOST requires equal-length aligned fixture lists")
    n = len(system_a)
    if n == 0:
        raise ValueError("TOST requires at least one fixture pair")
    if replicates < 1:
        # RT-A: zero replicates would yield a degenerate [0, 0] "CI" and a
        # free equivalence certificate — fail closed instead.
        raise ValueError("TOST requires at least one bootstrap replicate")

    observed = _metric_diff(system_a, system_b, metric)
    rng = random.Random(seed)
    diffs: list[float] = []
    for _ in range(replicates):
        indices = [rng.randrange(n) for _ in range(n)]
        sample_a = [system_a[i] for i in indices]
        sample_b = [system_b[i] for i in indices]
        diffs.append(_metric_diff(sample_a, sample_b, metric))
    diffs.sort()

    ci_lower = _percentile(diffs, alpha)
    ci_upper = _percentile(diffs, 1 - alpha)
    below = sum(1 for diff in diffs if diff <= -margin)
    above = sum(1 for diff in diffs if diff >= margin)
    p_lower = (below + 1) / (replicates + 1)
    p_upper = (above + 1) / (replicates + 1)
    stable = n >= _MIN_CLUSTERS_FOR_STABLE_CI
    equivalent = stable and (-margin < ci_lower) and (ci_upper < margin)
    return EquivalenceTestResult(
        metric=metric,
        observed_diff=observed,
        margin=margin,
        alpha=alpha,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        ci_level=1 - 2 * alpha,
        p_lower=p_lower,
        p_upper=p_upper,
        p_tost=max(p_lower, p_upper),
        equivalent=equivalent,
        stable=stable,
        replicates=replicates,
        seed=seed,
        n_pairs=n,
    )


@dataclass(frozen=True)
class HolmResult:
    """Holm (1979) step-down FWER adjustment over a family of p-values."""

    alpha: float
    family_size: int
    adjusted_p: Mapping[str, float]
    reject: Mapping[str, bool]
    method: str = "holm_bonferroni"

    def as_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "alpha": self.alpha,
            "family_size": self.family_size,
            "adjusted_p": {name: round(value, 6) for name, value in self.adjusted_p.items()},
            "reject": dict(self.reject),
        }


def holm_bonferroni(
    p_values: Mapping[str, float],
    *,
    alpha: float = 0.05,
) -> HolmResult:
    """Holm (1979) step-down FWER adjustment for a family of p-values.

    Adjusted p_(i) = max_{j<=i} min(1, (m − j + 1) · p_(j)) over the
    ascending order — monotone by construction, valid under arbitrary
    dependence, uniformly more powerful than plain Bonferroni. Rejection at
    ``alpha`` follows the step-down rule (equivalently adjusted p <= alpha).
    """

    if not p_values:
        raise ValueError("holm_bonferroni requires at least one p-value")
    for name, p_value in p_values.items():
        if not 0.0 <= p_value <= 1.0:
            raise ValueError(f"p-value out of [0, 1] for {name!r}: {p_value}")
    m = len(p_values)
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running_max = 0.0
    for rank, (name, p_value) in enumerate(ordered):
        running_max = max(running_max, min(1.0, (m - rank) * p_value))
        adjusted[name] = running_max
    return HolmResult(
        alpha=alpha,
        family_size=m,
        adjusted_p={name: adjusted[name] for name in p_values},
        reject={name: adjusted[name] <= alpha for name in p_values},
    )


def paired_scalar_permutation_test(
    values_a: Sequence[float],
    values_b: Sequence[float],
    *,
    metric: str = "scalar",
    replicates: int = 10000,
    seed: int = 20260726,
    alternative: str = "two_sided",
) -> PairedTestResult:
    """Paired sign-flip permutation test on per-cluster scalar pairs.

    Statistic: mean(b_i − a_i). Under H0 the A/B assignment within each
    pair is exchangeable, so flipping a pair negates its difference. Exact
    enumeration for n <= 12; Monte-Carlo with the Phipson & Smyth (2010)
    add-one estimator otherwise. Companion to the FixtureCounts variant for
    metrics that are already one scalar per cluster (e.g. per-case nDCG).
    """

    if alternative not in ("two_sided", "less", "greater"):
        raise ValueError(f"unknown alternative {alternative!r}")
    if len(values_a) != len(values_b):
        raise ValueError("paired test requires equal-length aligned value lists")
    n = len(values_a)
    if n == 0:
        raise ValueError("paired test requires at least one pair")
    if replicates < 1:
        raise ValueError("paired test requires at least one replicate")
    for value in (*values_a, *values_b):
        if not math.isfinite(value):
            raise ValueError("paired test requires finite values")

    diffs = [b - a for a, b in zip(values_a, values_b, strict=True)]
    observed = sum(diffs) / n
    tolerance = 1e-12

    def is_extreme(diff: float) -> bool:
        if alternative == "two_sided":
            return abs(diff) >= abs(observed) - tolerance
        if alternative == "less":
            return diff <= observed + tolerance
        return diff >= observed - tolerance

    def diff_for_mask(mask: int) -> float:
        total = 0.0
        for index, diff in enumerate(diffs):
            total += -diff if (mask >> index) & 1 else diff
        return total / n

    if n <= _EXACT_ENUMERATION_MAX_N:
        total_masks = 1 << n
        extreme = sum(1 for mask in range(total_masks) if is_extreme(diff_for_mask(mask)))
        return PairedTestResult(
            metric=metric,
            observed_diff=observed,
            p_value=extreme / total_masks,
            exact=True,
            permutations=total_masks,
            seed=None,
            n_pairs=n,
            alternative=alternative,
        )

    rng = random.Random(seed)
    extreme = 0
    for _ in range(replicates):
        mask = rng.getrandbits(n)
        if is_extreme(diff_for_mask(mask)):
            extreme += 1
    return PairedTestResult(
        metric=metric,
        observed_diff=observed,
        p_value=(extreme + 1) / (replicates + 1),
        exact=False,
        permutations=replicates,
        seed=seed,
        n_pairs=n,
        alternative=alternative,
    )


def paired_scalar_bootstrap_diff_ci(
    values_a: Sequence[float],
    values_b: Sequence[float],
    *,
    metric: str = "scalar",
    replicates: int = 1000,
    alpha: float = 0.05,
    seed: int = 20260726,
) -> BootstrapCI:
    """Percentile CI for mean(B − A) with joint index resampling of pairs."""

    if len(values_a) != len(values_b):
        raise ValueError("paired CI requires equal-length aligned value lists")
    n = len(values_a)
    if n == 0:
        raise ValueError("paired CI requires at least one pair")
    if replicates < 1:
        raise ValueError("bootstrap requires at least one replicate")
    diffs = [b - a for a, b in zip(values_a, values_b, strict=True)]
    for value in diffs:
        if not math.isfinite(value):
            raise ValueError("paired CI requires finite values")
    point = sum(diffs) / n
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(replicates):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    return BootstrapCI(
        metric=f"diff_{metric}",
        point=point,
        lower=_percentile(means, alpha / 2),
        upper=_percentile(means, 1 - alpha / 2),
        replicates=replicates,
        alpha=alpha,
        seed=seed,
        n_clusters=n,
        method="paired_scalar_percentile_bootstrap",
        stable=n >= _MIN_CLUSTERS_FOR_STABLE_CI,
    )


def cohen_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> float:
    """Cohen's kappa (1960) for two annotators over nominal labels."""

    if len(labels_a) != len(labels_b):
        raise ValueError("cohen_kappa requires equal-length label sequences")
    if not labels_a:
        raise ValueError("cohen_kappa requires at least one item")
    n = len(labels_a)
    observed = sum(1 for a, b in zip(labels_a, labels_b, strict=True) if a == b) / n
    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    expected = sum((counts_a[label] / n) * (counts_b.get(label, 0) / n) for label in counts_a)
    if math.isclose(expected, 1.0):
        return 1.0 if math.isclose(observed, 1.0) else 0.0
    return (observed - expected) / (1 - expected)


def gwet_ac1(labels_a: Sequence[str], labels_b: Sequence[str]) -> float:
    """Gwet's AC1 (2008) for two annotators — imbalance-robust vs Cohen κ paradox.

    pe = (1/(q-1)) * Σ_k π_k (1-π_k), where π_k is the average category
    prevalence across both raters and q is the number of categories present.
    """

    if len(labels_a) != len(labels_b):
        raise ValueError("gwet_ac1 requires equal-length label sequences")
    if not labels_a:
        raise ValueError("gwet_ac1 requires at least one item")
    n = len(labels_a)
    observed = sum(1 for a, b in zip(labels_a, labels_b, strict=True) if a == b) / n
    categories = sorted(set(labels_a) | set(labels_b))
    q = len(categories)
    if q < 2:
        return 1.0 if math.isclose(observed, 1.0) else 0.0
    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    expected = 0.0
    for label in categories:
        pi = (counts_a[label] + counts_b[label]) / (2.0 * n)
        expected += pi * (1.0 - pi)
    expected /= q - 1
    if math.isclose(expected, 1.0):
        return 1.0 if math.isclose(observed, 1.0) else 0.0
    return (observed - expected) / (1.0 - expected)


def krippendorff_alpha_nominal(
    units: Sequence[Mapping[str, str | None]],
) -> float:
    """Krippendorff's alpha for nominal data (coincidence-matrix formulation).

    ``units`` maps annotator id -> label (``None`` / absent = missing). Units
    with fewer than two non-missing labels are excluded (unpairable).
    Formula (Krippendorff 2019): alpha = 1 - (n-1) * sum_{c != k} o_ck /
    (n^2 - sum_c n_c^2), where o is the coincidence matrix and n the number
    of pairable values.
    """

    coincidences: dict[tuple[str, str], float] = {}
    value_totals: Counter[str] = Counter()
    n_pairable = 0
    for unit in units:
        values = [label for label in unit.values() if label is not None]
        m = len(values)
        if m < 2:
            continue
        n_pairable += m
        for value in values:
            value_totals[value] += 1
        for index, value_c in enumerate(values):
            for value_k in values[:index] + values[index + 1 :]:
                pair = (value_c, value_k)
                coincidences[pair] = coincidences.get(pair, 0.0) + 1 / (m - 1)

    if n_pairable < 2:
        raise ValueError("krippendorff_alpha requires at least one pairable unit")
    observed_disagreement = sum(count for (c, k), count in coincidences.items() if c != k)
    expected_denominator = n_pairable * n_pairable - sum(
        total * total for total in value_totals.values()
    )
    if expected_denominator == 0:
        # Single category everywhere: no variance — perfect agreement by
        # convention when no disagreement was observed.
        return 1.0 if observed_disagreement == 0 else 0.0
    return 1.0 - (n_pairable - 1) * observed_disagreement / expected_denominator


def agreement_artifact(
    units: Sequence[Mapping[str, str | None]],
    *,
    kappa_threshold: float = 0.60,
    alpha_threshold: float = 0.67,
    ac1_threshold: float = 0.60,
) -> dict[str, object]:
    """Build the agreement artifact consumed by the RT-001 publishability gate.

    Emits ``cohen_kappa`` / ``gwet_ac1`` when exactly two annotators labeled every
    pairable unit; ``krippendorff_alpha`` always (>=2 annotators, missing
    tolerated). Thresholds follow the intake protocol (kappa>=0.60,
    alpha>=0.67 per Krippendorff's customary cut-off; AC1>=0.60 for imbalance).
    """

    annotators = sorted({name for unit in units for name in unit})
    alpha_value = krippendorff_alpha_nominal(units)
    payload: dict[str, object] = {
        "artifact_type": "annotation_agreement",
        "schema_version": "1.1.0",
        "annotators": annotators,
        "unit_count": len(units),
        "krippendorff_alpha": round(alpha_value, 6),
        "alpha_threshold": alpha_threshold,
        "pass_alpha_0_67": alpha_value >= alpha_threshold,
        "claim_boundary": (
            "agreement on fixture/customer labels; never upgrades fixture "
            "evidence to customer evidence (RT-001); report κ + α + AC1"
        ),
    }
    if len(annotators) == 2:
        first, second = annotators
        pairs = [
            (unit.get(first), unit.get(second))
            for unit in units
            if unit.get(first) is not None and unit.get(second) is not None
        ]
        if pairs:
            left = [str(a) for a, _ in pairs]
            right = [str(b) for _, b in pairs]
            kappa_value = cohen_kappa(left, right)
            ac1_value = gwet_ac1(left, right)
            payload["cohen_kappa"] = round(kappa_value, 6)
            payload["gwet_ac1"] = round(ac1_value, 6)
            payload["kappa_threshold"] = kappa_threshold
            payload["ac1_threshold"] = ac1_threshold
            payload["pass_threshold_0_60"] = kappa_value >= kappa_threshold
            payload["pass_ac1_0_60"] = ac1_value >= ac1_threshold
    if "pass_threshold_0_60" not in payload:
        # Fall back to alpha for the kappa-position gate when kappa is
        # undefined (>2 annotators or no complete pairs).
        payload["pass_threshold_0_60"] = alpha_value >= kappa_threshold
    return payload
