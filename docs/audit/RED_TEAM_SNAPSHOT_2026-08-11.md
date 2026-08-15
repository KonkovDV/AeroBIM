<!-- claims-lint: allow-file reason="Red Team Stage A factual snapshot; no product accuracy claims" -->
---
title: "AeroBIM Red Team Snapshot — Stage A"
date: "2026-08-11"
head_sha: "a818bfe2eeeaa2cf2b5c98cdd331887e519aacf7"
stage: "A"
claim_boundary: "Inventory only. Not a GO/NO_GO product verdict. Not customer accuracy."
---

# RED TEAM SNAPSHOT — 2026-08-11 (Stage A)

**Rule:** this file is a factual inventory of the checked-out tree. It is **not** remediation and **not** proof that older Red Team reports still hold.

## 0. Capture metadata

| Field | Value |
| --- | --- |
| Capture time (local) | 2026-08-11 (~10:05–10:30 MSK) |
| Working directory | this repository |
| Remote | `https://github.com/KonkovDV/AeroBIM` (fetch/push) |
| Branch | `main` tracking `origin/main` |
| HEAD | `a818bfe2eeeaa2cf2b5c98cdd331887e519aacf7` |
| HEAD short | `a818bfe` |
| HEAD subject | `feat(tz): fixture clash measure + drawing overlay evidence` |
| HEAD author | KonkovDV `<KonkovDV@users.noreply.github.com>` |
| HEAD committer date | `2026-08-11T10:02:03+03:00` |
| HEAD signature | **Good** (`G`) — RSA `24D8BC0C78AAABA6` / KonkovDV |
| Parent | `7c75155bb79e6b52ac7cda4a0847166dd5bed1b4` |

## 1. Working tree

```text
 M audit/evidence/ifc-release-benchmark-2026-08.json
 M docs/evidence/ifc-release-benchmark-2026-08.md
```

- Tree is **dirty** (2 modified evidence files; not staged).
- `main...origin/main` was **in sync** at capture after `a818bfe` push (dirty files are local-only drift).

## 2. Branches and tags

| Kind | Names |
| --- | --- |
| Local | `main` (HEAD), `ci/signing-enforce-dryrun` @ `2e8fedb` |
| Remote | `origin/main`, `origin/ci/signing-enforce-dryrun`, `origin/HEAD → main` |
| Tags | `pilot-2026-pre` |
| Submodules | **none** (`.gitmodules` absent; no `.git/modules`) |
| Git LFS | Client present (`git-lfs/3.7.1`); LFS endpoint configured; **no tracked LFS file listing required for Stage A beyond env** |

## 3. History volume

| Metric | Value |
| --- | --- |
| Commits reachable from HEAD | **579** |
| Authors (all history, `git shortlog -sn --all`) | KonkovDV **670**; Konkov Dmitrij **3** (note: shortlog counts commits per author across refs; local + remote) |
| Window `2026-08-03 00:00` … `2026-08-12 00:00` (`--all`) | **158** commits |
| Window first-parent on `main` | **134** commits |
| Window unique paths touched (`--all`) | **641** files |
| Window first-parent churn (approx.) | ~**103 139** insertions / ~**14 886** deletions across ~133 shortstat rows |
| Signatures in window (`%G?`, `--all`) | **Good=20**, **None=134**, total counted **154** (see note) |
| Signatures all HEAD history | **Good=20**, **None=559**, total **579** |

**Note:** A4 signing enforcement was activated on **2026-08-11** (`7c75155`). Most August history before that date is unsigned (`N`). Recent tip commits on `main` are signed (`G`).

Supporting lists (generated 11.08.2026, not claims):

- `docs/audit/_window_commits_2026-08-11.tsv`
- `docs/audit/_window_unique_files_2026-08-11.txt`
- `docs/audit/_fp_commits_2026-08-11.txt`

## 4. Repository size

| Path | Approx. size |
| --- | --- |
| Working tree (all files) | **~3399.45 MiB** |
| `.git` | **~15.26 MiB** |

Largest tracked blobs observed (by object size; PDF evidence dominates):

| Size (bytes) | Path (representative) |
| --- | --- |
| ~1 090 007 | `docs/evidence/tracker-baseline-2026-08-07.pdf` |
| ~1 089 013 | `docs/evidence/baseline-2026-08.pdf` |
| ~430 890 | `samples/DATASET_MANIFEST.json` |
| ~416 736 | `audit/evidence/sprint3-open-corpus-battery-2026-08.json` |

## 5. Toolchain on capture host

| Tool | Version |
| --- | --- |
| Python | **3.13.7** (host) |
| Node | **v24.11.0** |
| npm | **11.6.1** |
| Docker | **29.5.2** |
| Git | **2.55.0.windows.3** |
| Declared backend target | Python **3.12+** (Dockerfile base `python:3.12-slim` digest-pinned) |
| Published runtime baseline Python | **3.12.13** (Linux CI; see §8) |

**ТРЕБУЕТСЯ ПРОВЕРКА:** full pytest/mypy/ruff green matrix on clean Linux 3.12 checkout was **not** re-run in Stage A.

## 6. Layout inventory

### 6.1 CI workflows (`.github/workflows/`)

- `academic-benchmark-release.yml`
- `ci.yml`
- `codeql.yml`
- `release-readiness.yml`

### 6.2 Docker / compose

| Artifact | Present |
| --- | --- |
| `backend/Dockerfile` | yes (multi-stage; digest-pinned base) |
| `artifacts/offline-bundle/Dockerfile` | yes |
| `docker-compose.yml` | yes (`context: ./backend`) |
| `docker-compose.production.yml` | yes |
| Root `.dockerignore` | **no** |
| `backend/.dockerignore` | **yes** (compose context) |

### 6.3 Dependency manifests / locks

| Artifact | Present |
| --- | --- |
| `backend/pyproject.toml` | yes |
| `backend/requirements-lock.txt` | yes (~120 KB) |
| `frontend/package.json` | yes |
| `frontend/package-lock.json` | yes |
| Root `package.json` / `uv.lock` / `poetry.lock` | no |

**Optional extras** (`backend/pyproject.toml`): `dev`, `raster`, `clash`, `docling`, `cad`, `vision`, `pdf-agpl`, `enterprise`.

### 6.4 Repo hygiene markers

| File | Present |
| --- | --- |
| `.gitignore` | yes |
| `.gitattributes` | yes |
| `.gitmodules` | no |
| Root `.dockerignore` | no |

## 7. Test surface (inventory, not execution proof)

| Surface | Count / note |
| --- | --- |
| Backend `tests/test_*.py` files | **270** |
| Frontend `*.test.*` / `*.spec.*` files | **15** |
| Frontend scripts | `test` → vitest; `build` → tsc + vite |
| Architecture import AST gate file | **`backend/tests/test_architecture_import_gate.py` absent** |
| Existing architecture-related tests | `test_architecture_seams.py`, `test_tz_architecture_ports.py` (capability/precision honesty — **not** full layer-import scanner) |

## 8. Published runtime baseline (in-tree artifact)

Source: `docs/evidence/runtime-baseline-latest.json`

| Field | Value |
| --- | --- |
| `commit_sha` | `3489cad44697c4378eebca8bc5552c7a853f2749` |
| `generated_at` | `2026-08-09T09:17:59Z` |
| Backend tests_collected / passed | 2012 / 2163 |
| Frontend tests_passed | 48 |
| Python in baseline env | 3.12.13 |
| Claim boundary in artifact | Engineering build evidence; fixture macro_f1 ≠ product accuracy; checkpoint NO_GO until RT-001/002/003 |

**Lag:** baseline SHA is **behind** Stage A HEAD `a818bfe`. Control `N43-baseline-one-commit-lag` remains **deferred** until **2026-08-17** (`governance/deferred_controls_registry.json`).

## 9. Governance / signing (current policy files)

| Control | State (file read 2026-08-11) |
| --- | --- |
| `A4-signing-enforcement` | **active** (`enforce_ci` + `fail_on_unverifiable_signature`) |
| `N43-baseline-one-commit-lag` | deferred → activate **2026-08-17** |
| `N47-ruf100` | deferred → **2026-08-25** |
| `N49-hitl-role-profile-boundary` | active |
| `N59-trusted-keys-already-trusted-signer` | deferred → **2026-08-25** |
| `governance/commit_signing_policy.json` | `enforce_ci=true`, `fail_on_unverifiable_signature=true`, `min_signed_ratio=0.03` |

## 10. Stage A scope boundary

Completed in this phase:

1. Factual HEAD / tree / history / toolchain inventory (**this file**).
2. Diff-window audit → `docs/audit/RED_TEAM_DIFF_AUDIT_2026-08-11.md`.

**Not done in Stage A (blocked until owner confirms Stage B):**

- Full-repo remediation
- Mutation audit battery
- SBOM / license / reproducibility report generation as closure claims
- Full Stage C clean-checkout gate matrix
- Closing RT-001/002/003 without customer evidence

## 11. Immediate VERIFIED observations (preview; details in diff audit)

These were reproduced against HEAD `a818bfe` during Stage A spot checks — **not** a complete Phase 2–20 audit:

| ID | Severity | Status | One-line |
| --- | --- | --- | --- |
| RT-20260811-01 | P1 | VERIFIED | `VlmAdvisoryClient._request_headers` lets `extra_headers` override `Authorization` / security headers |
| RT-20260811-02 | P1 | VERIFIED | `endpoint_looks_like_yandex` uses substring `"yandex" in host` (`not-yandex.evil` → True) |
| RT-20260811-03 | P2 | VERIFIED | No dedicated tests for `vlm_endpoint_gate.py` |
| RT-20260811-04 | P2 | VERIFIED | No automated domain→infrastructure import architecture gate |
| RT-20260811-05 | P3 | VERIFIED | Dirty local IFC release-benchmark evidence vs HEAD |
| RT-OIDC-BFF | — | ACCEPTED_RISK / OWNER | `/v1/auth/*` still **501** stubs (PKCE Phase 2.5 designed, not production BFF) |
| RT-BASELINE-LAG | — | ACCEPTED_RISK | Runtime baseline pinned to `3489cad`; N43 deferred to 17.08 |

---

*End of Stage A snapshot. Do not treat as full-repo GO.*
