---
title: "AeroBIM Repository Audit 2026-05-20"
status: active
version: "1.1.0"
last_updated: "2026-05-21"
tags: [aerobim, audit, fact-check, hygiene]
---

# AeroBIM repository audit (2026-05-20, refreshed 2026-05-21)

Method: repository inspection, `pytest` / `ruff` / `mypy`, `evaluate_extraction`, README and pilot-doc cross-check against code, language-policy sweep ([`LANGUAGE-POLICY-2026.md`](LANGUAGE-POLICY-2026.md)).

## Verified runtime state

| Check | Result |
|---|---|
| `pytest tests -q` | **292 passed**, 2 skipped |
| `ruff check src tests` | pass |
| `mypy src/aerobim --ignore-missing-imports` | 63 files, pass |
| `evaluate_extraction --min-macro-f1 0.70` | **PASS**, macro F1 = **0.86** |
| `Co-authored-by` in last 30 commits on `main` | none |
| Unique author on `main` | `KonkovDV` only |

## Confirmed capabilities

- Deterministic IFC + IDS + cross-document + narrative (regex) kernel.
- 2D overlay and drawing evidence in UI (`DrawingEvidencePanel`, live smoke).
- BCF 2.1/3.0, OpenRebar digest, `ConflictKind`, ISO 19650-lite fields.
- CI: lint, typecheck, tests, benchmark-smoke, extraction-quality, openapi-contract.

## Hygiene fixes (May 2026)

| ID | Issue | Action |
|---|---|---|
| H-01 | `backend/llm/` fine-tune scaffold outside pilot sign-off | Removed |
| H-02 | `reports/aerobim_ft_scaffold_gate_report_v1.json` with foreign paths | Removed |
| H-03 | `docs/superpowers/` internal donor control-plane specs | Removed |
| H-04 | IDE-branded git hygiene doc | Replaced by [`contributor-git-2026.md`](contributor-git-2026.md) |
| H-05 | `docs/05-fact-check-audit.md` pointing at `c:\plans\samolet` | Corrected to AeroBIM repo |
| H-06 | Vendor model names in public docs | Replaced with deterministic / non-deterministic wording |
| H-07 | `VlmDrawingAnalyzer` naming (legacy VLM label) | Renamed to `RasterDrawingAnalyzer` |
| H-08 | Tracked `artifacts/ci-benchmark-smoke/` with stale machine paths | Untracked; CI-only per [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md) |

## Open pilot gaps (non-blocking for CI)

| ID | Gap | Status |
|---|---|---|
| G-01 | Sign-off tables in `pilot-pre-pilot-gates-2026.md` | **Closed** 2026-05-21 |
| G-02 | Tag `pilot-2026-pre` | **Closed** at `1a5c03e` |
| G-03 | Academic audit v0.6 vs shipped overlay | **Closed** |
| G-04 | Dependabot triage | Policy in [`evidence/ops-hygiene-2026-05-21.md`](evidence/ops-hygiene-2026-05-21.md) |
| G-05 | GitHub About / topics | Manual; see ops-hygiene |
| G-06 | OIDC, arq/Redis, full Postgres hydration | Post-pilot |
| G-07 | Zero cross-doc on fixture pilot pack | Informational — do not overclaim on production data |
| G-08 | `.[clash]` / `.[docling]` opt-in | **Closed** — [`optional-adapters-smoke-2026.md`](optional-adapters-smoke-2026.md) |
| G-09 | FAIR/CODE reproducibility SSOT | **Closed** — [`REPRODUCIBILITY-2026.md`](REPRODUCIBILITY-2026.md) |

## Documentation vs code

| Claim | Fact |
|---|---|
| Macro F1 ≈ 0.86 | Confirmed via `evaluate_extraction` |
| 290+ tests | 292 passed |
| 2D overlay “planned” in older audit §5.1 | Shipped May 2026 |
| Fine-tuning in production sign-off | **No** |
| Learned vision in sign-off | **No** — OCR/layout baseline via `RasterDrawingAnalyzer` |

## Maintainer actions (2026-05-21)

1. Pre-pilot gates and tag `pilot-2026-pre` — done.
2. Before each push: [`evidence/pre-push-verification-2026-05-21.md`](evidence/pre-push-verification-2026-05-21.md).
3. Pilot weeks: [`pilot-start-package-2026.md`](pilot-start-package-2026.md), [`pilot-weekly-log-2026.md`](pilot-weekly-log-2026.md).
4. Post-pilot: [`post-pilot-go-no-go-memo-2026.md`](post-pilot-go-no-go-memo-2026.md).

## Reproduction commands

```powershell
cd AeroBIM\backend
.\.venv-pilot\Scripts\python.exe -m pytest tests -q
.\.venv-pilot\Scripts\python.exe -m ruff check src tests
.\.venv-pilot\Scripts\python.exe -m mypy src/aerobim --ignore-missing-imports
.\.venv-pilot\Scripts\python.exe -m aerobim.tools.evaluate_extraction --min-macro-f1 0.70
```
