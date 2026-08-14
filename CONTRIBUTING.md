# Contributing to AeroBIM

Thank you for improving AeroBIM.

AeroBIM is an open-source platform for cross-modal BIM validation. Contributions should preserve deterministic behavior, explicit provenance, and clean architecture boundaries.

## Read First

1. README.md
2. docs/TIER0_INDEX.md · docs/README.md
3. docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md
4. docs/pilot-claim-boundary-2026.md
5. SECURITY.md · audit/reports/CLAIMS_LOCK_2026_07_17.md

## Contribution Principles

- Keep dependency direction strict: core -> domain -> application -> infrastructure -> presentation.
- Do not bypass domain ports by wiring external libraries directly inside use cases.
- Preserve deterministic behavior in validation flows where deterministic mode already exists.
- Treat auditability as a feature: new behavior should be explainable in report artifacts.
- Keep diffs focused and reviewable.
- Do not claim customer accuracy, CDE-ready BCF, MEP system clash, or calculation *correctness* without evidence cited in [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](audit/reports/CLAIMS_LOCK_2026_07_17.md).

## Local Setup

```bash
cd backend
python3.12 -m venv .venv   # Windows: py -3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,raster]"
```

Optional local hooks (do not rewrite authorship metadata):

```bash
git config core.hooksPath .githooks
```

Optional extras:

```bash
pip install -e ".[clash]"
pip install -e ".[enterprise]"
```

## Validation Baseline

Run before opening a pull request:

```bash
cd backend
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
```

If formatting fails:

```bash
python -m ruff format src tests
```

## Git Commits (honest authorship)

Keep commit authorship truthful. If an AI assistant materially contributed, prefer an explicit `Co-authored-by:` trailer (or an equivalent honest note in the commit body). Do not strip or rewrite provenance trailers.

1. Commit from your shell or the VS Code task **AeroBIM: commit**.
2. Or run:

```powershell
cd AeroBIM
powershell -ExecutionPolicy Bypass -File scripts/git_commit.ps1 -Message "type: description"
```

Optional hooks: `git config core.hooksPath .githooks` (pass-through; does not erase co-authors).

## Pull Request Checklist

1. Describe the problem and the decision, not only the code diff.
2. Include executed validation commands and outcomes.
3. Update docs when behavior, API, contracts, or operational guidance changes.
4. Add or update tests for bug fixes and new capability.
5. Do not commit secrets, private models, customer data, or local environment files.

## API and Contract Changes

For public API or report-contract changes:

- keep backward-compatibility intent explicit;
- document OpenAPI via the live `/openapi.json` endpoint (do not commit generated OpenAPI dumps);
- highlight migration impact in the PR description.

## License

By contributing, you agree that your contributions are provided under the MIT License.
