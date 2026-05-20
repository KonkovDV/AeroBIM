---
title: "Pilot Weekly Log 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, kpi]
---

# Pilot Weekly Log (template)

Copy one section per pilot week. Keep customer identifiers out of the repo.

## Week 0 — Pre-pilot baseline (2026-05-21)

| Field | Value |
|---|---|
| Package revision | `project-package-pilot-moscow-v1` (fixture) |
| Git tag / image digest | `pilot-2026-pre` (pending push) |
| Engineer reviewer | maintainer verification |

### Pre-pilot gates

All gates 1–4 **pass** — see [`pilot-pre-pilot-gates-2026.md`](pilot-pre-pilot-gates-2026.md), [`evidence/pre-pilot-gates-evidence-2026-05-21.md`](evidence/pre-pilot-gates-evidence-2026-05-21.md).

### ConflictKind snapshot (fixture pack)

| Kind | Count |
|---|---:|
| *(none — 0 cross-document issues on pilot fixtures)* | 0 |

Optional extras smoke: not required for week 0; record `.[clash]` / `.[docling]` install or skip in later weeks per [`optional-adapters-smoke-2026.md`](optional-adapters-smoke-2026.md).

### Actions week 1

- [ ] Customer CDE BCF import + tool/version in case study
- [ ] First production package ingest
- [ ] Start TP/FP adjudication table

---

## Week N — YYYY-MM-DD

| Field | Value |
|---|---|
| Package revision | e.g. `pilot-moscow-v1-r2` |
| Git tag / image digest | e.g. `pilot-2026-w03` |
| Engineer reviewer | role only (no PII) |

### Runs

| Run | Ingest time | First cross-doc issue | Total issues | BCF exported |
|---|---|---|---|---:|
| 1 | | | | yes/no |
| 2 | | | | yes/no |

### Adjudication (TP / FP)

| Discipline | TP | FP | Notes |
|---|---:|---:|---|
| Fire | | | |
| Structure | | | |

### ConflictKind snapshot

```bash
cd backend
python -m aerobim.tools.summarize_conflict_breakdown --pack samples/benchmarks/project-package-pilot-moscow-v1.json
```

Record `conflict_kind_breakdown` here:

| Kind | Count |
|---|---:|
| unit-mismatch | |
| hard-conflict | |
| ambiguous-mapping | |

### Qualitative (1–5)

| Question | Score | Comment |
|---|---:|---|
| BCF usable in CDE? | | |
| False-positive burden | | |
| 2D overlay helped locate issue? | | |

### Actions next week

- [ ] …
