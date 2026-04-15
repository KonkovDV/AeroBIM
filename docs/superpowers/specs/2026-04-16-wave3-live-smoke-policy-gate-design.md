# AeroBIM Wave 3 Live-Smoke Policy Gate Design

## Goal

Add an explicit release-readiness policy switch that can require live-smoke execution for selected runs without making smoke mandatory by default.

## Problem

`release-readiness.yml` already supports optional live smoke via `run_live_smoke`, but there is no policy mechanism that enforces smoke when an operator wants a stricter release gate.

This creates ambiguity: a run intended as strict can be launched with smoke disabled by mistake.

## Decision

Add a new workflow input:

- `require_live_smoke_gate` (boolean, default `false`)

Add a fast policy-check job:

- if `require_live_smoke_gate=true` and `run_live_smoke=false`, fail immediately with a clear operator message.

Wire benchmark job to depend on this policy-check so the run is rejected early when policy is violated.

## Why This Is Minimal And Safe

- preserves current default behavior (smoke remains optional by default);
- introduces strict-gate mode only when explicitly requested;
- avoids changing benchmark semantics or frontend/backend runtime logic.

## Verification Plan

- changed-file diagnostics on workflow + docs;
- docs closure rail (`sync:metrics`, `sync:metrics:check`, `agent:preflight:docs`);
- commit as a standalone control-plane tranche.
