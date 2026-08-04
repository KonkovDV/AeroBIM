---
title: "Release policy — AeroBIM"
status: active
version: "1.0.0"
last_updated: "2026-08-05"
---

# Release policy (операционные имена и алиасы)

## Deprecated env aliases

| Alias | Canonical | Boot behavior | Remove after |
|---|---|---|---|
| `AEROBIM_LLM_LOCAL_ENABLED` | `AEROBIM_LLM_ADVISORY_ENABLED` | WARNING in `Settings.from_env` | **КТ#3 ends 2026-09-21** — delete alias code + docs after that date |

Do not add new docs/scripts that set only `LOCAL`. Prefer `ADVISORY`. Unpinned `/latest` model URIs remain forbidden.

## Checkpoint windows (TechLab Task 07)

| Gate | Window |
|---|---|
| КТ#2 | 04.08–20.08.2026 |
| КТ#3 | 03.09–21.09.2026 |
