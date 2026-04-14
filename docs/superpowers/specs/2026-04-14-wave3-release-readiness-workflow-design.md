# AeroBIM Wave 3 Release-Readiness Workflow Design

## Goal

Promote local benchmark and live-smoke runtime proofs into a repeatable CI/release-readiness stage without forcing heavy smoke checks on every push.

## Problem

`AeroBIM` already has benchmark and live-smoke tools, but they are run ad hoc from local shells.

That keeps evidence local and manual, which weakens release confidence as the project grows.

## Decision

Add a manual GitHub Actions workflow with two jobs:

1. benchmark job (always on dispatch):
   - run baseline and fire-compliance benchmark packs;
   - persist JSON outputs as workflow artifacts.
2. live-smoke job (optional via workflow input):
   - bootstrap backend/frontend dependencies;
   - run the one-command live review smoke harness;
   - persist smoke JSON and browser artifacts.

## Why Manual Dispatch

- preserves fast default CI (`ci.yml`) for normal push/PR loops;
- allows operators to run release-readiness checks when needed;
- avoids introducing flaky browser/runtime checks into every commit gate.

## Scope Boundaries

- no replacement of the current `ci.yml` pipeline;
- no mandatory smoke run on pull requests;
- no benchmark budget thresholds in this tranche.

## Verification Plan

- workflow file diagnostics;
- docs sync for the new release-readiness entrypoint;
- docs closure rail (`sync:metrics`, `sync:metrics:check`, docs preflight).