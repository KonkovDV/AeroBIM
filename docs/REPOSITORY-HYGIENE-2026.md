---
title: "Repository Hygiene 2026"
status: active
version: "1.0.0"
last_updated: "2026-05-21"
tags: [aerobim, hygiene, FAIR, governance, open-source]
---

# Repository hygiene (academic + industry, May 2026)

SSOT for **what belongs in the public GitHub repo** vs local-only vs CI-generated artifacts. Aligns with [FAIR Software](https://fairsoftwarechecklist.net/v0.2/), [Diataxis](https://diataxis.fr/) (tutorial/how-to/reference/explanation), and reproducible research software practice ([Scientific Data CODE beyond FAIR](https://www.nature.com/articles/s41597-026-01473-2), 2026).

## Principles

| Principle | AeroBIM rule |
|-----------|--------------|
| **Reproducibility** | Source + pinned fixtures + dated evidence in `docs/evidence/`; frozen tag `pilot-2026-pre` for metrics |
| **Minimal public surface** | No runtime `var/`, no NDA customer packs, no local CI dump with machine paths |
| **Separation of concerns** | Code in `backend/` + `frontend/`; norms in `samples/`; proof in `docs/evidence/`; navigation in `docs/README.md` |
| **No duplicate authority** | One SSOT per topic; mirrors link to canonical file |
| **Honest claims** | [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) lists verified vs planned |

## Repository layout (what to keep)

```text
AeroBIM/
├── backend/          # Application + tools + tests (canonical code)
├── frontend/         # Review shell
├── samples/          # Public fixtures only (IFC, IDS, rules, benchmark packs)
├── docs/
│   ├── README.md           # Documentation router (start here)
│   ├── REPRODUCIBILITY-2026.md
│   ├── REPOSITORY_HYGIENE-2026.md   # this file
│   ├── evidence/           # Dated, citeable verification snapshots
│   ├── partners/           # External-program text (TechLab application)
│   └── pilot-*.md, samolet-*.md   # Active operational SSOT
├── .github/workflows/  # CI truth (regenerate artifacts, do not rely on stale JSON in repo)
├── CITATION.cff
└── README.md
```

## Do not commit (`.gitignore`)

| Path | Reason |
|------|--------|
| `backend/var/` | Runtime reports, IFC copies from analysis |
| `artifacts/` | CI/local benchmark dumps (ephemeral; use Actions artifacts) |
| `docs/evidence/internal/` | NDA customer SLA, CDE screenshots |
| `project-package-samolet-pilot-v1.json` | Customer manifest (local only) |
| `.venv*`, `__pycache__`, `.pytest_cache` | Environment |
| `.env` | Secrets |

Operator layout for gitignored files: [`LOCAL_OPERATOR_ARTIFACTS.md`](LOCAL_OPERATOR_ARTIFACTS.md).

## `docs/evidence/` policy

**Commit:** dated files referenced by REPRODUCIBILITY, pre-pilot gates, pre-push verification, benchmark/ablation snapshots.

**Do not commit:** customer-specific SLA JSON, internal CDE proofs, scratch JSON from one-off runs.

Naming: `artifact-type-YYYY-MM-DD.{md,json}` (keep prior dates when refreshing — history for reviewers).

## Documentation tiers (Diataxis)

| Tier | Examples | Audience |
|------|----------|----------|
| **SSOT** | `REPRODUCIBILITY`, `06-architecture-reference`, `pilot-claim-boundary`, `samolet-techlab-alignment` | Reviewers, integrators |
| **How-to** | `15-local-quality-gate`, `pilot-execution-runbook`, `contributor-git` | Contributors |
| **Reference** | `ifc-compatibility-matrix`, `annotation-protocol`, `samples/benchmarks/README` | Implementers |
| **Explanation** | `01-strategy-and-plan`, `03-openbim-landscape` | Stakeholders |
| **Archive** | `02-microphoenix-extraction`, `08-microphoenix-adoption-matrix`, `10-academic-audit` (superseded by PROJECT-AUDIT) | History only — not first read |

## CI vs repo artifacts

GitHub Actions generates `artifacts/ci-benchmark-smoke/` per run. **Do not track** under git — avoids stale paths (e.g. old `C:\plans\samolet\` entries) and repo bloat. Download from Actions tab or regenerate locally per [`15-local-quality-gate.md`](15-local-quality-gate.md).

## openBIM / AEC alignment (May 2026)

| Practice | Repo embodiment |
|----------|-----------------|
| IDS 1.0 as contract | `samples/ids/`, IfcTester in CI |
| BCF 2.1 handoff | Export code + `pilot-cde-handoff` |
| ISO 19650-lite | Optional report fields (not full CDE product) |
| Research benchmark | RU ground truth + extraction gate |

## Maintenance checklist (each release)

1. `pytest -q`, `evaluate_extraction`, `measure_package_sla` on pilot pack.
2. Update evidence only when metrics change; add new dated file, do not silently overwrite history.
3. Refresh `docs/README.md` if new SSOT added.
4. No customer data in `git add -A` — use [`contributor-git-2026.md`](contributor-git-2026.md).
5. Do not move tag `pilot-2026-pre` without material-change protocol.

## Related

- [`evidence/README.md`](evidence/README.md) — evidence folder index
- [`../artifacts/README.md`](../artifacts/README.md) — why `artifacts/` is not in git
- [`PROJECT-AUDIT-2026-05-20.md`](PROJECT-AUDIT-2026-05-20.md) — hygiene findings log
