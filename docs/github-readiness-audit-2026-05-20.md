---
title: "GitHub Readiness Audit 2026-05-20"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
tags: [aerobim, audit, github, evidence]
---

# GitHub Readiness Audit (2026-05-20)

Fact-check of public claims against runnable evidence. Environment: Windows, Python 3.13, `backend/.venv-pilot`.

## Verification summary

| Check | Command | Result |
|---|---|---|
| Backend tests | `pytest tests -q` | **294 passed**, 2 skipped |
| Extraction gate | `evaluate_extraction --min-macro-f1 0.70` | **PASS** (macro F1 = 0.86) |
| Runtime baseline | `export_runtime_baseline` | **APPROVED** (4/4 commands) |
| Pilot replay | `test_pilot_deterministic_replay.py` | PASS (included in suite) |
| Conflict breakdown | `summarize_conflict_breakdown` (pilot pack) | 8 issues, 0 cross-doc on fixture pack |

## Metrics fact-check

| Claim (docs) | Measured | Match |
|---|---|---|
| 10 RU fixtures / 50 requirements | `russian-aec-ground-truth.json` | yes |
| Macro F1 ≈ 0.86 | 0.860 | yes |
| Architecture discipline F1 ≈ 0.73 | 0.733 | yes |
| CI gate F1 ≥ 0.70 | enforced in `ci.yml` + release workflow | yes |
| 290+ tests | 294 passed | yes (README says 290+) |

## Pilot H2 deliverables (plan waves 0–4)

| Wave | Status | Evidence |
|---|---|---|
| 0 SSOT + commit | done | `docs/13-academic-execution-plan-2026.md`, commit `3c67edb` |
| 1 Pre-pilot gates | docs + tools | `pilot-pre-pilot-gates-2026.md`, `summarize_conflict_breakdown.py` |
| 2 Spatial review | implemented | `DrawingEvidencePanel`, `run_live_review_smoke`, smoke-path §8–10 |
| 3 Pilot ops | templates | `pilot-execution-runbook-2026.md`, `pilot-weekly-log-2026.md` |
| 4 Post-pilot | template | `post-pilot-go-no-go-memo-2026.md` |

## Known limitations (do not overclaim)

- Pilot Moscow pack: **0 cross-document** issues on current fixtures (contradictions may appear on customer data).
- Optional extras `clash` / `docling`: not installed in audit venv (`optional_adapter_status: false`).
- `gh repo edit` requires GitHub CLI on maintainer machine (see `.github/repository-metadata.md`).

## Pre-push checklist

1. [x] Tests green locally
2. [x] Extraction gate green
3. [x] No `Co-authored-by` trailers on HEAD commit
4. [x] `git push origin main` (force-with-lease после rewrite авторов, HEAD `737a7d7`)
5. [ ] Optional: `gh repo edit` for About + topics
6. [x] Pre-pilot gates 1–4 signed off 2026-05-21 ([`pilot-pre-pilot-gates-2026.md`](pilot-pre-pilot-gates-2026.md))
7. [ ] Tag `pilot-2026-pre` pushed ([`pilot-frozen-tag-protocol-2026.md`](pilot-frozen-tag-protocol-2026.md))

## Maintainer push

```powershell
cd AeroBIM
git push origin main
```

Single-author commits: [`scripts/git_commit.ps1`](../scripts/git_commit.ps1), [`docs/contributor-git-2026.md`](contributor-git-2026.md). Full audit: [`PROJECT-AUDIT-2026-05-20.md`](PROJECT-AUDIT-2026-05-20.md).
