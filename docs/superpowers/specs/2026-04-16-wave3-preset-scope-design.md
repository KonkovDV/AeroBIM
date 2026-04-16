# AeroBIM Wave 3 Preset Scope Design

## Goal

Add explicit scope semantics to frontend report-filter presets so operators can distinguish local personal presets from team-shared presets.

## Problem

Preset transfer already supports JSON copy/import, but all presets are treated as generic local entities. This obscures ownership intent and makes team-shared payloads indistinguishable after import.

## Decision

1. Extend preset model with `scope: "local" | "team"`.
2. Add scope selector to preset save flow.
3. Include scope in JSON transfer payloads.
4. Default missing imported scope to `team` to mark external/shared payloads explicitly.
5. Display scope badge next to each preset chip.

## Why This Is Minimal

- no backend changes;
- no contract changes for report API;
- localStorage payload remains backward-compatible via scope normalization.

## Verification Plan

- frontend diagnostics;
- `npm test` and `npm run build` in frontend;
- docs/control-plane closure rail (`sync:metrics`, `sync:metrics:check`, `agent:preflight:docs`).
