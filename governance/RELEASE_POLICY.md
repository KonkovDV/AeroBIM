# Release Policy

## Scope

This policy defines release-readiness expectations for AeroBIM.

## Versioning

- Use SemVer tags: vMAJOR.MINOR.PATCH
- MAJOR for breaking API/report contract changes
- MINOR for backward-compatible feature additions
- PATCH for fixes and non-breaking hardening

## Pre-Release Baseline

Before release:

1. local quality gate passes (`ruff format --check`, `ruff check`, `mypy`, `pytest`);
2. release-readiness workflow passes for selected profile;
3. OpenAPI contract export and required path checks pass;
4. docs and README claim boundaries reflect actual delivered behavior;
5. no unresolved critical security findings.

## Evidence in Release Notes

Include:

- commit range and notable behavior changes;
- validation commands and workflow outcomes;
- contract/schema impact and migration notes;
- explicit known limitations.

## Publication Guardrails

- never publish secrets or sensitive project fixtures;
- keep benchmark claims traceable to named artifacts;
- keep roadmap items separate from delivered claims.
