# AeroBIM Wave 3 Release Threshold Mode Design

## Goal

Extend release-readiness benchmark rails with configurable threshold mode so operators can run either advisory or enforced budget checks.

## Problem

Benchmark threshold governance now exists in CI benchmark-smoke, but release-readiness did not expose an equivalent mode switch or profile selection for strict release runs.

## Decision

1. Add `benchmark_threshold_mode` input (`advisory` or `enforced`) to `release-readiness.yml`.
2. Add `benchmark_threshold_profile` input to select a profile file per run.
3. Evaluate thresholds inside `benchmark-rails` and publish both JSON + markdown threshold outputs as workflow artifacts.

## Why This Is Defensible

- preserves default behavior (`advisory`) while enabling strict policy runs (`enforced`);
- keeps policy profile explicit and versioned in the repository;
- aligns release-readiness evidence with CI benchmark-smoke evidence surfaces.

## Verification Plan

- changed-file diagnostics;
- docs/control-plane closure rail (`sync:metrics`, `sync:metrics:check`, `agent:preflight:docs`);
- atomic commit and push.
