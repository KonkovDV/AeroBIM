# AeroBIM Wave 3 Benchmark Threshold Advisory Design

## Goal

Introduce a deterministic, machine-readable benchmark threshold profile and evaluate CI benchmark artifacts against it in advisory mode.

## Problem

Benchmark summary artifacts exist, but threshold interpretation is still manual. That makes budget governance subjective and hard to evolve toward enforceable release policy.

## Decision

1. Add `samples/benchmarks/benchmark-thresholds.json` as the initial threshold profile.
2. Add `aerobim.tools.benchmark_threshold_gate`:
   - loads benchmark artifacts and threshold profile,
   - evaluates per-pack `avg_ms` and `reports_per_second`,
   - emits JSON results,
   - emits markdown summary,
   - supports `advisory` and `enforced` modes.
3. Integrate CI `benchmark-smoke` with advisory threshold evaluation and artifact publication.

## Why Advisory First

- preserves CI stability while initial threshold profile is still being calibrated;
- creates a quantitative evidence trail needed for eventual enforced gating;
- keeps governance explicit and reviewable in versioned JSON.

## Verification Plan

- changed-file diagnostics;
- targeted backend tests for threshold gate tool;
- docs/control-plane closure rail (`sync:metrics`, `sync:metrics:check`, `agent:preflight:docs`).
