"""Anytime-valid sequential regression monitor for extraction comparisons.

Wraps the Wave L/M paired comparison into a game-theoretic e-process
(Wave O): every ``--fail-on-regression`` style check spends alpha, so an
open-ended history of CI comparisons needs Ville-type control instead of
per-run alpha=0.05. Each invocation:

1. aligns baseline/candidate ``extraction_quality_report`` artifacts,
2. produces a per-run e-value by one of two pinned strategies:
   - ``mixture`` / ``power``: one-sided paired sign-flip permutation p
     (``alternative='less'``, exact for n<=12, add-one Monte-Carlo
     otherwise) calibrated to an e-value (Vovk & Wang 2021);
   - ``betting``: direct test-by-betting e-value on the per-fixture
     macro-F1 differences (Waudby-Smith & Ramdas JRSS-B 2024; truncated
     aGRAPA, one-sided, deterministic) — no p-value intermediary;
3. multiplies it into the persisted wealth and latches rejection when
   wealth >= 1/alpha (Ville 1939; safe testing: rejection is irreversible).

Exit code 1 iff the monitor is in the rejected state. Claim boundary: the
alarm concerns the fixture regression history only — never customer
accuracy (RT-001).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from aerobim.domain.eval_statistics import paired_permutation_test
from aerobim.domain.sequential_inference import (
    EProcessEntry,
    EProcessState,
    betting_evalue_one_sided,
    new_e_process_state,
    update_e_process,
    update_e_process_with_evalue,
)
from aerobim.tools.compare_extraction_runs import _load_fixture_counts


def _state_from_dict(payload: dict[str, Any]) -> EProcessState:
    if payload.get("artifact_type") != "sequential_regression_monitor":
        raise ValueError("state file is not a sequential_regression_monitor artifact")
    history = tuple(
        EProcessEntry(
            run_id=str(entry["run_id"]),
            p_value=float(entry["p_value"]),
            e_value=float(entry["e_value"]),
            wealth_after=float(entry["wealth_after"]),
        )
        for entry in payload.get("history") or []
    )
    kappa = payload.get("kappa")
    # RT-E: never trust persisted parameters blindly — route alpha/calibrator/
    # kappa through the same validation as fresh state, then rebuild wealth
    # from the validated shell (a tampered alpha would silently gut Ville's
    # threshold).
    validated = new_e_process_state(
        alpha=float(payload["alpha"]),
        calibrator=str(payload["calibrator"]),
        kappa=float(kappa) if kappa is not None else None,
    )
    wealth = float(payload["wealth"])
    if wealth <= 0.0 or not math.isfinite(wealth):
        raise ValueError(f"state wealth must be a positive finite number, got {wealth}")
    return EProcessState(
        alpha=validated.alpha,
        calibrator=validated.calibrator,
        kappa=validated.kappa,
        wealth=wealth,
        rejected=bool(payload["rejected"]),
        history=history,
    )


def monitor_step(
    state: EProcessState,
    baseline_path: Path,
    candidate_path: Path,
    *,
    run_id: str,
    metric: str = "macro_f1",
    replicates: int = 10000,
    seed: int = 20260725,
) -> tuple[EProcessState, dict[str, Any]]:
    """One monitored comparison; returns (new_state, step_report)."""

    baseline = _load_fixture_counts(baseline_path)
    candidate = _load_fixture_counts(candidate_path)
    shared_ids = sorted(set(baseline) & set(candidate))
    if not shared_ids:
        raise ValueError("no shared fixture_ids between the two artifacts")
    aligned_a = [baseline[fixture_id] for fixture_id in shared_ids]
    aligned_b = [candidate[fixture_id] for fixture_id in shared_ids]

    if state.calibrator == "betting":
        if metric != "macro_f1":
            raise ValueError("betting monitor currently supports metric=macro_f1 only")
        from aerobim.domain.eval_statistics import _METRIC_FNS

        metric_fn = _METRIC_FNS[metric]
        diffs = [
            metric_fn([counts_b]) - metric_fn([counts_a])
            for counts_a, counts_b in zip(aligned_a, aligned_b, strict=True)
        ]
        bet = betting_evalue_one_sided(diffs)
        new_state = update_e_process_with_evalue(state, run_id=run_id, e_value=bet.e_value)
        evidence: dict[str, Any] = {"betting": bet.as_dict()}
    else:
        test = paired_permutation_test(
            aligned_a,
            aligned_b,
            metric=metric,
            replicates=replicates,
            seed=seed,
            alternative="less",
        )
        new_state = update_e_process(state, run_id=run_id, p_value=test.p_value)
        evidence = {"permutation_test": test.as_dict()}

    latest = new_state.history[-1]
    step = {
        "run_id": run_id,
        "metric": metric,
        "n_pairs": len(shared_ids),
        **evidence,
        "e_value": round(latest.e_value, 6),
        "wealth": round(new_state.wealth, 6),
        "threshold": new_state.threshold,
        "rejected": new_state.rejected,
    }
    return new_state, step


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True, help="Monitor state JSON (persisted)")
    parser.add_argument("--run-id", required=True, help="Unique id for this comparison run")
    parser.add_argument("--metric", default="macro_f1")
    parser.add_argument("--alpha", type=float, default=0.05, help="Used only when creating state")
    parser.add_argument(
        "--calibrator",
        choices=("mixture", "power", "betting"),
        default="mixture",
        help="Used only when creating state",
    )
    parser.add_argument("--replicates", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260725)
    args = parser.parse_args(argv)

    if args.state.exists():
        state = _state_from_dict(json.loads(args.state.read_text(encoding="utf-8")))
        # Creation-time parameters are frozen with the state; a differing
        # CLI value must not be silently ignored (alpha-shopping trap).
        if abs(args.alpha - state.alpha) > 1e-12 or args.calibrator != state.calibrator:
            print(
                f"warning: --alpha/--calibrator ignored; state pins alpha={state.alpha}, "
                f"calibrator={state.calibrator} (delete the state file to change them)",
                file=sys.stderr,
            )
    else:
        state = new_e_process_state(alpha=args.alpha, calibrator=args.calibrator)

    state, step = monitor_step(
        state,
        args.baseline.resolve(),
        args.candidate.resolve(),
        run_id=args.run_id,
        metric=args.metric,
        replicates=args.replicates,
        seed=args.seed,
    )
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(
        json.dumps(state.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(step, ensure_ascii=False, indent=2))
    if state.rejected:
        print(
            "Anytime-valid regression alarm: e-process wealth "
            f"{state.wealth:.4f} >= 1/alpha = {state.threshold:.1f}. "
            "Rejection is irreversible; investigate before further bumps.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
