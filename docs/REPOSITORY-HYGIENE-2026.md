---
title: "Repository Hygiene 2026"
status: active
version: "1.1.0"
last_updated: "2026-07-19"
tags: [aerobim, hygiene, FAIR, governance, open-source]
---

# Repository hygiene (academic + industry)

SSOT for **what belongs on public GitHub** vs local-only vs CI-generated artifacts. Aligns with [FAIR Software](https://fairsoftwarechecklist.net/v0.2/), [Diataxis](https://diataxis.fr/), and reproducible research software practice.

## Principles

| Principle | AeroBIM rule |
|-----------|--------------|
| **Reproducibility** | Source + pinned fixtures + dated evidence in `docs/evidence/`; frozen tag `pilot-2026-pre` for metrics |
| **Minimal public surface** | Samolet TZ pack + claims/blockers + architecture SSOT + jury/strategy memos. **No** Red Team phase deltas, AI prompts, or deep-audit scratch |
| **Separation of concerns** | Code in `backend/` + `frontend/`; norms in `samples/`; proof in `docs/evidence/`; navigation in `docs/README.md` |
| **No duplicate authority** | One SSOT per topic; mirrors link to canonical file |
| **Honest claims** | [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) lists verified vs planned · checkpoint **NO_GO** |

## Public layout (keep)

```text
AeroBIM/
├── backend/ · frontend/     # Product code
├── samples/                 # Public fixtures only
├── docs/
│   ├── README.md · TIER0_INDEX.md
│   ├── docs.md · samolet.md # Jury + strategy (public)
│   ├── tz/ · architecture/ · partners/ · evidence/
│   └── archive/             # Historical snapshots only
├── audit/
│   ├── reports/             # CRITICAL_BLOCKERS, CLAIMS_*, TZ_RUNTIME only
│   └── evidence/            # Citeable JSON/MD snapshots (not *.txt dumps)
├── ops/ · .github/workflows/
├── CITATION.cff · README.md · README.ru.md
└── …
```

## Do not commit (`.gitignore`)

| Path | Reason |
|------|--------|
| `backend/var/` | Runtime reports, IFC copies |
| `artifacts/` | CI/local benchmark dumps |
| `docs/evidence/internal/` | NDA customer SLA, CDE screenshots |
| `docs/prompts/` | Operator AI session prompts |
| `.local/` | Prompts, engineering wave logs, moved Red Team reports |
| `audit/reports/RED_TEAM_*.md` (and related globs) | Phase deltas — local only |
| `audit/evidence/*.txt` | Scratch dumps |
| `samples/customer/**` | Customer packs (README only in git) |
| `.venv*`, `__pycache__`, `.env` | Environment / secrets |
| `.cursor/` | IDE agent state |

Operator layout: [`LOCAL_OPERATOR_ARTIFACTS.md`](LOCAL_OPERATOR_ARTIFACTS.md).

## `docs/evidence/` policy

**Commit:** dated files referenced by REPRODUCIBILITY, gates, claim matrices.

**Do not commit:** customer-specific SLA JSON, internal CDE proofs, one-off scratch.

Naming: `artifact-type-YYYY-MM-DD.{md,json}`.

## Documentation tiers (Diataxis)

| Tier | Examples | Audience |
|------|----------|----------|
| **SSOT** | `docs.md`, `samolet.md`, TZ pack, Claims Lock, CRITICAL_BLOCKERS, TARGET architecture, claim-boundary | Reviewers, jury |
| **How-to** | `15-local-quality-gate`, pilot runbooks, `contributor-git` | Contributors |
| **Reference** | IFC matrix, `audit/reports/*`, benchmarks README | Implementers |
| **Archive** | [`archive/`](archive/) — MicroPhoenix `01`–`11` | History only |

## Maintenance checklist

1. Keep public router (`docs/README.md` · `TIER0_INDEX.md` · root README) aligned when adding SSOT.
2. Never `git add` Red Team phase reports, prompts, or customer corpus.
3. Do not move tag `pilot-2026-pre` without material-change protocol.
4. One language per file — [`LANGUAGE-POLICY-2026.md`](LANGUAGE-POLICY-2026.md).

## Related

- [`evidence/README.md`](evidence/README.md)
- [`../artifacts/README.md`](../artifacts/README.md)
- [`../audit/reports/README.md`](../audit/reports/README.md)
