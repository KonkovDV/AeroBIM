---
title: "Local Quality Gate"
status: active
version: "0.1.0"
last_updated: "2026-04-25"
tags: [aerobim, ci, quality, ruff, mypy, pytest]
---

# Local Quality Gate

## Purpose

This document defines the minimum local validation commands that should pass before opening a pull request or pushing directly to `main`.

The goal is CI parity for formatting, linting, typing, and tests.

## Baseline Commands

Run from `AeroBIM/backend`:

```bash
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
```

## Formatter Recovery

If formatting check fails with `Would reformat ...`, apply formatting and re-run the check:

```bash
python -m ruff format src tests
python -m ruff format --check src tests
```

## Scope And Interpretation

- `ruff format --check`: style and canonical formatting.
- `ruff check`: static lint rules.
- `mypy src`: typing discipline for backend source.
- `pytest tests -q`: runtime regression safety.

These checks are intentionally simple and deterministic for local developer loops.

## Current Known Non-Blocking Warnings

As of 2026-04-25, repository-wide `ruff check` no longer reports the earlier `UP038` advisories in this repo slice.

The current baseline command set in this document now passes cleanly for local CI parity.
