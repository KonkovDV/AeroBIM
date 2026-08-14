<!-- claims-lint: allow-file reason="Live vertical-slice CLI pin; forbidden phrases as non-claims; NO_GO" -->
---
title: "Vertical slice live CLI pin 2026-08-14"
date: "2026-08-14"
claim_boundary: "Fixture demo hashes. Checkpoint NO_GO. Not customer accuracy. Not CV. Not CDE-ready."
---

# Vertical slice live CLI (14.08.2026)

Command (from `backend/`, venv with `.[dev,raster,pdf-agpl]`):

```powershell
python -m aerobim.tools.run_demo_vertical_slice
```

Exit **0**. stderr: `VERDICT: NOT PASS` · `summary.passed=false` · `outcome=failed` · `checkpoint=NO_GO`.

Binaries stay in gitignored `artifacts/vertical-slice-demo/`. Do not treat this pin as customer GO. BCF ZIP is a structural export; CDE import was not verified.

| Artifact | sha256 (run 1 = run 2 unless noted) |
| --- | --- |
| overlay-problem-zone.png | `9826281f83a1a5608a3bd88e7d4f4f52475a702c5f3c3a5b4100d05f05f6a349` |
| run-manifest.json | `0ff1f6d085c8306edd85469f967be87051617da622955e3724f948983edd8c56` |
| LIMITATIONS.json | `78877c146bb9525b866e9c18f3605fa819615b8f8bc49628a596ffc5f20e1965` |
| reproducibility_hash | `f67038c00578fae123f4ecfcbe05cc536382cb445a9f0364513590d92225fa6d` |
| report.json / report.html / findings.bcfzip | drift via `created_at` |

Input PDF sha256: `6aa1789a027f3a60be21bc68c26bb17440d4c54e827859c6268b590710125fcf`.  
HEAD at run: `d809d3677492c988d35024e9e06664ae7f949b89` (`working_tree_dirty=false`).  
`reproducibility_hash` / `run-manifest.json` changed vs the dirty-tree pin because `code_version` binds the git SHA. Overlay PNG and LIMITATIONS.json did not. A later docs-only pin commit does not change those two.
VLM: Qwen LIVE on fixture (prior 13.08 artifact); Kimi GATED; `comparison_not_run`.

## Local gates measured 14.08 (after solvable-blocker pass)

| Gate | Result |
| --- | --- |
| BCF 2.1 XSD on `artifacts/vertical-slice-demo/findings.bcfzip` | `xsd_status=passed` · VersionId `2.1` · 7 topics. ZIP sha256 drifts with `created_at`. Structural only. **Not** CDE import. |
| Frontend vitest | **54 passed** / 7 files (vitest 4.1.4) |
| Full `pytest tests -q` | **2151 passed**, 11 skipped, 0 failed (Python 3.13.7) |
| `mypy src/aerobim --strict --ignore-missing-imports` | 0 errors / 335 files |
| `ruff check src tests` + `ruff format --check` | PASS |
| `lint_claims.py` / `--full-docs` / `--matrix-guard` / `--claim-boundary-guard` | OK |
| `verify_evidence_bundle` wall-guid | passed (10 hashes). Do not edit hashed `wall-guid/README.md`. |
| Python 3.12 | **not installed locally** (`py -3.12` → no runtime). Hashes remain 3.13.7 only. |
