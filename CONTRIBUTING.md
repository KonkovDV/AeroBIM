# Contributing to AeroBIM

Thank you for improving AeroBIM.

AeroBIM is an open-source platform for cross-modal BIM validation. Contributions should preserve deterministic behavior, explicit provenance, and clean architecture boundaries.

## Read First

1. README.md
2. docs/06-architecture-reference.md
3. docs/09-implementation-and-verification-rails.md
4. docs/15-local-quality-gate.md
5. SECURITY.md

## Contribution Principles

- Keep dependency direction strict: core -> domain -> application -> infrastructure -> presentation.
- Do not bypass domain ports by wiring external libraries directly inside use cases.
- Preserve deterministic behavior in validation flows where deterministic mode already exists.
- Treat auditability as a feature: new behavior should be explainable in report artifacts.
- Keep diffs focused and reviewable.

## Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,vision]"
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

## Pull Request Checklist

1. Describe the problem and the decision, not only the code diff.
2. Include executed validation commands and outcomes.
3. Update docs when behavior, API, contracts, or operational guidance changes.
4. Add or update tests for bug fixes and new capability.
5. Do not commit secrets, private models, customer data, or local environment files.

## API and Contract Changes

For public API or report-contract changes:

- keep backward-compatibility intent explicit;
- update docs/openapi.json and related API documentation;
- highlight migration impact in the PR description.

## License

By contributing, you agree that your contributions are provided under the MIT License.
