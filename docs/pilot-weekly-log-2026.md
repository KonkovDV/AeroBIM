---
title: "Pilot Weekly Log 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, pilot, kpi]
---

# Pilot Weekly Log (template)

Copy one section per pilot week. Keep customer identifiers out of the repo.

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
