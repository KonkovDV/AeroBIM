<!-- claims-lint: allow-file reason="Red Team hygiene for IFC release benchmark evidence; no product GO" -->
---
title: "Red Team — IFC release benchmark hygiene 2026-08-12"
date: "2026-08-12"
claim_boundary: "Evidence hygiene only. fixture_only. Not customer accuracy. Not Checkpoint GO."
---

# Red Team: IFC release benchmark local dirt → clean tip

## Scope

Clear leftover working-tree drift called out after KT#2 max-eng:

| Path | Action |
| --- | --- |
| `audit/evidence/ifc-release-benchmark-2026-08.json` | Commit refreshed suite (2026-08-10 run) after path normalization |
| `docs/evidence/ifc-release-benchmark-2026-08.md` | Commit matching table / generated_at |
| `docs/audit/_window_files_2026-08-11.txt` | **Delete** (ephemeral per-commit file inventory; not evidence) |

## Reproduction

```text
python -c "…normalize pack_path/storage_dir to repo-relative…"
python scripts/lint_claims.py --matrix-guard
git status -sb   # expect only intentional staged files before commit
```

## Results

| Check | Result | Status |
| --- | --- | --- |
| `claim_level` | `fixture_only` | VERIFIED |
| `customer_accuracy_not_established` | `true` | VERIFIED |
| IFC SHA256 per pack | unchanged vs prior tip | VERIFIED |
| issue_count / requirement_count | IFC2X3 6/3; IFC4 4/3; IFC4X3 4/3 | VERIFIED |
| Timing table | p50/p95/max refreshed (machine noise; not accuracy) | VERIFIED |
| Absolute `C:\plans\…` in JSON path fields | removed → repo-relative | VERIFIED mitigated |
| `_window_files_*.txt` | deleted, not committed | VERIFIED |
| `matrix-guard` | OK | VERIFIED |
| Checkpoint | unchanged (out of scope) | N/A |

## Findings

### RT-BENCH-HYG-01 — Absolute Windows paths in re-run JSON
- **Severity:** P2 hygiene / portability  
- **Status:** FIXED before commit  
- **Detail:** Re-run wrote `pack_path` / `storage_dir` as absolute `C:\plans\AeroBIM\…`. Normalized to prior relative form (`samples/benchmarks/…`, `backend/var/reports`).

### RT-BENCH-HYG-02 — Scratch `_window_files` must not enter history
- **Severity:** P2 hygiene  
- **Status:** FIXED  
- **Detail:** Untracked session inventory deleted; not staged.

### RT-BENCH-HYG-03 — Timing drift is not accuracy
- **Severity:** informational  
- **Status:** ACCEPTED  
- **Detail:** Faster p50/p95 vs 2026-08-08 tip is OS noise on identical fixture SHA256; claims stay fixture_only.

## P0 defects

**None.**

## Verdict

Working tree dirt closed correctly: refreshed fixture benchmark evidence + scratch deleted. **No Checkpoint / customer accuracy claim.**
